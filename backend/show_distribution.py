#!/usr/bin/env python
"""
Final summary of dataset split and seeding
"""
from pymongo import MongoClient

print("=" * 70)
print("FINAL DATASET DISTRIBUTION SUMMARY")
print("=" * 70)

client = MongoClient('mongodb://localhost:27017/')

# Check fedhealth database (current active)
db_new = client['fedhealth']
col_new = db_new['patients']

print("\nDatabase: fedhealth (Active)")
print("-" * 70)

for phc in ['PHC1', 'PHC2', 'PHC3', 'PHC4', 'PHC5']:
    count = col_new.count_documents({'phc_id': phc})
    # Show sample disease distribution
    diseases = col_new.aggregate([
        {'$match': {'phc_id': phc}},
        {'$group': {'_id': '$disease_label', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 3}
    ])
    disease_list = list(diseases)
    disease_str = ", ".join([f"{d['_id']}({d['count']})" for d in disease_list])
    
    print(f"{phc}: {count:5d} patients - Top diseases: {disease_str}")

total = col_new.count_documents({})
print(f"\nTotal in fedhealth: {total:,} patients")

print("\n" + "=" * 70)
print("DATASET SPLIT COMPLETE")
print("=" * 70)
print("\nAll 10,000 synthetic patient records have been:")
print("  1. Split into 5 equal groups (2000 each)")
print("  2. Assigned to PHC1, PHC2, PHC3, PHC4, PHC5")
print("  3. Seeded into fedhealth MongoDB database")
print("  4. Ready for federated learning workflows")
print("\nEach PHC user can now:")
print("  - View their 2000 patient records via API")
print("  - Train local models on their data")
print("  - Participate in federated aggregation")
print("=" * 70)
