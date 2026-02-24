"""
FedHealthAI Backend API Views - Refactored for MVP Polish

Provides:
- Authentication (Register, Login)
- Patient Management (Submit, List)
- Federated Learning (Training trigger, Model aggregation)
- Surveillance Dashboards (PHC, District, Officer)
- Health Check

All endpoints enforce strict privacy-first data isolation.
"""

import logging
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from api.models import User, LocalModel, GlobalModel, Patient, PHC, Alert, CohortSnapshot
from api.authentication import (
    hash_password, verify_password, generate_token, JWTAuthentication
)
from api.ml_utils import (
    train_federated_model, aggregate_models,
    should_trigger_local_training, increment_patient_count,
    get_latest_global_model, get_latest_local_model,
    handle_patient_creation
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================
# STANDARDIZED ERROR RESPONSE HELPER
# ============================================

def error_response(error_msg, details="", status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standardized API error response format.
    
    Args:
        error_msg (str): Short error message
        details (str): Detailed explanation (optional)
        status_code (int): HTTP status code
        
    Returns:
        tuple: (Response, status_code)
    """
    response_data = {"error": error_msg}
    if details:
        response_data["details"] = details
    return Response(response_data, status=status_code), status_code


# ============================================
# PRIVACY-FIRST HELPER FUNCTIONS
# ============================================

def get_phc_aggregated_metrics(phc_id):
    """
    Get aggregated metrics for a PHC WITHOUT exposing patient-level data.
    
    Privacy guarantee: No raw patient records are accessed.
    
    Args:
        phc_id (str): PHC identifier
        
    Returns:
        dict: Aggregated model metrics (no patient data)
    """
    try:
        latest_model = LocalModel.objects.filter(phc_id=phc_id).order_by('-version').first()
        
        if not latest_model:
            return {
                'phc_id': phc_id,
                'total_patients': 0,
                'model_version': None,
                'model_accuracy': 0.0,
                'last_updated': None
            }
        
        return {
            'phc_id': phc_id,
            'total_patients': latest_model.sample_count,
            'model_version': latest_model.version_string,
            'model_accuracy': float(latest_model.accuracy),
            'model_metrics': {
                'precision': float(latest_model.precision),
                'recall': float(latest_model.recall),
                'f1_score': float(latest_model.f1_score),
            },
            'last_updated': latest_model.trained_at.isoformat() if latest_model.trained_at else None
        }
    except Exception as e:
        logger.error(f"Error getting metrics for {phc_id}: {str(e)}")
        return {
            'phc_id': phc_id,
            'error': "Unable to retrieve metrics",
            'total_patients': 0
        }


def validate_phc_access(user, requested_phc_id):
    """
    Enforce: PHC users can ONLY access their own PHC data.
    
    Returns:
        tuple: (is_allowed: bool, reason: str)
    """
    if user.role == 'PHC_USER':
        if user.phc_id != requested_phc_id:
            return False, f"Access denied: You can only access your assigned PHC"
    return True, "Access granted"


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

class RegisterView(APIView):
    """Register a new user with role and PHC assignment."""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            name = request.data.get('name', '')
            role = request.data.get('role', 'PHC_USER')
            phc_id = request.data.get('phc_id')

            # Validation
            if not username or not password:
                return Response({
                    'error': 'Username and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not username.strip() or not password.strip():
                return Response({
                    'error': 'Username and password cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)

            valid_roles = ['PHC_USER', 'DISTRICT_ADMIN', 'SURVEILLANCE_OFFICER']
            if role not in valid_roles:
                return Response({
                    'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            if role == 'PHC_USER' and not phc_id:
                return Response({
                    'error': 'PHC selection is required for PHC User role'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if username already exists
            if User.objects(username=username).first():
                return Response({
                    'error': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user
            user = User.objects.create(
                username=username,
                password_hash=hash_password(password),
                role=role,
                phc_id=phc_id
            )

            # Generate token for immediate login
            token = generate_token(str(user.id))

            logger.info(f"User registered: {username} ({role})")

            return Response({
                'message': 'User registered successfully',
                'token': token,
                'user': {
                    'id': str(user.id),
                    'username': username,
                    'role': role
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return Response({
                'error': f'Registration failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    """Authenticate user and return JWT token."""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            if not username or not password:
                return Response({
                    'error': 'Username and password are required'
                }, status=status.HTTP_401_UNAUTHORIZED)

            user = User.objects.get(username=username)

            if not verify_password(password, user.password_hash):
                logger.warning(f"Failed login attempt: {username}")
                return Response({
                    'error': 'Invalid username or password'
                }, status=status.HTTP_401_UNAUTHORIZED)

            token = generate_token(str(user.id))
            logger.info(f"User logged in: {username}")

            return Response({
                'token': token,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'role': user.role,
                    'phc_id': user.phc_id
                }
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.warning(f"Login attempt with non-existent user")
            return Response({
                'error': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return Response({
                'error': f'Login failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# PATIENT MANAGEMENT ENDPOINTS
# ============================================

class PatientSubmitView(APIView):
    """Submit a patient record from PHC and trigger training if needed."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if request.user.role != 'PHC_USER':
                return Response({
                    'error': 'Only PHC users can submit patients'
                }, status=status.HTTP_403_FORBIDDEN)

            phc_id = request.user.phc_id
            
            # Map PHC to city (handle both PHC1 and PHC_1 formats)
            phc_to_city = {
                'PHC1': 'Mumbai', 'PHC_1': 'Mumbai',
                'PHC2': 'Delhi', 'PHC_2': 'Delhi',
                'PHC3': 'Bangalore', 'PHC_3': 'Bangalore',
                'PHC4': 'Chennai', 'PHC_4': 'Chennai',
                'PHC5': 'Kolkata', 'PHC_5': 'Kolkata'
            }
            city = phc_to_city.get(phc_id, 'Unknown')
            
            # Validate required fields (18-column schema)
            required_fields = [
                'age', 'temperature_c', 'heart_rate', 'bp_systolic',
                'wbc_count', 'platelet_count', 'hemoglobin', 'disease_label'
            ]
            missing_fields = [f for f in required_fields if f not in request.data or request.data.get(f) == '']
            if missing_fields:
                return Response({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate unique patient_id
            patient_count = Patient.objects.count() + 1
            patient_id = f"P{patient_count:05d}"
            
            # Create patient record with 18 columns
            patient = Patient.objects.create(
                patient_id=patient_id,
                phc_id=phc_id,
                city=city,
                # Demographics
                age=int(request.data.get('age')),
                gender=request.data.get('gender', 'Unknown'),
                # Symptoms (binary 0/1)
                fever=int(request.data.get('fever', 0)),
                cough=int(request.data.get('cough', 0)),
                fatigue=int(request.data.get('fatigue', 0)),
                headache=int(request.data.get('headache', 0)),
                vomiting=int(request.data.get('vomiting', 0)),
                breathlessness=int(request.data.get('breathlessness', 0)),
                # Vital Signs
                temperature_c=float(request.data.get('temperature_c')),
                heart_rate=int(request.data.get('heart_rate')),
                bp_systolic=int(request.data.get('bp_systolic')),
                # Lab Values
                wbc_count=int(request.data.get('wbc_count')),
                platelet_count=int(request.data.get('platelet_count')),
                hemoglobin=float(request.data.get('hemoglobin')),
                # Diagnosis
                disease_label=request.data.get('disease_label'),
                severity_level=request.data.get('severity_level', 'Low')
            )
            
            logger.info(f"Patient submitted for {phc_id}: {patient.disease_label}")
            
            # Create cohort snapshot for historical tracking
            self._create_cohort_snapshot(phc_id)
            
            # Check training trigger via post-patient-creation pipeline
            training_result = handle_patient_creation(phc_id)
            
            return Response({
                'message': 'Patient recorded successfully',
                'patient_id': str(patient.id),
                'training': training_result
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}", exc_info=True)
            return Response({
                'error': f'Invalid data type: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Patient submission error: {str(e)}", exc_info=True)
            return Response({
                'error': f'Patient submission failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_cohort_snapshot(self, phc_id):
        """Create a cohort snapshot for historical tracking after patient submission."""
        try:
            # Use PyMongo directly to avoid mongoengine schema caching issues
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/')
            db_name = 'fedhealth_db'  # Match the database used by mongoengine
            db = client[db_name]
            patients_col = db['patients']
            
            # Get patients for this PHC using PyMongo (no schema validation)
            patients_docs = list(patients_col.find({'phc_id': phc_id}))
            if not patients_docs:
                return
            
            total = len(patients_docs)
            
            # Calculate demographics
            ages = [p.get('age') for p in patients_docs if p.get('age')]
            avg_age = sum(ages) / len(ages) if ages else 0
            males = sum(1 for p in patients_docs if p.get('gender') == 'Male')
            females = sum(1 for p in patients_docs if p.get('gender') == 'Female')
            male_pct = (males / total * 100) if total > 0 else 0
            female_pct = (females / total * 100) if total > 0 else 0
            
            # Calculate symptoms
            fever_count = sum(1 for p in patients_docs if p.get('fever') == 1)
            cough_count = sum(1 for p in patients_docs if p.get('cough') == 1)
            fatigue_count = sum(1 for p in patients_docs if p.get('fatigue') == 1)
            headache_count = sum(1 for p in patients_docs if p.get('headache') == 1)
            vomiting_count = sum(1 for p in patients_docs if p.get('vomiting') == 1)
            breathlessness_count = sum(1 for p in patients_docs if p.get('breathlessness') == 1)
            
            # Calculate vital signs
            temps = [p.get('temperature_c') for p in patients_docs if p.get('temperature_c')]
            avg_temp = sum(temps) / len(temps) if temps else 0
            hrs = [p.get('heart_rate') for p in patients_docs if p.get('heart_rate')]
            avg_hr = sum(hrs) / len(hrs) if hrs else 0
            bps = [p.get('bp_systolic') for p in patients_docs if p.get('bp_systolic')]
            avg_bp = sum(bps) / len(bps) if bps else 0
            
            # Calculate lab values
            wbcs = [p.get('wbc_count') for p in patients_docs if p.get('wbc_count')]
            avg_wbc = sum(wbcs) / len(wbcs) if wbcs else 0
            platelets = [p.get('platelet_count') for p in patients_docs if p.get('platelet_count')]
            avg_platelet = sum(platelets) / len(platelets) if platelets else 0
            hbs = [p.get('hemoglobin') for p in patients_docs if p.get('hemoglobin')]
            avg_hb = sum(hbs) / len(hbs) if hbs else 0
            
            # Calculate disease distribution
            disease_dist = {}
            for p in patients_docs:
                disease = p.get('disease_label', 'Unknown')
                disease_dist[disease] = disease_dist.get(disease, 0) + 1
            
            # Calculate severity
            high_severity = sum(1 for p in patients_docs if p.get('severity_level') in ['High', 'Critical'])
            high_severity_pct = (high_severity / total * 100) if total > 0 else 0
            
            # Create snapshot
            snapshot = CohortSnapshot.objects.create(
                phc_id=phc_id,
                total_patients=total,
                average_age=round(avg_age, 2),
                male_percentage=round(male_pct, 2),
                female_percentage=round(female_pct, 2),
                fever_percentage=round((fever_count / total * 100), 2),
                cough_percentage=round((cough_count / total * 100), 2),
                fatigue_percentage=round((fatigue_count / total * 100), 2),
                headache_percentage=round((headache_count / total * 100), 2),
                vomiting_percentage=round((vomiting_count / total * 100), 2),
                breathlessness_percentage=round((breathlessness_count / total * 100), 2),
                average_temperature_c=round(avg_temp, 2),
                average_heart_rate=round(avg_hr, 2),
                average_bp_systolic=round(avg_bp, 2),
                average_wbc_count=round(avg_wbc, 0),
                average_platelet_count=round(avg_platelet, 0),
                average_hemoglobin=round(avg_hb, 2),
                disease_distribution=disease_dist,
                high_severity_percentage=round(high_severity_pct, 2),
                snapshot_date=datetime.now()
            )
            logger.info(f"Created cohort snapshot for {phc_id}: {total} patients")
        except Exception as e:
            logger.error(f"Failed to create cohort snapshot: {str(e)}", exc_info=True)


class PHCPatientsView(APIView):
    """Retrieve all patients for the authenticated PHC user."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.user.role != 'PHC_USER':
                return error_response(
                    "Only PHC users can view records",
                    status_code=status.HTTP_403_FORBIDDEN
                )[0]

            phc_id = request.user.phc_id
            
            # Verify access
            is_allowed, reason = validate_phc_access(request.user, phc_id)
            if not is_allowed:
                return error_response(reason, status_code=status.HTTP_403_FORBIDDEN)[0]
            
            # Query both databases - new submissions in 'fedhealth', seed data in 'fedhealth_db'
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/')
            
            all_patients = []
            
            # 1. First, get newly submitted patients from 'fedhealth' (via mongoengine)
            try:
                db_new = client['fedhealth']
                patients_col_new = db_new['patients']
                new_patients = list(patients_col_new.find(
                    {'phc_id': phc_id},
                    sort=[('created_at', -1)]
                ))
                all_patients.extend(new_patients)
                logger.info(f"Found {len(new_patients)} new patients in 'fedhealth' for {phc_id}")
            except Exception as e:
                logger.warning(f"Could not query 'fedhealth' database: {str(e)}")
            
            # 2. Then, get seed data from 'fedhealth_db'
            try:
                db_seed = client['fedhealth_db']
                patients_col_seed = db_seed['patients']
                seed_patients = list(patients_col_seed.find(
                    {'phc_id': phc_id},
                    sort=[('created_at', -1)]
                ))
                all_patients.extend(seed_patients)
                logger.info(f"Found {len(seed_patients)} seed patients in 'fedhealth_db' for {phc_id}")
            except Exception as e:
                logger.warning(f"Could not query 'fedhealth_db' database: {str(e)}")
            
            # 3. Deduplicate by _id and return
            seen_ids = set()
            unique_patients = []
            for p in all_patients:
                pid = str(p.get('_id', ''))
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    unique_patients.append(p)
            
            data = [{
                'id': str(p.get('_id', '')),
                'age': p.get('age'),
                'gender': p.get('gender'),
                'fever': p.get('fever'),
                'cough': p.get('cough'),
                'fatigue': p.get('fatigue'),
                'headache': p.get('headache'),
                'vomiting': p.get('vomiting'),
                'breathlessness': p.get('breathlessness'),
                'temperature_c': p.get('temperature_c'),
                'heart_rate': p.get('heart_rate'),
                'bp_systolic': p.get('bp_systolic'),
                'wbc_count': p.get('wbc_count'),
                'platelet_count': p.get('platelet_count'),
                'hemoglobin': p.get('hemoglobin'),
                'disease_label': p.get('disease_label'),
                'severity_level': p.get('severity_level'),
                'created_at': p.get('created_at').isoformat() if p.get('created_at') else None
            } for p in unique_patients]
            
            logger.info(f"Retrieved {len(data)} total unique patients for {phc_id}")

            return Response({
                'count': len(data),
                'patients': data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving patients: {str(e)}")
            return error_response(
                "Failed to retrieve patients",
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )[0]


# ============================================
# FEDERATED LEARNING ENDPOINTS
# ============================================

class AggregateModelsView(APIView):
    """Trigger model aggregation (District Admin only)."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if request.user.role != 'DISTRICT_ADMIN':
                return error_response(
                    "Only district admins can aggregate models",
                    status_code=status.HTTP_403_FORBIDDEN
                )[0]

            logger.info("Aggregation requested by district admin")
            
            # Auto-trigger training for any PHC with >= 20 patients that hasn't trained yet
            from api.models import Patient, LocalModel
            for phc_num in range(1, 5):
                phc_id = f'PHC_{phc_num}'
                patient_count = Patient.objects.filter(phc_id=phc_id).count()
                has_model = LocalModel.objects.filter(phc_id=phc_id).first() is not None
                
                if patient_count >= 20 and not has_model:
                    logger.info(f"Auto-training {phc_id} ({patient_count} patients)")
                    train_federated_model(phc_id)

            result = aggregate_models(automatic=False)
            
            if not result:
                return error_response(
                    "No trained models to aggregate",
                    "Please submit patients from PHC dashboards first",
                    status_code=status.HTTP_400_BAD_REQUEST
                )[0]
            
            logger.info(f"Aggregation successful: {result['version_string']}")

            return Response({
                'message': 'Models aggregated successfully',
                'accuracy': round(result.get('accuracy', 0), 4),
                'num_contributors': result.get('num_contributors'),
                'contributors': result.get('contributors'),
                'version': result.get('version'),
                'version_string': result.get('version_string'),
                'timestamp': result.get('timestamp')
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Aggregation failed: {str(e)}")
            return error_response(
                "Aggregation failed",
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )[0]


class SurveillanceAlertsView(APIView):
    """Retrieve surveillance alerts (District Admin & Surveillance Officer)."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.user.role not in ['DISTRICT_ADMIN', 'SURVEILLANCE_OFFICER']:
                return error_response(
                    "Access denied",
                    status_code=status.HTTP_403_FORBIDDEN
                )[0]

            # Get alerts from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            alerts = Alert.objects.filter(
                created_at__gte=thirty_days_ago
            ).order_by('-created_at')[:100]
            
            alert_data = [{
                'id': str(a.id),
                'phc_id': a.phc_id,
                'alert_type': a.alert_type,
                'risk_score': round(float(a.risk_score), 2) if a.risk_score else 0,
                'severity': a.severity,
                'created_at': a.created_at.isoformat(),
                'message': a.message
            } for a in alerts]
            
            logger.info(f"Retrieved {len(alert_data)} alerts")

            return Response({
                'total_alerts': len(alert_data),
                'alerts': alert_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving alerts: {str(e)}")
            return error_response(
                "Failed to retrieve alerts",
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )[0]


# ============================================
# DASHBOARD ENDPOINTS
# ============================================

class PHCDashboardMetricsView(APIView):
    """PHC Dashboard: Local model metrics, drift status, risk scores."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            if request.user.role != 'PHC_USER':
                return error_response(
                    "Only PHC users can access their dashboard",
                    status_code=status.HTTP_403_FORBIDDEN
                )[0]
            
            phc_id = request.user.phc_id
            
            # Get latest local model
            latest_model = LocalModel.objects.filter(phc_id=phc_id).order_by('-trained_at').first()
            
            model_accuracy = 0.0
            model_version = None
            drift_detected = False
            
            if latest_model:
                model_accuracy = float(latest_model.accuracy) if latest_model.accuracy else 0.0
                model_version = latest_model.version_string
                
                # Check for drift (>10% accuracy drop)
                if latest_model.version > 1:
                    previous_model = LocalModel.objects.filter(
                        phc_id=phc_id,
                        version=latest_model.version - 1
                    ).first()
                    
                    if previous_model and previous_model.accuracy:
                        accuracy_drop = float(previous_model.accuracy) - model_accuracy
                        drift_detected = accuracy_drop > 10.0
            
            # Get patient count
            patient_count = Patient.objects.filter(phc_id=phc_id).count()
            
            # Get latest risk score
            latest_alert = Alert.objects.filter(phc_id=phc_id).order_by('-created_at').first()
            risk_score = float(latest_alert.risk_score) if latest_alert else 0.0
            alert_severity = latest_alert.severity if latest_alert else 'UNKNOWN'
            
            # Get alert history
            alerts_7_days = Alert.objects.filter(
                phc_id=phc_id,
                created_at__gte=datetime.utcnow() - timedelta(days=7)
            ).order_by('created_at')
            
            alert_history = [{
                'date': a.created_at.isoformat(),
                'risk_score': round(float(a.risk_score), 2),
                'severity': a.severity
            } for a in alerts_7_days]
            
            logger.info(f"PHC Dashboard accessed for {phc_id}")

            return Response({
                'phc_id': phc_id,
                'model': {
                    'version': model_version,
                    'accuracy': round(model_accuracy, 4),
                    'last_trained': latest_model.trained_at.isoformat() if latest_model else None
                },
                'drift': {
                    'detected': drift_detected,
                    'warning': 'Model accuracy dropped >10%' if drift_detected else None
                },
                'risk': {
                    'latest_score': round(risk_score, 2),
                    'severity': alert_severity
                },
                'patients': {'total': patient_count},
                'alerts_7_days': alert_history,
                'last_updated': datetime.utcnow().isoformat()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"PHC dashboard error: {str(e)}")
            return error_response(
                "Failed to load PHC dashboard",
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )[0]


class DistrictDashboardMetricsView(APIView):
    """District Dashboard: Global model, aggregation, PHC metrics."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            if request.user.role not in ['DISTRICT_ADMIN', 'SURVEILLANCE_OFFICER']:
                return error_response(
                    "Access denied",
                    status_code=status.HTTP_403_FORBIDDEN
                )[0]
            
            # Get global model
            latest_global = GlobalModel.objects.order_by('-version').first()
            
            global_accuracy = 0.0
            contributors = []
            
            if latest_global:
                global_accuracy = float(latest_global.accuracy) if latest_global.accuracy else 0.0
                contributors = latest_global.contributors or []
            
            # Get all PHCs
            phc_ids = set([u.phc_id for u in User.objects.filter(role='PHC_USER') if u.phc_id])
            
            phc_metrics = []
            high_risk_phcs = []
            
            for phc_id in phc_ids:
                latest_local = LocalModel.objects.filter(phc_id=phc_id).order_by('-trained_at').first()
                latest_alert = Alert.objects.filter(phc_id=phc_id).order_by('-created_at').first()
                patient_count = Patient.objects.filter(phc_id=phc_id).count()
                
                risk_score = float(latest_alert.risk_score) if latest_alert else 0.0
                severity = latest_alert.severity if latest_alert else 'UNKNOWN'
                
                phc_data = {
                    'phc_id': phc_id,
                    'local_model_version': latest_local.version_string if latest_local else 'Not trained',
                    'local_model_accuracy': round(float(latest_local.accuracy), 4) if latest_local else 0.0,
                    'risk_score': round(risk_score, 2),
                    'severity': severity,
                    'patients': patient_count
                }
                
                phc_metrics.append(phc_data)
                
                if severity in ['HIGH', 'CRITICAL']:
                    high_risk_phcs.append(phc_data)
            
            logger.info(f"District Dashboard accessed, {len(phc_metrics)} PHCs")
            
            # Calculate average risk score across all PHCs (capped at 100)
            if phc_metrics:
                avg_risk = sum([p['risk_score'] for p in phc_metrics]) / len(phc_metrics)
                avg_risk = min(avg_risk, 100.0)  # Cap at 100%
            else:
                avg_risk = 0.0

            return Response({
                'global_model': {
                    'version': latest_global.version if latest_global else 0,
                    'accuracy': round(global_accuracy, 4),
                    'contributors': contributors,
                    'total_contributors': len(contributors),
                    'aggregation_round': len(contributors)
                },
                'average_phc_risk_score': round(avg_risk, 4),
                'phc_breakdown': phc_metrics,
                'high_risk_phcs': high_risk_phcs,
                'last_updated': datetime.utcnow().isoformat()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"District dashboard error: {str(e)}")
            return error_response(
                "Failed to load district dashboard",
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )[0]


class SurveillanceDashboardMetricsView(APIView):
    """Surveillance Dashboard: Outbreak trends, alerts, heatmap."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            if request.user.role != 'SURVEILLANCE_OFFICER':
                return error_response(
                    "Only surveillance officers can access this",
                    status_code=status.HTTP_403_FORBIDDEN
                )[0]
            
            # Get alerts from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_alerts = Alert.objects.filter(
                created_at__gte=thirty_days_ago
            ).order_by('created_at')
            
            # Outbreak trend (daily aggregation)
            trend_data = {}
            for alert in recent_alerts:
                date_key = alert.created_at.strftime('%Y-%m-%d')
                if date_key not in trend_data:
                    trend_data[date_key] = {'count': 0, 'high': 0, 'critical': 0}
                
                trend_data[date_key]['count'] += 1
                if alert.severity == 'CRITICAL':
                    trend_data[date_key]['critical'] += 1
                elif alert.severity == 'HIGH':
                    trend_data[date_key]['high'] += 1
            
            outbreak_trend = [{
                'date': date,
                'alert_count': data['count'],
                'high_severity': data['high'],
                'critical_severity': data['critical']
            } for date, data in sorted(trend_data.items())]
            
            # Alert history
            alert_history = [{
                'id': str(a.id),
                'phc_id': a.phc_id,
                'type': a.alert_type,
                'severity': a.severity,
                'risk_score': round(float(a.risk_score), 2),
                'created_at': a.created_at.isoformat()
            } for a in recent_alerts.order_by('-created_at')[:100]]
            
            # Heatmap (PHC-based)
            heatmap_data = {}
            phc_ids = set([u.phc_id for u in User.objects.filter(role='PHC_USER') if u.phc_id])
            
            for phc_id in phc_ids:
                phc_alerts = Alert.objects.filter(phc_id=phc_id, created_at__gte=thirty_days_ago)
                
                if phc_alerts.count() > 0:
                    avg_risk = sum(float(a.risk_score) for a in phc_alerts) / len(phc_alerts)
                    
                    # Count severity distribution
                    severity_dist = {
                        'CRITICAL': sum(1 for a in phc_alerts if a.severity == 'CRITICAL'),
                        'HIGH': sum(1 for a in phc_alerts if a.severity == 'HIGH'),
                        'MEDIUM': sum(1 for a in phc_alerts if a.severity == 'MEDIUM'),
                        'LOW': sum(1 for a in phc_alerts if a.severity == 'LOW'),
                    }
                    
                    # Determine highest severity
                    highest_severity = 'LOW'
                    if severity_dist['CRITICAL'] > 0:
                        highest_severity = 'CRITICAL'
                    elif severity_dist['HIGH'] > 0:
                        highest_severity = 'HIGH'
                    elif severity_dist['MEDIUM'] > 0:
                        highest_severity = 'MEDIUM'
                    
                    heatmap_data[phc_id] = {
                        'alert_count': phc_alerts.count(),
                        'avg_risk_score': round(avg_risk, 2),
                        'severity_distribution': severity_dist,
                        'highest_severity': highest_severity
                    }
            
            # Summary
            critical_alerts = sum(1 for a in recent_alerts if a.severity == 'CRITICAL')
            high_alerts = sum(1 for a in recent_alerts if a.severity == 'HIGH')
            if recent_alerts:
                avg_risk = sum(float(a.risk_score) for a in recent_alerts) / len(list(recent_alerts))
                avg_risk = min(avg_risk, 100.0)  # Cap at 100%
            else:
                avg_risk = 0.0
            
            logger.info(f"Surveillance Dashboard accessed, {len(recent_alerts)} alerts")

            return Response({
                'summary': {
                    'total_alerts': len(list(recent_alerts)),
                    'critical_alerts': critical_alerts,
                    'high_alerts': high_alerts,
                    'average_risk_score': round(avg_risk, 2),
                    'affected_phcs': len(heatmap_data)
                },
                'outbreak_trend': outbreak_trend,
                'alert_history': alert_history,
                'heatmap': heatmap_data,
                'last_updated': datetime.utcnow().isoformat()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Surveillance dashboard error: {str(e)}")
            return error_response(
                "Failed to load surveillance dashboard",
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )[0]


# ============================================
# HEALTH CHECK ENDPOINT (NEW)
# ============================================

class HealthCheckView(APIView):
    """System health check endpoint - verifies MongoDB and ML collections."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Verify MongoDB connection
            db_status = "connected"
            ml_status = "operational"
            
            try:
                # Ping database
                User.objects.exists()
            except Exception as e:
                db_status = "disconnected"
                logger.warning(f"Database connection check failed: {str(e)}")
            
            # Verify local_models collection
            try:
                LocalModel.objects.count()
            except Exception as e:
                ml_status = "degraded"
                logger.warning(f"Local models collection check failed: {str(e)}")
            
            # Verify global_models collection
            try:
                GlobalModel.objects.count()
            except Exception as e:
                ml_status = "degraded"
                logger.warning(f"Global models collection check failed: {str(e)}")
            
            # Determine overall status
            is_healthy = db_status == "connected" and ml_status == "operational"
            overall_status = "healthy" if is_healthy else "degraded"
            http_status = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
            
            logger.info(f"Health check: {overall_status} (db={db_status}, ml={ml_status})")

            return Response({
                'status': overall_status,
                'database': db_status,
                'ml_engine': ml_status,
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0'
            }, status=http_status)

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class CohortHistoryView(APIView):
    """Retrieve historical cohort snapshots for trend analysis"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """Get historical cohort snapshots for the user's PHC"""
        try:
            user = request.user
            phc_id = user.phc_id if user.role == 'PHC_USER' else request.query_params.get('phc_id')
            
            if not phc_id:
                return Response({
                    'error': 'PHC ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch historical snapshots using PyMongo to avoid schema cache issues
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/')
            # Try 'fedhealth' first (where mongoengine writes), then fall back to 'fedhealth_db'
            db = client['fedhealth']
            
            # Get snapshots from MongoDB - cohort_snapshots are created by mongoengine
            snapshots_col = db['cohort_snapshots']
            snapshots_docs = list(snapshots_col.find(
                {'phc_id': phc_id},
                sort=[('snapshot_date', -1)]
            ).limit(30))
            
            if not snapshots_docs:
                # If no snapshots exist in 'fedhealth', try 'fedhealth_db'
                db_alt = client['fedhealth_db']
                snapshots_col = db_alt['cohort_snapshots']
                snapshots_docs = list(snapshots_col.find(
                    {'phc_id': phc_id},
                    sort=[('snapshot_date', -1)]
                ).limit(30))
            
            if not snapshots_docs:
                # If no snapshots exist, create one from current patients
                # Query both databases for all patients
                all_patients = []
                
                # New patients from fedhealth
                try:
                    db_patients = client['fedhealth']
                    patients_col = db_patients['patients']
                    new_patients = list(patients_col.find({'phc_id': phc_id}))
                    all_patients.extend(new_patients)
                except Exception as e:
                    logger.warning(f"Could not get new patients from fedhealth: {str(e)}")
                
                # Seed data from fedhealth_db
                try:
                    db_patients = client['fedhealth_db']
                    patients_col = db_patients['patients']
                    seed_patients = list(patients_col.find({'phc_id': phc_id}))
                    all_patients.extend(seed_patients)
                except Exception as e:
                    logger.warning(f"Could not get seed patients from fedhealth_db: {str(e)}")
                
                if all_patients:
                    # Create a new snapshot from all patients
                    snapshot_doc = self._create_snapshot_from_patients(phc_id, all_patients)
                    if snapshot_doc:
                        snapshots_docs = [snapshot_doc]
                    else:
                        snapshots_docs = []
                else:
                    snapshots_docs = []
            
            return Response({
                'phc_id': phc_id,
                'snapshots': [self._serialize_snapshot(s) for s in snapshots_docs]
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error retrieving cohort history: {str(e)}", exc_info=True)
            return Response({
                'error': f'Failed to retrieve history: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_snapshot_from_patients(self, phc_id, patients):
        """Generate a cohort snapshot from patient data (raw documents from PyMongo)"""
        try:
            patient_list = list(patients) if not isinstance(patients, list) else patients
            if not patient_list:
                return None
            
            # Calculate metrics from raw document dictionaries
            total = len(patient_list)
            fever_count = sum(1 for p in patient_list if p.get('fever') == 1)
            cough_count = sum(1 for p in patient_list if p.get('cough') == 1)
            fatigue_count = sum(1 for p in patient_list if p.get('fatigue') == 1)
            headache_count = sum(1 for p in patient_list if p.get('headache') == 1)
            vomiting_count = sum(1 for p in patient_list if p.get('vomiting') == 1)
            breathlessness_count = sum(1 for p in patient_list if p.get('breathlessness') == 1)
            male_count = sum(1 for p in patient_list if p.get('gender') == 'Male')
            high_severity_count = sum(1 for p in patient_list if p.get('severity_level') == 'High')
            
            # Calculate averages (handle missing values)
            ages = [p.get('age') for p in patient_list if p.get('age')]
            avg_age = sum(ages) / len(ages) if ages else 0
            
            temps = [p.get('temperature_c') for p in patient_list if p.get('temperature_c')]
            avg_temp = sum(temps) / len(temps) if temps else 0
            
            hrs = [p.get('heart_rate') for p in patient_list if p.get('heart_rate')]
            avg_hr = sum(hrs) / len(hrs) if hrs else 0
            
            bps = [p.get('bp_systolic') for p in patient_list if p.get('bp_systolic')]
            avg_bp = sum(bps) / len(bps) if bps else 0
            
            wbcs = [p.get('wbc_count') for p in patient_list if p.get('wbc_count')]
            avg_wbc = sum(wbcs) / len(wbcs) if wbcs else 0
            
            platelets = [p.get('platelet_count') for p in patient_list if p.get('platelet_count')]
            avg_platelet = sum(platelets) / len(platelets) if platelets else 0
            
            hbs = [p.get('hemoglobin') for p in patient_list if p.get('hemoglobin')]
            avg_hb = sum(hbs) / len(hbs) if hbs else 0
            
            # Create snapshot
            snapshot = CohortSnapshot.objects.create(
                phc_id=phc_id,
                total_patients=total,
                average_age=round(avg_age, 2),
                male_percentage=round((male_count / total) * 100, 2),
                female_percentage=round((1 - male_count / total) * 100, 2),
                fever_percentage=round((fever_count / total) * 100, 2),
                cough_percentage=round((cough_count / total) * 100, 2),
                fatigue_percentage=round((fatigue_count / total) * 100, 2),
                headache_percentage=round((headache_count / total) * 100, 2),
                vomiting_percentage=round((vomiting_count / total) * 100, 2),
                breathlessness_percentage=round((breathlessness_count / total) * 100, 2),
                average_wbc_count=round(avg_wbc, 0),
                average_temperature_c=round(avg_temp, 2),
                average_heart_rate=round(avg_hr, 2),
                average_bp_systolic=round(avg_bp, 2),
                average_platelet_count=round(avg_platelet, 0),
                average_hemoglobin=round(avg_hb, 2),
                high_severity_percentage=round((high_severity_count / total) * 100, 2),
                disease_distribution=self._calculate_disease_distribution(patient_list)
            )
            return snapshot.to_mongo()  # Return as dict for consistency with PyMongo documents
        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}", exc_info=True)
            return None
    
    def _calculate_disease_distribution(self, patients):
        """Calculate disease distribution from patients"""
        distribution = {}
        for p in patients:
            label = p.disease_label or 'Unknown'
            distribution[label] = distribution.get(label, 0) + 1
        return distribution
    
    def _serialize_snapshot(self, snapshot):
        """Convert snapshot to dictionary (handles both ORM objects and raw PyMongo dicts)"""
        # Handle raw dictionary from PyMongo
        if isinstance(snapshot, dict):
            snapshot_date = snapshot.get('snapshot_date')
            if snapshot_date and hasattr(snapshot_date, 'isoformat'):
                snapshot_date = snapshot_date.isoformat()
            return {
                'snapshot_date': snapshot_date,
                'total_patients': snapshot.get('total_patients', 0),
                'average_age': float(snapshot.get('average_age', 0)),
                'fever_percentage': float(snapshot.get('fever_percentage', 0)),
                'cough_percentage': float(snapshot.get('cough_percentage', 0)),
                'fatigue_percentage': float(snapshot.get('fatigue_percentage', 0)),
                'headache_percentage': float(snapshot.get('headache_percentage', 0)),
                'vomiting_percentage': float(snapshot.get('vomiting_percentage', 0)),
                'breathlessness_percentage': float(snapshot.get('breathlessness_percentage', 0)),
                'average_wbc_count': float(snapshot.get('average_wbc_count', 0)),
                'average_temperature_c': float(snapshot.get('average_temperature_c', 0)),
                'average_heart_rate': float(snapshot.get('average_heart_rate', 0)),
                'average_bp_systolic': float(snapshot.get('average_bp_systolic', 0)),
                'average_platelet_count': float(snapshot.get('average_platelet_count', 0)),
                'average_hemoglobin': float(snapshot.get('average_hemoglobin', 0)),
                'high_severity_percentage': float(snapshot.get('high_severity_percentage', 0)),
                'disease_distribution': snapshot.get('disease_distribution', {})
            }
        
        # Handle ORM object
        return {
            'snapshot_date': snapshot.snapshot_date.isoformat() if snapshot.snapshot_date else None,
            'total_patients': snapshot.total_patients,
            'average_age': float(snapshot.average_age),
            'fever_percentage': float(snapshot.fever_percentage),
            'cough_percentage': float(snapshot.cough_percentage),
            'fatigue_percentage': float(snapshot.fatigue_percentage),
            'headache_percentage': float(snapshot.headache_percentage),
            'vomiting_percentage': float(snapshot.vomiting_percentage),
            'breathlessness_percentage': float(snapshot.breathlessness_percentage),
            'average_wbc_count': float(snapshot.average_wbc_count),
            'average_temperature_c': float(snapshot.average_temperature_c),
            'average_heart_rate': float(snapshot.average_heart_rate),
            'average_bp_systolic': float(snapshot.average_bp_systolic),
            'average_platelet_count': float(snapshot.average_platelet_count),
            'average_hemoglobin': float(snapshot.average_hemoglobin),
            'high_severity_percentage': float(snapshot.high_severity_percentage),
            'disease_distribution': snapshot.disease_distribution or {}
        }
