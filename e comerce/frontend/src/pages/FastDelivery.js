import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import ProductCard from '../components/ProductCard';
import './FarmProducts.css';

function FastDelivery() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      // Load both home and farm products
      const [homeResponse, farmResponse] = await Promise.all([
        axios.get('/api/home-products'),
        axios.get('/api/products')
      ]);
      
      const allProducts = [...homeResponse.data, ...farmResponse.data];
      setProducts(allProducts);
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fastDeliveryProducts = products.filter(product => 
    user && product.pincode === user.pincode &&
    (product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
     (product.description && product.description.toLowerCase().includes(searchTerm.toLowerCase())))
  );

  return (
    <div className="fast-delivery-page">
      <section className="page-header" style={{background: 'linear-gradient(135deg, #00bb66 0%, #00aa55 100%)'}}>
        <div className="header-content">
          <h1>🚀 30-Minute Delivery</h1>
          <p>Super fast delivery for products in your area</p>
          {user && user.pincode && (
            <p style={{marginTop: '8px', fontSize: '16px'}}>
              📍 Your Pincode: {user.pincode}
            </p>
          )}
        </div>
      </section>

      <div className="container">
        {!user ? (
          <div className="alert alert-warning" style={{marginBottom: '24px'}}>
            Please <a href="/login" style={{color: '#00bb66', fontWeight: '600'}}>login</a> to see products available for 30-minute delivery in your area.
          </div>
        ) : !user.pincode ? (
          <div className="alert alert-warning" style={{marginBottom: '24px'}}>
            Please update your profile with your pincode to see fast delivery products.
          </div>
        ) : (
          <>
            <div className="search-section">
              <input
                type="text"
                placeholder="🔍 Search fast delivery products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>

            {loading ? (
              <div className="loading">Loading products...</div>
            ) : (
              <>
                <h2 className="section-title">
                  Available for Fast Delivery
                  <span className="product-count">({fastDeliveryProducts.length} items)</span>
                </h2>
                
                {fastDeliveryProducts.length === 0 ? (
                  <div className="no-products">
                    <h3>No fast delivery products available in your area yet</h3>
                    <p>Check back soon or explore our other products!</p>
                  </div>
                ) : (
                  <div className="products-grid">
                    {fastDeliveryProducts.map(product => (
                      <ProductCard 
                        key={product.id} 
                        product={product}
                        showFastDelivery={true}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default FastDelivery;
