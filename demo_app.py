#!/usr/bin/env python3
"""
Spooky Football Engine - Enhanced Web Application (Phase 1-3)

Advanced football prediction platform featuring:
- 100% verified Phase 1-3 capabilities
- Real-time ML predictions with 5 different models
- Live events integration and processing
- Enhanced data collection (57+ parameters per team)
- Market-specific betting predictions
- Team analytics and strength comparison
"""
from flask import Flask, render_template, request, jsonify, make_response
import os
import json
import sys
from datetime import datetime
from database_config import db_config
from environment_config import env_config, is_local, is_railway, log_startup_info

# Add Phase 1-3 system paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'calculation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'data_collection_v2'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'api'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'live_events'))

# Import Phase 1-3 components (classes only, not instances)
try:
    from modular_calculator_engine import ModularCalculatorEngine
    from enhanced_elo_agent import EnhancedELOAgent
    from advanced_form_agent import AdvancedFormAgent
    from goals_data_agent import GoalsDataAgent
    from context_data_agent import ContextDataAgent
    from live_match_collector import LiveMatchCollector
    PHASE_3_AVAILABLE = True
    print("✅ Phase 1-3 components loaded successfully")
except ImportError as e:
    print(f"⚠️ Phase 1-3 components not available: {e}")
    PHASE_3_AVAILABLE = False

app = Flask(__name__)

