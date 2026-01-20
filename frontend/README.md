# AgriConnect - React Frontend

This is the interactive React.js frontend for the AgriConnect e-commerce platform.

## ✨ Recent Updates (Dec 2025)

### Modern React 18.3+ Features
- Code splitting and lazy loading for better performance
- Error boundaries for graceful error handling
- Custom hooks for reusable logic
- Memoization with `useMemo` and `useCallback`
- React Suspense for loading states

### Developer Experience Improvements
- ESLint configuration for code quality
- Prettier for consistent formatting
- EditorConfig for team consistency
- Updated dependencies to latest stable versions

See [UPDATES.md](./UPDATES.md) for detailed changelog.

## Features

- 🎨 **Modern UI/UX**: Beautiful, responsive design with smooth animations
- ⚡ **Fast & Interactive**: React.js 18.3+ for dynamic user experience
- 🛒 **Smart Shopping Cart**: Real-time cart updates with localStorage persistence
- 👤 **User Authentication**: Secure login/signup with session management
- 📦 **Order Management**: Complete order history and tracking
- ⚙️ **Admin Dashboard**: Manage orders with pincode filtering
- 🚀 **30-Min Delivery**: Location-based fast delivery feature
- 🛡️ **Error Handling**: Comprehensive error boundaries and validation
- 📱 **Responsive**: Mobile-first design with accessibility support

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- npm (v8 or higher)
- Python 3.x (for Flask backend)

### Installation

1. **Install Frontend Dependencies**
```bash
cd frontend
npm install
```

2. **Install Backend Dependencies**
```bash
cd ..
pip install flask flask-cors
```

### Running the Application

1. **Start Flask Backend** (in project root):
```bash
python app.py
```
The Flask API will run on http://localhost:5000

2. **Start React Frontend** (in frontend folder):
```bash
cd frontend
npm start
```
The React app will run on http://localhost:3000

### Building for Production

```bash
cd frontend
npm run build
```

This creates an optimized production build in the `frontend/build` folder.

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Header.js          # Navigation header
│   │   └── ProductCard.js     # Product display card
│   ├── context/
│   │   ├── AuthContext.js     # Authentication state
│   │   └── CartContext.js     # Shopping cart state
│   ├── pages/
│   │   ├── Home.js            # Home page with products
│   │   ├── FarmProducts.js    # Farmer products page
│   │   ├── FastDelivery.js    # 30-min delivery page
│   │   ├── Cart.js            # Shopping cart page
│   │   ├── Checkout.js        # Checkout page
│   │   ├── Profile.js         # User profile & orders
│   │   ├── Login.js           # Login page
│   │   ├── Signup.js          # Signup page
│   │   └── Admin.js           # Admin dashboard
│   ├── App.js                 # Main app component
│   └── index.js               # Entry point
└── package.json
```

## API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/signup` - User registration
- `POST /api/logout` - User logout
- `GET /api/me` - Get current user

### Products
- `GET /api/home-products` - Get home page products
- `GET /api/products` - Get farm products

### Orders
- `POST /api/place-order` - Place new order
- `GET /api/profile` - Get user orders & stats
- `POST /api/update-user-details` - Update user profile

### Admin
- `GET /api/admin/orders` - Get all orders (admin only)
- `POST /api/update-order-status` - Update order status

## Technologies Used

- **Frontend**: React 18, React Router 6, Axios
- **Backend**: Flask, SQLite
- **Styling**: CSS3 with CSS Variables
- **State Management**: React Context API
- **HTTP Client**: Axios

## Demo Credentials

- **Admin**: username: `admin`, password: `admin123`
- **User**: Create a new account via signup

## Features Breakdown

### Smart Cart Management
- Add/remove items
- Update quantities
- Real-time total calculation
- Persistent storage (localStorage)

### User Profile
- View/edit profile details
- Order history with status
- Order statistics
- Total spending tracking

### Admin Dashboard
- View all orders
- Filter by pincode
- Update order status
- Real-time statistics

### 30-Minute Delivery
- Location-based filtering
- Pincode matching
- Visual delivery badges
- Separate product categorization

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

Private project - All rights reserved
