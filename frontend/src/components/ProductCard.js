import React, { useState } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import './ProductCard.css';

function ProductCard({ product, showFastDelivery = false }) {
  const { addToCart } = useCart();
  const { user } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);

  const handleAddToCart = () => {
    addToCart(product, quantity);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  const isFastDelivery = showFastDelivery && user && product.pincode === user.pincode;

  return (
    <div className={`product-card ${added ? 'added' : ''}`}>
      {isFastDelivery && (
        <div className="fast-delivery-badge">
          🚀 30-Minute Delivery!
        </div>
      )}
      
      <div className="product-image">
        <img src={product.image || '/placeholder.jpg'} alt={product.name} />
      </div>
      
      <div className="product-info">
        <h3>{product.name}</h3>
        <p className="product-description">{product.description}</p>
        
        <div className="product-details">
          <span className="product-price">₹{product.price}</span>
          <span className="product-unit">per {product.unit || 'kg'}</span>
        </div>

        {product.seller && (
          <p className="product-seller">
            👨‍🌾 Seller: {product.seller}
          </p>
        )}

        <div className="product-actions">
          <div className="quantity-selector">
            <button 
              onClick={() => setQuantity(Math.max(1, quantity - 1))}
              className="qty-btn"
            >
              -
            </button>
            <span className="quantity">{quantity}</span>
            <button 
              onClick={() => setQuantity(quantity + 1)}
              className="qty-btn"
            >
              +
            </button>
          </div>
          
          <button 
            onClick={handleAddToCart}
            className={`btn-add-cart ${added ? 'added' : ''}`}
          >
            {added ? '✓ Added!' : '🛒 Add to Cart'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProductCard;
