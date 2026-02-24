import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import Patient

# Count by PHC using count()
for phc_id in ['PHC1', 'PHC2', 'PHC3', 'PHC4']:
    count = Patient.objects.filter(phc_id=phc_id).count()
    print(f"{phc_id}: {count} patients")
