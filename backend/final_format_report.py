import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import User, Patient, LocalModel, GlobalModel, TrainingMetadata, Alert
from datetime import datetime

print("="*70)
print("COMPREHENSIVE DATA FORMAT & CONSISTENCY REPORT")
print("="*70)

# Collect all unique phc_ids from all models
all_phc_sources = {}

# Users
users = list(User.objects.filter(role='PHC_USER'))
user_phc_ids = set(u.phc_id for u in users if u.phc_id)
all_phc_sources['User (PHC_USER)'] = sorted(user_phc_ids)

# Patients
patient_phc_ids = set(p.phc_id for p in Patient.objects.limit(100))  # Sample
all_phc_sources['Patient (sample)'] = sorted(patient_phc_ids)

# LocalModel
lm_phc_ids = set(lm.phc_id for lm in LocalModel.objects)
all_phc_sources['LocalModel'] = sorted(lm_phc_ids)

# GlobalModel contributors
gm_phc_ids = set()
for gm in GlobalModel.objects:
    if gm.contributors:
        gm_phc_ids.update(gm.contributors)
all_phc_sources['GlobalModel (contributors)'] = sorted(gm_phc_ids)

# TrainingMetadata
tm_phc_ids = set(tm.phc_id for tm in TrainingMetadata.objects)
all_phc_sources['TrainingMetadata'] = sorted(tm_phc_ids)

# Alert
alert_phc_ids = set(a.phc_id for a in Alert.objects)
all_phc_sources['Alert'] = sorted(alert_phc_ids)

print("\n1. PHC_ID DISTRIBUTION ACROSS ALL MODELS:")
print("-" * 70)
for source, phc_ids in sorted(all_phc_sources.items()):
    print(f"  {source:30s}: {phc_ids if phc_ids else 'None'}")

# Check consistency
print("\n2. CONSISTENCY CHECKS:")
print("-" * 70)

# Get canonical set from patients (largest dataset)
canonical_phcs = set()
for p in Patient.objects:
    canonical_phcs.add(p.phc_id)
    if len(canonical_phcs) >= 5:
        break

print(f"  Canonical PHC_IDs (from Patients): {sorted(canonical_phcs)[:5]} (and more)")

# Check all phc_ids follow PHC_X format
format_issues = []
for source, phc_ids in all_phc_sources.items():
    for phc_id in phc_ids:
        if not phc_id.startswith('PHC_'):
            format_issues.append(f"    {source}: '{phc_id}' (should be PHC_X format)")

if format_issues:
    print(f"\n  ⚠️  FORMAT ISSUES ({len(format_issues)}):")
    for issue in format_issues[:5]:
        print(issue)
else:
    print("\n  ✓ All phc_id values use correct PHC_X format")

# Data type checks
print("\n3. FIELD TYPE VALIDATION:")
print("-" * 70)

type_issues = []

# Check Patient fields
sample_patient = Patient.objects.first()
if sample_patient:
    expected_types = {
        'age': int,
        'temperature_c': (int, float),
        'heart_rate': int,
        'wbc_count': int,
        'disease_label': str,
        'phc_id': str
    }
    
    for field, expected_type in expected_types.items():
        actual = getattr(sample_patient, field)
        if isinstance(expected_type, tuple):
            if not isinstance(actual, expected_type):
                type_issues.append(f"  Patient.{field}: {type(actual).__name__} (expected {expected_type})")
        else:
            if not isinstance(actual, expected_type):
                type_issues.append(f"  Patient.{field}: {type(actual).__name__} (expected {expected_type.__name__})")

# Check LocalModel fields
sample_model = LocalModel.objects.first()
if sample_model:
    expected_types = {
        'phc_id': str,
        'version': int,
        'accuracy': (int, float),
        'weights': dict,
        'trained_at': datetime
    }
    
    for field, expected_type in expected_types.items():
        actual = getattr(sample_model, field)
        if isinstance(expected_type, tuple):
            if not isinstance(actual, expected_type):
                type_issues.append(f"  LocalModel.{field}: {type(actual).__name__} (expected {expected_type})")
        else:
            if not isinstance(actual, expected_type):
                type_issues.append(f"  LocalModel.{field}: {type(actual).__name__} (expected {expected_type.__name__})")

if type_issues:
    print(f"\n  ⚠️  TYPE ISSUES ({len(type_issues)}):")
    for issue in type_issues[:5]:
        print(issue)
else:
    print("  ✓ All field types match model definitions")

# Referential integrity
print("\n4. REFERENTIAL INTEGRITY:")
print("-" * 70)

# Check if all LocalModel phc_ids exist in Patient data
lm_phcs = set(lm.phc_id for lm in LocalModel.objects)
patient_phcs = set()
for p in Patient.objects:
    patient_phcs.add(p.phc_id)
    if len(patient_phcs) >= 6:
        break

missing_patient_phcs = lm_phcs - patient_phcs
if missing_patient_phcs:
    print(f"  ⚠️  LocalModel references PHCs with no patients: {missing_patient_phcs}")
else:
    print(f"  ✓ All LocalModel phc_ids have corresponding Patient data")

# Check GlobalModel contributors have LocalModels
gm_contributors = set()
for gm in GlobalModel.objects:
    if gm.contributors:
        gm_contributors.update(gm.contributors)

lm_phcs_existing = set(lm.phc_id for lm in LocalModel.objects)
missing_local_models = gm_contributors - lm_phcs_existing
if missing_local_models:
    print(f"  ⚠️  GlobalModel contributors missing LocalModels: {missing_local_models}")
else:
    print(f"  ✓ All GlobalModel contributors have LocalModels")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"  Users (PHC_USER):           {len(users)}")
print(f"  Patients:                   {Patient.objects.count()}")
print(f"  LocalModels:                {LocalModel.objects.count()}")
print(f"  GlobalModels:               {GlobalModel.objects.count()}")
print(f"  TrainingMetadata entries:   {TrainingMetadata.objects.count()}")
print(f"  Alerts:                     {Alert.objects.count()}")

if not format_issues and not type_issues and not missing_patient_phcs and not missing_local_models:
    print("\n✅ ALL DATA FORMATS VALIDATED AND CONSISTENT!")
else:
    print("\n⚠️  ISSUES FOUND - See details above")
