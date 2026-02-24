#!/usr/bin/env python
"""
Test Dashboard Metrics endpoints with correct URLs
"""
import json
import urllib.request
import urllib.error

test_endpoints = [
    ("PHC Dashboard Metrics", "/api/dashboards/phc/"),
    ("District Dashboard Metrics", "/api/dashboards/district/"),
    ("Surveillance Dashboard Metrics", "/api/dashboards/surveillance/"),
    ("Cohort History", "/api/cohort/history/"),
]

print("=" * 70)
print("TESTING DASHBOARD METRICS ENDPOINTS")
print("=" * 70)

for name, endpoint in test_endpoints:
    url = f"http://localhost:8000{endpoint}"
    print(f"\n📌 Testing {name}")
    print(f"   GET {url}")
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            print(f"   ✅ Status: {response.status}")
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"   ⚠️  Status: {e.code} (authentication required - endpoint exists)")
        elif e.code == 403:
            print(f"   ⚠️  Status: {e.code} (forbidden - authentication required - endpoint exists)")
        elif e.code == 500:
            print(f"   ❌ Status: {e.code} (Internal Server Error)")
            try:
                error_msg = json.loads(e.read().decode())
                print(f"   Error details: {json.dumps(error_msg, indent=2)[:200]}")
            except:
                print(f"   Response: {e.read().decode()[:200]}")
        else:
            print(f"   ⚠️  Status: {e.code} ({e.reason})")
            
    except urllib.error.URLError as e:
        print(f"   ❌ Connection Error: {e.reason}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ Summary:")
print("   ✅ = Endpoint working")
print("   ⚠️  401/403  = Endpoint exists, requires auth")
print("   ❌ 500    = Endpoint error (needs fixing)")
print("=" * 70)
