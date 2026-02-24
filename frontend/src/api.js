import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
};

export const phcAPI = {
  submitPatient: (patientData) => api.post('/phc/patient/', patientData),
  getPatients: () => api.get('/phc/patients/'),
};

export const adminAPI = {
  aggregateModels: () => api.post('/admin/aggregate/', {}),
};

export const surveillanceAPI = {
  getAlerts: () => api.get('/surveillance/alerts/'),
};

// STEP 7: Dashboard Metrics APIs
export const dashboardAPI = {
  // PHC Dashboard - local model accuracy, drift warnings, risk scores, alerts
  getPHCMetrics: () => api.get('/dashboards/phc/'),
  
  // District Dashboard - global model, aggregation, contributing PHCs, average risk
  getDistrictMetrics: () => api.get('/dashboards/district/'),
  
  // Surveillance Dashboard - outbreak trends, alert history, heatmap data
  getSurveillanceMetrics: () => api.get('/dashboards/surveillance/'),
  
  // Cohort history for trend analysis
  getCohortHistory: () => api.get('/cohort/history/'),
};

