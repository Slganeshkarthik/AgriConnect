import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Components
import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load pages for better performance
const Home = lazy(() => import('./pages/Home'));
const FarmProducts = lazy(() => import('./pages/FarmProducts'));
const FastDelivery = lazy(() => import('./pages/FastDelivery'));
const Cart = lazy(() => import('./pages/Cart'));
const Checkout = lazy(() => import('./pages/Checkout'));
const Profile = lazy(() => import('./pages/Profile'));
const Login = lazy(() => import('./pages/Login'));
const Signup = lazy(() => import('./pages/Signup'));
const Admin = lazy(() => import('./pages/Admin'));

// Context
import { CartProvider } from './context/CartContext';
import { AuthProvider, useAuth } from './context/AuthContext';

// Loading component
const LoadingSpinner = () => (
  <div className="loading-spinner" role="status" aria-live="polite">
    <div className="spinner"></div>
    <p>Loading...</p>
  </div>
);

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return user ? children : <Navigate to="/login" replace />;
}

function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return user && user.username === 'admin' ? children : <Navigate to="/" replace />;
}

function AppContent() {
  return (
    <div className="App">
      <Header />
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/farmers" element={<FarmProducts />} />
        <Route path="/30-min" element={<FastDelivery />} />
        <Route path="/cart" element={<Cart />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route 
          path="/checkout" 
          element={
            <PrivateRoute>
              <Checkout />
            </PrivateRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <PrivateRoute>
              <Profile />
            </PrivateRoute>
          } 
        />
        <Route 
          path="/admin" 
          element={
            <AdminRoute>
              <Admin />
            </AdminRoute>
          } 
        />
        <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <CartProvider>
            <AppContent />
          </CartProvider>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
