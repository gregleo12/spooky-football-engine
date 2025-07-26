#!/usr/bin/env python3
"""
Football Strength Demo Web Application

A simple Flask web app that demonstrates the dual strength scoring system:
- Select home and away teams from dropdown menus
- Automatically detects same league vs cross-league matches
- Shows appropriate strength scores (local for same league, European for cross-league)
- Displays match prediction and strength comparison
"""
from flask import Flask, render_template, request, jsonify
import os
import json
from database_config import db_config

app = Flask(__name__)

# Load team API IDs at module level
team_api_ids_path = os.path.join(os.path.dirname(__file__), 'agents', 'shared', 'team_api_ids.json')
TEAM_API_IDS = {}

try:
    with open(team_api_ids_path, 'r') as f:
        club_api_ids = json.load(f)
        TEAM_API_IDS.update(club_api_ids)
except Exception as e:
    print(f"Warning: Could not load team API IDs from {team_api_ids_path}: {e}")
    # Fallback to essential Premier League mappings
    TEAM_API_IDS = {
        'Liverpool': 40,
        'Manchester City': 50,
        'Manchester United': 33,
        'Chelsea': 49,
        'Arsenal': 42,
        'Tottenham Hotspur': 47,
        'Everton': 45,
        'Fulham': 36,
        'Brighton & Hove Albion': 51,
        'Aston Villa': 66,
        'Newcastle United': 34,
        'West Ham United': 48,
        'Wolverhampton Wanderers': 39,
        'Leicester City': 46,
        'Bournemouth': 35,
        'Crystal Palace': 52,
        'Brentford': 55,
        'Nottingham Forest': 65,
        'Southampton': 41,
        'Ipswich Town': 57
    }

# Add international teams
INTERNATIONAL_TEAMS = {
    'Brazil': 6,
    'France': 2,
    'Argentina': 26,
    'England': 10,
    'Spain': 9,
    'Germany': 25,
    'Portugal': 27,
    'Netherlands': 1118,
    'Italy': 768,
    'Belgium': 1,
    'Croatia': 3,
    'Uruguay': 7,
    'Colombia': 8,
    'Denmark': 21,
    'Mexico': 16,
    'USA': 22,
    'Switzerland': 15,
    'Poland': 24,
    'Senegal': 13,
    'Morocco': 31,
    'Japan': 12,
    'Wales': 767,
    'Serbia': 14,
    'Australia': 29,
    'South Korea': 17
}
TEAM_API_IDS.update(INTERNATIONAL_TEAMS)

