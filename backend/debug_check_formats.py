import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import Patient

# Get first 10 patients and show their phc_id
print("First 10 patients:")
try:
    patients = list(Patient.objects[:10])
    for i, p in enumerate(patients):
        print(f"  {i+1}. phc_id: '{p.phc_id}', disease_label: '{p.disease_label}'")
except Exception as e:
    print(f"Error: {e}")

# Check both formats
for phc_format in ['PHC1', 'PHC_1', 'PHC-1']:
    count = Patient.objects.filter(phc_id=phc_format).count()
    if count > 0:
        print(f"\nFound {count} patients with phc_id={phc_format}")
