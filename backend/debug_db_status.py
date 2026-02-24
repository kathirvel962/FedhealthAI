#!/usr/bin/env python
"""Check what's in both databases"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

# Check both databases
for db_name in ['fedhealth', 'fedhealth_db']:
    db = client[db_name]
    patients_col = db['patients']
    count = patients_col.count_documents({})
    print(f"Database '{db_name}': {count} patient records")

# Now check what mongoengine sees
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import Patient
from mongoengine import get_db

# Check the connection
current_db = get_db()
print(f"\nMongoengine connected to database: {current_db.name}")
print(f"Total patients visible to ORM: {Patient.objects.count()}")
