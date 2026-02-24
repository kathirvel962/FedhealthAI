#!/usr/bin/env python
"""Check fedhealth_db directly"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['fedhealth_db']
patients_col = db['patients']

# Check for records with 'diagnosis' or 'rash' fields
bad_records = list(patients_col.find({
    '$or': [
        {'diagnosis': {'$exists': True}},
        {'rash': {'$exists': True}}
    ]
}).limit(5))

if bad_records:
    print(f"Found {len(bad_records)} records with bad schema")
    print(f"Sample record fields: {list(bad_records[0].keys())}")
else:
    print("No records with bad schema found")

# Count total
print(f"Total records: {patients_col.count_documents({})}")

# Check a sample good record
good_record = patients_col.find_one({'disease_label': {'$exists': True}})
if good_record:
    print(f"\nGood record fields: {list(good_record.keys())}")
else:
    print("No good records found")

# Count records with and without disease_label
with_label = patients_col.count_documents({'disease_label': {'$exists': True}})
without_label = patients_col.count_documents({'disease_label': {'$exists': False}})

print(f"\nWith disease_label: {with_label}")
print(f"Without disease_label: {without_label}")
