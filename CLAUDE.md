# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **comprehensive football strength analysis system** with a Flask web application called "Spooky" designed for football prediction games. The system calculates competition-aware team strength scores across Top 5 European leagues plus international teams using 6 core parameters. The web application provides real-time team vs team analysis with European competition integration and interactive features.

**Current Status**: Phase 2 Complete - 47% of full blueprint implemented with live web interface.

## Environment Setup

The project uses a Python virtual environment located at `venv/`. To work with this codebase:

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install requests beautifulsoup4 playwright
```

## Database Architecture

The system uses SQLite with a clean **competition-aware schema**:

### Current Tables (Production)
- `teams`: Team information with UUID primary keys (98 teams across 5 leagues)
- `competitions`: League/competition definitions (8 competitions: 5 domestic + 3 European)
- `competition_team_strength`: **Primary strength data table** with competition-normalized metrics

### Key Files
- `models/setup_db.py`: Database schema creation
- `models/seed_teams.py`: Team data seeding
- `models/create_competition_aware_schema.py`: Competition-aware schema setup
- `db/football_strength.db`: SQLite database file

## Core Components

### Current System Architecture

The system has been **cleaned and organized** into a streamlined structure:

#### Team Strength Agents (`agents/team_strength/`) ✅ PRODUCTION
- `competition_elo_agent.py`: ELO ratings calculated per-competition with fixtures
- `competition_form_agent.py`: Recent form scores (last 5 matches) per-competition  
- `competition_squad_value_agent.py`: Squad market values from Transfermarkt per-competition
- `competition_squad_depth_agent.py`: Squad size analysis per-competition

#### Data Management (`agents/data_collection/`)
- `add_top5_league_teams.py`: Populates teams across all 5 major European leagues

#### Analysis Tools (`agents/analysis/`)
- `competition_summary_report.py`: Comprehensive data coverage and quality report

#### Shared Utilities (`agents/shared/`)
- `competition_normalizer.py`: **KEY UTILITY** - Competition-aware normalization logic
- `team_api_ids.json`: Maps team names to API-Football team IDs
- `debug.py`: Agent debugging utilities

#### Legacy (`agents/legacy/`)
- `player_agent.py`: **ARCHIVED** - Not used in calculations

### Calculation Scripts
- `main.py`: Main strength calculation with weighted scoring system (18% ELO, 15% squad value, 5% form, 2% squad depth)
- `working_main.py`: Detailed calculation script with parameter breakdown for each team
- `debug_main.py`: Database debugging and verification script

### Archive System
All temporary files, validation reports, and legacy scripts are organized in `archive/`:
- `archive/validation_reports/`: Historical validation and credibility reports
- `archive/legacy_scripts/`: Old agents and migration scripts
- `archive/database_backups/`: Database backups before major changes

## API Configuration

The system uses API-Football (v3.football.api-sports.io) with the following configuration:
- API Key: Stored directly in agent files (53faec37f076f995841d30d0f7b2dd9d)
- Leagues: All Top 5 European leagues (Premier League: 39, La Liga: 140, Serie A: 135, Bundesliga: 78, Ligue 1: 61)
- Season: 2024 (current season data)

## Team Strength Parameters (47% of Full Blueprint) ✅ PHASE 2 COMPLETE

The system implements 6 core strength parameters with competition-aware normalization:

### Core Team Strength (40%)
- **ELO Score: 18%** - Match-based team strength (normalized per-competition)
- **Squad Value Score: 15%** - Market-based team quality from Transfermarkt (100% real data coverage)
- **Form Score: 5%** - Recent performance (last 5 matches)
- **Squad Depth Score: 2%** - Squad size and depth measure

### Historical Data Analysis (7%) ✅ NEW IN PHASE 2
- **H2H Performance: 4%** - Head-to-head historical performance analysis
- **Scoring Patterns: 3%** - Goal-scoring trends and defensive patterns

### Competition-Aware Normalization ✅ VALIDATED
**Key Innovation**: Each parameter is normalized within its competition context:
- Values are scaled 0-1 within each league (e.g., best Premier League team = 1.0, worst = 0.0)
- This ensures fair comparison across different competition levels
- Cross-league rankings use raw values, within-league rankings use normalized values

## Data Quality Status ✅ PRODUCTION READY

### Coverage (100% Complete)
- **Teams**: 96/96 teams across 5 leagues
- **ELO Data**: 96/96 teams with real API-Football ratings
- **Squad Values**: 96/96 teams with real Transfermarkt data (no estimates)
- **Form Data**: 96/96 teams with recent match performance
- **Squad Depth**: 96/96 teams with composition analysis

### Global Top 10 Most Valuable Teams
1. **Real Madrid** (La Liga): €1,370M
2. **Manchester City** (Premier League): €1,340M
3. **Chelsea** (Premier League): €1,250M
4. **Arsenal** (Premier League): €1,240M
5. **Liverpool** (Premier League): €1,150M
6. **Paris Saint Germain** (Ligue 1): €1,140M
7. **Barcelona** (La Liga): €1,130M
8. **Bayern München** (Bundesliga): €889M
9. **Tottenham Hotspur** (Premier League): €847M
10. **Manchester United** (Premier League): €822M

## Common Commands

### Primary System (Competition-Aware)
```bash
# Run strength calculations
python main.py                    # Main calculation
python working_main.py           # Detailed breakdown
python debug_main.py             # Database debugging

# Update all metrics (recommended workflow)
python agents/team_strength/competition_elo_agent.py
python agents/team_strength/competition_form_agent.py
python agents/team_strength/competition_squad_value_agent.py
python agents/team_strength/competition_squad_depth_agent.py

