// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';
const API_TIMEOUT = parseInt(process.env.REACT_APP_API_TIMEOUT) || 10000;

// Feature Flags
export const FEATURES = {
  ENABLE_ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
  ENABLE_ERROR_TRACKING: process.env.REACT_APP_ENABLE_ERROR_TRACKING === 'true',
  ENABLE_PERFORMANCE_MONITORING: process.env.REACT_APP_ENABLE_PERFORMANCE_MONITORING === 'true',
};

// API Endpoints
export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/api/login`,
  SIGNUP: `${API_BASE_URL}/api/signup`,
  LOGOUT: `${API_BASE_URL}/api/logout`,
  ME: `${API_BASE_URL}/api/me`,
  PRODUCTS: `${API_BASE_URL}/api/products`,
  FARM_PRODUCTS: `${API_BASE_URL}/api/farm-products`,
  CART: `${API_BASE_URL}/api/cart`,
  CHECKOUT: `${API_BASE_URL}/api/checkout`,
  PROFILE: `${API_BASE_URL}/api/profile`,
};

// App Constants
export const APP_CONFIG = {
  NAME: 'AgriConnect',
  VERSION: '1.0.0',
  ENVIRONMENT: process.env.NODE_ENV,
  API_TIMEOUT,
};

// Local Storage Keys
export const STORAGE_KEYS = {
  CART: 'cart',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
};

export default {
  FEATURES,
  API_ENDPOINTS,
  APP_CONFIG,
  STORAGE_KEYS,
};
