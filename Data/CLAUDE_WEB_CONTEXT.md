# Football Strength Analysis System - Context for Claude Web

This document provides comprehensive context for Claude Pro web version to understand and assist with the football team strength analysis system.

## Project Overview

This is a Python-based football team strength analysis system that calculates comprehensive team ratings for Premier League teams using multiple data sources and weighted scoring algorithms.

### Core Purpose
- Fetches real-time football data from API-Football
- Calculates team strength scores using 4 key metrics
- Stores data in SQLite database for analysis
- Provides weighted rankings of Premier League teams

## System Architecture

### Database Structure (SQLite)
```sql
-- Teams table with UUID primary keys
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Parameters table storing various team metrics
CREATE TABLE team_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT NOT NULL,
    parameter TEXT NOT NULL,
    value REAL,
    last_updated DATETIME,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    UNIQUE(team_id, parameter)
);
```

### Key Files Structure
```
football_strength/
├── agents/                    # Data collection agents
│   ├── elo_agent.py          # ELO rating calculations
│   ├── form_agent.py         # Recent form analysis
│   ├── player_agent.py       # Player rating aggregation
│   ├── squad_depth_agent.py  # Squad size analysis
│   └── team_api_ids.json     # API team ID mappings
├── models/                    # Database management
│   ├── setup_db.py           # Database schema creation
│   ├── seed_teams.py         # Team data seeding
│   └── reset_teams.py        # Database reset utility
├── db/
│   └── football_strength.db  # SQLite database file
├── main.py                   # Primary calculation script
├── working_main.py           # Alternative with detailed output
├── debug_main.py             # Database debugging utility
└── venv/                     # Python virtual environment
```

## Data Collection System

### API Configuration
- **Service**: API-Football (v3.football.api-sports.io)
- **API Key**: 53faec37f076f995841d30d0f7b2dd9d
- **League ID**: 39 (Premier League)
- **Season**: 2024
- **Rate Limiting**: 5 requests per pause interval

### Data Agents

#### 1. ELO Agent (`elo_agent.py`)
- **Purpose**: Calculates team strength based on match statistics
- **Metrics**: Win rate, goals per game, goal difference, clean sheets
- **Output**: ELO-equivalent score (1200-2000 range)
- **Normalization**: Converts to 0-1 scale for weighting

#### 2. Form Agent (`form_agent.py`)
- **Purpose**: Analyzes recent team performance
- **Data Source**: Last 5 matches with weighted scoring
- **Weights**: [0.3, 0.25, 0.2, 0.15, 0.1] (most recent to oldest)
- **Scoring**: Win=3pts, Draw=1pt, Loss=0pts, normalized to 0-1

#### 3. Player Agent (`player_agent.py`)
- **Purpose**: Aggregates individual player ratings
- **Data Source**: Player statistics from current season
- **Validation**: Ratings 1.0-10.0, flexible minute requirements
- **Fallback**: 7.0 average when API fails
- **Output**: Team average player rating

#### 4. Squad Depth Agent (`squad_depth_agent.py`)
- **Purpose**: Measures squad size and depth
- **Calculation**: Squad size / 5.0 (normalized)
- **Fallback**: 6.75 when data unavailable

## Scoring Algorithm

### Weight Distribution (40% of total blueprint)
```python
WEIGHTS = {
    "elo_score": 0.15,           # 15% - Overall team strength
    "form_score": 0.10,          # 10% - Recent form (last 5 matches)  
    "player_rating_score": 0.10, # 10% - Player quality
    "squad_depth_score": 0.05    # 5% - Squad depth
}
# Total: 40% (Team Strength category from larger blueprint)
```

### Normalization Functions
```python
def normalize_parameter(value, param_name):
    if param_name == "elo_score":
        return max(0, min(1, (value - 1200) / 800))
    elif param_name == "form_score":
        return max(0, min(1, value / 3.0))
    elif param_name == "player_rating_score":
        return max(0, min(1, (value - 6.0) / 2.5))
    elif param_name == "squad_depth_score":
        return max(0, min(1, (value - 3.0) / 4.0))
```

## Current Premier League Teams (2024-25 Season)

