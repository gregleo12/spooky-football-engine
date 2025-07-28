#!/usr/bin/env python3
"""
Fresh Football Analytics Web Application
Purpose-built for 10-parameter Railway PostgreSQL system
Clean architecture without legacy compatibility issues
"""
from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
import json
import os
from db_interface import db

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Test database connection on startup
if db.test_connection():
    print("✅ Database connection successful")
else:
    print("❌ Database connection failed - check Railway PostgreSQL")

@app.route('/')
def index():
    """Landing page with system overview"""
    stats = db.get_system_stats()
    return render_template('index.html', stats=stats, timestamp=datetime.now())

@app.route('/health')
def health_check():
    """System health check endpoint"""
    is_healthy = db.test_connection()
    stats = db.get_system_stats() if is_healthy else {}
    
    health_data = {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'database_connected': is_healthy,
        'timestamp': datetime.now().isoformat(),
        'stats': stats
    }
    
    status_code = 200 if is_healthy else 503
    return jsonify(health_data), status_code

@app.route('/api/teams')
def api_teams():
    """Get all teams organized by league"""
    teams_by_league = db.get_all_teams()
    
    # Flatten for all teams list
    all_teams = []
    for league, teams in teams_by_league.items():
        for team in teams:
            all_teams.append({
                'name': team['name'],
                'league': league,
                'elo_score': team['elo_score'],
                'squad_value': team['squad_value']
            })
    
    return jsonify({
        'teams_by_league': teams_by_league,
        'all_teams': all_teams,
        'total_teams': len(all_teams)
    })

@app.route('/api/team/<team_name>')
def api_team_detail(team_name):
    """Get complete data for a specific team"""
    team_data = db.get_team_data(team_name)
    
    if team_data:
        return jsonify(team_data)
    else:
        return jsonify({'error': f'Team {team_name} not found'}), 404

@app.route('/api/compare/<team1>/<team2>')
def api_compare_teams(team1, team2):
    """Compare two teams head-to-head"""
    comparison = db.compare_teams(team1, team2)
    
    if comparison:
        # Calculate win probabilities
        total_strength = comparison['team1_strength'] + comparison['team2_strength']
        if total_strength > 0:
            team1_prob = (comparison['team1_strength'] / total_strength) * 100
            team2_prob = (comparison['team2_strength'] / total_strength) * 100
        else:
            team1_prob = team2_prob = 50.0
        
        # Add home advantage for team1
        home_advantage = 5.0 if comparison['same_league'] else 3.0
        team1_prob = min(95.0, team1_prob + home_advantage)
        team2_prob = 100.0 - team1_prob
        
        comparison['team1_probability'] = round(team1_prob, 1)
        comparison['team2_probability'] = round(team2_prob, 1)
        comparison['favorite'] = team1 if team1_prob > team2_prob else team2
        
        return jsonify(comparison)
    else:
        return jsonify({'error': 'One or both teams not found'}), 404

@app.route('/api/odds/<team1>/<team2>')
def api_betting_odds(team1, team2):
    """Generate betting odds for a match"""
    comparison = db.compare_teams(team1, team2)
    
    if not comparison:
        return jsonify({'error': 'One or both teams not found'}), 404
    
    # Calculate base probabilities
    total_strength = comparison['team1_strength'] + comparison['team2_strength']
    if total_strength > 0:
        home_win_prob = (comparison['team1_strength'] / total_strength)
        away_win_prob = (comparison['team2_strength'] / total_strength)
    else:
        home_win_prob = away_win_prob = 0.45
    
    # Add home advantage
    home_advantage = 0.05 if comparison['same_league'] else 0.03
    home_win_prob = min(0.95, home_win_prob + home_advantage)
    
    # Calculate draw probability based on team similarity
    strength_diff = abs(comparison['team1_strength'] - comparison['team2_strength'])
    draw_prob = max(0.10, min(0.35, 0.25 - strength_diff * 0.1))
    
    # Normalize probabilities
    away_win_prob = 1 - home_win_prob - draw_prob
    
    # Convert to decimal odds with margin
    margin = 1.05  # 5% bookmaker margin
    odds = {
        'match_outcome': {
            'home_win': {
                'probability': round(home_win_prob * 100, 1),
                'odds': round(margin / home_win_prob, 2),
                'team': team1
            },
            'draw': {
                'probability': round(draw_prob * 100, 1),
                'odds': round(margin / draw_prob, 2)
            },
            'away_win': {
                'probability': round(away_win_prob * 100, 1),
                'odds': round(margin / away_win_prob, 2),
                'team': team2
            }
        },
        'goals_market': {
            'over_2_5': {
                'probability': 55.0,
                'odds': 1.91
            },
            'under_2_5': {
                'probability': 45.0,
                'odds': 2.10
            }
        },
        'btts': {
            'yes': {
                'probability': 52.0,
                'odds': 2.02
            },
            'no': {
                'probability': 48.0,
                'odds': 2.08
            }
        }
    }
    
    return jsonify(odds)

@app.route('/api/admin/stats')
def api_admin_stats():
    """Get comprehensive system statistics for admin dashboard"""
    stats = db.get_system_stats()
    
    # Get league breakdown
    teams_by_league = db.get_all_teams()
    league_counts = {league: len(teams) for league, teams in teams_by_league.items()}
    
    return jsonify({
        'system_stats': stats,
        'league_counts': league_counts,
        'last_updated': datetime.now().isoformat()
    })

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard with full system monitoring"""
    stats = db.get_system_stats()
    teams_by_league = db.get_all_teams()
    
    return render_template('admin.html', 
                         stats=stats, 
                         teams_by_league=teams_by_league,
                         timestamp=datetime.now())

@app.route('/compare')
def compare_page():
    """Team comparison interface"""
    teams_by_league = db.get_all_teams()
    return render_template('compare.html', teams_by_league=teams_by_league)

@app.route('/odds')
def odds_page():
    """Betting odds interface"""
    teams_by_league = db.get_all_teams()
    return render_template('odds.html', teams_by_league=teams_by_league)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Fresh Football Analytics App")
    print(f"📊 10-Parameter Railway PostgreSQL System")
    print(f"🌐 Starting on port {port}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)