# Railway Metabase Deployment Guide

## 🚀 Deploy Metabase to Railway for 24/7 Access

### Prerequisites
- Railway CLI installed: `npm install -g @railway/cli`
- Logged into Railway: `railway login`
- Existing Railway project with PostgreSQL database

### Deployment Options

## Option 1: Railway Template (Recommended - Fastest)

### Step 1: Add Metabase Service to Existing Railway Project
```bash
# Navigate to your project
cd "/Users/matos/Football App Projects/spooky-football-engine"

# Login to Railway (if not already)
railway login

# Link to your existing project
railway link

# Add Metabase service using template
railway add --template metabase
```

### Step 2: Configure Environment Variables
In Railway dashboard → Metabase service → Variables:
```
MB_DB_TYPE=postgres
MB_DB_CONNECTION_URI=${{ Postgres.DATABASE_URL }}
MB_JETTY_HOST=0.0.0.0
MB_JETTY_PORT=${{ PORT }}
```

## Option 2: Docker Deployment (Custom Build)

### Step 1: Deploy Custom Metabase
```bash
# Create new service for Metabase
railway service create metabase

# Deploy using our custom Dockerfile
railway up --service metabase --dockerfile Dockerfile.metabase
```

### Step 2: Environment Configuration
Set these variables in Railway dashboard:
```
DATABASE_URL=${{ Postgres.DATABASE_URL }}
PORT=${{ PORT }}
MB_DB_TYPE=postgres
MB_ENCRYPTION_SECRET_KEY=your-32-character-secret-key-here
```

## Option 3: Manual Railway Dashboard Setup

### Step 1: Railway Dashboard
1. Go to railway.app → Your project
2. Click "New Service" → "Docker Image"
3. Use image: `metabase/metabase:latest`

### Step 2: Environment Variables
Add these variables in Railway dashboard:
```
MB_DB_TYPE=postgres
MB_DB_CONNECTION_URI=${{ Postgres.DATABASE_URL }}
MB_JETTY_HOST=0.0.0.0
MB_JETTY_PORT=${{ PORT }}
MB_ENCRYPTION_SECRET_KEY=football-analytics-secret-key-2024
```

### Step 3: Service Configuration
- **Port**: Use $PORT (Railway assigns dynamically)
- **Health Check**: `/api/health`
- **Start Command**: Default (Metabase will auto-start)

---

## 🔧 Quick CLI Deployment (Choose This!)

```bash
# 1. Navigate to project
cd "/Users/matos/Football App Projects/spooky-football-engine"

# 2. Login and link project
railway login
railway link

# 3. Create Metabase service
railway service create metabase-analytics

# 4. Deploy Metabase
railway deploy --service metabase-analytics --image metabase/metabase:latest

# 5. Set environment variables
railway variables set MB_DB_TYPE=postgres --service metabase-analytics
railway variables set MB_JETTY_HOST=0.0.0.0 --service metabase-analytics
railway variables set MB_ENCRYPTION_SECRET_KEY=football-analytics-secret-2024 --service metabase-analytics

# 6. Connect to PostgreSQL (replace with your actual Postgres service name)
railway variables set MB_DB_CONNECTION_URI='${{ Postgres.DATABASE_URL }}' --service metabase-analytics
```

---

## 📝 Post-Deployment Setup

### 1. Get Your Public URL
After deployment, Railway will provide a URL like:
`https://metabase-analytics-production-xxxx.up.railway.app`

### 2. Initial Metabase Setup
1. Visit your public URL
2. Create admin account
3. Skip database setup (already configured)
4. Start creating dashboards!

### 3. Database Connection (Should be Automatic)
Metabase should automatically connect to your Railway PostgreSQL with:
- **98 teams** across 5 leagues
- **100% parameter coverage**
- **All strength metrics** ready for visualization

---

## 🎯 Expected Results

### Successful Deployment Indicators
```
✅ Service Status: Running
✅ Public URL: https://your-metabase.up.railway.app
✅ Health Check: Passing (/api/health)
✅ Database Connection: Automatic via DATABASE_URL
✅ Admin Setup: Ready for first-time configuration
```

### Database Connection Verification
Once deployed, your Metabase should automatically show:
- **3 Tables**: teams, competitions, competition_team_strength
- **98 Records**: Full team dataset
- **5 Competitions**: All major European leagues
- **100% Coverage**: All parameters populated

---

## 🚨 Troubleshooting

### Common Issues
- **"Database connection failed"**: Check MB_DB_CONNECTION_URI format
- **"Service won't start"**: Verify PORT environment variable
- **"Memory issues"**: Metabase needs ~1GB RAM (Railway provides this)
- **"503 errors"**: Service still starting (wait 2-3 minutes)

### Debug Commands
```bash
# Check service status
railway status --service metabase-analytics

# View logs
railway logs --service metabase-analytics

# Check environment variables
railway variables --service metabase-analytics
```

---

## 💰 Railway Costs
- **Metabase Service**: ~$5-10/month (depends on usage)
- **Combined with PostgreSQL**: ~$10-15/month total
- **Always-on access**: 24/7 availability included

---

## 🔐 Security Notes
- **Admin Access**: Set strong password on first setup
- **Database**: Read-only access recommended for dashboards
- **Public URL**: Consider adding authentication for production use
- **HTTPS**: Automatic SSL provided by Railway

---

## 📊 Next Steps After Deployment
1. **Access your public Metabase URL**
2. **Complete admin setup wizard**
3. **Verify database connection** (should be automatic)
4. **Import dashboard queries** from `metabase_dashboard_queries.sql`
5. **Create 4 dashboards**: System Health, Analytics, Performance, Advanced
6. **Share URL** with your team for 24/7 access!

Your football analytics system will be accessible worldwide at your Railway URL!