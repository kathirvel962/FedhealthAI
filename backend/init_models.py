#!/usr/bin/env python
"""
Initialize local models for all PHCs from existing patient data
This populates the dashboard with real model metrics
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
django.setup()

from api.models import Patient, PHC
from api.ml_utils import train_federated_model
import pandas as pd

print("\n" + "="*80)
print("INITIALIZING LOCAL MODELS FOR ALL PHCs")
print("="*80)

# Train model for each PHC that has patient data
phcs = ['PHC1', 'PHC2', 'PHC3', 'PHC4']

for phc_id in phcs:
    patient_count = Patient.objects.filter(phc_id=phc_id).count()
    
    if patient_count == 0:
        print(f"\n⏭️  Skipping {phc_id} - no patient data")
        continue
    
    print(f"\n📊 Training model for {phc_id}...")
    print(f"    Patients in database: {patient_count}")
    
    try:
        # Train and save model
        result = train_federated_model(phc_id, trigger_reason='INITIALIZATION')
        
        if result['error']:
            print(f"    ❌ Error: {result['error']}")
        else:
            print(f"    ✅ Model trained successfully!")
            print(f"       Accuracy: {result['accuracy']:.1%}")
            print(f"       Samples: {result['num_samples']}")
            print(f"       Version: {result['version_string']}")
    except Exception as e:
        print(f"    ❌ Exception: {str(e)}")

print("\n" + "="*80)
print("✅ INITIALIZATION COMPLETE")
print("="*80)
print("Dashboard should now show real model metrics for each PHC.\n")
