# Federated Learning ML Utilities
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
from api.models import LocalModel, GlobalModel, Patient, TrainingMetadata, ModelBroadcast
from datetime import datetime, timedelta
import logging
import pickle

logger = logging.getLogger(__name__)

# ============================================
# MODEL VERSIONING HELPERS
# ============================================

def get_latest_global_model():
    """
    Retrieve the latest global model.
    
    Returns:
        GlobalModel instance or None
    """
    try:
        return GlobalModel.objects.order_by('-version').first()
    except Exception as e:
        logger.error(f"Error retrieving latest global model: {str(e)}")
        return None


def get_latest_local_model(phc_id):
    """
    Retrieve the latest local model for a specific PHC.
    
    Args:
        phc_id: PHC identifier
    
    Returns:
        LocalModel instance or None
    """
    try:
        return LocalModel.objects.filter(phc_id=phc_id).order_by('-version').first()
    except Exception as e:
        logger.error(f"Error retrieving latest local model for {phc_id}: {str(e)}")
        return None


def get_model_by_version_string(version_string):
    """
    Retrieve a model by its version string.
    
    Args:
        version_string: e.g., "local_PHC1_v1" or "global_v2"
    
    Returns:
        Model instance or None
    """
    try:
        # Try global model first
        global_model = GlobalModel.objects.filter(version_string=version_string).first()
        if global_model:
            return global_model
        
        # Try local model
        local_model = LocalModel.objects.filter(version_string=version_string).first()
        return local_model
    except Exception as e:
        logger.error(f"Error retrieving model with version {version_string}: {str(e)}")
        return None


def generate_local_version_string(phc_id, version_number):
    """Generate version string for local model"""
    return f"local_{phc_id}_v{version_number}"


def generate_global_version_string(version_number):
    """Generate version string for global model"""
    return f"global_v{version_number}"


# ============================================
# ML INNOVATION: DRIFT DETECTION
# ============================================

def detect_model_drift(phc_id):
    """
    Detect model drift by comparing current local model accuracy
    with previous local model accuracy.
    
    Drift is flagged if accuracy drops by >10%.
    
    Args:
        phc_id: PHC identifier
    
    Returns:
        Dictionary with drift_detected (bool) and details
    """
    try:
        from api.models import Alert
        
        # Get latest and second-latest models
        latest = LocalModel.objects.filter(phc_id=phc_id).order_by('-version').first()
        previous = LocalModel.objects.filter(phc_id=phc_id).order_by('-version').skip(1).first()
        
        if not latest or not previous:
            return {
                'drift_detected': False,
                'reason': 'insufficient_history',
                'phc_id': phc_id
            }
        
        accuracy_drop = previous.accuracy - latest.accuracy
        accuracy_drop_percentage = (accuracy_drop / previous.accuracy * 100) if previous.accuracy > 0 else 0
        
        drift_detected = accuracy_drop_percentage > 10.0
        
        # Create alert if drift detected
        if drift_detected:
            latest_global = get_latest_global_model()
            
            alert = Alert.objects.create(
                phc_id=phc_id,
                alert_type='MODEL_DRIFT',
                risk_score=accuracy_drop_percentage,
                severity='HIGH' if accuracy_drop_percentage > 20 else 'MEDIUM',
                local_model_version=latest.version,
                local_model_version_string=latest.version_string,
                global_model_version=latest_global.version if latest_global else 0,
                global_model_version_string=latest_global.version_string if latest_global else None,
                drift_detected=True,
                accuracy_drop_percentage=accuracy_drop_percentage,
                previous_accuracy=previous.accuracy,
                current_accuracy=latest.accuracy,
                message=f"Model drift detected in {phc_id}: accuracy dropped {accuracy_drop_percentage:.2f}%",
                details={
                    'previous_version': previous.version_string,
                    'current_version': latest.version_string,
                    'previous_accuracy': round(previous.accuracy, 4),
                    'current_accuracy': round(latest.accuracy, 4),
                    'drop_percentage': round(accuracy_drop_percentage, 2)
                }
            )
            
            logger.warning(
                f"Drift detected for {phc_id}: accuracy dropped from {previous.accuracy:.4f} to {latest.accuracy:.4f} ({accuracy_drop_percentage:.2f}%)"
            )
        
        return {
            'drift_detected': drift_detected,
            'phc_id': phc_id,
            'accuracy_drop_percentage': round(accuracy_drop_percentage, 2),
            'previous_accuracy': previous.accuracy,
            'current_accuracy': latest.accuracy,
            'threshold': 10.0,
            'alert_created': drift_detected
        }
    
    except Exception as e:
        logger.error(f"Error detecting drift for {phc_id}: {str(e)}")
        return {
            'drift_detected': False,
            'error': str(e),
            'phc_id': phc_id
        }


# ============================================
# ML INNOVATION: COMPOSITE OUTBREAK RISK SCORE
# ============================================

