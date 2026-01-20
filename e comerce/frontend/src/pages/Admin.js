import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Admin.css';

function Admin() {
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [selectedPincode, setSelectedPincode] = useState('all');
  const [pincodes, setPincodes] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  useEffect(() => {
    filterOrders();
  }, [selectedPincode, orders]);

  const loadOrders = async () => {
    try {
      const response = await axios.get('/api/admin/orders');
      const allOrders = response.data.orders || [];
      setOrders(allOrders);
      
      // Extract unique pincodes
      const uniquePincodes = [...new Set(allOrders.map(order => order.pincode))].filter(Boolean);
      setPincodes(uniquePincodes);
      
      updateStats(allOrders);
    } catch (error) {
      console.error('Failed to load orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterOrders = () => {
    if (selectedPincode === 'all') {
      setFilteredOrders(orders);
      updateStats(orders);
    } else {
      const filtered = orders.filter(order => order.pincode === selectedPincode);
      setFilteredOrders(filtered);
      updateStats(filtered);
    }
  };

  const updateStats = (ordersList) => {
    setStats({
      total: ordersList.length,
      pending: ordersList.filter(o => o.status === 'pending').length
    });
  };

  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      const response = await axios.post('/api/update-order-status', {
        order_id: orderId,
        status: newStatus
      });

      if (response.data.success) {
        // Update local state
        setOrders(orders.map(order =>
          order.id === orderId ? { ...order, status: newStatus } : order
        ));
        alert('Order status updated successfully!');
      }
    } catch (error) {
      alert('Failed to update order status');
    }
  };

  const handleDownloadInvoice = (orderId) => {
    window.open(`/api/download-invoice/${orderId}`, '_blank');
  };

  return (
    <div className="admin-page">
      <div className="container">
        <div className="admin-header">
          <div>
            <h1>⚙️ Admin Dashboard</h1>
            <p>Manage all orders</p>
          </div>
          
          <div className="filter-section">
            <label>Filter by Pincode:</label>
            <select 
              value={selectedPincode} 
              onChange={(e) => setSelectedPincode(e.target.value)}
              className="pincode-select"
            >
              <option value="all">All Pincodes</option>
              {pincodes.map(pincode => (
                <option key={pincode} value={pincode}>{pincode}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Orders</div>
          </div>
          <div className="stat-card pending">
            <div className="stat-value">{stats.pending}</div>
            <div className="stat-label">Pending Orders</div>
          </div>
          <div className="stat-card completed">
            <div className="stat-value">{stats.total - stats.pending}</div>
            <div className="stat-label">Completed Orders</div>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading orders...</div>
        ) : filteredOrders.length === 0 ? (
          <div className="no-orders">
            <p>No orders found</p>
          </div>
        ) : (
          <div className="orders-grid">
            {filteredOrders.map(order => (
              <div key={order.id} className={`admin-order-card ${order.status}`}>
                <div className="order-header">
                  <span className="order-number">#{order.order_number}</span>
                  <span className={`status-badge status-${order.status}`}>
                    {order.status}
                  </span>
                </div>

                <div className="order-info">
                  <div className="info-grid">
                    <div>
                      <strong>Customer:</strong> {order.name}
                    </div>
                    <div>
                      <strong>Phone:</strong> {order.phone}
                    </div>
                    <div>
                      <strong>Pincode:</strong> {order.pincode}
                    </div>
                    <div>
                      <strong>Date:</strong> {order.created_at}
                    </div>
                  </div>

                  <div className="address-section">
                    <strong>Address:</strong> {order.address}
                  </div>

                  <div className="order-footer">
                    <div className="order-total">
                      <strong>Total:</strong> ₹{order.total_amount}
                    </div>

                    <div className="status-actions">
                      <button 
                        onClick={() => handleDownloadInvoice(order.id)}
                        className="btn-action btn-invoice"
                        title="Download Invoice"
                      >
                        📄 Invoice
                      </button>
                      {order.status === 'pending' && (
                        <>
                          <button 
                            onClick={() => handleStatusUpdate(order.id, 'completed')}
                            className="btn-action btn-complete"
                          >
                            ✓ Complete
                          </button>
                          <button 
                            onClick={() => handleStatusUpdate(order.id, 'cancelled')}
                            className="btn-action btn-cancel"
                          >
                            ✗ Cancel
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Admin;
