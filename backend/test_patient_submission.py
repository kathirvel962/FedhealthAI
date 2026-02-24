#!/usr/bin/env python
"""Test patient submission workflow"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import User, Patient
from api.authentication import hash_password, generate_token
from rest_framework.test import APIClient
from django.test import RequestFactory

print("=== TESTING PATIENT SUBMISSION ===\n")

# Get or create test user
user = User.objects(username='phc1_user').first()
if not user:
    user = User.objects.create(
        username='phc1_test',
        password_hash=hash_password('password123'),
        role='PHC_USER',
        phc_id='PHC1'
    )
    print(f"Created test user: {user.username} with phc_id={user.phc_id}")
else:
    print(f"Using existing user: {user.username} with phc_id={user.phc_id}")

# Generate token
token = generate_token(str(user.id))
print(f"Generated token: {token[:50]}...")

# Create API client
client = APIClient()

# Test patient submission
patient_data = {
    'age': 35,
    'gender': 'Male',
    'fever': 1,
    'cough': 0,
    'fatigue': 1,
    'headache': 0,
    'vomiting': 0,
    'breathlessness': 0,
    'temperature_c': 38.5,
    'heart_rate': 88,
    'bp_systolic': 130,
    'wbc_count': 7500,
    'platelet_count': 250000,
    'hemoglobin': 14.2,
    'disease_label': 'Viral Fever',
    'severity_level': 'Medium'
}

print(f"\n=== SUBMITTING PATIENT ===")
print(f"Using endpoint: /api/phc/patient/")
print(f"Patient data: {json.dumps(patient_data, indent=2)}")

response = client.post(
    '/api/phc/patient/',
    data=json.dumps(patient_data),
    HTTP_AUTHORIZATION=f'Bearer {token}',
    content_type='application/json'
)

print(f"\nResponse status: {response.status_code}")
print(f"Response data: {response.data if hasattr(response, 'data') else response.content}")

if response.status_code == 201:
    print("\n✅ Patient submitted successfully!")
    
    # Now try to retrieve the patient
    print("\n=== RETRIEVING PATIENTS ===")
    patients_response = client.get(
        '/api/phc/patients/',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    
    print(f"Response status: {patients_response.status_code}")
    if hasattr(patients_response, 'data'):
        print(f"Total patients: {patients_response.data.get('count', '?')}")
        if patients_response.data.get('patients'):
            print(f"Sample patient: {patients_response.data['patients'][0] if patients_response.data['patients'] else 'None'}")
    
else:
    print(f"\n❌ Patient submission failed!")
    print(f"Error: {response.data if hasattr(response, 'data') else response.content}")

# Check database directly
print(f"\n=== DATABASE CHECK ===")
phc1_patients = Patient.objects.filter(phc_id='PHC1')
print(f"Total PHC1 patients in database: {phc1_patients.count()}")