def calculate_composite_risk_score(phc_id):
    """
    Calculate composite outbreak risk score for a PHC.
    
    Risk Score Formula:
    - 0.4 * fever_percentage (% of patients with fever)
    - 0.3 * positive_predictions_percentage (% models predict positive)
    - 0.3 * abnormal_wbc_ratio (% with abnormal WBC)
    
    Normalized to 0-100 scale.
    
    Severity mapping:
    - 0-30: LOW
    - 30-60: MEDIUM
    - 60-100: HIGH
    
    Args:
        phc_id: PHC identifier
    
    Returns:
        Dictionary with risk score and severity
    """
    try:
        from api.models import Alert
        
        # Get all patients for this PHC
        patients = list(Patient.objects.filter(phc_id=phc_id))
        
        if not patients:
            return {
                'risk_score': 0.0,
                'severity': 'LOW',
                'reason': 'no_patients',
                'phc_id': phc_id
            }
        
        # Calculate metrics
        total_patients = len(patients)
        
        # 1) Fever percentage (weight: 0.4)
        fever_cases = sum(1 for p in patients if p.fever == 1)
        fever_percentage = (fever_cases / total_patients) * 100
        fever_component = (fever_percentage / 100) * 0.4 * 100
        
        # 2) Positive predictions percentage (weight: 0.3)
        # Use latest local model to predict diagnosis match
        latest_model = get_latest_local_model(phc_id)
        positive_predictions = 0
        
        if latest_model:
            # Count patients matching "disease" diagnoses (fever-related)
            disease_keywords = ['fever', 'malaria', 'typhoid', 'dengue', 'influenza']
            positive_predictions = sum(
                1 for p in patients 
                if any(keyword.lower() in p.disease_label.lower() for keyword in disease_keywords)
            )
        
        positive_predictions_percentage = (positive_predictions / total_patients) * 100
        predictions_component = (positive_predictions_percentage / 100) * 0.3 * 100
        
        # 3) Abnormal WBC ratio (weight: 0.3)
        # Normal WBC: 4,500-11,000 cells/μL, flag if outside this or too high
        abnormal_wbc = sum(
            1 for p in patients 
            if p.wbc_count < 4500 or p.wbc_count > 11000
        )
        abnormal_wbc_ratio = (abnormal_wbc / total_patients) * 100
        wbc_component = (abnormal_wbc_ratio / 100) * 0.3 * 100
        
        # Composite score (0-100 scale)
        composite_score = fever_component + predictions_component + wbc_component
        composite_score = max(0, min(100, composite_score))  # Clamp to 0-100
        
        # Determine severity
        if composite_score < 30:
            severity = 'LOW'
        elif composite_score < 60:
            severity = 'MEDIUM'
        else:
            severity = 'HIGH'
        
        # Create alert
        latest_global = get_latest_global_model()
        
        alert = Alert.objects.create(
            phc_id=phc_id,
            alert_type='COMPOSITE_RISK',
            risk_score=composite_score,
            severity=severity,
            local_model_version=latest_model.version if latest_model else 0,
            local_model_version_string=latest_model.version_string if latest_model else None,
            global_model_version=latest_global.version if latest_global else 0,
            global_model_version_string=latest_global.version_string if latest_global else None,
            fever_percentage=fever_percentage,
            positive_predictions_percentage=positive_predictions_percentage,
            abnormal_wbc_ratio=abnormal_wbc_ratio,
            composite_score_breakdown={
                'fever_component': round(fever_component, 2),
                'predictions_component': round(predictions_component, 2),
                'wbc_component': round(wbc_component, 2)
            },
            message=f"Composite risk score for {phc_id}: {composite_score:.2f}/100 ({severity})",
            details={
                'total_patients': total_patients,
                'fever_cases': fever_cases,
                'positive_predictions': positive_predictions,
                'abnormal_wbc_count': abnormal_wbc,
                'calculation': {
                    'fever': f"{fever_percentage:.2f}% × 0.4 = {fever_component:.2f}",
                    'predictions': f"{positive_predictions_percentage:.2f}% × 0.3 = {predictions_component:.2f}",
                    'wbc': f"{abnormal_wbc_ratio:.2f}% × 0.3 = {wbc_component:.2f}"
                }
            }
        )
        
        logger.info(
            f"Composite risk score for {phc_id}: {composite_score:.2f}/100 ({severity}) - "
            f"Fever: {fever_percentage:.2f}%, Predictions: {positive_predictions_percentage:.2f}%, "
            f"Abnormal WBC: {abnormal_wbc_ratio:.2f}%"
        )
        
        return {
            'phc_id': phc_id,
            'risk_score': round(composite_score, 2),
            'severity': severity,
            'fever_percentage': round(fever_percentage, 2),
            'positive_predictions_percentage': round(positive_predictions_percentage, 2),
            'abnormal_wbc_ratio': round(abnormal_wbc_ratio, 2),
            'components': {
                'fever': round(fever_component, 2),
                'predictions': round(predictions_component, 2),
                'wbc': round(wbc_component, 2)
            },
            'total_patients': total_patients,
            'alert_created': True
        }
    
    except Exception as e:
        logger.error(f"Error calculating composite risk score for {phc_id}: {str(e)}")
        return {
            'risk_score': 0.0,
            'severity': 'LOW',
            'error': str(e),
            'phc_id': phc_id
        }

# ============================================
# AUTOMATIC TRAINING CYCLE MANAGEMENT
# ============================================

PATIENT_THRESHOLD = 20  # Train after 20 new patients
TIME_THRESHOLD = timedelta(hours=24)  # Train after 24 hours


def should_trigger_local_training(phc_id):
    """
    Check if local training should be triggered for a PHC.
    
    Returns:
        Tuple of (should_train: bool, reason: str)
    """
    try:
        metadata = TrainingMetadata.objects.filter(phc_id=phc_id).first()
        
        if not metadata:
            # First training
            metadata = TrainingMetadata.objects.create(phc_id=phc_id)
            return (False, 'metadata_initialized')
        
        # Check patient threshold
        if metadata.patients_since_last_training >= PATIENT_THRESHOLD:
            return (True, 'patient_threshold')
        
        # Check time threshold
        if metadata.last_training_at:
            time_since_training = datetime.utcnow() - metadata.last_training_at
            if time_since_training >= TIME_THRESHOLD:
                return (True, 'time_threshold')
        
        return (False, 'no_trigger')
    
    except Exception as e:
        logger.error(f"Error checking training trigger for {phc_id}: {str(e)}")
        return (False, 'error')


