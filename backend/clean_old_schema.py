#!/usr/bin/env python
"""Remove all old schema patient records from fedhealth_db"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['fedhealth_db']
patients = db['patients']

# Find all records with 'diagnosis' or 'rash' fields (old schema)
old_count = patients.count_documents({
    '$or': [
        {'diagnosis': {'$exists': True}},
        {'rash': {'$exists': True}}
    ]
})

print(f"Found {old_count} records with old schema (diagnosis/rash fields)")

if old_count > 0:
    # Delete them
    result = patients.delete_many({
        '$or': [
            {'diagnosis': {'$exists': True}},
            {'rash': {'$exists': True}}
        ]
    })
    print(f"Deleted {result.deleted_count} old schema records")
else:
    print("No old schema records found")

# List all unique fields to ensure consistency
sample = list(patients.find().limit(1))
if sample:
    print(f"\nSample record fields: {list(sample[0].keys())}")

# Count totals
total = patients.count_documents({})
print(f"\nTotal records remaining: {total}")

# Check PHC1 distribution
phc1_count = patients.count_documents({'phc_id': 'PHC1'})
print(f"PHC1 records: {phc1_count}")