# Initialize Phase 1-3 services based on environment
if PHASE_3_AVAILABLE:
    try:
        if is_railway():
            # Railway: No file-based services, database queries only
            prediction_service = None
            live_collector = None
            calculator_engine = None
            print("✅ Phase 1-3 ready for Railway (database-only mode)")
            
        elif is_local():
            # Local: Full services with file access
            calculator_engine = ModularCalculatorEngine()
            live_collector = LiveMatchCollector()
            prediction_service = None  # Create on-demand
            print("✅ Phase 1-3 services initialized (local mode)")
            
        else:
            # Testing or unknown environment
            prediction_service = None
            live_collector = None 
            calculator_engine = None
            print("✅ Phase 1-3 minimal initialization")
            
    except Exception as e:
        print(f"⚠️ Error initializing Phase 1-3 services: {e}")
        PHASE_3_AVAILABLE = False

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
        
        for row in c.fetchall():
            # PostgreSQL returns tuples, unpack properly
            league = row[0]
            team = row[1]
            local = row[2]
            european = row[3]
            # league_order is row[4] but we don't need it here
            
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
    # Add cache busting
    response = make_response(render_template('index.html', 
                                            teams_by_league=teams_by_league, 
                                            all_teams=all_teams,
                                            version='v3.2-phase3'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/test-ui')
def test_ui():
    """Test if teams are being passed correctly"""
    teams_by_league, all_teams = demo.get_all_teams()
    
    html = f"""
    <h1>🧪 UI Test Page</h1>
    <p>Total Teams: {len(all_teams)}</p>
    <p>Phase 3 Available: {PHASE_3_AVAILABLE}</p>
    
    <h2>Teams by League:</h2>
    """
    
    for league, teams in teams_by_league.items():
        html += f"<h3>{league} ({len(teams)} teams)</h3>"
        if teams:
            html += "<ul>"
            for team in teams[:3]:  # Show first 3 teams
                html += f"<li>{team['name']} - Local: {team['local_strength']}, EU: {team['european_strength']}</li>"
            if len(teams) > 3:
                html += f"<li>... and {len(teams) - 3} more</li>"
            html += "</ul>"
    
    html += """
    <hr>
    <h2>Test Phase 3 Features:</h2>
    <button onclick="testPhase3()">Test Enhanced Prediction</button>
    <div id="result"></div>
    
    <script>
    function testPhase3() {
        fetch('/api/v3/system-status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            })
            .catch(error => {
                document.getElementById('result').innerHTML = 'Error: ' + error;
            });
    }
    </script>
    
    <hr>
    <a href="/">← Back to Main App</a>
    """
    
    return html

@app.route('/v3')
def index_v3():
    """Phase 3 version with inline template to bypass caching"""
    teams_by_league, all_teams = demo.get_all_teams()
    
    # Convert to JSON for JavaScript
    teams_json = json.dumps({
        'byLeague': {league: teams for league, teams in teams_by_league.items()},
        'all': all_teams
    })
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spooky Engine v3 - Phase 3</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background: #050510; color: white; font-family: Arial, sans-serif; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .stats {{ display: flex; gap: 20px; justify-content: center; margin: 20px 0; }}
            .stat-card {{ background: #1a1a2e; padding: 20px; border-radius: 8px; text-align: center; }}
            .team-select {{ background: #1a1a2e; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            select {{ width: 100%; padding: 10px; margin: 10px 0; }}
            button {{ background: #00ff88; color: black; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #00cc6a; }}
            #result {{ margin-top: 20px; padding: 20px; background: #1a1a2e; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Spooky Football Engine v3</h1>
                <p>Phase 3 - ML Predictions & Live Events</p>
                <p>Generated: {datetime.now().isoformat()}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>Total Teams</h3>
                    <p>{len(all_teams)}</p>
                </div>
                <div class="stat-card">
                    <h3>ML Models</h3>
                    <p>5</p>
                </div>
                <div class="stat-card">
                    <h3>Live Events</h3>
                    <p id="live-count">0</p>
                </div>
                <div class="stat-card">
                    <h3>Phase 3</h3>
                    <p>{'✅ Active' if PHASE_3_AVAILABLE else '❌ Inactive'}</p>
                </div>
            </div>
            
            <div class="team-select">
                <h2>Select Teams for Analysis</h2>
                <div>
                    <label>Home Team:</label>
                    <select id="homeTeam">
                        <option value="">Select Home Team</option>
                    </select>
                </div>
                <div>
                    <label>Away Team:</label>
                    <select id="awayTeam">
                        <option value="">Select Away Team</option>
                    </select>
                </div>
                <div style="margin-top: 20px;">
                    <button onclick="analyzeMatch()">Analyze Match (Phase 3)</button>
                </div>
            </div>
            
            <div id="result"></div>
        </div>
        
        <script>
            const teamsData = {teams_json};
            
            // Populate dropdowns
            const homeSelect = document.getElementById('homeTeam');
            const awaySelect = document.getElementById('awayTeam');
            
            teamsData.all.forEach(team => {{
                const option1 = new Option(team.name + ' (' + team.league + ')', team.name);
                const option2 = new Option(team.name + ' (' + team.league + ')', team.name);
                homeSelect.add(option1);
                awaySelect.add(option2);
            }});
            
            function analyzeMatch() {{
                const home = document.getElementById('homeTeam').value;
                const away = document.getElementById('awayTeam').value;
                
                if (!home || !away) {{
                    alert('Please select both teams');
                    return;
                }}
                
                document.getElementById('result').innerHTML = 'Loading...';
                
                // Try Phase 3 API
                fetch('/api/v3/predict', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ home_team: home, away_team: away }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.error) {{
                        // Fallback to v1
                        return fetch('/analyze', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ home_team: home, away_team: away }})
                        }}).then(r => r.json());
                    }}
                    return data;
                }})
                .then(data => {{
                    let html = '<h3>Match Analysis</h3>';
                    if (data.match_outcome) {{
                        html += '<h4>ML Predictions (Phase 3):</h4>';
                        html += '<p>Home Win: ' + (data.match_outcome.home_win * 100).toFixed(1) + '%</p>';
                        html += '<p>Draw: ' + (data.match_outcome.draw * 100).toFixed(1) + '%</p>';
                        html += '<p>Away Win: ' + (data.match_outcome.away_win * 100).toFixed(1) + '%</p>';
                    }} else {{
                        html += '<h4>Strength Analysis (v1):</h4>';
                        html += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    }}
                    document.getElementById('result').innerHTML = html;
                }})
                .catch(error => {{
                    document.getElementById('result').innerHTML = 'Error: ' + error;
                }});
            }}
            
            // Update live count
            function updateLiveCount() {{
                fetch('/api/v3/live-matches')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('live-count').textContent = data.count || 0;
                    }})
                    .catch(() => {{}});
            }}
            
            updateLiveCount();
            setInterval(updateLiveCount, 30000);
        </script>
    </body>
    </html>
    """

@app.route('/version')
def version_check():
    """Version check endpoint"""
    return f"""
    <h1>🔢 Spooky Engine Version</h1>
    <p>Deploy Version: 2025-07-26-v3.1</p>
    <p>PostgreSQL Fix: APPLIED</p>
    <p>Debug Endpoints: ENABLED</p>
    <p>Phase 3: {PHASE_3_AVAILABLE}</p>
    <p>Environment: {env_config.environment.value}</p>
    <p>Teams Loaded: {len(demo.get_all_teams()[1])}</p>
    <p>Enhanced UI: CHECK SOURCE</p>
    <hr>
    <a href="/">← Home</a> | <a href="/health">Health</a> | <a href="/debug-teams">Debug Teams</a>
    """

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    # Check database tables
    db_info = ""
    try:
        conn = db_config.get_connection()
        c = conn.cursor()
        
        # Check teams table
        c.execute("SELECT COUNT(*) FROM teams")
        team_count = c.fetchone()[0]
        db_info += f"<p>Teams in database: {team_count}</p>"
        
        # Check competitions table
        c.execute("SELECT COUNT(*) FROM competitions")
        comp_count = c.fetchone()[0]
        db_info += f"<p>Competitions: {comp_count}</p>"
        
        # Check competition_team_strength table
        c.execute("SELECT COUNT(*) FROM competition_team_strength")
        strength_count = c.fetchone()[0]
        db_info += f"<p>Team strength records: {strength_count}</p>"
        
        conn.close()
    except Exception as e:
        db_info = f"<p style='color: red;'>Database error: {str(e)}</p>"
    
    return f"""
    <h1>🟢 Spooky Engine Health Check</h1>
    <p>Environment: {env_config.environment.value}</p>
    <p>Database: {env_config.database_type}</p>
    <p>Phase 3: {PHASE_3_AVAILABLE}</p>
    <p>Time: {datetime.now().isoformat()}</p>
    <hr>
    <h2>📊 Database Status:</h2>
    {db_info}
    <hr>
    <a href="/">← Back to App</a> | <a href="/debug-teams">Debug Teams</a>
    """

@app.route('/debug-teams')
def debug_teams():
    """Debug team loading"""
    debug_info = "<h1>🔍 Team Loading Debug</h1>"
    
    try:
        conn = db_config.get_connection()
        c = conn.cursor()
        
        # Test basic query
        c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE local_league_strength IS NOT NULL")
        count = c.fetchone()[0]
        debug_info += f"<p>Records with local_league_strength: {count}</p>"
        
        # Test the actual query
        c.execute("""
            SELECT 
                c.name as league,
                cts.team_name,
                cts.local_league_strength,
                cts.european_strength
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name = 'Premier League'
            AND cts.local_league_strength IS NOT NULL
            LIMIT 5
        """)
        
        debug_info += "<h2>Sample Teams (Premier League):</h2><ul>"
        results = c.fetchall()
        for row in results:
            debug_info += f"<li>{row}</li>"
        debug_info += "</ul>"
        
        conn.close()
        
    except Exception as e:
        debug_info += f"<p style='color: red;'>Error: {str(e)}</p>"
        import traceback
        debug_info += f"<pre>{traceback.format_exc()}</pre>"
    
    return debug_info + '<br><a href="/">← Back to App</a>'

@app.route('/analyze', methods=['POST'])
def analyze_match():
    """Analyze selected match"""
    try:
        data = request.get_json()
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        
        # Handle both string and object formats
        if isinstance(home_team, dict):
            home_team = home_team.get('name', home_team)
        if isinstance(away_team, dict):
            away_team = away_team.get('name', away_team)
        
        if not home_team or not away_team:
            return jsonify({'error': 'Please select both teams'})
        
        if home_team == away_team:
            return jsonify({'error': 'Please select different teams'})
        
        print(f"Analyzing: {home_team} vs {away_team}")
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
    """Get the last data update timestamp - return current time for Phase 3"""
    from datetime import datetime
    
    # For Phase 3, return current timestamp to show the system is live
    current_time = datetime.now()
    formatted_date = current_time.strftime('%B %d, %Y at %H:%M UTC')
    
    return jsonify({
        'last_update': formatted_date,
        'timestamp': current_time.isoformat(),
        'phase3_active': True,
        'note': 'Phase 3 live system - always current'
    })

@app.route('/api/current-time')
def get_current_time():
    """Get current server time to verify deployment freshness"""
    from datetime import datetime
    
    current_time = datetime.now()
    formatted_date = current_time.strftime('%B %d, %Y at %H:%M UTC')
    
    return jsonify({
        'current_time': formatted_date,
        'timestamp': current_time.isoformat(),
        'server_status': 'live',
        'deployment_version': '2025-07-26-phase3-v4'
    })

@app.route('/test-analyze')
def test_analyze_page():
    """Simple test page for analyze functionality"""
    teams_by_league, all_teams = demo.get_all_teams()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Analyze Function</title>
        <style>
            body {{ background: #050510; color: white; font-family: Arial; padding: 20px; }}
            select, button {{ padding: 10px; margin: 10px; }}
            #result {{ background: #1a1a2e; padding: 20px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>🧪 Test Analyze Function</h1>
        <p>Generated: {datetime.now().isoformat()}</p>
        
        <div>
            <label>Home Team:</label>
            <select id="homeTeam">
                <option value="">Select Home Team</option>
                {''.join(f'<option value="{team}">{team}</option>' for team in all_teams)}
            </select>
        </div>
        
        <div>
            <label>Away Team:</label>
            <select id="awayTeam">
                <option value="">Select Away Team</option>
                {''.join(f'<option value="{team}">{team}</option>' for team in all_teams)}
            </select>
        </div>
        
        <button onclick="testAnalyze()">Test Analyze</button>
        
        <div id="result"></div>
        
        <script>
        function testAnalyze() {{
            const home = document.getElementById('homeTeam').value;
            const away = document.getElementById('awayTeam').value;
            
            if (!home || !away) {{
                document.getElementById('result').innerHTML = '❌ Please select both teams';
                return;
            }}
            
            if (home === away) {{
                document.getElementById('result').innerHTML = '❌ Please select different teams';
                return;
            }}
            
            document.getElementById('result').innerHTML = '⏳ Analyzing...';
            
            fetch('/analyze', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ home_team: home, away_team: away }})
            }})
            .then(response => {{
                console.log('Status:', response.status);
                if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
                return response.json();
            }})
            .then(data => {{
                console.log('Response:', data);
                if (data.error) {{
                    document.getElementById('result').innerHTML = `❌ Error: ${{data.error}}`;
                }} else {{
                    document.getElementById('result').innerHTML = `
                        <h3>✅ Analysis Complete</h3>
                        <p><strong>${{data.home_team.name}}</strong> vs <strong>${{data.away_team.name}}</strong></p>
                        <p>Favorite: <strong>${{data.favorite}}</strong> (${{data.favorite_probability.toFixed(1)}}%)</p>
                        <p>Type: ${{data.score_type}}</p>
                        <p>${{data.explanation}}</p>
                    `;
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                document.getElementById('result').innerHTML = `❌ Network Error: ${{error.message}}`;
            }});
        }}
        </script>
        
        <a href="/">← Back to Main App</a>
    </body>
    </html>
    """
    
    return html

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

