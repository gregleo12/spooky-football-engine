# Metabase Open Source Setup for Spooky Football Engine

## Overview
This guide covers installing Metabase open source to visualize and analyze the football team strength data from the Spooky Football Engine database.

## Prerequisites
- Docker installed on your system
- Access to the football_strength.db SQLite database
- Port 3000 available for Metabase web interface

## Quick Start (Docker Method - Recommended)

### 1. Create Metabase Docker Setup
```bash
# Create metabase directory
mkdir metabase-spooky
cd metabase-spooky

# Create docker-compose.yml for easy management
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  metabase:
    image: metabase/metabase:latest
    container_name: spooky-metabase
    hostname: metabase
    volumes:
      - ./metabase-data:/metabase-data
      - ../db:/db:ro  # Mount database directory as read-only
    environment:
      - MB_DB_FILE=/metabase-data/metabase.db
    ports:
      - "3000:3000"
    restart: unless-stopped
EOF
```

### 2. Start Metabase
```bash
# Start Metabase container
docker-compose up -d

# Check if running
docker-compose ps

# View logs (optional)
docker-compose logs -f metabase
```

### 3. Initial Setup
1. Open browser to http://localhost:3000
2. Complete initial setup wizard:
   - Create admin account
   - Skip "Add your data" for now
   - Complete setup

## Database Connection Configuration

### Connect to SQLite Database
1. Go to Admin → Databases
2. Click "Add database"
3. Select "SQLite" as database type
4. Configure connection:
   - **Display name**: `Spooky Football Engine`
   - **Database file path**: `/db/football_strength.db`
   - **Advanced options**: Leave defaults
5. Click "Save"
6. Test connection - should show "Successfully connected"

## Initial Dashboard Setup

### Key Tables to Explore
The system contains these main tables:
- `teams`: Team information (98 teams across 5 leagues + international)
- `competitions`: League/competition definitions 
- `competition_team_strength`: **Primary data table** with all metrics

### Recommended Initial Queries

#### 1. Top Teams by Strength (Global)
```sql
SELECT 
    cts.team_name,
    c.name as league,
    cts.local_league_strength,
    cts.european_strength,
    cts.elo_score,
    cts.squad_value_score
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
WHERE cts.local_league_strength IS NOT NULL
ORDER BY cts.european_strength DESC
LIMIT 20
```

#### 2. League Comparison
```sql
SELECT 
    c.name as league,
    COUNT(*) as team_count,
    AVG(cts.local_league_strength) as avg_strength,
    AVG(cts.squad_value_score) as avg_squad_value,
    AVG(cts.elo_score) as avg_elo
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
WHERE c.name != 'International'
GROUP BY c.name
ORDER BY avg_strength DESC
```

#### 3. Squad Value vs Performance
```sql
SELECT 
    cts.team_name,
    c.name as league,
    cts.squad_value_score as squad_value_millions,
    cts.local_league_strength,
    cts.elo_score
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
WHERE cts.squad_value_score IS NOT NULL 
AND c.name != 'International'
ORDER BY cts.squad_value_score DESC
```

## Dashboard Creation Guide

### Dashboard 1: League Overview
**Visualizations to create:**
1. **Bar Chart**: Average strength by league
2. **Scatter Plot**: Squad value vs ELO score
3. **Table**: Top 10 teams by European strength
4. **Pie Chart**: Team distribution by league

### Dashboard 2: Team Analysis
**Visualizations to create:**
1. **Line Chart**: Team strength parameters breakdown
2. **Heat Map**: League vs strength metrics
3. **Box Plot**: Strength distribution by league
4. **Table**: Detailed team metrics with filters

### Dashboard 3: Competition Analysis
**Visualizations to create:**
1. **Bar Chart**: European vs domestic strength comparison
2. **Scatter Plot**: ELO vs squad value correlation
3. **Histogram**: Strength score distribution
4. **Table**: Competition participation and performance

## Advanced Configuration

### Custom Metabase Settings
Add these environment variables to docker-compose.yml for enhanced features:

```yaml
environment:
  - MB_DB_FILE=/metabase-data/metabase.db
  - MB_SITE_NAME=Spooky Football Analytics
  - MB_SITE_URL=http://localhost:3000
  - MB_ADMIN_EMAIL=admin@spooky.local
  - JAVA_TIMEZONE=UTC
```

### Security Considerations
- Change default admin password immediately
- Consider setting up HTTPS for production use
- Backup metabase-data directory regularly
- Set up user permissions for different access levels

## Data Refresh Strategy

Since the football data updates regularly, consider:

1. **Manual Refresh**: Use "Sync database schema" in Admin → Databases
2. **Scheduled Refresh**: Set up automatic data refresh in dashboard settings
3. **Real-time Updates**: Configure database to notify Metabase of changes

## Useful Metabase Features for Football Data

### Filters and Parameters
- League selector dropdown
- Team name search
- Strength range sliders
- Season/date filters

### Custom Metrics
Create calculated fields for:
- Strength rankings within league
- Performance ratios (strength per squad value)
- Z-scores for normalized comparisons

### Alerts and Subscriptions
- Weekly top performers report
- Strength change notifications
- Custom team performance alerts

## Troubleshooting

### Common Issues
1. **Database not found**: Ensure path `/db/football_strength.db` is correct
2. **Permission denied**: Check Docker volume mounting permissions
3. **Port 3000 in use**: Change port in docker-compose.yml
4. **Slow queries**: Add indexes to frequently queried columns

### Performance Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX idx_team_strength ON competition_team_strength(local_league_strength);
CREATE INDEX idx_competition ON competition_team_strength(competition_id);
CREATE INDEX idx_team_name ON competition_team_strength(team_name);
```

## Backup and Maintenance

### Backup Metabase Configuration
```bash
# Backup metabase data
tar -czf metabase-backup-$(date +%Y%m%d).tar.gz metabase-data/

# Restore from backup
tar -xzf metabase-backup-YYYYMMDD.tar.gz
```

### Update Metabase
```bash
# Pull latest image
docker-compose pull metabase

# Restart with new image
docker-compose up -d
```

## Integration with Spooky Web App

Consider creating API endpoints in demo_app.py to serve Metabase visualizations:
- Embed Metabase charts in main application
- Share dashboard URLs
- Export data for external analysis

## Next Steps
1. Set up initial dashboards using provided queries
2. Create user accounts for different access levels
3. Configure automated data refresh schedules
4. Explore advanced visualizations and custom metrics

---

## Quick Command Reference
```bash
# Start Metabase
docker-compose up -d

# Stop Metabase
docker-compose down

# View logs
docker-compose logs -f metabase

# Access Metabase
open http://localhost:3000
```