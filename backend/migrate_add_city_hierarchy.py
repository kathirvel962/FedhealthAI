#!/usr/bin/env python
"""
PART 2 — Migration Script: Add City Hierarchy to Existing PHCs
Updates existing PHCs with city information without changing any other functionality.
"""
import os
import sys
import mongoengine
from datetime import datetime

# Connect to MongoDB
MONGO_URL = "mongodb+srv://joshuarubertr2024cse:Joshua123@practice.rzgpqce.mongodb.net/fedhealth?retryWrites=true&w=majority"
mongoengine.connect('fedhealth', host=MONGO_URL)

sys.path.insert(0, os.path.dirname(__file__))
from api.models import Patient, PHC

# City mapping for PHCs
CITY_MAPPING = {
    'PHC_1': 'Pollachi',
    'PHC_2': 'Pollachi',
    'PHC_3': 'Thondamuthur',
    'PHC_4': 'Thondamuthur',
    'PHC_5': 'Kinathukadavu'
}

print("\n" + "="*70)
print("MIGRATION: ADD CITY HIERARCHY TO EXISTING PHCS")
print("="*70)

print("\n1. Updating Patient Records with City Information...")
total_updated = 0
for phc_id, city in CITY_MAPPING.items():
    count = Patient.objects.filter(phc_id=phc_id).update(
        set__city=city
    )
    print(f"   {phc_id} -> {city}: {count} patients updated")
    total_updated += count

print(f"\n   Total patients updated: {total_updated}")

# Verify the update
print("\n2. Verification - Sample records by PHC:")
for phc_id in CITY_MAPPING.keys():
    sample = Patient.objects.filter(phc_id=phc_id).first()
    if sample:
        print(f"   {phc_id}: city = {sample.city}")

# Create PHC records if they don't exist
print("\n3. Creating PHC Records with City Information...")
for phc_id, city in CITY_MAPPING.items():
    phc_exists = PHC.objects.filter(name=phc_id).first()
    if not phc_exists:
        PHC.objects.create(
            name=phc_id,
            district_id='Coimbatore',
            city=city
        )
        print(f"   ✓ Created PHC: {phc_id} in {city}")
    else:
        # Update existing PHC with city if missing
        if not phc_exists.city:
            phc_exists.city = city
            phc_exists.save()
            print(f"   ✓ Updated PHC: {phc_id} with city: {city}")
        else:
            print(f"   → PHC: {phc_id} already has city: {phc_exists.city}")

print("\n4. Final Verification - PHC Collection:")
all_phcs = PHC.objects.all()
if all_phcs:
    for phc in all_phcs:
        count = Patient.objects.filter(phc_id=phc.name).count()
        print(f"   {phc.name}: city={phc.city}, patients={count}")
else:
    print("   No PHC records found")

print("\n" + "="*70)
print("MIGRATION COMPLETE")
print("="*70)
print("\nSummary:")
print(f"  - Total patients updated with city: {total_updated}")
print(f"  - City mapping: {len(CITY_MAPPING)} PHC → City pairs")
print(f"  - Coimbatore district: All PHCs")
print("\nCity-level hierarchy is now ready for risk calculations.")
print("="*70 + "\n")
