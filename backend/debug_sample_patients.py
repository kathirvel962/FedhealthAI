import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import Patient

# Get first 5 patients and show their phc_id
print("First 10 patients:")
patients = list(Patient.objects[:10])
for p in patients:
    print(f"  ID: {p.id}, phc_id: {p.phc_id}, age: {p.age}, diagnosis: {p.diagnosis}")

# Get unique phc_ids by collecting them
phc_ids = set()
count = 0
for p in Patient.objects:
    if p.phc_id:
        phc_ids.add(p.phc_id)
    count += 1
    if count >= 100:  # Only look at first 100
        break

print(f"\nUnique phc_ids in first 100 patients: {sorted(phc_ids)}")
