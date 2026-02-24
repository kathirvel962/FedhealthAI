import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import LocalModel, GlobalModel, TrainingMetadata, Alert

print("="*60)
print("CROSS-MODEL FORMAT VALIDATION")
print("="*60)

# Check LocalModel phc_id formats
print("\n1. LOCAL MODEL PHC_ID FORMAT:")
print("-" * 60)
local_models = list(LocalModel.objects[:10])
phc_id_formats = set()
format_mismatches = []

for model in local_models:
    phc_id_formats.add(model.phc_id)
    if not model.phc_id.startswith('PHC_'):
        format_mismatches.append(f"LocalModel v{model.version_string}: phc_id='{model.phc_id}' (should be PHC_X)")

for fmt in sorted(phc_id_formats):
    count = LocalModel.objects.filter(phc_id=fmt).count()
    print(f"  {fmt}: {count} models")

if format_mismatches:
    print(f"\n⚠️  MISMATCH FOUND: {len(format_mismatches)} LocalModels with wrong phc_id format")
    for msg in format_mismatches[:5]:
        print(f"    - {msg}")
else:
    print("\n✓ All LocalModels have correct phc_id format")

# Check GlobalModel format
print("\n2. GLOBAL MODEL CONTENTS:")
print("-" * 60)
global_models = list(GlobalModel.objects[:5])
if global_models:
    for gm in global_models:
        print(f"  v{gm.version} ({gm.version_string}):")
        print(f"    Contributors: {gm.contributors}")
        print(f"    Contributor versions: {gm.contributor_versions}")
else:
    print("  No global models found")

# Check TrainingMetadata format
print("\n3. TRAINING METADATA PHC_ID FORMAT:")
print("-" * 60)
training_meta = list(TrainingMetadata.objects)
for tm in training_meta:
    mismatch = "" if tm.phc_id.startswith('PHC_') else " ⚠️ MISMATCH"
    print(f"  {tm.phc_id}: patients_since={tm.patients_since_last_training}{mismatch}")

# Check Alert format
print("\n4. ALERTS PHC_ID FORMAT:")
print("-" * 60)
alerts = list(Alert.objects[:10])
alert_phc_formats = set()
for alert in alerts:
    alert_phc_formats.add(alert.phc_id)

for fmt in sorted(alert_phc_formats):
    count = Alert.objects.filter(phc_id=fmt).count()
    print(f"  {fmt}: {count} alerts")

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
print("\nKEY ISSUES TO FIX:")

issues = []

# Check LocalModel vs Patient phc_id mismatch
local_phc_count = len(phc_id_formats)
if any(f.startswith('PHC_') for f in phc_id_formats):
    issues.append("✓ LocalModel phc_ids are correctly formatted (PHC_X)")
else:
    issues.append("⚠️  LocalModel phc_ids have OLD format (PHC1 instead of PHC_1)")

if issues:
    for issue in issues:
        print(f"  {issue}")
