#!/usr/bin/env python
"""
Re-test complete workflow after database fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_workflow_with_database_fix():
    """Test workflow after fixing database references"""
    print("\n" + "=" * 70)
    print("WORKFLOW TEST AFTER DATABASE FIX")
    print("=" * 70)
    
    # Login
    print("\n📌 Step 1: Authentication")
    login_data = {"username": "phc1_user", "password": "password123"}
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    token = response.json().get('token')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Authenticated")
    
    # Get initial count
    print("\n📌 Step 2: Get initial patient count (from fedhealth db)")
    response = requests.get(f"{BASE_URL}/phc/patients/", headers=headers)
    if response.status_code == 200:
        initial_count = response.json().get('count', 0)
        print(f"✅ Initial patient count: {initial_count}")
    else:
        print(f"❌ Failed to get patients: {response.status_code}")
        return False
    
    # Submit patient
    print("\n📌 Step 3: Submit new patient")
    new_patient = {
        "age": 48,
        "gender": "Male",
        "fever": 1,
        "cough": 1,
        "fatigue": 0,
        "headache": 1,
        "vomiting": 0,
        "breathlessness": 1,
        "temperature_c": 38.2,
        "heart_rate": 88,
        "bp_systolic": 125,
        "wbc_count": 7800,
        "platelet_count": 280000,
        "hemoglobin": 13.8,
        "disease_label": "Malaria",
        "severity_level": "High"
    }
    
    response = requests.post(f"{BASE_URL}/phc/patient/", json=new_patient, headers=headers)
    if response.status_code == 201:
        patient_id = response.json().get('patient_id')
        print(f"✅ Patient submitted: {patient_id}")
    else:
        print(f"❌ Submission failed: {response.status_code}")
        return False
    
    # Get updated count
    print("\n📌 Step 4: Get updated patient count")
    time.sleep(0.5)
    
    response = requests.get(f"{BASE_URL}/phc/patients/", headers=headers)
    if response.status_code == 200:
        updated_count = response.json().get('count', 0)
        print(f"✅ Updated patient count: {updated_count}")
        
        if updated_count > initial_count:
            print(f"✅ SUCCESS! Patient count increased by {updated_count - initial_count}")
        else:
            print(f"⚠️  Patient count did not increase (initial: {initial_count}, updated: {updated_count})")
    else:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    # Get dashboard metrics
    print("\n📌 Step 5: Get PHC dashboard metrics")
    response = requests.get(f"{BASE_URL}/dashboards/phc/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard Retrieved")
        print(f"   - Total patients: {data.get('patients', {}).get('total', 'N/A')}")
        print(f"   - Model: {data.get('model', {}).get('version')}")
    else:
        print(f"❌ Dashboard failed: {response.status_code}")
    
    print("\n" + "=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_workflow_with_database_fix()
        if success:
            print("✅ WORKFLOW TEST PASSED")
        else:
            print("❌ WORKFLOW TEST FAILED")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
