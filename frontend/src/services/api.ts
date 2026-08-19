import axios from 'axios';
import type { TravelRequest, ApprovalRequest, TravelResponse, HealthResponse, MetricsResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 3 minutes for long-running travel planning
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const travelApi = {
  // Health check
  async healthCheck(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },

  // Submit travel request
  async submitTravelRequest(data: TravelRequest): Promise<TravelResponse> {
    const response = await api.post<TravelResponse>('/api/travel', data);
    return response.data;
  },

  // Approve or reject travel plan
  async approveTravelPlan(data: ApprovalRequest): Promise<TravelResponse> {
    const response = await api.post<TravelResponse>('/api/travel/approve', data);
    return response.data;
  },

  // Get system metrics
  async getMetrics(): Promise<MetricsResponse> {
    const response = await api.get<MetricsResponse>('/api/metrics');
    return response.data;
  },
};

export default api;
