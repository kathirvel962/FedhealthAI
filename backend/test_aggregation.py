#!/usr/bin/env python
"""
Test script to verify the aggregation endpoint works with fixed PHC IDs.
"""
import os
import sys
import mongoengine
from datetime import datetime

# Connect to MongoDB
MONGO_URL = "mongodb+srv://joshuarubertr2024cse:Joshua123@practice.rzgpqce.mongodb.net/fedhealth?retryWrites=true&w=majority"
mongoengine.connect('fedhealth', host=MONGO_URL)

sys.path.insert(0, os.path.dirname(__file__))
from api.models import LocalModel, GlobalModel
from api.ml_utils import aggregate_models

print("\n" + "="*70)
print("TESTING MODEL AGGREGATION")
print("="*70)

# Check existing models
print("\nLocal Models in Database:")
models = LocalModel.objects()
print(f"Total models: {models.count()}")
for m in models:
    print(f"  - PHC: {m.phc_id}, Version: {m.version_string}, Accuracy: {m.accuracy:.4f}")

# Test aggregation
print("\nAttempting aggregation...")
result = aggregate_models(automatic=False)

if result:
    print("\n✓ Aggregation SUCCESS!")
    print(f"  Global Version: {result['version_string']}")
    print(f"  Accuracy: {result['accuracy']:.4f}")
    print(f"  Contributors: {', '.join(result['contributors'])}")
    print(f"  Num Contributors: {result['num_contributors']}")
else:
    print("\n✗ Aggregation FAILED - No models to aggregate")

# Check global models
print("\nGlobal Models in Database:")
global_models = GlobalModel.objects()
print(f"Total: {global_models.count()}")
for gm in global_models.order_by('-version')[:3]:
    print(f"  - {gm.version_string}: Accuracy={gm.accuracy:.4f}, Contributors={len(gm.contributors)}")

print("\n" + "="*70)
