#!/usr/bin/env python
"""Deep inspection of what's in the database"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

# Check fedhealth_db 
db_db = client['fedhealth_db']
patients_col = db_db['patients']

print("=== FEDHEALTH_DB PATIENTS COLLECTION ===")
print(f"Total count: {patients_col.count_documents({})}")

# Get all field names across all documents
all_fields = set()
for doc in patients_col.find().limit(100):
    all_fields.update(doc.keys())

print(f"All fields found: {sorted(all_fields)}")

# Check for problematic records
problem_docs = list(patients_col.find({
    '$and': [
        {'$or': [
            {'diagnosis': {'$exists': True}},
            {'rash': {'$exists': True}}
        ]},
        {'_id': 1}  # Match condition
    ]
}).limit(5))

if problem_docs:
    print(f"\nFound {len(problem_docs)} problematic documents")
    for doc in problem_docs:
        print(f"  ID: {doc['_id']}, Fields: {list(doc.keys())}")
else:
    print("\nNo problematic documents found")

# Try aggregation to find unique field sets
print("\n=== CHECKING DOCUMENT STRUCTURE ===")
pipeline = [
    {'$group': {'_id': None, 'fields': {' $addToSet': {'$objectToArray': '$$ROOT'}}}},
    {'$limit': 1}
]

# Simpler approach: check indexes
print("\n=== INDEXES ===")
indexes = patients_col.list_indexes()
for idx in indexes:
    print(f"Index: {idx['name']} - Key: {idx['key']}")
