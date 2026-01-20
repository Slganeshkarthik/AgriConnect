# AgriConnect Frontend - Vercel Deployment

## 🚀 Deploy to Vercel

### Quick Deploy

1. **Install Vercel CLI** (optional):
   ```bash
   npm i -g vercel
   ```

2. **Deploy via Vercel Dashboard**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Configure settings:

### Vercel Configuration

**Root Directory**: `frontend`

**Build Settings**:
- **Framework Preset**: Create React App
- **Build Command**: `npm run build`
- **Output Directory**: `build`
- **Install Command**: `npm install`

### Environment Variables

Add in Vercel Dashboard → Settings → Environment Variables:

```
REACT_APP_API_URL=https://your-backend.onrender.com
```

### After Deployment

1. Update API URL in environment variables
2. Redeploy if needed
3. Your app will be live at: `https://your-app.vercel.app`

## Local Development

```bash
cd frontend
npm install
npm start
```

Runs on `http://localhost:3000`