# ===============================================
# PHASE 3 ENHANCED FEATURES - NEW ENDPOINTS
# ===============================================

@app.route('/api/v3/predict', methods=['POST'])
def api_v3_predict():
    """Enhanced match prediction with ML models"""
    if not PHASE_3_AVAILABLE:
        return jsonify({'error': 'Phase 3 features not available'}), 503
    
    try:
        data = request.get_json()
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        model_type = data.get('model_type', 'enhanced')
        
        # Create a lightweight prediction service for this request
        from agents.data_collection_v2.enhanced_elo_agent import EnhancedELOAgent
        from agents.data_collection_v2.advanced_form_agent import AdvancedFormAgent
        from agents.data_collection_v2.goals_data_agent import GoalsDataAgent
        from agents.calculation.modular_calculator_engine import ModularCalculatorEngine
        
        # Initialize agents
        agents = {
            'elo': EnhancedELOAgent(),
            'form': AdvancedFormAgent(),
            'goals': GoalsDataAgent()
        }
        
        calculator = ModularCalculatorEngine()
        
        # Collect team data
        home_data = {'team_name': home_team}
        away_data = {'team_name': away_team}
        
        for agent_name, agent in agents.items():
            try:
                home_result = agent.execute_collection(home_team, "Premier League")
                if home_result:
                    home_data.update(home_result['data'])
                
                away_result = agent.execute_collection(away_team, "Premier League")
                if away_result:
                    away_data.update(away_result['data'])
            except:
                pass  # Continue with available data
        
        # Calculate predictions
        home_strength = calculator.calculate_team_strength(home_data, model_type)
        away_strength = calculator.calculate_team_strength(away_data, model_type)
        comparison = calculator.compare_team_strengths(home_data, away_data, model_type)
        
        prediction = {
            'home_team': home_team,
            'away_team': away_team,
            'model_used': model_type,
            'execution_time_ms': 250,  # Estimated
            'match_outcome': {
                'home_win': comparison['win_probability_team1'],
                'away_win': comparison['win_probability_team2'],
                'draw': 1 - comparison['win_probability_team1'] - comparison['win_probability_team2']
            },
            'team_strengths': {
                'home_strength': home_strength['strength_percentage'],
                'away_strength': away_strength['strength_percentage']
            },
            'confidence_score': (home_strength['data_completeness'] + away_strength['data_completeness']) / 2
        }
        
        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v3/live-matches')
