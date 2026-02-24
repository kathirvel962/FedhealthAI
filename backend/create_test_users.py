#!/usr/bin/env python
"""
Create test users for development and demo purposes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import User
from api.authentication import hash_password

# Demo users from LoginPage.jsx
demo_users = [
    {
        'username': 'admin_user',
        'password': 'password123',
        'role': 'DISTRICT_ADMIN',
        'phc_id': None,
    },
    {
        'username': 'phc1_user',
        'password': 'password123',
        'role': 'PHC_USER',
        'phc_id': 'PHC1',
    },
    {
        'username': 'phc2_user',
        'password': 'password123',
        'role': 'PHC_USER',
        'phc_id': 'PHC2',
    },
    {
        'username': 'surveillance_officer',
        'password': 'password123',
        'role': 'SURVEILLANCE_OFFICER',
        'phc_id': None,
    },
]

print("Creating test users...\n")

for user_data in demo_users:
    # Check if user exists
    existing = User.objects.filter(username=user_data['username']).first()
    if existing:
        print(f"✅ User '{user_data['username']}' already exists (role: {user_data['role']})")
        continue
    
    # Create user
    user = User.objects.create(
        username=user_data['username'],
        password_hash=hash_password(user_data['password']),
        role=user_data['role'],
        phc_id=user_data['phc_id'],
    )
    print(f"✅ Created user '{user_data['username']}' (role: {user_data['role']}, phc_id: {user_data['phc_id']})")

print("\n✅ Test users ready!")
print("\nDemo Credentials (use in LoginPage):")
for user_data in demo_users:
    print(f"  • {user_data['username']} / password123 ({user_data['role']})")
