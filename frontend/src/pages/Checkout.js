import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import './Checkout.css';

function Checkout() {
  const { cart, getCartTotal, clearCart } = useCart();
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: user?.name || '',
    address: user?.address || '',
    pincode: user?.pincode || '',
    phone: user?.phone || ''
  });

  const [isEditing, setIsEditing] = useState(!user?.name || !user?.address);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSaveDetails = async () => {
    if (!formData.name || !formData.address || !formData.pincode || !formData.phone) {
      setError('Please fill in all fields');
      return;
    }

    if (!/^\d{6}$/.test(formData.pincode)) {
      setError('Please enter a valid 6-digit pincode');
      return;
    }

    if (!/^\d{10}$/.test(formData.phone)) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }

    try {
      const response = await axios.post('/api/update-user-details', formData);
      if (response.data.success) {
        updateUser(formData);
        setIsEditing(false);
        setError('');
      }
    } catch (err) {
      setError('Failed to update details');
    }
  };

  const handlePlaceOrder = async () => {
    if (isEditing) {
      setError('Please save your delivery details first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const orderData = {
        cart: cart.map(item => ({
          id: item.id,
          name: item.name,
          price: item.price,
          quantity: item.quantity
        }))
      };

      const response = await axios.post('/api/place-order', orderData);

      if (response.data.success) {
        clearCart();
        alert(`Order placed successfully! Order Number: ${response.data.order_number}`);
        navigate('/profile');
      } else {
        setError(response.data.message || 'Failed to place order');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  if (cart.length === 0) {
    return (
      <div className="container">
        <div className="empty-cart">
          <div className="empty-cart-icon">🛒</div>
          <h2>Your cart is empty</h2>
          <p>Add items to your cart before checking out</p>
          <button onClick={() => navigate('/')} className="btn btn-primary">
            Start Shopping
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="container">
        <h1>📦 Checkout</h1>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="checkout-layout">
          <div className="checkout-details">
            <div className="card">
              <div className="card-header">
                <h2>Delivery Details</h2>
                {!isEditing && (
                  <button onClick={() => setIsEditing(true)} className="btn-edit">
                    ✏️ Edit
                  </button>
                )}
              </div>

              {isEditing ? (
                <div className="edit-form">
                  <div className="form-group">
                    <label>Full Name</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="Enter your full name"
                    />
                  </div>
                  <div className="form-group">
                    <label>Delivery Address</label>
                    <textarea
                      name="address"
                      value={formData.address}
                      onChange={handleChange}
                      placeholder="Enter complete address"
                      rows="3"
                    />
                  </div>
                  <div className="form-group">
                    <label>Pincode</label>
                    <input
                      type="text"
                      name="pincode"
                      value={formData.pincode}
                      onChange={handleChange}
                      placeholder="6-digit pincode"
                      maxLength="6"
                    />
                  </div>
                  <div className="form-group">
                    <label>Phone Number</label>
                    <input
                      type="text"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="10-digit phone number"
                      maxLength="10"
                    />
                  </div>
                  <div className="form-actions">
                    <button onClick={handleSaveDetails} className="btn btn-primary">
                      Save Details
                    </button>
                    {user?.name && (
                      <button onClick={() => setIsEditing(false)} className="btn btn-outline">
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="details-view">
                  <p><strong>Name:</strong> {formData.name}</p>
                  <p><strong>Address:</strong> {formData.address}</p>
                  <p><strong>Pincode:</strong> {formData.pincode}</p>
                  <p><strong>Phone:</strong> {formData.phone}</p>
                </div>
              )}
            </div>

            <div className="card">
              <h2>Order Items</h2>
              <div className="order-items">
                {cart.map(item => (
                  <div key={item.id} className="order-item">
                    <div className="item-info">
                      <h4>{item.name}</h4>
                      <p>₹{item.price} × {item.quantity}</p>
                    </div>
                    <div className="item-subtotal">
                      ₹{(item.price * item.quantity).toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="order-summary">
            <div className="card">
              <h2>Order Summary</h2>
              <div className="summary-row">
                <span>Subtotal:</span>
                <span>₹{getCartTotal().toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>Delivery:</span>
                <span className="free">FREE</span>
              </div>
              <hr />
              <div className="summary-row total">
                <span>Total:</span>
                <span>₹{getCartTotal().toFixed(2)}</span>
              </div>

              <button
                onClick={handlePlaceOrder}
                className="btn btn-primary btn-full"
                disabled={loading || isEditing}
              >
                {loading ? 'Placing Order...' : 'Place Order'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Checkout;
