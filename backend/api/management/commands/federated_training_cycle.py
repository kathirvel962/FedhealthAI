"""
Django management command for periodic federated training cycle.

Usage:
    python manage.py federated_training_cycle [--aggressive]

Options:
    --aggressive: Train all PHCs regardless of thresholds (once per 24h max)
"""

from django.core.management.base import BaseCommand
from api.models import Patient, LocalModel
from api.ml_utils import (
    should_trigger_local_training,
    should_trigger_global_aggregation,
    train_federated_model,
    try_automatic_aggregation,
    get_latest_global_model
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run federated training cycle for all PHCs with proper versioning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aggressive',
            action='store_true',
            help='Train all PHCs with sufficient data',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting federated training cycle...'))
        self.stdout.write("="*70)
        
        phc_ids = ['PHC1', 'PHC2', 'PHC3', 'PHC4']
        trained_phcs = []
        
        # PHASE 1: LOCAL TRAINING
        self.stdout.write(self.style.WARNING('\n[PHASE 1] LOCAL TRAINING'))
        self.stdout.write("-"*70)
        
        for phc_id in phc_ids:
            should_train, trigger_reason = should_trigger_local_training(phc_id)
            patient_count = Patient.objects.filter(phc_id=phc_id).count()
            
            self.stdout.write(f"\n{phc_id}:")
            self.stdout.write(f"  • Patients: {patient_count}")
            self.stdout.write(f"  • Should train: {should_train} ({trigger_reason})")
            
            if should_train:
                self.stdout.write(self.style.WARNING(f"  → Training..."))
                result = train_federated_model(phc_id, trigger_reason=trigger_reason)
                
                if result.get('error'):
                    self.stdout.write(self.style.ERROR(f"    ✗ Error: {result['error']}"))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"    ✓ {result['version_string']} (Accuracy: {result['accuracy']:.4f})"
                    ))
                    trained_phcs.append({
                        'phc_id': phc_id,
                        'version_string': result['version_string'],
                        'accuracy': result['accuracy'],
                        'ml_insights': result.get('ml_insights', {})
                    })
                    
                    # Show ML insights
                    ml_insights = result.get('ml_insights', {})
                    if ml_insights:
                        self.stdout.write(self.style.WARNING("  📊 ML Innovation Metrics:"))
                        
                        # Drift detection
                        drift = ml_insights.get('drift_detection', {})
                        if drift and not drift.get('error'):
                            if drift.get('drift_detected'):
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"    ⚠️  MODEL DRIFT: {drift.get('accuracy_drop_percentage', 0):.1f}% accuracy drop"
                                    )
                                )
                                self.stdout.write(
                                    f"       Previous: {drift.get('previous_accuracy', 0):.4f} → Current: {drift.get('current_accuracy', 0):.4f}"
                                )
                            else:
                                self.stdout.write(
                                    self.style.SUCCESS("    ✓ No model drift detected")
                                )
                        
                        # Risk score
                        risk = ml_insights.get('composite_risk_score', {})
                        if risk and not risk.get('error'):
                            severity = risk.get('severity', 'UNKNOWN')
                            severity_style = {
                                'HIGH': self.style.ERROR,
                                'MEDIUM': self.style.WARNING,
                                'LOW': self.style.SUCCESS,
                            }.get(severity, self.style.WARNING)
                            
                            self.stdout.write(
                                severity_style(
                                    f"    🔴 RISK SCORE: {risk.get('risk_score', 0):.1f}/100 [{severity}]"
                                )
                            )
                            self.stdout.write(
                                f"       Fever: {risk.get('fever_percentage', 0):.1f}% | "
                                f"Predictions: {risk.get('positive_predictions_percentage', 0):.1f}% | "
                                f"WBC Abnormal: {risk.get('abnormal_wbc_ratio', 0):.1f}%"
                            )
        
        # PHASE 2: CHECK FOR AGGREGATION
        self.stdout.write(self.style.WARNING('\n[PHASE 2] GLOBAL AGGREGATION'))
        self.stdout.write("-"*70)
        
        should_aggregate, reason, pending_phcs = should_trigger_global_aggregation()
        self.stdout.write(f"\nPending PHCs: {pending_phcs}")
        self.stdout.write(f"Should aggregate: {should_aggregate} ({reason})")
        
        aggregation_result = None
        if should_aggregate:
            self.stdout.write(self.style.WARNING("  → Aggregating..."))
            aggregation_result = try_automatic_aggregation()
            
            if aggregation_result:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ {aggregation_result['version_string']} (Accuracy: {aggregation_result['accuracy']:.4f})"
                ))
                self.stdout.write(f"    Contributors: {', '.join(aggregation_result['contributors'])}")
            else:
                self.stdout.write(self.style.ERROR("  ✗ Aggregation failed"))
        
        # SUMMARY
        latest_global = get_latest_global_model()
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("[SUMMARY]"))
        self.stdout.write("-"*70)
        self.stdout.write(f"Local models trained: {len(trained_phcs)}")
        if trained_phcs:
            for item in trained_phcs:
                self.stdout.write(f"  • {item['phc_id']}: {item['version_string']}")
        
        if aggregation_result:
            self.stdout.write(f"\nGlobal model created: {aggregation_result['version_string']}")
            self.stdout.write(f"  • Accuracy: {aggregation_result['accuracy']:.4f}")
            self.stdout.write(f"  • Contributors: {len(aggregation_result['contributors'])}")
        else:
            if latest_global:
                self.stdout.write(f"Latest global model: {latest_global.version_string}")
                self.stdout.write(f"  • Accuracy: {latest_global.accuracy:.4f}")
                self.stdout.write(f"  • Contributors: {len(latest_global.contributors)}")
        
        # ML Innovation Summary
        self.stdout.write(self.style.WARNING("\n[ML INNOVATION METRICS]"))
        self.stdout.write("-"*70)
        
        phcs_with_drift = [item for item in trained_phcs if item['ml_insights'].get('drift_detection', {}).get('drift_detected')]
        if phcs_with_drift:
            self.stdout.write(self.style.ERROR(f"PHCs with Model Drift: {len(phcs_with_drift)}"))
            for item in phcs_with_drift:
                drift = item['ml_insights'].get('drift_detection', {})
                self.stdout.write(
                    f"  • {item['phc_id']}: {drift.get('accuracy_drop_percentage', 0):.1f}% drop"
                )
        else:
            self.stdout.write(self.style.SUCCESS("✓ No model drift detected in any PHC"))
        
        phcs_with_high_risk = [item for item in trained_phcs if item['ml_insights'].get('composite_risk_score', {}).get('severity') == 'HIGH']
        if phcs_with_high_risk:
            self.stdout.write(self.style.ERROR(f"\nPHCs with HIGH Risk Score: {len(phcs_with_high_risk)}"))
            for item in phcs_with_high_risk:
                risk = item['ml_insights'].get('composite_risk_score', {})
                self.stdout.write(
                    f"  • {item['phc_id']}: {risk.get('risk_score', 0):.1f}/100"
                )
        
        self.stdout.write("\n" + "="*70)
