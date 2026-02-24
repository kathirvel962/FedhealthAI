#!/usr/bin/env python
"""
Check where newly submitted patients are being stored
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

import requests
import json
from pymongo import MongoClient
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def check_patient_submission():
    """Check where newly submitted patients go"""
    print("=" * 70)
    print("CHECK: NEWLY SUBMITTED PATIENT STORAGE")
    print("=" * 70)
    
    # Login
    print("\n📌 Step 1: Login")
    login_data = {"username": "phc1_user", "password": "password123"}
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    token = response.json().get('token')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in")
    
    # Submit patient
    print("\n📌 Step 2: Submit patient")
    new_patient = {
        "age": 50,
        "gender": "Female",
        "fever": 1,
        "cough": 0,
        "fatigue": 1,
        "headache": 1,
        "vomiting": 0,
        "breathlessness": 0,
        "temperature_c": 37.5,
        "heart_rate": 85,
        "bp_systolic": 120,
        "wbc_count": 8000,
        "platelet_count": 300000,
        "hemoglobin": 14.0,
        "disease_label": "Dengue",
        "severity_level": "High"
    }
    
    submit_response = requests.post(f"{BASE_URL}/phc/patient/", json=new_patient, headers=headers)
    if submit_response.status_code == 201:
        submitted_patient_id = submit_response.json().get('patient_id')
        print(f"✅ Patient submitted: {submitted_patient_id}")
    else:
        print(f"❌ Submission failed: {submit_response.status_code}")
        return
    
    # Search database for the patient
    print("\n📌 Step 3: Search database for newly submitted patient")
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['fedhealth_db']
    patients_col = db['patients']
    
    # Search by recently submitted time
    recent = list(patients_col.find({
        'disease_label': 'Dengue',
        'phc_id': 'PHC1'
    }).sort('created_at', -1).limit(5))
    
    if recent:
        print(f"✅ Found {len(recent)} Dengue patients in PHC1:")
        for p in recent:
            print(f"   - ID: {p.get('_id')}, Created: {p.get('created_at')}")
            if str(p.get('_id')) == submitted_patient_id:
                print(f"   ✅ MATCHED newly submitted patient!")
    else:
        print(f"❌ No Dengue patients found in PHC1")
    
    # Check if there's a separate collection for new submissions
    print("\n📌 Step 4: Check all collections")
    collections = db.list_collection_names()
    for col_name in collections:
        if 'patient' in col_name.lower():
            col = db[col_name]
            count = col.count_documents({})
            print(f"✅ Collection '{col_name}': {count} documents")

if __name__ == "__main__":
    try:
        check_patient_submission()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
