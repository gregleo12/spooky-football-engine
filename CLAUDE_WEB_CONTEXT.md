# CLAUDE WEB CONTEXT

## Project Overview
**Football Strength Analysis Engine** - A comprehensive web application called "Spooky" (formerly "Match Predictor") that calculates team strength scores for football prediction games.

## Current Status: Phase 2C COMPLETE - Production Live with Fresh Architecture

### ✅ Live Production Application
1. **Fresh Football Analytics Web App** 
   - **Live URL**: https://spooky-football-engine-production.up.railway.app/
   - **Architecture**: Clean `fresh_football_app/` build (not legacy demo_app.py)
   - **Railway PostgreSQL**: 98 teams with complete 10-parameter coverage
   - **Modern Dark Theme**: Professional betting platform aesthetic with neon cyan accents

2. **Core Strength Engine (100% Working)**
   - ELO Score: 18% weight
   - Squad Value Score: 15% weight  
   - Form Score: 5% weight
   - Squad Depth Score: 2% weight
   - Key Player Availability: 10% weight
   - Motivation Factor: 10% weight
   - Tactical Matchup: 10% weight
   - Offensive Rating: 10% weight
   - Defensive Rating: 10% weight
   - H2H Performance: 10% weight

3. **Production Features**
   - **Admin Dashboard** (`/admin`): Real-time system monitoring and health checks
   - **Team Comparison** (`/compare`): Professional head-to-head analysis with 10 parameters
   - **Betting Odds Calculator** (`/odds`): Multi-market odds (match result, goals, BTTS)
   - **Full REST API**: Complete endpoints for teams, comparison, odds, and health
   - **Modern UI**: Dark theme with perfect contrast and professional appearance

## Recent Major Updates (Current Session)

### Phase 2 Implementation ✅
- **European Competition Integration**: Added Champions League and Europa League data
- **Scoring Patterns Analysis**: New 3% weight component analyzing goal-scoring trends
- **System Weight**: Increased from 44% to 47% total

### Web App Enhancements ✅
1. **Last Update Timestamp**: Shows when data was last refreshed
2. **Team Form Display**: Shows W/D/L for last 5 games per team
3. **Interactive Form Details**: Click form letters to see match details in popup
4. **Bug Fixes**: Resolved duplicate teams in dropdown selection

### Technical Architecture

#### Backend (Python/SQLite)
- **Database**: SQLite with competition-aware schema
- **API Integration**: API-Football for live data
- **Web Scraping**: Transfermarkt for squad values
- **Historical Data**: European competitions and H2H analysis

#### Frontend (Flask/HTML/CSS/JS)
- **Framework**: Flask with Jinja2 templates
- **Styling**: Modern CSS with gradients and animations
- **Interactivity**: JavaScript for dynamic content
- **Mobile**: Responsive design for all devices

#### Data Collection Agents
- **Team Strength Agents** (`agents/team_strength/`): Core metrics
- **Historical Data Agents** (`agents/historical_data/`): H2H and European data ✅ NEW
- **Shared Utilities** (`agents/shared/`): Normalization and utilities

## System Capabilities

### Team Strength Analysis
- **96 Teams**: Premier League, La Liga, Serie A, Bundesliga, Ligue 1
- **28 International Teams**: Major national teams
- **Competition-Aware**: Normalized within each league context
- **Real Data**: 100% real values from authoritative sources

### Match Analysis Features
- **Same League**: Uses local league strength scores
- **Cross League**: Uses European strength scores
- **International**: Uses international strength scores
- **H2H History**: Real match history from API-Football
- **Upcoming Fixtures**: Next 5 fixtures for each team
- **Form Analysis**: Last 5 games with detailed breakdowns

### Current Hosting Status
- **Production URL**: https://spooky-football-engine-production.up.railway.app/ ✅ LIVE
- **Architecture**: Fresh Football Analytics App (`fresh_football_app/` directory)
- **Database**: Railway PostgreSQL with 98 teams, 10 parameters, 100% coverage
- **Deployment**: Auto-deploy from GitHub with Railway integration
- **Status**: PRODUCTION READY - All features operational

## Deployment Progress (Session 2 - July 25, 2025)

