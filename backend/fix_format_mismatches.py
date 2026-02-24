import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import LocalModel, GlobalModel, TrainingMetadata, Alert

print("="*60)
print("FIXING DATA FORMAT MISMATCHES")
print("="*60)

# Fix LocalModel phc_ids
print("\n1. FIXING LOCALMODEL PHC_IDS:")
print("-" * 60)
local_models = list(LocalModel.objects)
for lm in local_models:
    if not lm.phc_id.startswith('PHC_'):
        old_phc = lm.phc_id
        lm.phc_id = lm.phc_id.replace('PHC', 'PHC_')
        lm.save()
        print(f"  Updated: {old_phc} -> {lm.phc_id}")
print(f"Total LocalModels updated: {len(local_models)}")

# Fix GlobalModel contributors
print("\n2. FIXING GLOBALMODEL CONTRIBUTORS:")
print("-" * 60)
global_models = list(GlobalModel.objects)
for gm in global_models:
    updated = False
    # Fix contributors list
    if gm.contributors:
        new_contributors = [c.replace('PHC', 'PHC_') if not c.startswith('PHC_') else c for c in gm.contributors]
        if gm.contributors != new_contributors:
            print(f"  Updated v{gm.version} contributors: {gm.contributors} -> {new_contributors}")
            gm.contributors = new_contributors
            updated = True
    
    # Fix contributor_versions keys
    if gm.contributor_versions:
        new_versions = {}
        for k, v in gm.contributor_versions.items():
            new_k = k.replace('PHC', 'PHC_') if not k.startswith('PHC_') else k
            new_versions[new_k] = v
            if k != new_k:
                updated = True
        if updated:
            print(f"  Updated v{gm.version} contributor_versions keys")
            gm.contributor_versions = new_versions
    
    if updated:
        gm.save()
print(f"Total GlobalModels updated: {len([gm for gm in global_models if gm.contributors and any(not c.startswith('PHC_') for c in gm.contributors)])}")

# Fix TrainingMetadata phc_ids
print("\n3. FIXING TRAININGMETADATA PHC_IDS:")
print("-" * 60)
training_metas = list(TrainingMetadata.objects)
for tm in training_metas:
    if not tm.phc_id.startswith('PHC_'):
        old_phc = tm.phc_id
        tm.phc_id = tm.phc_id.replace('PHC', 'PHC_')
        tm.save()
        print(f"  Updated: {old_phc} -> {tm.phc_id}")
print(f"Total TrainingMetadata updated: {len(training_metas)}")

# Fix Alert phc_ids
print("\n4. FIXING ALERT PHC_IDS:")
print("-" * 60)
alerts = list(Alert.objects)
for alert in alerts:
    if not alert.phc_id.startswith('PHC_'):
        old_phc = alert.phc_id
        alert.phc_id = alert.phc_id.replace('PHC', 'PHC_')
        alert.save()
        print(f"  Updated: {old_phc} -> {alert.phc_id}")
print(f"Total Alerts updated: {len([a for a in alerts if not a.phc_id.startswith('PHC_')])}")

print("\n" + "="*60)
print("VERIFICATION")
print("="*60)

# Verify
lm_formats = set(lm.phc_id for lm in LocalModel.objects)
tm_formats = set(tm.phc_id for tm in TrainingMetadata.objects)
alert_formats = set(a.phc_id for a in Alert.objects)

print(f"\nLocalModel phc_ids: {sorted(lm_formats)}")
print(f"TrainingMetadata phc_ids: {sorted(tm_formats)}")
print(f"Alert phc_ids: {sorted(alert_formats)}")

all_correct = all(f.startswith('PHC_') for f in (lm_formats | tm_formats | alert_formats))
if all_correct:
    print("\n✓ All format mismatches fixed!")
else:
    print("\n⚠️  Some mismatches remain")
