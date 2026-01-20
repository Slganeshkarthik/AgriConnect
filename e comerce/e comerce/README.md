# AgriConnect E-Commerce Platform

Full-stack e-commerce platform connecting farmers directly to consumers.

## 🚀 Live Demo

- **Backend API**: [Your Render URL]
- **Frontend**: [Your Vercel URL]

## 🛠️ Tech Stack

**Backend:**
- Flask (Python)
- SQLite Database
- Flask-CORS

**Frontend:**
- React 18
- React Router 6
- Context API
- Axios

## 📦 Features

- 🛒 Shopping cart with localStorage
- 👤 User authentication & profiles
- 📦 Order management & tracking
- ⚡ 30-minute delivery option
- 🌾 Direct farmer-to-consumer marketplace
- 👨‍💼 Admin dashboard
- 💳 Payment integration (Razorpay)

## 🔧 Local Setup

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py
```

Backend runs on `http://localhost:5000`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run React app
npm start
```

Frontend runs on `http://localhost:3000`

## 🌐 Deployment

### Deploy Backend on Render

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3.11

### Deploy Frontend on Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Navigate to frontend: `cd frontend`
3. Deploy: `vercel --prod`
4. Update API URL in frontend code

## 📝 Environment Variables

```
SECRET_KEY=your-secret-key
FLASK_ENV=production
PORT=5000
```

## 👥 Demo Credentials

- **Admin**: username: `admin`, password: `admin123`
- **User**: Sign up to create account

## 📄 License

Private Project - All Rights Reserved

## 🤝 Contributing

This is a private project. Contact the owner for collaboration.
