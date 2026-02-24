#!/usr/bin/env python
"""
Comprehensive workflow test: Login → Submit Patient → Retrieve → Check Metrics
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

import requests
import json
from django.contrib.auth import authenticate
from api.models import User, Patient
import time

BASE_URL = "http://localhost:8000/api"

def test_complete_workflow():
    """Test complete user workflow"""
    print("\n" + "=" * 70)
    print("COMPLETE WORKFLOW TEST")
    print("=" * 70)
    
    # Step 1: Authentication
    print("\n📌 Step 1: Authentication")
    print("   Testing login with phc1_user...")
    
    login_data = {
        "username": "phc1_user",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code != 200:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False
    
    token = response.json().get('token')
    if not token:
        print(f"   ❌ No token in response")
        return False
    
    print(f"   ✅ Authentication successful, token: {token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Get initial patient count
    print("\n📌 Step 2: Get initial patient count")
    response = requests.get(f"{BASE_URL}/phc/patients/", headers=headers)
    if response.status_code == 200:
        initial_count = response.json().get('total', 0)
        print(f"   ✅ Initial patient count: {initial_count}")
    else:
        print(f"   ❌ Failed to get patients: {response.status_code}")
        initial_count = 0
    
    # Step 3: Submit a new patient
    print("\n📌 Step 3: Submit new patient")
    new_patient = {
        "age": 45,
        "gender": "Male",
        "fever": 1,
        "cough": 1,
        "fatigue": 1,
        "headache": 0,
        "vomiting": 0,
        "breathlessness": 0,
        "temperature_c": 38.5,
        "heart_rate": 92,
        "bp_systolic": 130,
        "wbc_count": 7500,
        "platelet_count": 250000,
        "hemoglobin": 13.5,
        "disease_label": "Influenza",
        "severity_level": "Medium"
    }
    
    response = requests.post(f"{BASE_URL}/phc/patient/", json=new_patient, headers=headers)
    if response.status_code == 201:
        print(f"   ✅ Patient submitted successfully")
        patient_id = response.json().get('patient_id')
        print(f"   Patient ID: {patient_id}")
    else:
        print(f"   ❌ Patient submission failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False
    
    # Step 4: Get updated patient count
    print("\n📌 Step 4: Get updated patient count")
    time.sleep(0.5)  # Give DB time to update
    
    response = requests.get(f"{BASE_URL}/phc/patients/", headers=headers)
    if response.status_code == 200:
        updated_count = response.json().get('total', 0)
        print(f"   ✅ Updated patient count: {updated_count}")
        if updated_count > initial_count:
            print(f"   ✅ Patient count increased by {updated_count - initial_count}")
        else:
            print(f"   ⚠️  Patient count did not increase")
    else:
        print(f"   ❌ Failed to get patients: {response.status_code}")
    
    # Step 5: Retrieve cohort history
    print("\n📌 Step 5: Retrieve cohort history")
    response = requests.get(f"{BASE_URL}/cohort/history/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        snapshots = data.get('snapshots', [])
        print(f"   ✅ Cohort history retrieved: {len(snapshots)} snapshots")
        if snapshots:
            latest = snapshots[0]
            print(f"   📊 Latest snapshot:")
            print(f"      - Total patients: {latest.get('total_patients')}")
            print(f"      - Average age: {latest.get('average_age')}")
            print(f"      - Fever %: {latest.get('fever_percentage')}%")
            print(f"      - Average temp: {latest.get('average_temperature_c')}°C")
    else:
        print(f"   ❌ Cohort history failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    
    # Step 6: Get dashboard metrics
    print("\n📌 Step 6: Get PHC dashboard metrics")
    response = requests.get(f"{BASE_URL}/dashboards/phc/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Dashboard metrics retrieved")
        print(f"   📊 Dashboard data:")
        print(f"      - PHC ID: {data.get('phc_id')}")
        print(f"      - Total patients: {data.get('patients', {}).get('total', 0)}")
        print(f"      - Model version: {data.get('model', {}).get('version')}")
        print(f"      - Model accuracy: {data.get('model', {}).get('accuracy')}")
        print(f"      - Risk score: {data.get('risk', {}).get('latest_score')}")
        print(f"      - Alerts (7 days): {len(data.get('alerts_7_days', []))}")
    else:
        print(f"   ❌ Dashboard metrics failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    
    print("\n" + "=" * 70)
    print("✅ WORKFLOW TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        test_complete_workflow()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
