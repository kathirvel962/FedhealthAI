import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import Patient

# Verify the fix
for phc_id in ['PHC_1', 'PHC_2', 'PHC_3', 'PHC_4', 'PHC_5']:
    count = Patient.objects.filter(phc_id=phc_id).count()
    print(f"{phc_id}: {count} patients")

print(f"\nTotal: {Patient.objects.count()} patients")
