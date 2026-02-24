#!/usr/bin/env python
"""
Register trained XGBoost models in MongoDB
Inserts model metrics into local_models collection
"""
import json
import os
from datetime import datetime
from pymongo import MongoClient

MONGO_URL = 'mongodb+srv://kathirvel:kathir@practicemongodb.gj0nfd.mongodb.net/fedhealth_db?retryWrites=true&w=majority'

PHCS = ['PHC1', 'PHC2', 'PHC3', 'PHC4', 'PHC5']
MODEL_DIR = 'd:/FedhealthAI/FedhealthAI/backend/models'

def register_models_in_mongodb():
    """Register trained models in MongoDB"""
    print("=" * 70)
    print("REGISTERING TRAINED MODELS IN MONGODB")
    print("=" * 70)
    
    client = MongoClient(MONGO_URL)
    db = client['fedhealth_db']
    
    # Connect to mongoengine as well
    import mongoengine
    mongoengine.connect('fedhealth_db', host=MONGO_URL)
    
    from api.models import LocalModel
    
    total_registered = 0
    
    for phc_id in PHCS:
        print(f"\n{phc_id}:")
        
        # Read metrics
        metrics_file = os.path.join(MODEL_DIR, f'{phc_id}_metrics.json')
        if not os.path.exists(metrics_file):
            print(f"   ✗ Metrics file not found: {metrics_file}")
            continue
        
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        print(f"   ✓ Loaded metrics from {metrics_file}")
        
        # Check if model already exists
        existing = LocalModel.objects.filter(
            phc_id=phc_id,
            version_string=f'local_{phc_id}_v1'
        ).first()
        
        if existing:
            print(f"   ✓ Updating existing model")
            existing.accuracy = metrics['accuracy']
            existing.precision = metrics['precision']
            existing.recall = metrics['recall']
            existing.f1_score = metrics['f1']
            existing.sample_count = metrics['training_samples'] + metrics['test_samples']
            existing.num_train_samples = metrics['training_samples']
            existing.num_test_samples = metrics['test_samples']
            existing.trained_at = datetime.utcnow()
            existing.triggered_by = 'manual'
            existing.weights = {'model_type': 'xgboost', 'classes': metrics['classes']}
            existing.save()
        else:
            print(f"   ✓ Creating new model record")
            model = LocalModel(
                phc_id=phc_id,
                version=1,
                version_string=f'local_{phc_id}_v1',
                accuracy=metrics['accuracy'],
                precision=metrics['precision'],
                recall=metrics['recall'],
                f1_score=metrics['f1'],
                sample_count=metrics['training_samples'] + metrics['test_samples'],
                num_train_samples=metrics['training_samples'],
                num_test_samples=metrics['test_samples'],
                trained_at=datetime.utcnow(),
                triggered_by='manual',
                weights={'model_type': 'xgboost', 'classes': metrics['classes']},
                aggregated=False
            )
            model.save()
        
        print(f"   ✓ Accuracy: {metrics['accuracy']:.4f}")
        print(f"   ✓ Precision: {metrics['precision']:.4f}")
        print(f"   ✓ Recall: {metrics['recall']:.4f}")
        print(f"   ✓ F1: {metrics['f1']:.4f}")
        
        total_registered += 1
    
    # Verify in MongoDB
    print(f"\n5. Verifying in MongoDB")
    for phc_id in PHCS:
        model = LocalModel.objects.filter(phc_id=phc_id).order_by('-version').first()
        if model:
            print(f"   {phc_id}: {model.version_string} - Accuracy: {model.accuracy:.4f}")
    
    print("\n" + "=" * 70)
    print(f"SUCCESS: Registered {total_registered} models in MongoDB")
    print("=" * 70)
    print("\nThe dashboard should now show the correct accuracy metrics!")
    
    client.close()

if __name__ == "__main__":
    register_models_in_mongodb()
