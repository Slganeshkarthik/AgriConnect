import axios from 'axios';
import { API_ENDPOINTS, APP_CONFIG } from '../config/constants';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_ENDPOINTS.BASE_URL,
  timeout: APP_CONFIG.API_TIMEOUT,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any custom headers or tokens here
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle different error status codes
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Unauthorized - redirect to login
          console.error('Unauthorized access');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          break;
        case 403:
          console.error('Forbidden access');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 500:
          console.error('Server error');
          break;
        default:
          console.error('API error:', error.response.status);
      }
    } else if (error.request) {
      console.error('Network error - no response received');
    } else {
      console.error('Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// API methods
export const apiService = {
  // Auth endpoints
  login: (credentials) => api.post('/api/login', credentials),
  signup: (userData) => api.post('/api/signup', userData),
  logout: () => api.post('/api/logout'),
  getCurrentUser: () => api.get('/api/me'),
  
  // Product endpoints
  getProducts: (params) => api.get('/api/products', { params }),
  getProduct: (id) => api.get(`/api/products/${id}`),
  getFarmProducts: (params) => api.get('/api/farm-products', { params }),
  
  // Cart endpoints
  getCart: () => api.get('/api/cart'),
  addToCart: (item) => api.post('/api/cart', item),
  updateCartItem: (id, data) => api.put(`/api/cart/${id}`, data),
  removeFromCart: (id) => api.delete(`/api/cart/${id}`),
  
  // Checkout
  checkout: (orderData) => api.post('/api/checkout', orderData),
  
  // Profile
  getProfile: () => api.get('/api/profile'),
  updateProfile: (data) => api.put('/api/profile', data),
};

export default api;
