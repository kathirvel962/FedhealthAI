#!/usr/bin/env python
"""Check database at PyMongo level"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['fedhealth_db']
patients_col = db['patients']

print(f"Total records in MongoDB: {patients_col.count_documents({})}")
print(f"Records with city='Mumbai': {patients_col.count_documents({'city': 'Mumbai'})}")
print(f"Records without city field: {patients_col.count_documents({'city': {'$exists': False}})}")

# Check a sample record
sample = patients_col.find_one()
if sample:
    print(f"\nSample record keys: {list(sample.keys())}")
