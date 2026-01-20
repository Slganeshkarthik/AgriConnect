import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

function Profile() {
  const { user, updateUser } = useAuth();
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({
    totalOrders: 0,
    pendingOrders: 0,
    completedOrders: 0,
    totalSpent: 0
  });
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    address: user?.address || '',
    pincode: user?.pincode || '',
    phone: user?.phone || ''
  });

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      const response = await axios.get('/api/profile');
      setOrders(response.data.orders || []);
      setStats({
        totalOrders: response.data.total_orders || 0,
        pendingOrders: response.data.pending_orders || 0,
        completedOrders: response.data.completed_orders || 0,
        totalSpent: response.data.total_spent || 0
      });
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSaveProfile = async () => {
    if (!/^\d{6}$/.test(formData.pincode)) {
      alert('Please enter a valid 6-digit pincode');
      return;
    }

    if (!/^\d{10}$/.test(formData.phone)) {
      alert('Please enter a valid 10-digit phone number');
      return;
    }

    try {
      const response = await axios.post('/api/update-user-details', formData);
      if (response.data.success) {
        updateUser(formData);
        setIsEditing(false);
        alert('Profile updated successfully!');
      }
    } catch (error) {
      alert('Failed to update profile');
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'pending': return 'status-pending';
      case 'completed': return 'status-completed';
      case 'cancelled': return 'status-cancelled';
      default: return '';
    }
  };

  const handleDownloadInvoice = (orderId) => {
    // Open invoice in new window
    window.open(`/api/download-invoice/${orderId}`, '_blank');
  };

  return (
    <div className="profile-page">
      <div className="container">
        <h1>👤 My Profile</h1>

        <div className="profile-grid">
          <div className="profile-section">
            <div className="card">
              <div className="card-header">
                <h2>Profile Details</h2>
                {!isEditing && (
                  <button onClick={() => setIsEditing(true)} className="btn-edit">
                    ✏️ Edit
                  </button>
                )}
              </div>

              {isEditing ? (
                <div className="edit-form">
                  <div className="form-group">
                    <label>Name</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="form-group">
                    <label>Address</label>
                    <input
                      type="text"
                      name="address"
                      value={formData.address}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="form-group">
                    <label>Pincode</label>
                    <input
                      type="text"
                      name="pincode"
                      value={formData.pincode}
                      onChange={handleChange}
                      maxLength="6"
                    />
                  </div>
                  <div className="form-group">
                    <label>Phone</label>
                    <input
                      type="text"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      maxLength="10"
                    />
                  </div>
                  <div className="form-actions">
                    <button onClick={handleSaveProfile} className="btn btn-primary">
                      Save Changes
                    </button>
                    <button onClick={() => setIsEditing(false)} className="btn btn-outline">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="profile-info">
                  <div className="info-row">
                    <strong>Name:</strong>
                    <span>{user?.name || 'Not set'}</span>
                  </div>
                  <div className="info-row">
                    <strong>Username:</strong>
                    <span>{user?.username}</span>
                  </div>
                  <div className="info-row">
                    <strong>Address:</strong>
                    <span>{user?.address || 'Not set'}</span>
                  </div>
                  <div className="info-row">
                    <strong>Pincode:</strong>
                    <span>{user?.pincode || 'Not set'}</span>
                  </div>
                  <div className="info-row">
                    <strong>Phone:</strong>
                    <span>{user?.phone || 'Not set'}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="stats-section">
            <div className="card">
              <h2>Order Statistics</h2>
              <div className="stats-grid">
                <div className="stat-box primary">
                  <div className="stat-number">{stats.totalOrders}</div>
                  <div className="stat-label">Total Orders</div>
                </div>
                <div className="stat-box warning">
                  <div className="stat-number">{stats.pendingOrders}</div>
                  <div className="stat-label">Pending</div>
                </div>
                <div className="stat-box success">
                  <div className="stat-number">{stats.completedOrders}</div>
                  <div className="stat-label">Completed</div>
                </div>
              </div>
              <div className="total-spent">
                <strong>Total Spent:</strong> ₹{stats.totalSpent.toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        <div className="orders-section">
          <div className="card">
            <h2>📦 Order History</h2>
            {loading ? (
              <div className="loading">Loading orders...</div>
            ) : orders.length === 0 ? (
              <div className="no-orders">
                <p>No orders yet</p>
                <p>Start shopping to see your orders here!</p>
              </div>
            ) : (
              <div className="orders-list">
                {orders.map(order => (
                  <div key={order.id} className={`order-card ${order.status}`}>
                    <div className="order-header">
                      <span className="order-number">#{order.order_number}</span>
                      <div className="order-header-actions">
                        <span className={`status-badge ${getStatusClass(order.status)}`}>
                          {order.status}
                        </span>
                        <button 
                          onClick={() => handleDownloadInvoice(order.id)}
                          className="btn-download-invoice"
                          title="Download Invoice"
                        >
                          📄 Invoice
                        </button>
                      </div>
                    </div>
                    <div className="order-details">
                      <p><strong>Date:</strong> {order.created_at}</p>
                      <p><strong>Total:</strong> ₹{order.total_amount}</p>
                      <p><strong>Items:</strong> {order.item_count} product(s)</p>
                      <p><strong>Delivery:</strong> {order.address}, {order.pincode}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
