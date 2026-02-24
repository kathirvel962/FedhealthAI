#!/usr/bin/env python
"""
Simple test of combined database queries
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

import requests
import json

BASE_URL = "http://localhost:8000/api"

# Login
print("Step 1: Logging in...")
login_data = {"username": "phc1_user", "password": "password123"}
response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
token = response.json().get('token')
headers = {"Authorization": f"Bearer {token}"}
print(f"OK - Token obtained")

# Get patient count
print("\nStep 2: Getting patient count...")
response = requests.get(f"{BASE_URL}/phc/patients/", headers=headers)
data = response.json()
count = data.get('count', 0)
print(f"OK - Patient count: {count}")

# Get just first patient to see data
print("\nStep 3: Checking first patient record...")
if data.get('patients'):
    first_patient = data['patients'][0]
    print(f"Patient found: {first_patient.get('id')}, Disease: {first_patient.get('disease_label')}")
else:
    print("No patients found")

# Test authenticated endpoint without auth
print("\nStep 4: Testing cohort history (with auth)...")
response = requests.get(f"{BASE_URL}/cohort/history/", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Snapshots: {len(data.get('snapshots', []))}")
else:
    print(f"Error: {response.text[:100]}")

print("\nDone")
