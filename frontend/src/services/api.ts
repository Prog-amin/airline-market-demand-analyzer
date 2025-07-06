import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { store } from '../store';
import { logout } from '../features/auth/authSlice';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor to add auth token to requests
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('authToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 Unauthorized
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.status === 401) {
      // If 401 response, clear token and redirect to login
      store.dispatch(logout());
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (email: string, password: string) => 
    api.post('/auth/login', { username: email, password }),
  
  register: (email: string, password: string, name: string) => 
    api.post('/auth/register', { email, password, name }),
  
  getMe: () => api.get('/auth/me'),
  
  refreshToken: () => api.post('/auth/refresh-token'),
};

// Flights API
export const flightsApi = {
  searchFlights: (params: {
    origin: string;
    destination: string;
    departureDate: string;
    returnDate?: string;
    adults?: number;
    children?: number;
    infants?: number;
    travelClass?: string;
    nonStop?: boolean;
    maxPrice?: number;
    includeAirlines?: string[];
    excludeAirlines?: string[];
    useRealData?: boolean;
  }) => api.get('/flights/search', { params }),
  
  getFlightDetails: (id: string) => api.get(`/flights/${id}`),
};

// Insights API
export const insightsApi = {
  getInsights: (flightData: any) => 
    api.post('/insights/insights', { flight_data: flightData }),
  
  getAvailableModels: () => api.get('/insights/models'),
};

// Airports API
export const airportsApi = {
  searchAirports: (query: string) => 
    api.get('/airports/search', { params: { q: query } }),
  
  getAirportDetails: (iataCode: string) => 
    api.get(`/airports/${iataCode}`),
};

export default api;
