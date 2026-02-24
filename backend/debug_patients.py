import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import User, Patient

print("=== USERS ===")
users = User.objects.all()
for u in users:
    print(f"  {u.id}: {u.username} (role={u.role}, phc_id={u.phc_id})")

print(f"\n=== PATIENTS ===")
print(f"Total patients: {Patient.objects.count()}")

# Get unique PHC IDs from patients
from django.db.models import Q
phcs = set()
for p in Patient.objects.all():
    phcs.add(p.phc_id)
print(f"PHCs with patients: {sorted(phcs)}")

# Count by PHC
for phc_id in sorted(phcs):
    count = Patient.objects.filter(phc_id=phc_id).count()
    print(f"  {phc_id}: {count} patients")
