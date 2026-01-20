# Installation Guide for AgriConnect React App

## Quick Start

### 1. Install Python Dependencies

```powershell
pip install flask flask-cors
```

### 2. Install Node.js Dependencies

```powershell
cd frontend
npm install
```

### 3. Start the Backend Server

Open a PowerShell terminal in the project root:

```powershell
python app.py
```

The Flask server will start on http://localhost:5000

### 4. Start the React Development Server

Open another PowerShell terminal:

```powershell
cd frontend
npm start
```

The React app will automatically open in your browser at http://localhost:3000

## Troubleshooting

### If flask-cors is not found:
```powershell
pip install --upgrade flask flask-cors
```

### If npm install fails:
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Port already in use:
- Flask (5000): Change port in app.py
- React (3000): React will offer to use a different port

## Next Steps

1. Visit http://localhost:3000
2. Login with demo credentials: admin / admin123
3. Explore the interactive React interface!
