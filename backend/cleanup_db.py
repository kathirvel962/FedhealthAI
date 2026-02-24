"""Clear all MongoDB collections"""
import sys
import os
sys.path.insert(0, '/d/FedhealthAI/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')

import django
django.setup()

from api.models import User, Patient, PHC, LocalModel, GlobalModel, Alert, TrainingMetadata

# Drop all collections
User.drop_collection()
Patient.drop_collection()
PHC.drop_collection()
LocalModel.drop_collection()
GlobalModel.drop_collection()
Alert.drop_collection()
TrainingMetadata.drop_collection()

print("✅ All MongoDB collections cleared successfully!")
