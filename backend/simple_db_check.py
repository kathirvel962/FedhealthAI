#!/usr/bin/env python
"""Simple database check"""
from pymongo import MongoClient

c = MongoClient()
fed_count = c['fedhealth']['patients'].count_documents({})
fed_db_count = c['fedhealth_db']['patients'].count_documents({})

print(f"fedhealth database: {fed_count} patients")
print(f"fedhealth_db database: {fed_db_count} patients")

# Sample from each
fed_sample = c['fedhealth']['patients'].find_one()
fed_db_sample = c['fedhealth_db']['patients'].find_one()

print(f"\nfedhealth sample: {fed_sample.get('patient_id', 'NO PATIENT_ID') if fed_sample else 'EMPTY'}")
print(f"fedhealth_db sample: {fed_db_sample.get('patient_id', 'NO PATIENT_ID') if fed_db_sample else 'EMPTY'}")

# Show a field count comparison
fed_fields = list(fed_sample.keys()) if fed_sample else []
fed_db_fields = list(fed_db_sample.keys()) if fed_db_sample else []

print(f"\nfedhealth record has {len(fed_fields)} fields")
print(f"fedhealth_db record has {len(fed_db_fields)} fields")