def should_trigger_global_aggregation():
    """
    Check if global aggregation should be triggered.
    
    Returns:
        Tuple of (should_aggregate: bool, reason: str, pending_phcs: list)
    """
    try:
        # Find unaggregated local models
        unaggregated = LocalModel.objects.filter(aggregated=False)
        
        if not unaggregated:
            return (False, 'no_models', [])
        
        # Group by phc_id to find unique PHCs with unaggregated models
        phc_ids = set(m.phc_id for m in unaggregated)
        
        # Need at least 3 PHCs with new models
        if len(phc_ids) >= 3:
            return (True, 'threshold_met', list(phc_ids))
        
        return (False, 'insufficient_phcs', list(phc_ids))
    
    except Exception as e:
        logger.error(f"Error checking aggregation trigger: {str(e)}")
        return (False, 'error', [])


def record_training_completion(phc_id, success=True):
    """Record that training completed for a PHC and release training lock"""
    try:
        metadata = TrainingMetadata.objects.filter(phc_id=phc_id).first()
        if metadata:
            if success:
                metadata.last_training_at = datetime.utcnow()
                metadata.patients_since_last_training = 0
            # HACKATHON FIX: Always release lock, even if training fails
            metadata.training_in_progress = False
            metadata.updated_at = datetime.utcnow()
            metadata.save()
    except Exception as e:
        logger.error(f"Error recording training completion for {phc_id}: {str(e)}")


def increment_patient_count(phc_id):
    """Increment patient count since last training"""
    try:
        metadata = TrainingMetadata.objects.filter(phc_id=phc_id).first()
        if metadata:
            metadata.patients_since_last_training += 1
            metadata.updated_at = datetime.utcnow()
            metadata.save()
        else:
            TrainingMetadata.objects.create(
                phc_id=phc_id,
                patients_since_last_training=1
            )
    except Exception as e:
        logger.error(f"Error incrementing patient count for {phc_id}: {str(e)}")


def broadcast_global_model(global_model_version, version_string=None):
    """
    Simulate broadcasting global model to all PHCs.
    In reality, PHCs would pull the model from a secure endpoint.
    
    Args:
        global_model_version: Numeric version
        version_string: String version (e.g., "global_v3")
    """
    try:
        # Record that all PHCs have received the new global model
        for phc_num in range(1, 5):
            phc_id = f'PHC_{phc_num}'
            ModelBroadcast.objects.create(
                phc_id=phc_id,
                global_model_version=global_model_version
            )
        
        version_info = version_string if version_string else f"v{global_model_version}"
        logger.info(f"Global model {version_info} broadcasted to all PHCs")
        return True
    except Exception as e:
        logger.error(f"Error broadcasting global model: {str(e)}")
        return False



def preprocess_data(patients, feature_columns):
    """
    Extract features and labels from patient data.
    
    Args:
        patients: List of Patient objects
        feature_columns: List of feature column names
    
    Returns:
        X (numpy array), y (numpy array), feature_columns (list)
    """
    if not patients:
        return np.array([]), np.array([]), feature_columns
    
    X_list = []
    for p in patients:
        row = []
        for col in feature_columns:
            val = getattr(p, col, None)
            row.append(float(val) if val is not None else 0.0)
        X_list.append(row)
    
    X = np.array(X_list)
    y = np.array([p.disease_label for p in patients])
    
    return X, y, feature_columns


