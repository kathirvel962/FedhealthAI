import mongoengine
import sys
import os

# Connect to MongoDB
MONGO_URL = "mongodb+srv://joshuarubertr2024cse:Joshua123@practice.rzgpqce.mongodb.net/fedhealth?retryWrites=true&w=majority"
print("Connecting to MongoDB...")
mongoengine.connect('fedhealth', host=MONGO_URL)
print("Connected!")

# Import models
sys.path.insert(0, os.path.dirname(__file__))
from api.models import Patient, LocalModel

print("\nChecking data...")
total = Patient.objects.count()
print(f"Total patients: {total}")

for phc in ['PHC_1', 'PHC_2', 'PHC_3', 'PHC_4', 'PHC_5']:
    count = Patient.objects.filter(phc_id=phc).count()
    models = LocalModel.objects.filter(phc_id=phc).count()
    print(f"{phc}: {count} patients, {models} models")

print("\nDone!")
