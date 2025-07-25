-- PostgreSQL Schema for Football Strength Database
-- Migration from SQLite to PostgreSQL

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean migration)
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS competition_team_strength CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

-- Create teams table
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100),
    founded INTEGER,
    venue_name VARCHAR(255),
    venue_city VARCHAR(255),
    venue_capacity INTEGER,
    logo_url TEXT,
    team_code VARCHAR(10)
);

-- Create competitions table
CREATE TABLE competitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100),
    api_league_id INTEGER,
    type VARCHAR(50) CHECK(type IN ('domestic_league', 'european_competition')),
    tier INTEGER, -- 1=top tier, 2=second tier, etc.
    season VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create competition_team_strength table
CREATE TABLE competition_team_strength (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    competition_id UUID NOT NULL,
    team_id UUID NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    
    -- Team Strength Metrics (normalized within competition)
    elo_score REAL,
    elo_normalized REAL,
    squad_value_score REAL,
    squad_value_normalized REAL, 
    form_score REAL,
    form_normalized REAL,
    squad_depth_score REAL,
    squad_depth_normalized REAL,
    
    -- Historical Data Metrics
    h2h_performance REAL,
    h2h_normalized REAL,
    scoring_patterns REAL,
    scoring_normalized REAL,
    form_vs_opposition REAL,
    form_opposition_normalized REAL,
    competition_context REAL,
    competition_normalized REAL,
    
    -- Composite scores
    overall_strength REAL,
    local_league_strength REAL,
    european_strength REAL,
    
    -- Metadata
    last_updated TIMESTAMP,
    season VARCHAR(10) DEFAULT '2024',
    
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    FOREIGN KEY (team_id) REFERENCES teams(id),
    UNIQUE(competition_id, team_id, season)
);

-- Create matches table
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_team_id UUID,
    away_team_id UUID,
    home_team_name VARCHAR(255),
    away_team_name VARCHAR(255),
    home_score INTEGER,
    away_score INTEGER,
    competition_id UUID,
    competition_name VARCHAR(255),
    match_date DATE,
    season VARCHAR(10),
    status VARCHAR(20),
    api_fixture_id INTEGER UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id)
);

-- Create indexes for better performance
CREATE INDEX idx_teams_name ON teams(name);
CREATE INDEX idx_competitions_name ON competitions(name);
CREATE INDEX idx_competition_team_strength_team ON competition_team_strength(team_id);
CREATE INDEX idx_competition_team_strength_comp ON competition_team_strength(competition_id);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);
CREATE INDEX idx_matches_competition ON matches(competition_id);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_api_fixture ON matches(api_fixture_id);

-- Create composite indexes for common queries
CREATE INDEX idx_matches_team_names ON matches(home_team_name, away_team_name);
CREATE INDEX idx_matches_season_status ON matches(season, status);
CREATE INDEX idx_competition_team_season ON competition_team_strength(competition_id, team_id, season);