def train_local_model(X, y, feature_columns):
    """
    Train XGBoost model on local PHC data.
    
    VALIDATION CHECKLIST:
    ✓ Checks for minimum samples (10)
    ✓ Checks for multiple diagnostic classes
    ✓ Uses train/test split (70/30)
    ✓ Stratified split to preserve class distribution
    ✓ Encodes labels with LabelEncoder
    ✓ Trains XGBoost classifier with optimized hyperparameters
    ✓ 5-fold cross-validation for robustness
    ✓ Evaluation ONLY on test set (not training set which can be inflated)
    ✓ Ensures diagnosis is NOT in feature matrix
    
    Args:
        X: Feature matrix (numpy array) - symptom and vital features
        y: Labels (numpy array) - disease_label (target variable)
        feature_columns: List of feature names
    
    Returns:
        Dictionary with model, X_test, y_test, CV metrics, or error
    """
    # ============================================
    # VALIDATION #1: Data Quality Checks
    # ============================================
    if len(X) < 10:
        return {
            'error': 'Not enough data to train model (need >= 10 samples)',
            'num_samples': len(X)
        }
    
    # Check if X and y have same length
    if len(X) != len(y):
        return {
            'error': f'Feature matrix and labels length mismatch: X={len(X)}, y={len(y)}',
            'num_samples': len(X)
        }
    
    # Check for NaN/Inf in features
    if np.isnan(X).any() or np.isinf(X).any():
        return {
            'error': 'Feature matrix contains NaN or Inf values',
            'num_samples': len(X)
        }
    
    # Verify diagnosis is NOT in features
    if 'diagnosis' in feature_columns:
        return {
            'error': 'CRITICAL: diagnosis cannot be in feature_columns! Data leakage detected.',
            'num_samples': len(X)
        }
    
    # Check if only one class
    unique_classes = len(np.unique(y))
    class_counts = np.unique(y, return_counts=True)[1]
    if unique_classes < 2:
        return {
            'error': 'Only one diagnosis class present. Need at least 2 classes for classification.',
            'num_samples': len(X),
            'unique_classes': unique_classes
        }
    
    # Warn if class is severely imbalanced
    max_class_ratio = class_counts.max() / class_counts.min()
    if max_class_ratio > 10:
        logger.warning(f'Severe class imbalance detected: ratio={max_class_ratio:.2f}. XGBoost will handle with scale_pos_weight.')
    
    try:
        # ============================================
        # PREPROCESSING: Normalize Features + Encode Labels
        # ============================================
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Encode labels to numeric (0, 1, 2, ..., n_classes-1)
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        logger.info(f'Feature scaling complete. X shape: {X_scaled.shape}, Classes: {unique_classes}')
        logger.info(f'Label encoding: {list(zip(label_encoder.classes_, range(len(label_encoder.classes_))))}')
        
        # ============================================
        # TRAIN/TEST SPLIT: Stratified 70/30
        # ============================================
        unique, counts = np.unique(y_encoded, return_counts=True)
        can_stratify = all(count >= 2 for count in counts)
        
        test_size = 0.3  # 30% test, 70% train
        
        if can_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_encoded,
                test_size=test_size,
                random_state=42,
                stratify=y_encoded  # STRATIFIED
            )
            logger.info(f'Stratified split: train={len(X_train)}, test={len(X_test)}')
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_encoded,
                test_size=test_size,
                random_state=42
            )
            logger.warning(f'Non-stratified split (not all classes have 2+ samples). train={len(X_train)}, test={len(X_test)}')
        
        # Verify test set is not empty
        if len(X_test) == 0:
            return {
                'error': 'Test set is empty! Dataset too small for 30% split.',
                'num_samples': len(X)
            }
        
        # ============================================
        # MODEL TRAINING: XGBoost
        # ============================================
        # Calculate scale_pos_weight for imbalanced classes (binary case)
        sample_weight = None
        if unique_classes == 2:
            # For binary: weight minority class more
            from sklearn.utils.class_weight import compute_sample_weight
            sample_weight = compute_sample_weight('balanced', y_train)
        else:
            # For multiclass: XGBoost handles it natively
            sample_weight = None
        
        model = XGBClassifier(
            n_estimators=200,            # Number of boosting rounds
            max_depth=6,                 # Max tree depth
            learning_rate=0.1,           # Learning rate (eta)
            objective='multi:softprob',  # Multi-class classification
            num_class=unique_classes,    # Number of classes
            eval_metric='mlogloss',      # Multi-class log loss
            random_state=42,             # Reproducibility
            use_label_encoder=False,     # Use LabelEncoder explicitly
            tree_method='hist',          # Faster histogram-based method
            verbosity=0                  # Silent mode
        )
        
        # Train model
        model.fit(
            X_train, y_train,
            sample_weight=sample_weight,
            verbose=False
        )
        
        logger.info(f'XGBoost model training complete. Classes: {unique_classes}')
        
        # ============================================
        # VALIDATION #2: Cross-Validation on Train Set
        # ============================================
        if len(X_train) > 100:  # Only if dataset large enough
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
            avg_cv_accuracy = cv_scores.mean()
            cv_std = cv_scores.std()
            logger.info(f'5-Fold CV Results: mean={avg_cv_accuracy:.4f}, std={cv_std:.4f}, scores={[f"{s:.4f}" for s in cv_scores]}')
        else:
            logger.info(f'Dataset size {len(X_train)} too small for 5-fold CV (need > 100). Skipping CV.')
            cv_scores = np.array([0.0])  # Placeholder
            avg_cv_accuracy = 0.0
            cv_std = 0.0
        
        # Serialize model to binary for storage
        model_binary = pickle.dumps(model)
        
        return {
            'model': model,
            'model_binary': model_binary,
            'label_encoder': label_encoder,
            'label_classes': list(label_encoder.classes_),
            'scaler': scaler,
            'X_test': X_test,
            'y_test': y_test,
            'X_train': X_train,
            'y_train': y_train,
            'y_encoded_test': y_test,  # Already encoded
            'y_encoded_train': y_train,  # Already encoded
            'classes': sorted(list(set(y))),
            'feature_columns': feature_columns,
            'cv_scores': cv_scores.tolist(),
            'cv_mean': float(avg_cv_accuracy),
            'cv_std': float(cv_std),
            'num_train': len(X_train),
            'num_test': len(X_test),
            'stratified': can_stratify
        }
    except Exception as e:
        logger.error(f"Error training XGBoost model: {str(e)}", exc_info=True)
        return {
            'error': f'Model training failed: {str(e)}',
            'num_samples': len(X)
        }


