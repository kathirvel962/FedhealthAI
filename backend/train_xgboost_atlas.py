#!/usr/bin/env python
"""
XGBoost Training from MongoDB Atlas Data
Trains separate models for each PHC using the 10k seeded dataset
"""
import pandas as pd
import numpy as np
from pymongo import MongoClient
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle
from datetime import datetime
import json

# MongoDB Atlas Connection
MONGO_URL = 'mongodb+srv://kathirvel:kathir@practicemongodb.gj0nfd.mongodb.net/fedhealth_db?retryWrites=true&w=majority'

PHCS = ['PHC1', 'PHC2', 'PHC3', 'PHC4', 'PHC5']

def fetch_patients_from_atlas(phc_id):
    """Fetch patients for a PHC from MongoDB Atlas"""
    client = MongoClient(MONGO_URL)
    db = client['fedhealth_db']
    patients_col = db['patients']
    
    # Query patients for this PHC
    patients = list(patients_col.find({'phc_id': phc_id}))
    client.close()
    
    return patients

def prepare_training_data(patients):
    """Convert raw patient documents to feature matrix"""
    if not patients:
        return None, None
    
    # Extract features
    features = []
    labels = []
    
    for patient in patients:
        try:
            # Feature vector
            feature_row = [
                patient.get('age', 0),
                1 if patient.get('gender') == 'Male' else 0,  # 1 for Male, 0 for Female
                patient.get('fever', 0),
                patient.get('cough', 0),
                patient.get('fatigue', 0),
                patient.get('headache', 0),
                patient.get('vomiting', 0),
                patient.get('breathlessness', 0),
                patient.get('temperature_c', 0),
                patient.get('heart_rate', 0),
                patient.get('bp_systolic', 120),
                patient.get('wbc_count', 0),
                patient.get('platelet_count', 0),
                patient.get('hemoglobin', 0),
            ]
            features.append(feature_row)
            
            # Label (disease classification)
            disease = patient.get('disease_label', 'Unknown')
            labels.append(disease)
        except Exception as e:
            print(f"Error processing patient: {e}")
            continue
    
    return np.array(features), np.array(labels)

def train_phc_model(phc_id, features, labels):
    """Train XGBoost model for a PHC"""
    print(f"\n   Training XGBoost model...")
    
    # Encode disease labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(labels)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features, y_encoded, test_size=0.2, random_state=42
    )
    
    # Train XGBoost
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        objective='multi:softprob',
        num_class=len(le.classes_),
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    
    model.fit(X_train, y_train, verbose=False)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    
    print(f"   ✓ Accuracy:  {accuracy:.4f}")
    print(f"   ✓ Precision: {precision:.4f}")
    print(f"   ✓ Recall:    {recall:.4f}")
    print(f"   ✓ F1-Score:  {f1:.4f}")
    
    return model, le, {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'classes': list(le.classes_)
    }

def save_model(phc_id, model, label_encoder, metrics):
    """Save trained model and encoder to disk"""
    model_dir = 'd:/FedhealthAI/FedhealthAI/backend/models'
    
    # Create models directory if it doesn't exist
    import os
    os.makedirs(model_dir, exist_ok=True)
    
    # Save model
    model_path = f'{model_dir}/{phc_id}_xgboost.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"   ✓ Model saved: {model_path}")
    
    # Save label encoder
    encoder_path = f'{model_dir}/{phc_id}_label_encoder.pkl'
    with open(encoder_path, 'wb') as f:
        pickle.dump(label_encoder, f)
    print(f"   ✓ Encoder saved: {encoder_path}")
    
    # Save metrics
    metrics_path = f'{model_dir}/{phc_id}_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✓ Metrics saved: {metrics_path}")

def main():
    print("=" * 70)
    print("XGBOOST TRAINING FROM MONGODB ATLAS (10K Dataset)")
    print("=" * 70)
    
    total_trained = 0
    
    for phc_id in PHCS:
        print(f"\n{phc_id}:")
        print(f"   Getting data from MongoDB Atlas...")
        
        # Fetch data
        patients = fetch_patients_from_atlas(phc_id)
        print(f"   ✓ Fetched {len(patients)} patients")
        
        if len(patients) == 0:
            print(f"   ✗ No patients found for {phc_id}")
            continue
        
        # Prepare data
        features, labels = prepare_training_data(patients)
        if features is None or len(features) == 0:
            print(f"   ✗ No valid training data for {phc_id}")
            continue
        
        print(f"   ✓ Prepared {len(features)} samples")
        print(f"   ✓ Classes: {len(np.unique(labels))}")
        
        # Train model
        model, encoder, metrics = train_phc_model(phc_id, features, labels)
        
        # Save model
        save_model(phc_id, model, encoder, metrics)
        
        total_trained += 1
    
    print("\n" + "=" * 70)
    print(f"SUCCESS: Trained {total_trained} models")
    print("=" * 70)
    print("\nModels saved in: d:/FedhealthAI/FedhealthAI/backend/models/")
    print("\nModel files created:")
    for phc_id in PHCS:
        print(f"  - {phc_id}_xgboost.pkl")
        print(f"  - {phc_id}_label_encoder.pkl")
        print(f"  - {phc_id}_metrics.json")

if __name__ == "__main__":
    main()