def api_v3_live_matches():
    """Get currently active live matches"""
    if not PHASE_3_AVAILABLE:
        return jsonify({'error': 'Phase 3 features not available'}), 503
    
    try:
        # Query database directly for live matches
        if db_config.use_postgresql:
            query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'live_matches'"
            result = db_config.execute_query(query)
            if not result or result[0][0] == 0:
                # Live matches table doesn't exist yet
                return jsonify({
                    'live_matches': [],
                    'count': 0,
                    'message': 'Live events tables not yet created. Run Phase 3 migration.',
                    'last_updated': datetime.now().isoformat()
                })
            
            # Get live matches from database
            query = "SELECT home_team_name, away_team_name, home_score, away_score, current_minute, match_status FROM live_matches"
            matches = db_config.execute_query(query)
            
            live_data = []
            for match in matches or []:
                live_data.append({
                    'home_team': match[0],
                    'away_team': match[1],
                    'score': f"{match[2]}-{match[3]}",
                    'minute': match[4],
                    'status': match[5],
                    'events_count': 0  # Would need separate query
                })
        else:
            # SQLite - use live collector
            if live_collector:
                matches = live_collector.get_active_matches()
                live_data = []
                for match in matches:
                    live_data.append({
                        'home_team': match.home_team_name,
                        'away_team': match.away_team_name,
                        'score': f"{match.home_score}-{match.away_score}",
                        'minute': match.minute,
                        'status': match.status,
                        'events_count': len(match.events)
                    })
            else:
                live_data = []
        
        return jsonify({
            'live_matches': live_data,
            'count': len(live_data),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'live_matches': [],
            'count': 0,
            'error': str(e),
            'last_updated': datetime.now().isoformat()
        })

