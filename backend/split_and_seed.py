#!/usr/bin/env python
"""
Split the synthetic dataset into 5 parts (2000 each) and seed to MongoDB
Each PHC gets 2000 records assigned to its phc_id
"""
import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import Patient
from datetime import datetime
from pymongo import MongoClient

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
    """Split dataset and seed to MongoDB"""
    csv_path = 'd:/FedhealthAI/FedhealthAI/Synthetic_PHC_ABDM_Dataset_10000.csv'
    
    print("=" * 70)
    print("SPLITTING DATASET INTO 5 PHC GROUPS")
    print("=" * 70)
    
    # Read CSV
    print(f"\n1. Reading CSV file: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"   ✓ Loaded {len(df)} records")
        print(f"   Columns: {list(df.columns)}")
    except Exception as e:
        print(f"   ✗ Error reading CSV: {e}")
        return False
    
    # Clear existing patients from fedhealth database
    print(f"\n2. Clearing existing patients from fedhealth database")
    try:
        from api.models import Patient
        count = Patient.objects.count()
        Patient.objects.all().delete()
        print(f"   ✓ Deleted {count} existing patients")
    except Exception as e:
        print(f"   ✗ Error clearing: {e}")
    
    # Split into 5 groups
    print(f"\n3. Splitting into 5 PHC groups (2000 each)")
    total_seeded = 0
    
    for idx, phc_id in enumerate(PHCS):
        start = idx * 2000
        end = start + 2000
        
        phc_records = df.iloc[start:end].copy()
        phc_records['phc_id'] = phc_id
        phc_records['city'] = PHC_CITIES[phc_id]
        
        print(f"\n   {phc_id}:")
        print(f"      Records {start}-{end - 1} ({len(phc_records)} records)")
        
        # Seed to database
        try:
            created_count = 0
            for _, row in phc_records.iterrows():
                try:
                    patient = Patient.objects.create(
                        patient_id=f"P{start + created_count + 1:05d}",
                        phc_id=phc_id,
                        city=PHC_CITIES[phc_id],
                        age=int(row.get('age', 0)),
                        gender=str(row.get('gender', 'Unknown')),
                        fever=int(row.get('fever', 0)),
                        cough=int(row.get('cough', 0)),
                        fatigue=int(row.get('fatigue', 0)),
                        headache=int(row.get('headache', 0)),
                        vomiting=int(row.get('vomiting', 0)),
                        breathlessness=int(row.get('breathlessness', 0)),
                        temperature_c=float(row.get('temperature_c', 37.0)),
                        heart_rate=int(row.get('heart_rate', 70)),
                        bp_systolic=int(row.get('bp_systolic', 120)),
                        wbc_count=int(row.get('wbc_count', 7000)),
                        platelet_count=int(row.get('platelet_count', 250000)),
                        hemoglobin=float(row.get('hemoglobin', 13.5)),
                        disease_label=str(row.get('disease_label', 'Healthy')),
                        severity_level=str(row.get('severity_level', 'Low'))
                    )
                    created_count += 1
                except Exception as e:
                    pass  # Continue on errors
            
            total_seeded += created_count
            print(f"      ✓ Seeded {created_count} patients to {phc_id}")
        
        except Exception as e:
            print(f"      ✗ Error seeding {phc_id}: {e}")
    
    # Verify seeding
    print(f"\n4. Verifying seeded data")
    
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['fedhealth']
        
        for phc_id in PHCS:
            count = db['patients'].count_documents({'phc_id': phc_id})
            print(f"   {phc_id}: {count} patients in database")
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
    
    print("\n" + "=" * 70)
    print(f"✓ SEEDING COMPLETE: {total_seeded} total patients seeded to fedhealth")
    print("=" * 70)
    return True

if __name__ == "__main__":
    split_and_seed_dataset()
