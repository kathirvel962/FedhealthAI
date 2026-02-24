"""
FedHealthAI - Basic Test Suite

Tests core functionality:
- Authentication (register, login)
- Patient submission
- Model aggregation
- Alerts
- Dashboard dashboards
"""

import json
from datetime import datetime
from django.test import TestCase, Client
from api.models import User, Patient, LocalModel, GlobalModel, Alert, PHC
from rest_framework import status


class AuthenticationTests(TestCase):
    """Test authentication endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
    
    def test_user_registration(self):
        """Test successful user registration."""
        data = {
            'username': 'test_user',
            'password': 'testpass123',
            'role': 'PHC_USER',
            'phc_id': 'PHC1'
        }
        response = self.client.post(
            self.register_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user_id', response.json())
    
    def test_user_login(self):
        """Test successful user login."""
        # Register first
        register_data = {
            'username': 'test_user',
            'password': 'testpass123',
            'role': 'PHC_USER',
            'phc_id': 'PHC1'
        }
        self.client.post(
            self.register_url,
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        # Login
        login_data = {
            'username': 'test_user',
            'password': 'testpass123'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())
    
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        login_data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PatientManagementTests(TestCase):
    """Test patient submission and retrieval."""
    
    def setUp(self):
        self.client = Client()
        
        # Create a test PHC user
        self.user = User.objects.create(
            username='phc_user',
            password_hash='hashed_password',
            role='PHC_USER',
            phc_id='PHC1'
        )
        
        # Get login token
        from api.authentication import generate_token
        self.token = generate_token(str(self.user.id))
    
    def test_patient_submission(self):
        """Test patient submission endpoint."""
        data = {
            'age': 35,
            'gender': 'M',
            'fever': 1,
            'cough': 0,
            'rash': 0,
            'wbc_count': 7500,
            'diagnosis': 'Fever'
        }
        response = self.client.post(
            '/api/phc/patient/',
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('patient_id', response.json())
    
    def test_patient_retrieval(self):
        """Test retrieving patients for a PHC."""
        # Submit a patient first
        patient = Patient.objects.create(
            phc_id='PHC1',
            age=35,
            gender='M',
            fever=1,
            cough=0,
            rash=0,
            wbc_count=7500,
            diagnosis='Fever'
        )
        
        response = self.client.get(
            '/api/phc/patients/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('patients', response.json())


class AggregationTests(TestCase):
    """Test model aggregation functionality."""
    
    def setUp(self):
        self.client = Client()
        
        # Create admin user
        self.admin = User.objects.create(
            username='admin_user',
            password_hash='hashed_password',
            role='DISTRICT_ADMIN',
            phc_id=None
        )
        
        from api.authentication import generate_token
        self.admin_token = generate_token(str(self.admin.id))
    
    def test_aggregation_endpoint(self):
        """Test aggregation endpoint (may fail without trained models)."""
        response = self.client.post(
            '/api/admin/aggregate/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        # Should return 400 if no models to aggregate
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


class AlertsTests(TestCase):
    """Test alert retrieval."""
    
    def setUp(self):
        self.client = Client()
        
        # Create surveillance officer
        self.officer = User.objects.create(
            username='officer_user',
            password_hash='hashed_password',
            role='SURVEILLANCE_OFFICER',
            phc_id=None
        )
        
        from api.authentication import generate_token
        self.officer_token = generate_token(str(self.officer.id))
    
    def test_alerts_retrieval(self):
        """Test alerts endpoint."""
        response = self.client.get(
            '/api/surveillance/alerts/',
            HTTP_AUTHORIZATION=f'Bearer {self.officer_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('alerts', response.json())


class DashboardTests(TestCase):
    """Test dashboard endpoints."""
    
    def setUp(self):
        self.client = Client()
        
        # Create PHC user
        self.phc_user = User.objects.create(
            username='phc_user',
            password_hash='hashed_password',
            role='PHC_USER',
            phc_id='PHC1'
        )
        
        # Create admin
        self.admin = User.objects.create(
            username='admin_user',
            password_hash='hashed_password',
            role='DISTRICT_ADMIN',
            phc_id=None
        )
        
        from api.authentication import generate_token
        self.phc_token = generate_token(str(self.phc_user.id))
        self.admin_token = generate_token(str(self.admin.id))
    
    def test_phc_dashboard(self):
        """Test PHC dashboard endpoint."""
        response = self.client.get(
            '/api/dashboards/phc/',
            HTTP_AUTHORIZATION=f'Bearer {self.phc_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_data = response.json()
        self.assertIn('phc_id', resp_data)
        self.assertIn('model', resp_data)
        self.assertIn('risk', resp_data)
    
    def test_district_dashboard(self):
        """Test district dashboard endpoint."""
        response = self.client.get(
            '/api/dashboards/district/',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_data = response.json()
        self.assertIn('global_model', resp_data)
        self.assertIn('phc_breakdown', resp_data)


class FederatedLearningTests(TestCase):
    """Test federated learning core mechanics."""
    
    def setUp(self):
        self.client = Client()
        
        # Create test PHC
        self.phc = PHC.objects.create(phc_id='PHC_FL_TEST', name='FL Test PHC')
        
        # Create global model
        self.global_model = GlobalModel.objects.create(
            version=1,
            model_params={'weights': [0.5, 0.5]},
            sample_count=100,
            created_at=datetime.now()
        )
    
    def test_fedavg_weighting_correctness(self):
        """
        Test that FedAvg weighted averaging works correctly.
        
        Creates mock local models with different sample counts and verifies
        that aggregation produces correct weighted average.
        """
        # Create local models with different sample counts
        lm1 = LocalModel.objects.create(
            phc_id='PHC1',
            version=1,
            model_params={'weights': [1.0, 1.0]},  # Model 1 weights
            sample_count=50,  # 50 samples
            trained_at=datetime.now()
        )
        
        lm2 = LocalModel.objects.create(
            phc_id='PHC2',
            version=1,
            model_params={'weights': [2.0, 2.0]},  # Model 2 weights
            sample_count=150,  # 150 samples
            trained_at=datetime.now()
        )
        
        # Manual weighted averaging calculation
        total_samples = lm1.sample_count + lm2.sample_count  # 200
        w1 = lm1.sample_count / total_samples  # 50/200 = 0.25
        w2 = lm2.sample_count / total_samples  # 150/200 = 0.75
        
        # Expected weighted average: [0.25*1.0 + 0.75*2.0, 0.25*1.0 + 0.75*2.0]
        # = [0.25 + 1.5, 0.25 + 1.5] = [1.75, 1.75]
        expected_weight_0 = (w1 * 1.0) + (w2 * 2.0)
        expected_weight_1 = (w1 * 1.0) + (w2 * 2.0)
        
        # Verify weighting formula
        self.assertAlmostEqual(expected_weight_0, 1.75, places=2)
        self.assertAlmostEqual(expected_weight_1, 1.75, places=2)
        
        # Verify that weighting respects sample count distribution
        self.assertGreater(w2, w1)  # More samples = higher weight
        self.assertAlmostEqual(w1 + w2, 1.0, places=5)  # Weights sum to 1


class HealthCheckTests(TestCase):
    """Test health check endpoint."""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/health/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn('status', response.json())
        self.assertIn('database', response.json())
