import mongoengine
import sys
import os

MONGO_URL = "mongodb+srv://joshuarubertr2024cse:Joshua123@practice.rzgpqce.mongodb.net/fedhealth?retryWrites=true&w=majority"
print("Connecting to MongoDB...")
mongoengine.connect('fedhealth', host=MONGO_URL)

sys.path.insert(0, os.path.dirname(__file__))
from api.models import Patient, LocalModel
from api.ml_utils import train_federated_model

print("\n" + "="*70)
print("TRAINING PHC_5 WITH XGBOOST")
print("="*70)

phc_id = 'PHC_5'
patients = Patient.objects.filter(phc_id=phc_id).count()
print(f"\n{phc_id}: {patients} patients")

print(f"\nTraining XGBoost model for {phc_id}...")
result = train_federated_model(phc_id, trigger_reason='MANUAL_INITIALIZATION')

if result.get('error'):
    print(f"\nERROR: {result['error']}")
else:
    print(f"\nSUCCESS!")
    print(f"  Version: {result.get('version', 0)}")
    print(f"  Accuracy: {result.get('accuracy', 0):.2%}")
    print(f"  Precision: {result.get('precision', 0):.2%}")
    print(f"  Recall: {result.get('recall', 0):.2%}")
    print(f"  F1 Score: {result.get('f1_score', 0):.2%}")
    print(f"  Samples: {result.get('num_samples', 0)}")

print("\n" + "="*70)
print("COMPLETE")
print("="*70)