class FootballStrengthDemo:
    def __init__(self):
        self.db_path = "db/football_strength.db"
    
    def get_database_connection(self):
        """Get database connection (production-ready)"""
        return db_config.get_connection()
    
    def get_all_teams(self):
        """Get all teams grouped by league"""
        conn = self.get_database_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT DISTINCT
                c.name as league,
                cts.team_name,
                cts.local_league_strength,
                cts.european_strength,
                CASE c.name
                    WHEN 'Premier League' THEN 1
                    WHEN 'La Liga' THEN 2
                    WHEN 'Serie A' THEN 3
                    WHEN 'Bundesliga' THEN 4
                    WHEN 'Ligue 1' THEN 5
                    WHEN 'International' THEN 6
                END as league_order
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'International')
            AND (cts.season = '2024' OR c.name = 'International')
            AND cts.local_league_strength IS NOT NULL
            ORDER BY league_order, cts.team_name
        """)
        
        # Use ordered structure to maintain league order
        from collections import OrderedDict
        teams_by_league = OrderedDict()
        all_teams = []
        seen_teams = set()  # Track teams to avoid duplicates
        
        # Pre-populate with correct order
        league_order = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'International']
        for league in league_order:
            teams_by_league[league] = []
        
        for league, team, local, european, league_order in c.fetchall():
            # Create unique key for this team-league combination
            team_key = f"{team}_{league}"
            
            if team_key not in seen_teams:
                seen_teams.add(team_key)
                
                team_data = {
                    'name': team,
                    'league': league,
                    'local_strength': local,
                    'european_strength': european
                }
                
                teams_by_league[league].append(team_data)
                all_teams.append(team_data)
        
        conn.close()
        return teams_by_league, all_teams
    
    def get_team_data(self, team_name):
        """Get specific team data"""
        conn = self.get_database_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT 
                c.name as league,
                cts.team_name,
                cts.local_league_strength,
                cts.european_strength,
                cts.elo_score,
                cts.squad_value_score
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE cts.team_name = %s
        """, (team_name,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'league': result[0],
                'name': result[1],
                'local_strength': result[2],
                'european_strength': result[3],
                'elo': result[4],
                'squad_value': result[5]
            }
        return None
    
    def analyze_match(self, home_team, away_team):
        """Analyze a match between two teams"""
        try:
            home_data = self.get_team_data(home_team)
            away_data = self.get_team_data(away_team)
            
            if not home_data:
                return {'error': f'Team data not found for {home_team}'}
            if not away_data:
                return {'error': f'Team data not found for {away_team}'}
                
        except Exception as e:
            print(f"Error getting team data: {e}")
            return {'error': 'Database connection failed - please try again'}
        
        # Determine if same league or cross-league or international
        same_league = home_data['league'] == away_data['league']
        is_international = home_data['league'] == 'International' and away_data['league'] == 'International'
        
        # Choose appropriate strength scores
        if is_international:
            score_type = 'International'
            home_strength = home_data['european_strength']  # Use european strength for international
            away_strength = away_data['european_strength']
            explanation = f"International match between {home_data['name']} and {away_data['name']}, using international strength scores."
        elif same_league:
            score_type = 'Local League'
            home_strength = home_data['local_strength']
            away_strength = away_data['local_strength']
            explanation = f"Both teams play in {home_data['league']}, using local league strength scores."
        else:
            score_type = 'European'
            home_strength = home_data['european_strength']
            away_strength = away_data['european_strength']
            explanation = f"Cross-league match ({home_data['league']} vs {away_data['league']}), using European strength scores."
        
        # Calculate match prediction
        total_strength = home_strength + away_strength
        if total_strength > 0:
            home_probability = (home_strength / total_strength) * 100
            away_probability = (away_strength / total_strength) * 100
        else:
            home_probability = away_probability = 50.0
        
        # Add home advantage boost (5% for same league, 3% for European)
        home_advantage = 5.0 if same_league else 3.0
        home_probability = min(95.0, home_probability + home_advantage)
        away_probability = 100.0 - home_probability
        
        # Determine favorite
        if home_probability > away_probability:
            favorite = home_team
            favorite_prob = home_probability
        else:
            favorite = away_team
            favorite_prob = away_probability
        
        return {
            'home_team': home_data,
            'away_team': away_data,
            'same_league': same_league,
            'score_type': score_type,
            'home_strength': home_strength,
            'away_strength': away_strength,
            'home_probability': round(home_probability, 1),
            'away_probability': round(away_probability, 1),
            'favorite': favorite,
            'favorite_probability': round(favorite_prob, 1),
            'explanation': explanation
        }

# Initialize demo instance
demo = FootballStrengthDemo()

@app.route('/')
def index():
    """Main page with team selection"""
    teams_by_league, all_teams = demo.get_all_teams()
    return render_template('index.html', teams_by_league=teams_by_league, all_teams=all_teams)

@app.route('/analyze', methods=['POST'])
def analyze_match():
    """Analyze selected match"""
    try:
        data = request.get_json()
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        
        if not home_team or not away_team:
            return jsonify({'error': 'Please select both teams'})
        
        if home_team == away_team:
            return jsonify({'error': 'Please select different teams'})
        
        result = demo.analyze_match(home_team, away_team)
        return jsonify(result)
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({'error': 'Database connection failed - please try again'})

@app.route('/api/teams')
def api_teams():
    """API endpoint to get all teams"""
    teams_by_league, all_teams = demo.get_all_teams()
    return jsonify({
        'teams_by_league': teams_by_league,
        'all_teams': all_teams
    })

