# 🚀 Deployment Guide

## Architecture Overview

- **Frontend**: Next.js → Vercel
- **Backend**: FastAPI → Railway  
- **Database**: PostgreSQL → Supabase (already set up)
- **WebSockets**: Real-time terminal communication

## 🔧 Prerequisites

1. GitHub repository with your code
2. Supabase PostgreSQL database (✅ you have this)
3. Vercel account
4. Railway account

## 📋 Step-by-Step Deployment

### 1. Deploy Backend to Railway

**A. Push code to GitHub**
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

**B. Deploy to Railway**
1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository (whole repo, not just backend folder)
4. Railway will use the `railway.json` config to build with `backend/Dockerfile.api`

**C. Set Environment Variables in Railway**
```
PORT=8002
DATABASE_URL=postgresql://postgres:[YOUR_SUPABASE_PASSWORD]@[YOUR_SUPABASE_HOST]:5432/postgres
CORS_ORIGINS=https://your-app.vercel.app
```

**D. Get your Railway backend URL**
After deployment, Railway gives you a URL like: `https://your-backend.railway.app`

### 2. Deploy Frontend to Vercel

**A. Deploy to Vercel**
1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "New Project" → Select your repository
3. Set Root Directory to `frontend`
4. Vercel will auto-detect Next.js settings

**B. Set Environment Variables in Vercel**
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app/ws
```

**C. Deploy**
Click "Deploy" - Vercel will build and deploy automatically

### 3. Update CORS Settings

Once you have your Vercel URL (e.g., `https://your-app.vercel.app`):

1. Go back to Railway
2. Update the `CORS_ORIGINS` environment variable:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```
3. Redeploy the backend

## 🔍 Testing Your Deployment

1. **Visit your Vercel URL**: `https://your-app.vercel.app`
2. **Test API connection**: Check if dashboard loads properly
3. **Test WebSocket**: Try terminal commands in a workspace
4. **Test database**: Create sessions, workspaces, etc.

## 🐛 Troubleshooting

### Common Issues:

**Frontend can't reach backend:**
- Check `NEXT_PUBLIC_API_URL` in Vercel environment variables
- Ensure Railway backend is running

**WebSocket connection fails:**
- Check `NEXT_PUBLIC_WS_URL` uses `wss://` (not `ws://`)
- Verify Railway supports WebSocket connections

**Database connection errors:**
- Verify Supabase connection string in Railway
- Check Supabase firewall settings (should allow all IPs for Railway)

**CORS errors:**
- Update `CORS_ORIGINS` in Railway with exact Vercel URL
- No trailing slashes in URLs

## 📊 Monitoring

**Railway:**
- Check logs at `https://railway.app/project/[your-project]/deployments`
- Monitor health checks at `/api/health/`

**Vercel:**
- View deployment logs in Vercel dashboard
- Check function logs for errors

**Supabase:**
- Monitor database connections
- Check query performance

## 💰 Cost Estimates

- **Vercel**: Free tier (sufficient for most cases)
- **Railway**: ~$5-20/month depending on usage
- **Supabase**: Free tier up to 500MB database

## 🔄 Alternative: All-Docker Deployment

If you prefer Docker on a VPS:

```bash
# Build and run with docker-compose
docker-compose up --build -d
```

Create `docker-compose.yml` in project root if you want this option.

## 🎯 Next Steps After Deployment

1. Set up custom domain (optional)
2. Configure monitoring/alerts  
3. Set up CI/CD pipelines
4. Add environment-specific configurations
5. Implement backup strategies for Supabase

---

**✅ Your deployment stack: Vercel + Railway + Supabase**
This gives you automatic scaling, WebSocket support, and a managed database.