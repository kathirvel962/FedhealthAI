#!/usr/bin/env python
"""
Verify seeded data is accessible via API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("VERIFYING SEEDED DATA VIA API")
print("=" * 70)

# Login
print("\n1. Authenticating as phc1_user")
login_data = {"username": "phc1_user", "password": "password123"}
response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
if response.status_code != 200:
    print(f"   FAILED: {response.status_code}")
    exit(1)

token = response.json().get('token')
headers = {"Authorization": f"Bearer {token}"}
print(f"   OK - Token obtained")

# Test each PHC endpoint
phcs = ['PHC1', 'PHC2', 'PHC3', 'PHC4', 'PHC5']

print("\n2. Checking patient counts per PHC")
print("   (switching users for each PHC)")

for phc in phcs:
    # Login as that PHC user
    login_data = {"username": f"phc{phcs.index(phc) + 1}_user", "password": "password123"}
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code != 200:
        print(f"   {phc}: Login failed")
        continue
    
    token = response.json().get('token')
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get patients
    response = requests.get(f"{BASE_URL}/phc/patients/", headers=headers)
    if response.status_code == 200:
        count = response.json().get('count', 0)
        print(f"   {phc}: {count} patients")
    else:
        print(f"   {phc}: Error {response.status_code}")

print("\n3. Sample patient from PHC1")
response = requests.get(f"{BASE_URL}/phc/patients/?limit=1", headers=headers)
if response.status_code == 200:
    patients = response.json().get('patients', [])
    if patients:
        p = patients[0]
        print(f"   ID: {p.get('id')}")
        print(f"   Age: {p.get('age')}, Gender: {p.get('gender')}")
        print(f"   Disease: {p.get('disease_label')}, Severity: {p.get('severity_level')}")
        print(f"   Fever: {p.get('fever')}, Cough: {p.get('cough')}, Temp: {p.get('temperature_c')}C")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