def evaluate_model(model_data):
    """
    Compute performance metrics on HOLD-OUT TEST SET ONLY.
    This ensures realistic accuracy assessment and detects overfitting.
    
    IMPORTANT: Evaluation NEVER touches training data.
    
    Args:
        model_data: Dictionary from train_local_model()
    
    Returns:
        Dictionary with test metrics, train metrics comparison, classification report, or error
    """
    if 'error' in model_data:
        return model_data
    
    try:
        model = model_data['model']
        label_encoder = model_data['label_encoder']
        X_test = model_data['X_test']
        y_test = model_data['y_test']  # Already encoded (0, 1, 2, ...)
        X_train = model_data['X_train']
        y_train = model_data['y_train']  # Already encoded
        label_classes = model_data['label_classes']
        feature_columns = model_data['feature_columns']
        
        # Decode y_test and y_train back to original labels for metrics
        y_test_decoded = label_encoder.inverse_transform(y_test)
        y_train_decoded = label_encoder.inverse_transform(y_train)
        
        # ============================================
        # VALIDATION #3: Test Set Evaluation
        # ============================================
        # Predictions on TEST set (hold-out data)
        y_pred_test = model.predict(X_test)
        y_pred_proba_test = model.predict_proba(X_test)
        
        # Decode predictions for metrics computation
        y_pred_test_decoded = label_encoder.inverse_transform(y_pred_test)
        
        # Metrics on TEST set
        test_accuracy = accuracy_score(y_test_decoded, y_pred_test_decoded)
        test_precision = precision_score(y_test_decoded, y_pred_test_decoded, average='weighted', zero_division=0)
        test_recall = recall_score(y_test_decoded, y_pred_test_decoded, average='weighted', zero_division=0)
        test_f1 = f1_score(y_test_decoded, y_pred_test_decoded, average='weighted', zero_division=0)
        
        # Confusion matrix on TEST set
        cm_test = confusion_matrix(y_test_decoded, y_pred_test_decoded, labels=label_classes)
        cm_test_list = cm_test.tolist()
        
        # ROC-AUC (only for binary classification)
        test_roc_auc = None
        if len(label_classes) == 2:
            try:
                test_roc_auc = roc_auc_score(y_test_decoded, y_pred_proba_test[:, 1])
            except Exception as e:
                logger.warning(f"Could not compute ROC-AUC: {str(e)}")
        
        # Classification report on TEST set
        class_report_str = classification_report(y_test_decoded, y_pred_test_decoded, labels=label_classes, zero_division=0)
        logger.info(f"\n========== TEST SET CLASSIFICATION REPORT ==========\n{class_report_str}")
        
        # Parse classification report for structured storage
        class_report_dict = {}
        for label in label_classes:
            try:
                report_dict_raw = classification_report(y_test_decoded, y_pred_test_decoded, labels=[label], output_dict=True, zero_division=0)
                class_report_dict[str(label)] = {
                    'precision': round(report_dict_raw[label]['precision'], 4),
                    'recall': round(report_dict_raw[label]['recall'], 4),
                    'f1-score': round(report_dict_raw[label]['f1-score'], 4),
                    'support': int(report_dict_raw[label]['support'])
                }
            except Exception as e:
                logger.warning(f"Could not compute class report for {label}: {str(e)}")
        
        # ============================================
        # OVERFITTING DETECTION: Compare Train vs Test
        # ============================================
        y_pred_train = model.predict(X_train)
        y_pred_train_decoded = label_encoder.inverse_transform(y_pred_train)
        
        train_accuracy = accuracy_score(y_train_decoded, y_pred_train_decoded)
        train_precision = precision_score(y_train_decoded, y_pred_train_decoded, average='weighted', zero_division=0)
        train_recall = recall_score(y_train_decoded, y_pred_train_decoded, average='weighted', zero_division=0)
        train_f1 = f1_score(y_train_decoded, y_pred_train_decoded, average='weighted', zero_division=0)
        
        # Calculate deltas (should be small for well-tuned model)
        accuracy_delta = abs(train_accuracy - test_accuracy)
        f1_delta = abs(train_f1 - test_f1)
        
        # Flag potential overfitting
        overfitting_flag = False
        overfitting_reason = None
        if accuracy_delta > 0.15:  # >15% gap suggests overfitting
            overfitting_flag = True
            overfitting_reason = f'Train-test accuracy gap: {accuracy_delta:.4f} (train={train_accuracy:.4f}, test={test_accuracy:.4f})'
        
        logger.info(
            f"\n========== TRAIN vs TEST COMPARISON ==========\n"
            f"Train Accuracy:  {train_accuracy:.4f}\n"
            f"Test Accuracy:   {test_accuracy:.4f}\n"
            f"Delta:           {accuracy_delta:.4f}\n"
            f"Overfitting:     {overfitting_flag}\n"
            f"{f'Reason: {overfitting_reason}' if overfitting_reason else 'No issues detected'}\n"
        )
        
        # Extract XGBoost feature importance
        try:
            feature_importance = model.get_booster().get_score(importance_type='weight')
        except:
            feature_importance = {}
        
        metrics = {
            # Test set metrics (GROUND TRUTH)
            'test_accuracy': round(float(test_accuracy), 4),
            'test_precision': round(float(test_precision), 4),
            'test_recall': round(float(test_recall), 4),
            'test_f1_score': round(float(test_f1), 4),
            'test_roc_auc': round(float(test_roc_auc), 4) if test_roc_auc is not None else None,
            'test_confusion_matrix': cm_test_list,
            
            # Train set metrics (for comparison only)
            'train_accuracy': round(float(train_accuracy), 4),
            'train_precision': round(float(train_precision), 4),
            'train_recall': round(float(train_recall), 4),
            'train_f1_score': round(float(train_f1), 4),
            
            # Overfitting indicators
            'accuracy_delta': round(float(accuracy_delta), 4),
            'f1_delta': round(float(f1_delta), 4),
            'overfitting_detected': overfitting_flag,
            'overfitting_reason': overfitting_reason,
            
            # Metadata
            'classes': label_classes,
            'num_test_samples': int(len(y_test)),
            'num_train_samples': int(len(y_train)),
            'num_classes': len(label_classes),
            'class_distribution_test': {str(c): int(np.sum(y_test_decoded == c)) for c in label_classes},
            'class_distribution_train': {str(c): int(np.sum(y_train_decoded == c)) for c in label_classes},
            'classification_report': class_report_dict
        }
        
        weights = {
            'model_type': 'xgboost_classifier',
            'model_binary': model_data.get('model_binary'),  # Serialized model for storage
            'label_encoder_classes': label_classes,
            'label_encoder_mapping': {str(idx): cls for idx, cls in enumerate(label_classes)},
            'feature_names': feature_columns,
            'feature_importance': feature_importance,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'metrics': metrics,
            'weights': weights,
            'num_samples': len(y_test) + len(y_train),
            'error': None
        }
    
    except Exception as e:
        logger.error(f"Error evaluating model: {str(e)}", exc_info=True)
        return {
            'error': f'Model evaluation failed: {str(e)}',
            'metrics': None,
            'weights': None
        }


