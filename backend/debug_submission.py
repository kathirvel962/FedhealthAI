#!/usr/bin/env python
"""Debug patient submission and user setup"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import User, Patient
from api.authentication import hash_password

print("=== CHECKING USER SETUP ===")
for user in User.objects:
    print(f"Username: {user.username}, Role: {user.role}, PHC_ID: {user.phc_id}")

print(f"\n=== PATIENT DATA ===")
print(f"Total patients: {Patient.objects.count()}")

phc_ids = set(p.phc_id for p in Patient.objects.all())
print(f"PHC IDs in database: {sorted(phc_ids)}")

# Check specific PHC
phc1_patients = Patient.objects.filter(phc_id='PHC1').count()
print(f"PHC1 patients: {phc1_patients}")

# Check if any patients were created for test PHCs
for phc_id in ['PHC_1', 'PHC_2', 'PHC_3', 'PHC_4', 'PHC_5']:
    count = Patient.objects.filter(phc_id=phc_id).count()
    if count > 0:
        print(f"{phc_id}: {count} patients")

print("\n=== CHECKING USER PHCID FORMAT ===")
# Check test user
test_user = User.objects.filter(username='phc1_user').first()
if test_user:
    print(f"phc1_user has phc_id: '{test_user.phc_id}' (type: {type(test_user.phc_id)})")
