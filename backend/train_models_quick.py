#!/usr/bin/env python
"""Quick model initialization for all PHCs"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import LocalModel, Patient
from api.ml_utils import train_federated_model
import logging

logging.basicConfig(level=logging.WARNING)

print("\n" + "="*70)
print("TRAINING LOCAL MODELS FOR ALL PHCS")
print("="*70)

phcs = ['PHC1', 'PHC2', 'PHC3', 'PHC4']

for phc_id in phcs:
    existing = LocalModel.objects.filter(phc_id=phc_id).count()
    patients = Patient.objects.filter(phc_id=phc_id).count()
    
    print(f"\n{phc_id}: {patients} patients, {existing} models")
    
    if patients == 0:
        print(f"  → Skipping (no patient data)")
        continue
    
    if existing > 0:
        print(f"  → Skipping (model already exists)")
        continue
    
    try:
        print(f"  ↓ Training model...")
        result = train_federated_model(phc_id, trigger_reason='INITIALIZATION')
        
        if result.get('error'):
            print(f"    ❌ {result['error']}")
        else:
            print(f"    ✅ SUCCESS - Accuracy: {result['accuracy']:.1%}, Samples: {result['num_samples']}")
    except Exception as e:
        print(f"    ❌ Exception: {str(e)}")

print("\n" + "="*70)
print("✅ COMPLETE - Refresh dashboard to see updated metrics")
print("="*70 + "\n")