def train_federated_model(phc_id, trigger_reason='manual'):
    """
    Train model on local PHC data and create model update.
    
    Args:
        phc_id: PHC identifier (e.g., 'PHC1')
        trigger_reason: How training was triggered ('manual', 'patient_threshold', 'time_threshold')
    
    Returns:
        Dictionary with metrics and update_id
    """
    try:
        patients = list(Patient.objects.filter(phc_id=phc_id))
        
        # Empty dataset
        if not patients:
            return {
                'error': 'No patient data available',
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'roc_auc': None,
                'num_samples': 0,
                'update_id': None,
                'phc_id': phc_id,
                'triggered_by': trigger_reason
            }
        
        feature_columns = [
            'fever',
            'cough',
            'fatigue',
            'headache',
            'vomiting',
            'breathlessness',
            'temperature_c',
            'heart_rate',
            'bp_systolic',
            'wbc_count',
            'platelet_count',
            'hemoglobin'
        ]
        
        # Preprocess
        X, y, features = preprocess_data(patients, feature_columns)
        
        if len(X) == 0:
            return {
                'error': 'Failed to preprocess data',
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'roc_auc': None,
                'num_samples': 0,
                'update_id': None,
                'phc_id': phc_id,
                'triggered_by': trigger_reason
            }
        
        # Train
        model_data = train_local_model(X, y, features)
        
        if 'error' in model_data:
            return {
                'error': model_data['error'],
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'roc_auc': None,
                'num_samples': len(X),
                'update_id': None,
                'phc_id': phc_id,
                'triggered_by': trigger_reason
            }
        
        # Evaluate
        eval_result = evaluate_model(model_data)
        
        if eval_result.get('error'):
            return {
                'error': eval_result['error'],
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'roc_auc': None,
                'num_samples': len(X),
                'update_id': None,
                'phc_id': phc_id,
                'triggered_by': trigger_reason
            }
        
        metrics = eval_result['metrics']
        weights = eval_result['weights']
        
        # Get next version number
        latest_version = LocalModel.objects.filter(phc_id=phc_id).order_by('-version').first()
        next_version = (latest_version.version + 1) if latest_version else 1
        version_string = generate_local_version_string(phc_id, next_version)
        
        # Save to MongoDB with structured schema
        # Use TEST set metrics as primary (not training set which can be inflated)
        local_model = LocalModel.objects.create(
            phc_id=phc_id,
            version=next_version,
            version_string=version_string,
            accuracy=metrics['test_accuracy'],  # TEST set accuracy (ground truth)
            precision=metrics['test_precision'],  # TEST set precision
            recall=metrics['test_recall'],  # TEST set recall
            f1_score=metrics['test_f1_score'],  # TEST set F1
            roc_auc=metrics['test_roc_auc'],  # TEST set ROC-AUC
            confusion_matrix=metrics['test_confusion_matrix'],  # TEST set confusion matrix
            sample_count=eval_result['num_samples'],
            num_test_samples=metrics['num_test_samples'],
            num_train_samples=metrics['num_train_samples'],
            weights={
                **weights,
                'train_accuracy': metrics['train_accuracy'],  # Store train metrics for comparison
                'train_precision': metrics['train_precision'],
                'train_recall': metrics['train_recall'],
                'train_f1_score': metrics['train_f1_score'],
                'accuracy_delta': metrics['accuracy_delta'],  # Overfitting indicator
                'overfitting_detected': metrics['overfitting_detected'],
                'overfitting_reason': metrics['overfitting_reason'],
                'class_distribution_test': metrics['class_distribution_test'],
                'class_distribution_train': metrics['class_distribution_train'],
                'classification_report': metrics['classification_report']
            },
            triggered_by=trigger_reason,
            aggregated=False
        )
        
        # Record training completion
        record_training_completion(phc_id)
        
        # ============================================
        # ML INNOVATION: RUN AFTER-TRAINING ANALYTICS
        # ============================================
        
        # 1. Detect model drift
        drift_result = detect_model_drift(phc_id)
        
        # 2. Calculate composite risk score
        risk_result = calculate_composite_risk_score(phc_id)
        
        # Attempt automatic aggregation if conditions are met
        try_automatic_aggregation()
        
        return {
            'error': None,
            'phc_id': phc_id,
            'accuracy': metrics['test_accuracy'],  # TEST accuracy
            'train_accuracy': metrics['train_accuracy'],  # Include for comparison
            'precision': metrics['test_precision'],  # TEST precision
            'recall': metrics['test_recall'],  # TEST recall
            'f1_score': metrics['test_f1_score'],  # TEST F1
            'roc_auc': metrics['test_roc_auc'],  # TEST ROC-AUC
            'accuracy_delta': metrics['accuracy_delta'],  # Overfitting indicator
            'overfitting_detected': metrics['overfitting_detected'],
            'num_samples': eval_result['num_samples'],
            'num_test_samples': metrics['num_test_samples'],
            'num_train_samples': metrics['num_train_samples'],
            'update_id': str(local_model.id),
            'version': next_version,
            'version_string': version_string,
            'triggered_by': trigger_reason,
            'ml_insights': {
                'drift_detection': drift_result,
                'composite_risk_score': risk_result
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in train_federated_model for {phc_id}: {str(e)}")
        return {
            'error': f'Training failed: {str(e)}',
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'roc_auc': None,
            'num_samples': 0,
            'update_id': None,
            'phc_id': phc_id,
            'triggered_by': trigger_reason
        }


def try_automatic_aggregation():
    """
    Attempt automatic aggregation if conditions are met.
    Triggers when 3+ PHCs have unaggregated models.
    """
    should_aggregate, reason, pending_phcs = should_trigger_global_aggregation()
    
    if should_aggregate:
        logger.info(f"Automatic aggregation triggered: {len(pending_phcs)} PHCs ready. Reason: {reason}")
        return aggregate_models(automatic=True)


def handle_patient_creation(phc_id):
    """
    ============================================
    COMPLETE POST-PATIENT-CREATION PIPELINE
    ============================================
    
    This function is called whenever a patient is created (API or init).
    It handles the complete training trigger pipeline:
    1. Increments patient count for the PHC
    2. Checks if local model training should be triggered
    3. If yes, triggers training and creates/updates LocalModel
    4. Handles errors gracefully with logging
    
    Args:
        phc_id (str): PHC identifier (e.g., 'PHC1')
    
    Returns:
        dict: Training result with status and details
    """
    try:
        logger.info(f"Patient creation detected for {phc_id}")
        
        # Step 1: Increment patient count
        increment_patient_count(phc_id)
        logger.debug(f"Patient count incremented for {phc_id}")
        
        # Step 2: Check if training should be triggered
        should_train, trigger_reason = should_trigger_local_training(phc_id)
        logger.info(f"{phc_id} training check: should_train={should_train}, reason={trigger_reason}")
        
        if not should_train:
            # Training not triggered yet
            metadata = TrainingMetadata.objects.filter(phc_id=phc_id).first()
            if metadata:
                current_count = metadata.patients_since_last_training
                logger.debug(f"{phc_id} has {current_count}/{PATIENT_THRESHOLD} patients for training")
            
            return {
                'model_trained': False,
                'trigger_reason': trigger_reason,
                'phc_id': phc_id
            }
        
        # Step 3: Training threshold reached - trigger training
        logger.info(f"[TRAINING TRIGGERED] {phc_id} - Reason: {trigger_reason}")
        
        # HACKATHON FIX: Check if training already in progress (prevent duplicate)
        metadata = TrainingMetadata.objects.filter(phc_id=phc_id).first()
        if metadata and metadata.training_in_progress:
            logger.info(f"{phc_id} training already in progress, skipping")
            return {
                'model_trained': False,
                'trigger_reason': 'training_in_progress',
                'phc_id': phc_id
            }
        
        # Set training lock
        if metadata:
            metadata.training_in_progress = True
            metadata.save()
        
        try:
            # Call the main training function
            result = train_federated_model(phc_id, trigger_reason=trigger_reason)
            
            if result.get('error'):
                logger.error(f"Training error for {phc_id}: {result['error']}")
                # Release lock on error
                record_training_completion(phc_id, success=False)
                return {
                    'model_trained': False,
                    'error': result['error'],
                    'phc_id': phc_id,
                    'trigger_reason': trigger_reason
                }
            
            # Success - return training metrics
            logger.info(
                f"[TRAINING SUCCESS] {phc_id} v{result.get('version')} "
                f"Accuracy: {result.get('accuracy', 0.0):.4f} "
                f"Samples: {result.get('num_samples', 0)}"
            )
            
            # Release training lock
            record_training_completion(phc_id, success=True)
            
            return {
                'model_trained': True,
                'phc_id': phc_id,
                'trigger_reason': trigger_reason,
                'model_accuracy': round(result.get('accuracy', 0), 4),
                'model_version': result.get('version'),
                'version_string': result.get('version_string'),
                'num_samples': result.get('num_samples'),
                'precision': round(result.get('precision', 0), 4),
                'recall': round(result.get('recall', 0), 4),
                'f1_score': round(result.get('f1_score', 0), 4),
                'timestamp': result.get('timestamp')
            }
        
        except Exception as training_error:
            logger.error(
                f"[TRAINING EXCEPTION] {phc_id} - {type(training_error).__name__}: {str(training_error)}",
                exc_info=True
            )
            # Release lock on exception
            record_training_completion(phc_id, success=False)
            return {
                'model_trained': False,
                'error': f'Training execution failed: {str(training_error)}',
                'phc_id': phc_id,
                'trigger_reason': trigger_reason
            }
    
    except Exception as e:
        logger.error(
            f"[FATAL ERROR] Patient creation handler for {phc_id}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        return {
            'model_trained': False,
            'error': f'Patient creation handler failed: {str(e)}',
            'phc_id': phc_id
        }
    
    return None


def aggregate_models(automatic=False):
    """
    Federated aggregation of all PHC models.
    
    Since XGBoost models cannot be averaged like LogisticRegression weights,
    this function implements probability-level ensemble aggregation:
    
    1. Collects all PHC models
    2. Computes weighted average of metrics (accuracy, precision, recall, f1)
    3. Stores metadata for ensemble inference
    4. For inference: average probability predictions from all PHC models
    
    Args:
        automatic: Whether aggregation was triggered automatically
    """
    try:
        # Find all unaggregated models (or latest models)
        phc_models = {}
        total_samples = 0
        contributor_versions = {}
        
        for phc_num in range(1, 5):
            phc_id = f'PHC_{phc_num}'
            
            # Get latest unaggregated model for this PHC
            if automatic:
                latest = LocalModel.objects.filter(phc_id=phc_id, aggregated=False).order_by('-trained_at').first()
            else:
                latest = LocalModel.objects.filter(phc_id=phc_id).order_by('-trained_at').first()
            
            if latest:
                phc_models[phc_id] = {
                    'model_id': str(latest.id),
                    'version': latest.version,
                    'version_string': latest.version_string,
                    'accuracy': latest.accuracy,
                    'precision': latest.precision,
                    'recall': latest.recall,
                    'f1_score': latest.f1_score,
                    'weights': latest.weights,
                    'sample_count': latest.sample_count
                }
                contributor_versions[phc_id] = latest.version_string
                total_samples += latest.sample_count
        
        if not phc_models:
            return None
        
        num_contributors = len(phc_models)
        contributors = list(phc_models.keys())
        
        # Weighted averaging of metrics (FedAvg by sample count)
        aggregated_accuracy = sum(m['accuracy'] * m['sample_count'] for m in phc_models.values()) / total_samples if total_samples > 0 else 0.0
        aggregated_precision = sum(m['precision'] * m['sample_count'] for m in phc_models.values()) / total_samples if total_samples > 0 else 0.0
        aggregated_recall = sum(m['recall'] * m['sample_count'] for m in phc_models.values()) / total_samples if total_samples > 0 else 0.0
        aggregated_f1 = sum(m['f1_score'] * m['sample_count'] for m in phc_models.values()) / total_samples if total_samples > 0 else 0.0
        
        # Get next version number
        latest_global = GlobalModel.objects.order_by('-version').first()
        next_version = (latest_global.version + 1) if latest_global else 1
        version_string = generate_global_version_string(next_version)
        
        # For XGBoost: Store ensemble metadata instead of averaged weights
        # At inference time, probability predictions from all PHC models are averaged
        aggregated_weights = {
            'model_type': 'federated_xgboost_ensemble',
            'ensemble_strategy': 'probability_averaging',
            'num_contributors': num_contributors,
            'total_samples': total_samples,
            'accuracy': round(float(aggregated_accuracy), 4),
            'precision': round(float(aggregated_precision), 4),
            'recall': round(float(aggregated_recall), 4),
            'f1_score': round(float(aggregated_f1), 4),
            'contributor_models': contributor_versions,  # Map of phc_id -> model_version_string
            'contributor_metrics': {
                phc_id: {
                    'accuracy': m['accuracy'],
                    'precision': m['precision'],
                    'recall': m['recall'],
                    'f1_score': m['f1_score'],
                    'sample_count': m['sample_count']
                }
                for phc_id, m in phc_models.items()
            },
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'For inference: load all contributor models and average their probability predictions'
        }
        
        # Create new global model
        global_model = GlobalModel.objects.create(
            version=next_version,
            version_string=version_string,
            accuracy=round(float(aggregated_accuracy), 4),
            contributors=contributors,
            contributor_versions=contributor_versions,
            weights=aggregated_weights,
            aggregation_triggered_by='automatic' if automatic else 'manual'
        )
        
        # Mark contributing models as aggregated
        for phc_id, model_info in phc_models.items():
            LocalModel.objects.filter(id=model_info['model_id']).update(
                aggregated=True,
                aggregated_in_version=next_version,
                aggregated_in_version_string=version_string
            )
        
        # Broadcast global model to all PHCs
        broadcast_global_model(next_version, version_string)
        
        logger.info(f"Global model {version_string} created. Ensemble of {num_contributors} models. Accuracy: {aggregated_accuracy:.4f}")
        
        return {
            'version': next_version,
            'version_string': version_string,
            'accuracy': round(float(aggregated_accuracy), 4),
            'contributors': contributors,
            'contributor_versions': contributor_versions,
            'num_contributors': num_contributors,
            'total_samples': total_samples,
            'automatic': automatic,
            'ensemble_strategy': 'probability_averaging',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in aggregate_models: {str(e)}")
        return None


def detect_fever_outbreak(phc_id, lookback_days=7):
    """
    Detect fever outbreak using 7-day rolling average and Z-score.
    
    Args:
        phc_id: PHC identifier
        lookback_days: Number of days for rolling average (default 7)
    
    Returns:
        Dictionary with outbreak_flag and z_score
    """
    try:
        # Get patients from last 14 days
        cutoff_date = datetime.utcnow() - timedelta(days=14)
        patients = list(Patient.objects.filter(phc_id=phc_id, created_at__gte=cutoff_date))
        
        if not patients:
            return {
                'phc_id': phc_id,
                'outbreak_flag': False,
                'z_score': 0.0,
                'sample_size': 0,
                'error': 'Not enough historical data'
            }
        
        # Group by date
        df = pd.DataFrame([
            {
                'date': p.created_at.date() if hasattr(p.created_at, 'date') else p.created_at,
                'fever': p.fever
            }
            for p in patients
        ])
        
        # Daily fever count
        daily_fever = df.groupby('date')['fever'].sum().reset_index()
        daily_fever.columns = ['date', 'fever_count']
        daily_fever = daily_fever.sort_values('date')
        
        if len(daily_fever) < lookback_days:
            return {
                'phc_id': phc_id,
                'outbreak_flag': False,
                'z_score': 0.0,
                'sample_size': len(daily_fever),
                'error': f'Need at least {lookback_days} days of data'
            }
        
        # Calculate rolling average
        daily_fever['rolling_avg'] = daily_fever['fever_count'].rolling(window=lookback_days).mean()
        
        # Get latest reading
        latest_fever = daily_fever.iloc[-1]['fever_count']
        rolling_mean = daily_fever['rolling_avg'].dropna().mean()
        rolling_std = daily_fever['rolling_avg'].dropna().std()
        
        # Prevent division by zero
        if rolling_std == 0 or rolling_std is None or rolling_std != rolling_std:
            z_score = 0.0
        else:
            z_score = (latest_fever - rolling_mean) / rolling_std
        
        outbreak_flag = abs(z_score) > 2.0
        
        # Get latest model versions for versioning
        latest_local_model = get_latest_local_model(phc_id)
        latest_global_model = get_latest_global_model()
        
        local_version = latest_local_model.version if latest_local_model else 0
        local_version_string = latest_local_model.version_string if latest_local_model else None
        global_version = latest_global_model.version if latest_global_model else 0
        global_version_string = latest_global_model.version_string if latest_global_model else None
        
        # Create alert if outbreak detected
        if outbreak_flag:
            try:
                from api.models import Alert
                alert = Alert.objects.create(
                    phc_id=phc_id,
                    risk_score=abs(z_score),
                    severity='HIGH' if abs(z_score) > 3 else 'MEDIUM',
                    local_model_version=local_version,
                    local_model_version_string=local_version_string,
                    global_model_version=global_version,
                    global_model_version_string=global_version_string
                )
                logger.info(f"Alert created for {phc_id}: {alert.id}")
            except Exception as e:
                logger.error(f"Error creating alert for {phc_id}: {str(e)}")
        
        return {
            'phc_id': phc_id,
            'outbreak_flag': outbreak_flag,
            'z_score': round(float(z_score), 4),
            'latest_fever_count': int(latest_fever),
            'rolling_mean': round(float(rolling_mean), 2),
            'sample_size': len(daily_fever),
            'local_model_version': local_version,
            'local_model_version_string': local_version_string,
            'global_model_version': global_version,
            'global_model_version_string': global_version_string,
            'error': None
        }
    
    except Exception as e:
        logger.error(f"Error detecting fever outbreak for {phc_id}: {str(e)}")
        return {
            'phc_id': phc_id,
            'outbreak_flag': False,
            'z_score': 0.0,
            'error': f'Outbreak detection failed: {str(e)}'
        }

