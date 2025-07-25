import sqlite3

# Updated weights based on current system (Team Strength = 40% total)
WEIGHTS = {
    "elo_score": 0.18,           # 18% - Overall team strength (match results)
    "squad_value_score": 0.15,   # 15% - Squad market value (objective quality measure)
    "form_score": 0.05,          # 5% - Recent form (last 5 matches)
    "squad_depth_score": 0.02    # 2% - Squad depth (basic measure)
}
# REMOVED: player_rating_score due to unreliable 2024 data

def normalize_parameter(value, param_name):
    """Normalize different parameters to 0-1 scale"""
    if param_name == "elo_score":
        # ELO range roughly 1200-2000
        return max(0, min(1, (value - 1200) / 800))
    elif param_name == "form_score":
        # Form is 0-3, normalize to 0-1
        return max(0, min(1, value / 3.0))
    elif param_name == "squad_depth_score":
        # Squad depth 3-7 range
        return max(0, min(1, (value - 3.0) / 4.0))
    elif param_name == "squad_value_score":
        # Squad value scores are already normalized 0-1 by the scraper
        return max(0, min(1, value))
    else:
        return max(0, min(1, value))

def calculate_team_scores():
    print("🏆 FOOTBALL TEAM STRENGTH CALCULATOR")
    print("=" * 50)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Get all teams
    c.execute("SELECT id, name FROM teams ORDER BY name")
    teams = c.fetchall()
    
    results = []
    
    for team_id, team_name in teams:
        # Get all parameters for this team
        c.execute("""
            SELECT parameter, value 
            FROM team_parameters 
            WHERE team_id = ?
        """, (team_id,))
        
        params = {row[0]: row[1] for row in c.fetchall()}
        
        # Calculate weighted score
        total_score = 0
        missing_params = []
        available_weight = 0
        
        print(f"\n🏟️ {team_name}:")
        for param_name, weight in WEIGHTS.items():
            if param_name in params and params[param_name] is not None:
                normalized = normalize_parameter(params[param_name], param_name)
                contribution = weight * normalized
                total_score += contribution
                available_weight += weight
                print(f"  {param_name:<20}: {params[param_name]:<8} → {normalized:.3f} (weight: {weight:.1%}) = {contribution:.4f}")
            else:
                missing_params.append(param_name)
                print(f"  {param_name:<20}: Missing")
        
        # Scale up score if parameters are missing
        if available_weight > 0:
            final_score = total_score * (sum(WEIGHTS.values()) / available_weight)
        else:
            final_score = 0
            
        results.append((team_name, final_score, missing_params))
    
    conn.close()
    
    # Display results
    print(f"\n📊 FINAL TEAM STRENGTH RANKINGS:")
    print("=" * 60)
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    for i, (team_name, score, missing) in enumerate(results, 1):
        status = "✅ Complete" if not missing else f"⚠️ Missing: {', '.join(missing)}"
        print(f"{i:2d}. {team_name:<25} {score:.3f} {status}")
    
    print(f"\n💡 Total possible score: {sum(WEIGHTS.values()):.3f}")
    print(f"📋 Current system covers 40% of comprehensive football strength model")
    
    return results

if __name__ == "__main__":
    calculate_team_scores()