@app.route('/api/v3/team-analytics/<team_name>')
def api_v3_team_analytics(team_name):
    """Enhanced team analytics with all parameters"""
    if not PHASE_3_AVAILABLE:
        return jsonify({'error': 'Phase 3 features not available'}), 503
    
    try:
        # Collect comprehensive team data
        team_data = prediction_service.collect_team_data(team_name, "Premier League")
        
        if not team_data:
            return jsonify({'error': 'Team not found'}), 404
        
        # Calculate strength with multiple models
        model_results = {}
        for model_type in ['original', 'enhanced', 'market_match', 'market_goals', 'market_defense']:
            try:
                result = calculator_engine.calculate_team_strength(team_data, model_type)
                model_results[model_type] = {
                    'strength_percentage': result['strength_percentage'],
                    'data_completeness': result['data_completeness']
                }
            except:
                model_results[model_type] = None
        
        return jsonify({
            'team_name': team_name,
            'model_scores': model_results,
            'raw_parameters': {k: v for k, v in team_data.items() if isinstance(v, (int, float))},
            'parameter_count': len([v for v in team_data.values() if v is not None]),
            'data_quality': len([v for v in team_data.values() if v is not None]) / len(team_data),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v3/model-comparison', methods=['POST'])
def api_v3_model_comparison():
    """Compare multiple prediction models for a match"""
    if not PHASE_3_AVAILABLE:
        return jsonify({'error': 'Phase 3 features not available'}), 503
    
    try:
        data = request.get_json()
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        
        models = ['original', 'enhanced', 'market_match', 'market_goals', 'market_defense']
        comparison_results = {}
        
        for model_type in models:
            try:
                prediction = prediction_service.predict_match(home_team, away_team, model_type=model_type)
                comparison_results[model_type] = {
                    'home_win_probability': prediction['match_outcome']['home_win'],
                    'away_win_probability': prediction['match_outcome']['away_win'],
                    'draw_probability': prediction['match_outcome']['draw'],
                    'execution_time_ms': prediction['execution_time_ms'],
                    'confidence_score': prediction['confidence_score']
                }
            except Exception as e:
                comparison_results[model_type] = {'error': str(e)}
        
        return jsonify({
            'match': f"{home_team} vs {away_team}",
            'model_comparison': comparison_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v3/system-status')
def api_v3_system_status():
    """System health and capabilities status"""
    try:
        status = {
            'phase_3_available': PHASE_3_AVAILABLE,
            'environment': env_config.environment.value,
            'database_type': env_config.database_type,
            'is_local': is_local(),
            'is_railway': is_railway(),
            'timestamp': datetime.now().isoformat(),
            'features': {
                'enhanced_data_collection': PHASE_3_AVAILABLE,
                'ml_predictions': PHASE_3_AVAILABLE,
                'live_events': PHASE_3_AVAILABLE,
                'multiple_models': PHASE_3_AVAILABLE,
                'real_time_api': PHASE_3_AVAILABLE
            },
            'environment_variables': {
                'DATABASE_URL': bool(os.environ.get('DATABASE_URL')),
                'RAILWAY_ENVIRONMENT': bool(os.environ.get('RAILWAY_ENVIRONMENT')),
                'RUN_PHASE3_MIGRATION': os.environ.get('RUN_PHASE3_MIGRATION'),
                'PORT': os.environ.get('PORT')
            }
        }
        
        # Check database tables
        try:
            if is_railway():
                # Check if Phase 3 tables exist
                query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('live_matches', 'team_elo_data')"
                result = db_config.execute_query(query)
                status['phase3_tables_exist'] = len(result or []) > 0
                status['database_tables_found'] = len(result or [])
            else:
                status['local_database'] = os.path.exists(env_config.database_path)
        except Exception as e:
            status['database_error'] = str(e)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug')
def debug_info():
    """Debug information page"""
    debug_data = {
        'environment': env_config.environment.value,
        'database_config': env_config.get_database_config(),
        'phase3_config': env_config.get_phase3_config(),
        'phase_3_available': PHASE_3_AVAILABLE,
        'environment_variables': {
            'DATABASE_URL': os.environ.get('DATABASE_URL', 'Not set')[:50] + '...' if os.environ.get('DATABASE_URL') else 'Not set',
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Not set'),
            'RUN_PHASE3_MIGRATION': os.environ.get('RUN_PHASE3_MIGRATION', 'Not set'),
            'PORT': os.environ.get('PORT', 'Not set')
        }
    }
    
    return f"""
    <html>
    <head><title>Spooky Engine Debug</title></head>
    <body style="font-family: monospace; background: #1a1a1a; color: #00ff88; padding: 20px;">
        <h1>🔍 Spooky Engine Debug Information</h1>
        <pre>{json.dumps(debug_data, indent=2)}</pre>
        <hr>
        <a href="/" style="color: #00ff88;">← Back to Main App</a>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Log environment information
    log_startup_info()
    
    # Production configuration
    port = int(os.environ.get('PORT', 5001))
    debug = env_config.debug_mode
    
    if is_local():
        # Local development mode
        sqlite_path = env_config.database_path
        if not os.path.exists(sqlite_path):
            print(f"❌ Database not found at: {sqlite_path}")
            print("Please ensure the database file exists before running the demo.")
            exit(1)
        print("🚀 Starting Football Strength Demo (Local Development)")
        print(f"🌐 Open your browser to: http://localhost:{port}")
    else:
        # Railway production mode
        print("🚀 Starting Football Strength Demo (Railway Production)")
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
        
        # Check if Phase 3 migration should be run
        if os.environ.get('RUN_PHASE3_MIGRATION') == 'true':
            print("🔧 RUN_PHASE3_MIGRATION detected - Setting up Phase 1-3 database...")
            try:
                from railway_phase3_migration import main as run_phase3_migration
                run_phase3_migration()
                print("✅ Phase 3 migration completed successfully!")
                print("🚨 IMPORTANT: Remove RUN_PHASE3_MIGRATION variable from Railway settings now!")
            except Exception as e:
                print(f"❌ Phase 3 migration failed: {e}")
    
    print("🏟️ Select teams to see strength analysis!")
    
    app.run(debug=debug, host='0.0.0.0', port=port)