```json
{
    "Arsenal": 42,
    "Aston Villa": 66,
    "Bournemouth": 35,
    "Brentford": 55,
    "Brighton & Hove Albion": 51,
    "Chelsea": 49,
    "Crystal Palace": 52,
    "Everton": 45,
    "Fulham": 36,
    "Ipswich Town": 1459,
    "Leicester City": 46,
    "Liverpool": 40,
    "Manchester City": 50,
    "Manchester United": 33,
    "Newcastle United": 34,
    "Nottingham Forest": 65,
    "Southampton": 41,
    "Tottenham Hotspur": 47,
    "West Ham United": 48,
    "Wolverhampton Wanderers": 39
}
```

## Usage Instructions

### Environment Setup
```bash
# Navigate to project directory
cd /path/to/football_strength

# Activate virtual environment
source venv/bin/activate

# Dependencies are already installed:
# requests, beautifulsoup4, playwright, sqlite3 (built-in)
```

### Common Operations

#### 1. Database Setup (if needed)
```bash
python models/setup_db.py      # Create database schema
python models/seed_teams.py    # Populate teams table
```

#### 2. Data Collection
```bash
# Update individual metrics
python agents/elo_agent.py
python agents/form_agent.py
python agents/player_agent.py
python agents/squad_depth_agent.py

# Or run all agents sequentially (recommended)
```

#### 3. Calculate Team Strengths
```bash
python main.py              # Standard calculation with results
python working_main.py      # Detailed breakdown with debug info
python debug_main.py        # Database debugging and verification
```

### Output Examples

#### Main Calculation Output
```
🏆 FOOTBALL TEAM STRENGTH CALCULATOR
==================================================
📊 FINAL TEAM STRENGTH SCORES:
--------------------------------------------------
 1. Manchester City        0.387 ✅ Complete
 2. Arsenal                0.365 ✅ Complete
 3. Liverpool              0.342 ✅ Complete
 ...
💡 Total possible score: 0.400
```

#### Agent Output Example
```
👥 PLAYER RATING UPDATE SUMMARY:
✅ Successful: 17/20 teams
❌ Failed updates:
   • Team Name: Reason for failure
```

## Common Issues and Solutions

### 1. API Rate Limiting
- **Symptom**: HTTP 429 errors or timeouts
- **Solution**: Agents include automatic rate limiting (pause every 5 requests)

### 2. Missing Player Data
- **Symptom**: "No valid player ratings found"
- **Solution**: Script uses fallback values (7.0 for player ratings)

### 3. Team API ID Issues
- **Symptom**: "No player data returned for team ID"
- **Solution**: Check `team_api_ids.json` for correct mappings

### 4. Database Corruption
- **Symptom**: SQLite errors or inconsistent data
- **Solution**: Run `python models/reset_teams.py` then re-setup

## Recent Improvements (Latest Updates)

### Player Agent Fixes
- Updated season from 2023 to 2024
- Improved fallback average from 5.0 to 7.0
- Enhanced error handling and logging
- More flexible player rating validation
- Better API response debugging

### Team Mappings Updated
- Replaced relegated teams (Burnley, Luton Town, Sheffield United)
- Added promoted teams (Ipswich Town, Leicester City, Southampton)
- Verified API IDs for 2024-25 season

## Development Notes

### Code Style
- Uses emojis for logging clarity (🏆, 📊, ✅, ❌, ⚠️)
- Comprehensive error handling with fallback values
- Rate limiting to respect API constraints
- UUID-based team identification for data integrity

### Testing Approach
- No formal test framework currently implemented
- Manual testing via debug scripts
- Database verification through debug_main.py

### Extension Points
- Additional metrics can be added to agents/ directory
- Weight adjustments in main calculation scripts
- New normalization functions for different data ranges

## Security Considerations

- API key is currently embedded in code (consider environment variables)
- Database is local SQLite (no network security concerns)
- No user authentication required for local operation

## Performance Characteristics

- **Data Collection**: ~1-2 minutes for all agents
- **Calculation**: Near-instant for 20 teams
- **Database Size**: <1MB for full dataset
- **Memory Usage**: Minimal (<50MB during operation)

This system provides a robust foundation for football analytics with real-time data integration and flexible scoring algorithms. The modular design allows for easy extension and modification of both data sources and calculation methods.