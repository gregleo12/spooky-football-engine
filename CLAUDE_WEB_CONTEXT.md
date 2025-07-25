# CLAUDE WEB CONTEXT

## Project Overview
**Football Strength Analysis Engine** - A comprehensive web application called "Spooky" (formerly "Match Predictor") that calculates team strength scores for football prediction games.

## Current Status: Phase 2 Complete (47% of Full System)

### ✅ Completed Features
1. **Core Strength Engine (40% → 47%)**
   - ELO Score: 18% weight
   - Squad Value Score: 15% weight  
   - Form Score: 5% weight
   - Squad Depth Score: 2% weight
   - H2H Performance: 4% weight ✅ NEW
   - Scoring Patterns: 3% weight ✅ NEW

2. **Database Coverage**
   - 96 teams across 5 top European leagues
   - 384 European competition matches (273 CL, 111 EL) ✅ NEW
   - International teams (28 countries) ✅ NEW
   - Complete historical match data

3. **Flask Web Application "Spooky"** 
   - Team vs team strength comparison
   - Cross-league and international match analysis
   - Real-time API data integration
   - Last update timestamp display ✅ NEW
   - Team form display (last 5 games) ✅ NEW
   - Interactive form popup with match details ✅ NEW
   - H2H match history with API integration
   - Upcoming fixtures display
   - Mobile-responsive design
   - Duplicate teams issue resolved ✅ NEW

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

### Current Hosting
- **Local Development**: http://localhost:5001
- **Status**: Running locally, considering PostgreSQL migration for production deployment

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
**Ready for Production Deployment** - All core features implemented and tested. System is stable with 100% data coverage and all user-requested features working.

The application is currently running successfully on port 5001 with all new features (European data, scoring patterns, form display, timestamps) integrated and functional.