@app.route('/api/h2h/<home_team>/<away_team>')
def get_h2h_history(home_team, away_team):
    """Get real head-to-head history between two teams"""
    import requests
    
    # API configuration
    API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
    BASE_URL = "https://v3.football.api-sports.io"
    HEADERS = {"x-apisports-key": API_KEY}
    
    # Get team IDs from global mapping
    home_id = TEAM_API_IDS.get(home_team)
    away_id = TEAM_API_IDS.get(away_team)
    
    if not home_id or not away_id:
        # Return mock data for teams not in mapping
        return jsonify({
            'matches': [],
            'message': f'API mapping not available for {home_team if not home_id else away_team}'
        })
    
    try:
        # Fetch H2H data
        url = f"{BASE_URL}/fixtures/headtohead"
        params = {
            "h2h": f"{home_id}-{away_id}",
            "last": 20  # Get more to filter properly
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        # Debug logging (can be removed in production)
        # print(f"H2H API call for {home_team} vs {away_team}: Status {response.status_code}")
        # print(f"Raw response has {len(data.get('response', []))} fixtures")
        
        if response.status_code != 200 or not data.get('response'):
            return jsonify({'matches': [], 'error': 'No data available'})
        
        # Check if these are international teams
        international_teams = {'Brazil', 'France', 'Argentina', 'England', 'Spain', 'Germany', 
                              'Portugal', 'Netherlands', 'Italy', 'Belgium', 'Croatia', 'Uruguay',
                              'Colombia', 'Denmark', 'Mexico', 'Switzerland', 'Poland', 'Senegal',
                              'Morocco', 'Japan', 'USA', 'Wales', 'Serbia', 'Australia', 'South Korea'}
        
        is_international_match = home_team in international_teams and away_team in international_teams
        
        # Parse and filter fixtures more carefully
        matches = []
        target_teams = {home_team.lower(), away_team.lower()}
        
        for fixture in data['response']:
            # Only include finished matches with actual scores
            if (fixture['fixture']['status']['short'] not in ['FT', 'AET', 'PEN'] or 
                fixture['goals']['home'] is None or 
                fixture['goals']['away'] is None):
                continue
                
            home_name = fixture['teams']['home']['name']
            away_name = fixture['teams']['away']['name']
            competition = fixture['league']['name']
            
            # For international matches, be extra strict about competitions
            if is_international_match:
                # Only allow international competitions
                international_competitions = ['World Cup', 'UEFA Nations League', 'UEFA European Championship',
                                            'Copa America', 'CONMEBOL World Cup Qualifiers', 'UEFA World Cup Qualifiers',
                                            'International Friendly', 'Friendlies', 'FIFA World Cup']
                
                if not any(comp.lower() in competition.lower() for comp in international_competitions):
                    continue
            
            # Verify teams match what we requested (case insensitive)
            fixture_teams = {home_name.lower(), away_name.lower()}
            
            # Skip if teams don't match our request exactly
            if not target_teams.issubset(fixture_teams):
                continue
                
            match_data = {
                'date': fixture['fixture']['date'],
                'homeTeam': home_name,
                'awayTeam': away_name,
                'homeScore': fixture['goals']['home'],
                'awayScore': fixture['goals']['away'],
                'competition': competition
            }
            matches.append(match_data)
            
            # Stop once we have 5 valid matches
            if len(matches) >= 5:
                break
        
        return jsonify({'matches': matches})
        
    except Exception as e:
        print(f"Error fetching H2H: {e}")
        return jsonify({'matches': [], 'error': str(e)})

@app.route('/api/upcoming/<home_team>/<away_team>')
def get_upcoming_fixtures(home_team, away_team):
    """Get upcoming fixtures for both teams"""
    import requests
    from datetime import datetime, timedelta
    
    # API configuration
    API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
    BASE_URL = "https://v3.football.api-sports.io"
    HEADERS = {"x-apisports-key": API_KEY}
    
    try:
        fixtures = []
        today = datetime.now().strftime('%Y-%m-%d')
        future_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
        
        # Get fixtures for both teams
        for team in [home_team, away_team]:
            team_id = TEAM_API_IDS.get(team)
            if not team_id:
                continue
                
            url = f"{BASE_URL}/fixtures"
            params = {
                "team": team_id,
                "from": today,
                "to": future_date,
                "status": "NS"  # Not Started
            }
            
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get('response'):
                for fixture in data['response'][:3]:  # Next 3 fixtures per team
                    fixture_data = {
                        'date': fixture['fixture']['date'],
                        'homeTeam': fixture['teams']['home']['name'],
                        'awayTeam': fixture['teams']['away']['name'],
                        'competition': fixture['league']['name'],
                        'venue': fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else 'TBD'
                    }
                    fixtures.append(fixture_data)
        
        # Sort by date and remove duplicates
        seen = set()
        unique_fixtures = []
        for fixture in sorted(fixtures, key=lambda x: x['date']):
            fixture_key = (fixture['homeTeam'], fixture['awayTeam'], fixture['date'])
            if fixture_key not in seen:
                seen.add(fixture_key)
                unique_fixtures.append(fixture)
        
        return jsonify({'fixtures': unique_fixtures[:5]})  # Return max 5 fixtures
        
    except Exception as e:
        print(f"Error fetching upcoming fixtures: {e}")
        return jsonify({'fixtures': [], 'error': str(e)})

@app.route('/api/last-update')
def get_last_update():
    """Get the last data update timestamp"""
    try:
        conn = demo.get_database_connection()
        c = conn.cursor()
        
        # Get the most recent update timestamp from team parameters
        c.execute("""
            SELECT MAX(last_updated) as last_update
            FROM competition_team_strength
            WHERE last_updated IS NOT NULL
        """)
        
        result = c.fetchone()
        conn.close()
        
        if result and result[0]:
            # Parse the datetime and format it nicely
            from datetime import datetime
            try:
                last_update = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                formatted_date = last_update.strftime('%B %d, %Y at %H:%M UTC')
                return jsonify({
                    'last_update': formatted_date,
                    'timestamp': result[0]
                })
            except:
                return jsonify({
                    'last_update': result[0],
                    'timestamp': result[0]
                })
        else:
            return jsonify({'last_update': 'Unknown', 'timestamp': None})
            
    except Exception as e:
        print(f"Error getting last update: {e}")
        return jsonify({'last_update': 'Unknown', 'timestamp': None})

@app.route('/api/team-form/<team_name>')
def get_team_form(team_name):
    """Get last 5 games form for a team"""
    try:
        conn = demo.get_database_connection()
        c = conn.cursor()
        
        # Get last 5 matches for this team from our stored data
        c.execute("""
            SELECT 
                home_team_name, away_team_name, home_score, away_score,
                match_date, competition_name
            FROM matches 
            WHERE (home_team_name = %s OR away_team_name = %s)
            AND status = 'FT'
            AND home_score IS NOT NULL 
            AND away_score IS NOT NULL
            ORDER BY match_date DESC
            LIMIT 5
        """, (team_name, team_name))
        
        matches = c.fetchall()
        conn.close()
        
        form_data = []
        for match in matches:
            home_team, away_team, home_score, away_score, match_date, competition = match
            
            # Determine if team was home or away and the result
            if home_team == team_name:
                team_score = home_score
                opponent_score = away_score
                opponent = away_team
                venue = 'H'
            else:
                team_score = away_score
                opponent_score = home_score
                opponent = home_team
                venue = 'A'
            
            # Determine result
            if team_score > opponent_score:
                result = 'W'
                result_class = 'win'
            elif team_score < opponent_score:
                result = 'L'
                result_class = 'loss'
            else:
                result = 'D'
                result_class = 'draw'
            
            # Format date
            try:
                from datetime import datetime
                formatted_date = datetime.fromisoformat(match_date).strftime('%b %d')
            except:
                formatted_date = match_date
            
            form_data.append({
                'result': result,
                'result_class': result_class,
                'opponent': opponent,
                'score': f"{team_score}-{opponent_score}",
                'venue': venue,
                'date': formatted_date,
                'competition': competition
            })
        
        # Create form string (most recent first)
        form_string = ''.join([match['result'] for match in form_data])
        
        return jsonify({
            'form_string': form_string,
            'matches': form_data,
            'team': team_name
        })
        
    except Exception as e:
        print(f"Error getting team form for {team_name}: {e}")
        return jsonify({
            'form_string': '',
            'matches': [],
            'team': team_name,
            'error': str(e)
        })

@app.route('/teams-ranking')
def teams_ranking():
    """Teams ranking page"""
    return render_template('teams_ranking.html')

@app.route('/api/teams-ranking')
def api_teams_ranking():
    """API endpoint to get all teams ranked by strength"""
    try:
        conn = demo.get_database_connection()
        c = conn.cursor()
        
        # Get all teams with their raw (non-normalized) parameter values
        c.execute("""
            SELECT 
                cts.team_name,
                c.name as league,
                COALESCE(cts.overall_strength, 
                    (COALESCE(cts.elo_score, 0) * 0.18 + 
                     COALESCE(cts.squad_value_score, 0) * 0.15 + 
                     COALESCE(cts.form_score, 0) * 0.05 + 
                     COALESCE(cts.squad_depth_score, 0) * 0.02 + 
                     COALESCE(cts.h2h_performance, 0) * 0.04 + 
                     COALESCE(cts.scoring_patterns, 0) * 0.03)) as calculated_strength,
                cts.elo_score,
                cts.squad_value_score,
                cts.form_score,
                cts.squad_depth_score,
                cts.h2h_performance,
                cts.scoring_patterns,
                cts.confederation
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'International')
            AND (cts.season = '2024' OR c.name = 'International')
            AND (cts.overall_strength IS NOT NULL OR c.name = 'International')
            ORDER BY calculated_strength DESC
        """)
        
        teams = []
        for row in c.fetchall():
            team_name, league, overall, elo, squad_value, form, squad_depth, h2h, scoring, confederation = row
            
            # Format squad value - for national teams, show raw score, for clubs show millions
            if league == 'International':
                squad_value_formatted = f"{round(squad_value, 2)}" if squad_value else "N/A"
            else:
                squad_value_formatted = f"€{squad_value:,.0f}M" if squad_value else "N/A"
            
            teams.append({
                'rank': len(teams) + 1,
                'name': team_name,
                'league': league,
                'confederation': confederation if league == 'International' else None,
                'overall_strength': round(overall, 2) if overall else 0,
                'elo_score': round(elo, 0) if elo else 0,
                'squad_value': squad_value_formatted,
                'form_score': round(form, 2) if form else 0,
                'squad_depth': round(squad_depth, 1) if squad_depth else 0,
                'h2h_performance': round(h2h, 2) if h2h else 0,
                'scoring_patterns': round(scoring, 2) if scoring else 0,
                'is_national': league == 'International'
            })
        
        conn.close()
        
        # Separate clubs and nations
        clubs = [t for t in teams if not t['is_national']]
        nations = [t for t in teams if t['is_national']]
        
        # Re-rank separately
        for i, club in enumerate(clubs):
            club['rank'] = i + 1
        for i, nation in enumerate(nations):
            nation['rank'] = i + 1
        
        return jsonify({
            'clubs': clubs,
            'nations': nations,
            'total': len(teams)
        })
        
    except Exception as e:
        print(f"Error getting teams ranking: {e}")
        return jsonify({'error': 'Failed to load teams ranking'})

if __name__ == '__main__':
    # Production configuration
    port = int(os.environ.get('PORT', 5001))
    debug = not os.environ.get('DATABASE_URL')  # Disable debug in production (when DATABASE_URL exists)
    
    if debug:
        # Development mode - check SQLite database
        if not os.path.exists(demo.db_path):
            print(f"❌ Database not found at: {demo.db_path}")
            print("Please ensure the database file exists before running the demo.")
            exit(1)
        print("🚀 Starting Football Strength Demo (Development)")
        print(f"🌐 Open your browser to: http://localhost:{port}")
    else:
        # Production mode
        print("🚀 Starting Football Strength Demo (Production)")
        print(f"🌐 Running on port: {port}")
        print(f"🗄️ Database: {db_config.get_db_type()}")
        
        # Check if migration should be run
        if os.environ.get('RUN_MIGRATION') == 'true':
            print("🔧 RUN_MIGRATION detected - Running confederation migration...")
            try:
                from railway_migration_confederation import add_confederations_to_postgresql
                add_confederations_to_postgresql()
                print("✅ Migration completed successfully!")
                print("🚨 IMPORTANT: Remove RUN_MIGRATION variable from Railway settings now!")
            except Exception as e:
                print(f"❌ Migration failed: {e}")
    
    print("🏟️ Select teams to see strength analysis!")
    
    app.run(debug=debug, host='0.0.0.0', port=port)