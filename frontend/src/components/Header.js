import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import './Header.css';

function Header() {
  const { user, logout } = useAuth();
  const { getCartCount } = useCart();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
    setMenuOpen(false);
  };

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="brand">
          <span className="logo">🌾</span>
          <h1>AgriConnect</h1>
        </Link>

        <nav className={`nav ${menuOpen ? 'open' : ''}`}>
          <Link to="/" onClick={() => setMenuOpen(false)}>
            🏠 Home
          </Link>
          <Link to="/farmers" onClick={() => setMenuOpen(false)}>
            🚜 Farm Products
          </Link>
          <Link to="/30-min" onClick={() => setMenuOpen(false)}>
            🚀 30-Min Delivery
          </Link>
          <Link to="/cart" className="cart-link" onClick={() => setMenuOpen(false)}>
            🛒 Cart
            {getCartCount() > 0 && (
              <span className="cart-badge">{getCartCount()}</span>
            )}
          </Link>
          
          {user ? (
            <>
              <Link to="/profile" className="user-link" onClick={() => setMenuOpen(false)}>
                👤 {user.name || user.username}
              </Link>
              {user.username === 'admin' && (
                <Link to="/admin" onClick={() => setMenuOpen(false)}>
                  ⚙️ Admin
                </Link>
              )}
              {user && (
                <>
                  <Link to="/farmer-products" onClick={() => setMenuOpen(false)}>
                    🌾 My Products
                  </Link>
                  <Link to="/farmer-dashboard" onClick={() => setMenuOpen(false)}>
                    📊 Dashboard
                  </Link>
                </>
              )}
              <button onClick={handleLogout} className="btn-logout">
                ↩️ Logout
              </button>
            </>
          ) : (
            <Link to="/login" onClick={() => setMenuOpen(false)}>
              👤 Login
            </Link>
          )}
        </nav>

        <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? '✕' : '☰'}
        </button>
      </div>
    </header>
  );
}

export default Header;
