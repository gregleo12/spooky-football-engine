# Metabase Complete Setup Guide
## Football Analytics Business Intelligence Dashboard

### ✅ COMPLETED SETUP
- **Metabase Installation**: Running at http://localhost:3000
- **Railway Connection**: Verified (98 teams, 98 strength records)
- **Database Schema**: Synced (3 tables: teams, competitions, competition_team_strength)
- **Verification Queries**: All passed with 100% data coverage

---

## 🚀 NEXT STEPS FOR YOU

### 1. Complete Metabase Initial Setup
1. **Open Metabase**: http://localhost:3000
2. **Create Admin Account**:
   - Email: your-email@domain.com
   - Password: secure-password
   - Name: Your Name
3. **Skip optional steps** (language, analytics tracking)

### 2. Add Railway Database Connection
**Go to**: Admin (⚙️) → Databases → Add database

**Connection Details**:
```
Database Type: PostgreSQL
Display Name: Football Analytics Railway
Host: ballast.proxy.rlwy.net
Port: 10971
Database name: railway
Username: postgres
Password: WJFojeyIZjCfJlRscgARcdrFAqDXKJhT
```

**Click "Save"** - Metabase will automatically sync the schema

### 3. Verify Database Connection
After connection, you should see:
- ✅ **3 Tables discovered**: teams, competitions, competition_team_strength
- ✅ **Sample data preview** showing team names and strength scores
- ✅ **Green connection status** in Admin → Databases

---

## 📊 DASHBOARD CREATION GUIDE

### Dashboard 1: System Health Overview
**Purpose**: Monitor data quality and system performance

**Key Metrics to Create**:
1. **Total Teams** (should show 98)
2. **Parameter Coverage** (should show 100% for all metrics)
3. **Last Update Times** (data freshness)
4. **Value Range Validation** (ELO: 1321-1649)

**SQL Queries**: Use queries from `metabase_dashboard_queries.sql` section 1

### Dashboard 2: Football Analytics Insights
**Purpose**: Explore team strengths and league comparisons

**Key Visualizations**:
1. **Top 20 Teams by ELO** (table with rankings)
2. **League Strength Comparison** (bar chart)
3. **Team Tier Distribution** (pie chart: Elite/Strong/Average/Developing)
4. **Competition Depth Analysis** (scatter plot)

**SQL Queries**: Use queries from `metabase_dashboard_queries.sql` section 2

### Dashboard 3: Performance Monitoring
**Purpose**: Track system metrics and data quality

**Key Charts**:
1. **Parameter Distribution** (histograms)
2. **Data Quality Checks** (traffic light indicators)
3. **Outlier Detection** (teams outside normal ranges)
4. **Coverage Trends** (time series if historical data available)

**SQL Queries**: Use queries from `metabase_dashboard_queries.sql` section 3

---

## 🎯 EXPECTED RESULTS

### Database Connection Verification
When connected successfully, you should see:
```
✅ Teams: 98 (across 5 leagues)
✅ Competitions: 5 (Premier League, La Liga, Serie A, Bundesliga, Ligue 1)
✅ Strength Records: 98 (100% coverage)
✅ Top Team: Paris Saint Germain (ELO: 1649.0)
✅ Parameter Coverage: 100% for all 10 core metrics
```

### Top 5 Teams (Expected)
1. **Paris Saint Germain** (Ligue 1): 1649.0
2. **Bayern München** (Bundesliga): 1645.2  
3. **Barcelona** (La Liga): 1642.8
4. **Real Madrid** (La Liga): 1626.0
5. **Napoli** (Serie A): 1619.0

### League Distribution (Expected)
- **Premier League**: 20 teams
- **Serie A**: 20 teams
- **La Liga**: 20 teams
- **Ligue 1**: 19 teams
- **Bundesliga**: 19 teams

---

## 🔧 METABASE USAGE INSTRUCTIONS

### Creating Questions (Queries)
1. **Click "Ask a question"**
2. **Choose "Native query"** for custom SQL
3. **Select "Football Analytics Railway"** database
4. **Paste SQL from** `metabase_dashboard_queries.sql`
5. **Run query and save** with descriptive name

### Building Dashboards
1. **Go to "Browse data"** → **"Our analytics"**
2. **Click "New dashboard"**
3. **Add saved questions** to dashboard
4. **Arrange and resize** visualizations
5. **Add filters** for interactivity (league, team name, etc.)

### Recommended Dashboard Layout
```
+-------------------+-------------------+
|   System Health   |   Data Coverage   |
|    KPI Cards      |    Progress Bars  |
+-------------------+-------------------+
|          Team Rankings Table          |
|         (Top 20 by ELO)              |
+---------------------------------------+
| League Comparison | Team Distribution |
|   Bar Chart       |    Pie Chart      |
+-------------------+-------------------+
```

---

## 🚨 TROUBLESHOOTING

### Connection Issues
- **"Connection failed"**: Check Railway database is running
- **"Unknown host"**: Verify host: ballast.proxy.rlwy.net
- **"Authentication failed"**: Confirm password exactly as provided

### Data Issues
- **"No tables found"**: Database connection succeeded but schema not synced
- **"Empty results"**: Check database has data with verification queries
- **"Column not found"**: Use exact column names from schema analysis

### Performance Issues
- **Slow queries**: Add LIMIT clauses for testing
- **Timeout errors**: Use simpler queries first, then optimize
- **Memory issues**: Restart Metabase container if needed

---

## 🔄 MAINTENANCE COMMANDS

### Restart Metabase
```bash
cd "/Users/matos/Football App Projects/spooky-football-engine"
docker compose -f docker-compose.metabase.yml restart
```

### View Metabase Logs
```bash
docker logs football-metabase --tail 50
```

### Stop Metabase
```bash
docker compose -f docker-compose.metabase.yml down
```

### Remove Metabase (Clean Install)
```bash
docker compose -f docker-compose.metabase.yml down -v
docker compose -f docker-compose.metabase.yml up -d
```

---

## 📈 SUCCESS CRITERIA CHECKLIST

- [ ] **Metabase accessible** at http://localhost:3000
- [ ] **Admin account created** and logged in
- [ ] **Railway database connected** and synced
- [ ] **3 tables visible** in data browser
- [ ] **Sample queries return** expected results (98 teams)
- [ ] **System Health dashboard** shows 100% coverage
- [ ] **Football Analytics dashboard** displays team rankings
- [ ] **All verification queries** work without errors

---

## 🎊 COMPLETION STATUS

**Current Status**: 🟡 **Ready for Manual Configuration**

**Next Action**: Complete Metabase setup wizard and database connection as described above

**Total Time**: 15-30 minutes for complete dashboard setup

**Files Created**:
- ✅ `docker-compose.metabase.yml` - Docker configuration
- ✅ `metabase_dashboard_queries.sql` - All dashboard SQL queries
- ✅ `METABASE_COMPLETE_SETUP.md` - This complete guide

**System Ready**: All backend infrastructure verified and operational!