### ✅ Completed Deployment Preparation:
1. **Git Repository**: Initialized with comprehensive .gitignore
2. **Production Configuration**:
   - `requirements.txt`: All dependencies including gunicorn, psycopg2-binary
   - `Procfile`: Railway-ready with gunicorn configuration
   - `database_config.py`: Database abstraction supporting SQLite/PostgreSQL
   - `migrate_to_postgresql.py`: Complete migration script ready
   - `demo_app.py`: Modified for production (PORT env var, DATABASE_URL support)
3. **Initial Commit**: All 54 files committed and ready for push

### 📋 Deployment Checklist:
- ✅ Initialize git repository and create .gitignore
- ⏳ Create GitHub repository 'spooky-football-engine'
- ✅ Create requirements.txt with all dependencies
- ✅ Create Procfile for Railway deployment
- ✅ Modify demo_app.py for production configuration
- ✅ Set up Railway deployment with PostgreSQL (Phase 2B complete)
- ✅ Create database migration script
- ✅ Sync complete data to Railway PostgreSQL (98 teams, all parameters)
- ⏳ Test production deployment and verify all features

### 🚀 Next Steps for Deployment:
```bash
# Create GitHub repo and push code
gh repo create spooky-football-engine --public --description "Football team strength analysis engine with Flask web interface"
git remote add origin https://github.com/YOUR_USERNAME/spooky-football-engine.git
git branch -M main
git push -u origin main

# Then deploy to Railway:
# 1. Go to railway.app
# 2. Connect GitHub account
# 3. Deploy from spooky-football-engine repo
# 4. Add PostgreSQL service
# 5. Run migration: python migrate_to_postgresql.py
```

## Future Expansion (53% Remaining)

### Planned Categories
- **Match Context** (20%): Home advantage, match stakes, fatigue
- **Player Availability** (15%): Injuries, international duty, fitness  
- **Market Behavior** (10%): Betting market insights
- **External Factors** (5%): Weather, referee tendencies

### Deployment Considerations
- **Database Migration**: Considering SQLite → PostgreSQL
- **Hosting Platforms**: Render, Railway, DigitalOcean
- **Production Readiness**: All features tested and working

## Key Files Structure

### Web Application
- `demo_app.py`: Main Flask application
- `templates/index.html`: Frontend interface
- `database_config.py`: Database abstraction layer ✅ NEW
- `postgresql_schema.sql`: PostgreSQL migration schema ✅ NEW

### Core Engine
- `competition_team_strength_calculator.py`: Main strength calculation
- `agents/historical_data/`: New historical analysis agents ✅ NEW
- `agents/team_strength/`: Core strength metrics agents

### Documentation
- `CLAUDE.md`: Technical project guidance
- `PROJECT_LOG.md`: Session history tracking
- `CLAUDE_WEB_CONTEXT.md`: This file - web app context

## Development Status
**PHASE 2C COMPLETE** - Professional betting analytics platform deployed with modern dark theme.

### Current State (Session 6 - July 28, 2025) ✅ COMPLETE
- **Production App**: Live at https://spooky-football-engine-production.up.railway.app/
- **Fresh Architecture**: Complete rebuild in `fresh_football_app/` directory
- **Modern Dark Theme**: Professional neon cyan design with perfect contrast
- **Railway PostgreSQL**: 98 teams with 10 parameters at 100% coverage
- **All Features Working**: Admin dashboard, team comparison, betting odds calculator
- **Auto-Deploy**: GitHub integration for continuous deployment

### Key Files (Fresh App Architecture)
- `fresh_football_app/new_app.py`: Main Flask application with complete feature set
- `fresh_football_app/db_interface.py`: PostgreSQL interface for 10-parameter system
- `fresh_football_app/templates/`: Complete HTML templates with modern dark theme
- `fresh_football_app/Procfile`: Railway deployment configuration
- `fresh_football_app/requirements.txt`: Production dependencies

### Major Achievements
1. **Infrastructure Recovery**: Fixed Railway PostgreSQL by eliminating legacy queries
2. **Fresh App Development**: Built modern application from scratch
3. **Professional Design**: Implemented betting platform-quality dark theme
4. **Perfect Contrast**: Optimized readability matching industry standards
5. **Production Deployment**: Live application with all features operational

**Status**: Phase 2C Web App Integration COMPLETE - System ready for production use.