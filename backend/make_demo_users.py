#!/usr/bin/env python
"""Setup test users for demo"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import User
from api.authentication import hash_password

# Create or update demo users
users = [
    {'username': 'admin_user', 'password': 'password123', 'role': 'DISTRICT_ADMIN', 'phc_id': None},
    {'username': 'phc1_user', 'password': 'password123', 'role': 'PHC_USER', 'phc_id': 'PHC1'},
    {'username': 'phc2_user', 'password': 'password123', 'role': 'PHC_USER', 'phc_id': 'PHC2'},
    {'username': 'surveillance_officer', 'password': 'password123', 'role': 'SURVEILLANCE_OFFICER', 'phc_id': None},
]

print("Creating test users...")
for user_data in users:
    User.objects.filter(username=user_data['username']).delete()
    User.objects.create(
        username=user_data['username'],
        password_hash=hash_password(user_data['password']),
        role=user_data['role'],
        phc_id=user_data['phc_id']
    )
    print(f"✅ {user_data['username']} ({user_data['role']})")

print("\n✅ Test users ready!")
