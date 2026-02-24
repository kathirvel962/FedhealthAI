import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import Patient, User, LocalModel, GlobalModel, TrainingMetadata
import json

print("="*60)
print("DATA FORMAT VALIDATION CHECK")
print("="*60)

# Check Patient model
print("\n1. PATIENT MODEL FIELDS:")
print("-" * 60)
patient_sample = Patient.objects.first()
if patient_sample:
    print("Sample Patient Document:")
    for field, value in patient_sample.to_mongo().items():
        print(f"  {field}: {type(value).__name__:15} = {str(value)[:50]}")
else:
    print("  No patients found")

# Check User model
print("\n2. USER MODEL FIELDS:")
print("-" * 60)
user_sample = User.objects.first()
if user_sample:
    print("Sample User Document:")
    for field, value in user_sample.to_mongo().items():
        print(f"  {field}: {type(value).__name__:15} = {str(value)[:50]}")
else:
    print("  No users found")

# Check LocalModel model
print("\n3. LOCAL MODEL FIELDS:")
print("-" * 60)
local_model_sample = LocalModel.objects.first()
if local_model_sample:
    print("Sample LocalModel Document:")
    for field, value in local_model_sample.to_mongo().items():
        if field == 'weights':
            print(f"  {field}: {type(value).__name__:15} (dict with keys)")
        else:
            print(f"  {field}: {type(value).__name__:15} = {str(value)[:50]}")
else:
    print("  No local models found")

# Validation checks
print("\n4. DATA INTEGRITY CHECKS:")
print("-" * 60)

# Check Patient field types
patients_checked = 0
field_issues = []

for p in Patient.objects[:100]:
    patients_checked += 1
    
    # Check age is int
    if not isinstance(p.age, int):
        field_issues.append(f"Patient {p.id}: age is {type(p.age).__name__}, expected int")
    
    # Check temperature_c is float
    if not isinstance(p.temperature_c, (int, float)):
        field_issues.append(f"Patient {p.id}: temperature_c is {type(p.temperature_c).__name__}, expected float")
    
    # Check binary fields (fever, cough, etc) are 0 or 1
    for field in ['fever', 'cough', 'fatigue', 'headache', 'vomiting', 'breathlessness']:
        val = getattr(p, field)
        if val not in [0, 1]:
            field_issues.append(f"Patient {p.id}: {field}={val}, expected 0 or 1")
    
    # Check phc_id format
    if not p.phc_id.startswith('PHC_'):
        field_issues.append(f"Patient {p.id}: phc_id='{p.phc_id}', expected PHC_X format")
    
    # Check disease_label is valid
    valid_diseases = ['Healthy', 'Viral Fever', 'Dengue', 'Malaria', 'Typhoid', 'Pneumonia']
    if p.disease_label not in valid_diseases:
        field_issues.append(f"Patient {p.id}: disease_label='{p.disease_label}', not in valid list")

print(f"Checked {patients_checked} patients")
if field_issues:
    print(f"Found {len(field_issues)} issues:")
    for issue in field_issues[:10]:  # Show first 10
        print(f"  - {issue}")
    if len(field_issues) > 10:
        print(f"  ... and {len(field_issues) - 10} more")
else:
    print("✓ All patient fields have correct types and values")

# Check User role values
print("\n5. USER ROLE VALIDATION:")
print("-" * 60)
role_counts = {}
valid_roles = ['PHC_USER', 'DISTRICT_ADMIN', 'SURVEILLANCE_OFFICER']
role_issues = []

for user in User.objects:
    if user.role not in valid_roles:
        role_issues.append(f"User {user.username}: role='{user.role}', not valid")
    role_counts[user.role] = role_counts.get(user.role, 0) + 1

for role in valid_roles:
    print(f"  {role}: {role_counts.get(role, 0)} users")

if role_issues:
    print(f"Found {len(role_issues)} role issues:")
    for issue in role_issues:
        print(f"  - {issue}")
else:
    print("✓ All user roles are valid")

print("\n" + "="*60)
