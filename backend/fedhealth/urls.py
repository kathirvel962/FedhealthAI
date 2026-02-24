"""
FedHealthAI Backend URL Configuration - Refactored for MVP

Essential endpoints only:
- Authentication (register, login)
- Patient management (submit, list)
- Federated learning (aggregation)
- Surveillance (alerts)
- Dashboards (PHC, District, Officer)
- Health check
- API Documentation (Swagger/ReDoc)
"""

from django.urls import path
from api import views

urlpatterns = [
    # API Documentation (Swagger disabled - using drf_yasg requires pkg_resources)
    
    # Health Check
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    
    # Authentication
    path('api/auth/register/', views.RegisterView.as_view(), name='register'),
    path('api/auth/login/', views.LoginView.as_view(), name='login'),
    
    # Patient Management
    path('api/phc/patient/', views.PatientSubmitView.as_view(), name='patient-submit'),
    path('api/phc/patients/', views.PHCPatientsView.as_view(), name='phc-patients'),
    
    # Federated Learning
    path('api/admin/aggregate/', views.AggregateModelsView.as_view(), name='aggregate-models'),
    
    # Surveillance
    path('api/surveillance/alerts/', views.SurveillanceAlertsView.as_view(), name='surveillance-alerts'),
    
    # Dashboards
    path('api/dashboards/phc/', views.PHCDashboardMetricsView.as_view(), name='phc-dashboard'),
    path('api/dashboards/district/', views.DistrictDashboardMetricsView.as_view(), name='district-dashboard'),
    path('api/dashboards/surveillance/', views.SurveillanceDashboardMetricsView.as_view(), name='surveillance-dashboard'),
    
    # Historical Data
    path('api/cohort/history/', views.CohortHistoryView.as_view(), name='cohort-history'),
]
