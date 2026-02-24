#!/usr/bin/env python
"""
Simple test for cohort history endpoint - check if it returns data
"""
import json
import sys

# Test without Django setup - just HTTP request
try:
    import urllib.request
    import urllib.error
    
    url = "http://localhost:8000/api/cohort/history/"
    
    print("=" * 70)
    print("TESTING COHORT HISTORY ENDPOINT")
    print("=" * 70)
    print(f"\n📌 Testing GET {url}")
    
    try:
        # Try without authentication first
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"✅ Status: {response.status}")
            print(f"✅ Response has {len(data.get('snapshots', []))} snapshots")
            print(json.dumps(data, indent=2)[:500])
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"⚠️  Got 401 Unauthorized (expected - authentication required)")
            print("✅ Endpoint is responding (not a 500 error)")
        elif e.code == 500:
            print(f"❌ Got 500 Internal Server Error")
            print(f"Response: {e.read().decode()[:300]}")
        else:
            print(f"Got HTTP {e.code}: {e.reason}")
            print(f"Response: {e.read().decode()[:300]}")
            
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e.reason}")
        print("Is Django server running on port 8000?")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
