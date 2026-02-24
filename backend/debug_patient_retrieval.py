#!/usr/bin/env python
"""
Debug patient retrieval issue
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

import requests
import json
from pymongo import MongoClient

BASE_URL = "http://localhost:8000/api"

def debug_patient_retrieval():
    """Debug why patient count isn't updating"""
    print("=" * 70)
    print("DEBUG: PATIENT RETRIEVAL ISSUE")
    print("=" * 70)
    
    # Step 1: Start Django request to check user setup
    print("\n📌 Step 1: Check user setup")
    
    login_data = {"username": "phc1_user", "password": "password123"}
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json().get('token')
    print(f"✅ Token obtained")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get user info
    user_response = requests.get(f"{BASE_URL}/phc/patients/", headers=headers)
    print(f"✅ PHC Patients API response: {user_response.status_code}")
    
    # Step 2: Check database directly
    print("\n📌 Step 2: Check MongoDB directly")
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['fedhealth_db']
    
    # Check patients collection
    patients_col = db['patients']
    total_patients = patients_col.count_documents({})
    print(f"✅ Total patients in DB: {total_patients}")
    
    # Check patients for PHC1
    phc1_patients = patients_col.count_documents({'phc_id': 'PHC1'})
    print(f"✅ Patients with phc_id='PHC1': {phc1_patients}")
    
    # Check users to see what phc_id the logged-in user has
    users_col = db['users']
    phc1_user = users_col.find_one({'username': 'phc1_user'})
    if phc1_user:
        print(f"✅ phc1_user record found:")
        print(f"   - phc_id: {phc1_user.get('phc_id')}")
        print(f"   - role: {phc1_user.get('role')}")
    else:
        print(f"❌ phc1_user not found in DB")
    
    # Show sample recent patients
    print("\n📌 Step 3: Check recent patients in DB")
    recent_patients = list(patients_col.find({}).sort('created_at', -1).limit(5))
    print(f"✅ Recent patients:")
    for p in recent_patients:
        print(f"   - ID: {p.get('_id')}, PHC: {p.get('phc_id')}, Disease: {p.get('disease_label')}")
    
    # Step 4: Check API response structure
    print("\n📌 Step 4: Check API response structure")
    
    patient_data = user_response.json()
    print(f"✅ API Response keys: {list(patient_data.keys())}")
    print(f"✅ Response data: {json.dumps(patient_data, indent=2)[:300]}...")

if __name__ == "__main__":
    try:
        debug_patient_retrieval()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
