#!/usr/bin/env python
"""Clean up database with old schema from BOTH databases"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

# Clean BOTH databases
for db_name in ['fedhealth_db', 'fedhealth']:
    db = client[db_name]
    patients_col = db['patients']
    
    # Delete all records that have old schema fields
    result = patients_col.delete_many({
        '$or': [
            {'diagnosis': {'$exists': True}},
            {'rash': {'$exists': True}}
        ]
    })
    
    print(f"Deleted {result.deleted_count} patient records with old schema from {db_name}")
    print(f"Remaining patients in {db_name}: {patients_col.count_documents({})}")

print("\nDatabase cleanup complete!")

