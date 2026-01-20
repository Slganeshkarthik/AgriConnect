import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      setError(null);
      const response = await axios.get('/api/me', {
        timeout: 5000,
        withCredentials: true
      });
      if (response.data.success) {
        setUser(response.data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(async (username, password) => {
    try {
      setError(null);
      const response = await axios.post('/api/login', 
        { username, password },
        { withCredentials: true, timeout: 5000 }
      );
      if (response.data.success) {
        setUser(response.data.user);
        return { success: true };
      }
      return { success: false, message: response.data.message };
    } catch (error) {
      const message = error.response?.data?.message || 'Login failed';
      setError(message);
      return { success: false, message };
    }
  }, []);

  const signup = useCallback(async (username, password) => {
    try {
      setError(null);
      const response = await axios.post('/api/signup', 
        { username, password },
        { withCredentials: true, timeout: 5000 }
      );
      if (response.data.success) {
        setUser(response.data.user);
        return { success: true };
      }
      return { success: false, message: response.data.message };
    } catch (error) {
      const message = error.response?.data?.message || 'Signup failed';
      setError(message);
      return { success: false, message };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await axios.post('/api/logout', {}, { withCredentials: true });
      setUser(null);
      setError(null);
    } catch (error) {
      console.error('Logout failed:', error);
      setError(error.message);
    }
  }, []);

  const updateUser = useCallback((userData) => {
    setUser(prev => ({ ...prev, ...userData }));
  }, []);

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      error,
      login, 
      signup, 
      logout, 
      updateUser, 
      checkAuth 
    }}>
      {children}
    </AuthContext.Provider>
  );
};
