#!/usr/bin/env python
"""Seed patients using pure PyMongo to avoid index issues"""
import os
import sys
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

# Load CSV
CSV_PATH = r'd:\FedhealthAI\FedhealthAI\Synthetic_PHC_ABDM_Dataset_10000.csv'
df = pd.read_csv(CSV_PATH)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['fedhealth']  # Use correct database name from Django settings
patients_col = db['patients']

# Clear collection and drop ALL indexes
try:
    patients_col.drop()
    print("✅ Dropped patients collection")
except:
    pass

# Now recreate collection with documents WITHOUT unique indexes
print("\nInserting 10,000 patient records...")
documents = []

# Map PHC to city (example mapping)
phc_to_city = {
    'PHC1': 'Mumbai',
    'PHC2': 'Delhi',
    'PHC3': 'Bangalore',
    'PHC4': 'Chennai',
    'PHC5': 'Kolkata'
}

for idx, row in df.iterrows():
    phc = str(row['PHC_ID']).replace('PHC_', 'PHC')  # Normalize to PHC1, PHC2 etc
    doc = {
        'patient_id': str(row['Patient_ID']),
        'age': int(row['Age']),
        'gender': str(row['Gender']),
        'phc_id': phc,
        'city': phc_to_city.get(phc, 'Unknown'),  # Map PHC to city
        'fever': bool(row['Fever']),
        'cough': bool(row['Cough']),
        'fatigue': bool(row['Fatigue']),
        'headache': bool(row['Headache']),
        'vomiting': bool(row['Vomiting']),
        'breathlessness': bool(row['Breathlessness']),
        'temperature_c': float(row['Temperature_C']),
        'heart_rate': int(row['Heart_Rate']),
        'bp_systolic': 120,  # Default value
        'wbc_count': int(row['WBC_Count']),
        'platelet_count': int(row['Platelet_Count']),
        'hemoglobin': float(row['Hemoglobin']),
        'disease_label': str(row['Disease_Label']),
        'severity_level': str(row['Severity_Level']),
        'created_at': datetime.now()
    }
    documents.append(doc)
    
    if (idx + 1) % 1000 == 0:
        print(f"  Prepared {idx + 1} records...")

# Insert all documents
try:
    result = patients_col.insert_many(documents)
    print(f"\n✅ Successfully inserted {len(result.inserted_ids)} patient records")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Create non-unique indexes
try:
    patients_col.create_index('phc_id')
    print("✅ Created phc_id index")
    patients_col.create_index([('phc_id', 1), ('created_at', -1)])
    print("✅ Created phc_id + created_at index")
except Exception as e:
    print(f"⚠️  Index creation issue: {e}")

# Verify
count = patients_col.count_documents({})
print(f"\n📊 Final patient count in database: {count}")

# Show distribution
from collections import Counter
phc_dist = patients_col.aggregate([
    {'$group': {'_id': '$phc_id', 'count': {'$sum': 1}}}
])
print("\n📍 Distribution by PHC:")
for phc in sorted([d['_id'] for d in phc_dist]):
    count = patients_col.count_documents({'phc_id': phc})
    print(f"  {phc}: {count}")

print("\n✅ Database seeding complete!")
