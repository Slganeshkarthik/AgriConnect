import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ProductCard from '../components/ProductCard';
import './FarmProducts.css';

function FarmProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const response = await axios.get('/api/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (product.description && product.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (product.seller && product.seller.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="farm-products-page">
      <section className="page-header">
        <div className="header-content">
          <h1>🚜 Direct From Farmers</h1>
          <p>Support local farmers, get the freshest produce</p>
        </div>
      </section>

      <div className="container">
        <div className="search-section">
          <input
            type="text"
            placeholder="🔍 Search by product or farmer name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        {loading ? (
          <div className="loading">Loading farm products...</div>
        ) : (
          <>
            <h2 className="section-title">
              Farm Fresh Products
              <span className="product-count">({filteredProducts.length} items)</span>
            </h2>
            
            {filteredProducts.length === 0 ? (
              <div className="no-products">
                <p>No farm products found matching your search.</p>
              </div>
            ) : (
              <div className="products-grid">
                {filteredProducts.map(product => (
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
      </div>
    </div>
  );
}

export default FarmProducts;
