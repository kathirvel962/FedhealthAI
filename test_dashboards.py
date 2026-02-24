import urllib.request, json

print("Testing Dashboard Endpoints...")
print("-" * 40)

# Test all three user roles
tests = [
    ('phc1_user', 'phc'),
    ('surveillance_officer', 'surveillance'),
    ('admin_user', 'district')
]

for username, endpoint in tests:
    try:
        # Login
        login_req = urllib.request.Request(
            'http://localhost:8000/api/auth/login/',
            data=json.dumps({'username': username, 'password': 'password123'}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        token = json.load(urllib.request.urlopen(login_req))['token']
        
        # Test dashboard endpoint
        req = urllib.request.Request(
            f'http://localhost:8000/api/dashboards/{endpoint}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        response = urllib.request.urlopen(req)
        data = json.load(response)
        print(f'✓ {endpoint.capitalize():15} Dashboard: 200 OK')
        
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()[:100]
        print(f'✗ {endpoint.capitalize():15} Dashboard: HTTP {e.code} - {error_msg}')
    except Exception as e:
        print(f'✗ {endpoint.capitalize():15} Dashboard: {str(e)[:50]}')

print("-" * 40)
print("All tests completed!")
