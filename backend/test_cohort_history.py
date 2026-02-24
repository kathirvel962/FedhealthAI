#!/usr/bin/env python
"""
Test the cohort history endpoint fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

import requests
import json
from api.models import User
from rest_framework_simplejwt.tokens import RefreshToken

BASE_URL = "http://localhost:8000/api"

def get_user_token(username):
    """Get JWT token for a user"""
    try:
        user = User.objects.get(username=username)
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    except User.DoesNotExist:
        print(f"❌ User {username} not found")
        return None

def test_cohort_history():
    """Test the cohort history endpoint"""
    print("=" * 70)
    print("TESTING COHORT HISTORY ENDPOINT")
    print("=" * 70)
    
    # Get token
    token = get_user_token("phc1_user")
    if not token:
        print("❌ Could not get token for phc1_user")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test cohort history endpoint
    print("\n📌 Testing GET /api/cohort/history/...")
    try:
        response = requests.get(f"{BASE_URL}/cohort/history/", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Response successful (Status 200)")
            data = response.json()
            
            # Check response structure
            if isinstance(data, dict) and 'snapshots' in data:
                snapshots = data.get('snapshots', [])
                print(f"✅ Response contains 'snapshots' field with {len(snapshots)} items")
                
                if snapshots:
                    # Display first snapshot
                    snapshot = snapshots[0]
                    print(f"\n📊 First Snapshot:")
                    print(f"  - Snapshot Date: {snapshot.get('snapshot_date')}")
                    print(f"  - Total Patients: {snapshot.get('total_patients')}")
                    print(f"  - Average Age: {snapshot.get('average_age')}")
                    print(f"  - Fever Percentage: {snapshot.get('fever_percentage')}%")
                    print(f"  - Cough Percentage: {snapshot.get('cough_percentage')}%")
                    print(f"  - Average Temperature: {snapshot.get('average_temperature_c')}°C")
                    print(f"  - Average Heart Rate: {snapshot.get('average_heart_rate')} bpm")
                    print(f"  - Disease Distribution: {snapshot.get('disease_distribution')}")
                    print("\n✅ Cohort history endpoint is working correctly!")
                    return True
                else:
                    print("ℹ️  No snapshots returned (database may be empty)")
                    return True
            else:
                print(f"❌ Unexpected response format: {json.dumps(data, indent=2)[:200]}...")
                return False
        else:
            print(f"❌ Status Code {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the Django server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cohort_history()
    print("\n" + "=" * 70)
    if success:
        print("✅ COHORT HISTORY ENDPOINT TEST PASSED")
    else:
        print("❌ COHORT HISTORY ENDPOINT TEST FAILED")
    print("=" * 70)
