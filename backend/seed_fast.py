#!/usr/bin/env python
"""
Split and seed dataset using PyMongo for fast bulk insert
"""
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

# Map PHCs
PHCS = ['PHC1', 'PHC2', 'PHC3', 'PHC4', 'PHC5']
PHC_CITIES = {
    'PHC1': 'Mumbai',
    'PHC2': 'Delhi',
    'PHC3': 'Bangalore',
    'PHC4': 'Chennai',
    'PHC5': 'Kolkata'
}

def split_and_seed_dataset():
    """Split dataset and seed to MongoDB using PyMongo"""
    csv_path = 'd:/FedhealthAI/FedhealthAI/Synthetic_PHC_ABDM_Dataset_10000.csv'
    
    print("=" * 70)
    print("SPLITTING DATASET INTO 5 PHC GROUPS (PyMongo Fast Insert)")
    print("=" * 70)
    
    # Read CSV
    print(f"\n1. Reading CSV file")
    df = pd.read_csv(csv_path)
    print(f"   Loaded {len(df)} records")
    
    # Connect to MongoDB
    print(f"\n2. Connecting to MongoDB")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['fedhealth']
    patients_col = db['patients']
    
    # Clear existing
    print(f"\n3. Clearing existing patients")
    deleted = patients_col.delete_many({})
    print(f"   Deleted {deleted.deleted_count} records")
    
    # Split and insert
    print(f"\n4. Splitting and inserting data")
    total_inserted = 0
    
    for idx, phc_id in enumerate(PHCS):
        start = idx * 2000
        end = start + 2000
        
        print(f"\n   {phc_id} (records {start}-{end-1}):", end=" ")
        
        # Get records for this PHC
        phc_records = df.iloc[start:end].copy()
        
        # Convert to documents for MongoDB
        documents = []
        for i, (_, row) in enumerate(phc_records.iterrows()):
            doc = {
                'patient_id': f"P{start + i + 1:05d}",
                'phc_id': phc_id,
                'city': PHC_CITIES[phc_id],
                'age': int(row['Age']),
                'gender': str(row['Gender']),
                'fever': int(row['Fever']),
                'cough': int(row['Cough']),
                'fatigue': int(row['Fatigue']),
                'headache': int(row['Headache']),
                'vomiting': int(row['Vomiting']),
                'breathlessness': int(row['Breathlessness']),
                'temperature_c': float(row['Temperature_C']),
                'heart_rate': int(row['Heart_Rate']),
                'bp_systolic': 120,  # Default
                'wbc_count': int(row['WBC_Count']),
                'platelet_count': int(row['Platelet_Count']),
                'hemoglobin': float(row['Hemoglobin']),
                'disease_label': str(row['Disease_Label']),
                'severity_level': str(row['Severity_Level']),
                'created_at': datetime.utcnow()
            }
            documents.append(doc)
        
        # Bulk insert
        try:
            result = patients_col.insert_many(documents)
            inserted = len(result.inserted_ids)
            total_inserted += inserted
            print(f"Inserted {inserted} records")
        except Exception as e:
            print(f"Error: {e}")
    
    # Verify
    print(f"\n5. Verifying seeded data")
    for phc_id in PHCS:
        count = patients_col.count_documents({'phc_id': phc_id})
        print(f"   {phc_id}: {count} patients")
    
    total = patients_col.count_documents({})
    print(f"\n   Total in database: {total} patients")
    
    print("\n" + "=" * 70)
    print(f"SUCCESS: Seeded {total_inserted} patients to fedhealth database")
    print("=" * 70)

if __name__ == "__main__":
    split_and_seed_dataset()