# Data analysis
python agents/analysis/competition_summary_report.py
```

### Database Management
```bash
# Initial setup (if needed)
python models/setup_db.py
python models/seed_teams.py
python models/create_competition_aware_schema.py

# Populate teams across all leagues
python agents/data_collection/add_top5_league_teams.py
```

## Data Flow

### Current Production Flow
1. `setup_db.py` creates database schema
2. `seed_teams.py` populates teams across 5 major leagues
3. Competition agents fetch and store metrics in `competition_team_strength` table
4. Normalization occurs within each competition context
5. Main scripts calculate weighted strength scores and display results

## Key Dependencies

- `requests`: API calls to API-Football
- `sqlite3`: Database operations (built-in)
- `beautifulsoup4`: Web scraping for Transfermarkt data
- `playwright`: Browser automation for squad value scraping (fallback)

## Supported Competitions & Teams

### Domestic Leagues (96 teams total) ✅ COMPLETE
- **Premier League** (England): 20 teams
- **La Liga** (Spain): 20 teams  
- **Serie A** (Italy): 20 teams
- **Bundesliga** (Germany): 18 teams
- **Ligue 1** (France): 18 teams

### Team Examples by League
- **Premier League**: Manchester City, Chelsea, Arsenal, Liverpool, Tottenham, etc.
- **La Liga**: Real Madrid, Barcelona, Atletico Madrid, Athletic Club, etc.
- **Serie A**: Inter, Juventus, Napoli, AC Milan, Atalanta, etc.
- **Bundesliga**: Bayern München, RB Leipzig, Bayer Leverkusen, Borussia Dortmund, etc.
- **Ligue 1**: Paris Saint Germain, Monaco, Marseille, Lille, etc.

## System Status

### ✅ Production Ready Features
- Multi-competition data collection
- Competition-aware normalization
- Real-time agent updates
- 100% data coverage with real values
- Clean, organized codebase
- Comprehensive validation system

## Flask Web Application "Spooky" ✅ PRODUCTION READY

### Core Features
- **Team vs Team Analysis**: Compare any teams across 5 leagues + international
- **Competition-Aware Scoring**: Automatic detection of same-league vs cross-league matches
- **Real-Time Data**: Live API integration for form, fixtures, and H2H history
- **Interactive Interface**: Modern web UI with responsive design

### Recent Additions (Phase 2)
- **Last Update Timestamp**: Shows when data was last refreshed
- **Team Form Display**: Interactive W/D/L for last 5 games with match details
- **European Integration**: 384 European competition matches integrated
- **International Teams**: 28 major national teams supported
- **Mobile Optimized**: Full responsive design for all devices

### Web Application Files
- `demo_app.py`: Main Flask application with all API endpoints
- `templates/index.html`: Modern frontend with interactive features
- `database_config.py`: Database abstraction for SQLite/PostgreSQL flexibility

### API Endpoints
- `/`: Main application interface
- `/analyze`: Team strength comparison
- `/api/teams`: Team data by league
- `/api/h2h/<team1>/<team2>`: Head-to-head match history
- `/api/upcoming/<team1>/<team2>`: Upcoming fixtures
- `/api/last-update`: Data refresh timestamp
- `/api/team-form/<team>`: Last 5 games form data

### 🔮 Future Expansion (53% Remaining)
The current system represents 47% of the full blueprint. Remaining categories:
- **Match Context** (20%): Home advantage, match stakes, fatigue
- **Player Availability** (15%): Injuries, international duty, fitness
- **Market Behavior** (10%): Betting market insights
- **External Factors** (5%): Weather, referee tendencies
- **Real-Time Factors** (3%): Live match data, minute-by-minute updates

## Session Logging Protocol

**IMPORTANT**: To maintain continuity across Claude Code sessions:

1. **PROJECT_LOG.md**: Session history tracking what was accomplished
2. **CLAUDE_WEB_CONTEXT.md**: Web application status and deployment context
3. **Auto-update**: After significant tasks, proactively update documentation
4. **Three-file system**: 
   - `CLAUDE.md` (this file): Project guidance and current state
   - `PROJECT_LOG.md`: Historical log of work sessions
   - `CLAUDE_WEB_CONTEXT.md`: Web application and deployment status
5. **Archive system**: All temporary files and reports preserved in `archive/`

This ensures continuity across sessions and maintains project history.

## Production Deployment Guide ✅ READY

### Deployment Configuration
- **Platform**: Railway with PostgreSQL database
- **Repository Name**: `spooky-football-engine` (GitHub)
- **Local Folder**: `football_strength` (no need to match)
- **Production Files Created**:
  - `requirements.txt`: All Python dependencies
  - `Procfile`: Railway deployment configuration
  - `database_config.py`: SQLite/PostgreSQL abstraction
  - `migrate_to_postgresql.py`: Database migration script
  - `.gitignore`: Comprehensive exclusions

### Deployment Commands
```bash
# 1. Create GitHub repository
gh repo create spooky-football-engine --public --description "Football team strength analysis engine"

# 2. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/spooky-football-engine.git
git branch -M main
git push -u origin main

# 3. Deploy to Railway
# - Connect GitHub at railway.app
# - Deploy from repo
# - Add PostgreSQL service
# - Run migration script
```

### Environment Variables (Railway)
- `PORT`: Automatically set by Railway
- `DATABASE_URL`: Automatically set when PostgreSQL added
- No additional configuration needed!

## Important Notes

- **Clean Architecture**: All temporary/debug files moved to `archive/`
- **Real Data Only**: No estimated values used - all data from authoritative sources
- **Production Status**: 100% data coverage, fully validated, ready for game integration
- **Backup System**: Automatic database backups before major changes
- **Credibility Verified**: All team hierarchies and values validated as realistic
- **Deployment Ready**: All production files configured and tested