#!/usr/bin/env python
"""Fix MongoDB patient index issue by cleaning up null patient_ids"""
from pymongo import MongoClient
from pymongo import errors

# Connect directly to MongoDB to bypass mongoengine's index creation
client = MongoClient('mongodb://localhost:27017/')
db = client['fedhealth_db']
patients_collection = db['patients']

# First, drop the problematic index
try:
    patients_collection.drop_index('patient_id_1')
    print("✅ Dropped existing patient_id_1 index")
except errors.OperationFailure as e:
    print(f"ℹ️  Index status: {e}")

# Drop any other problematic indexes
try:
    patients_collection.drop_index('patient_id_1_phc_id_1')
    print("✅ Dropped patient_id_1_phc_id_1 index")
except errors.OperationFailure:
    pass

# Now delete documents with null patient_id
try:
    result = patients_collection.delete_many({'patient_id': None})
    print(f"✅ Deleted {result.deleted_count} patients with null patient_id")
except Exception as e:
    print(f"❌ Error deleting null patients: {e}")

# Also delete documents without patient_id field
try:
    result = patients_collection.delete_many({'patient_id': {'$exists': False}})
    print(f"✅ Deleted {result.deleted_count} patients without patient_id field")
except Exception as e:
    print(f"❌ Error deleting patients without field: {e}")

# Clean up - clear all diagnostic data if needed
print(f"\n📊 Final patient count: {patients_collection.count_documents({})}")
print("✅ Database cleanup complete!")
