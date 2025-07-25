import sqlite3

# Updated weights based on your blueprint (Team Strength = 40% total)
# These 4 parameters represent your current "Team Strength" category
WEIGHTS = {
    "elo_score": 0.18,           # 18% - Overall team strength (match results) - increased
    "squad_value_score": 0.15,   # 15% - Squad market value (objective quality measure) - increased
    "form_score": 0.05,          # 5% - Recent form (last 5 matches) - reduced but kept
    "squad_depth_score": 0.02    # 2% - Squad depth (basic measure)
}
# Total: 40% (Team Strength category from blueprint)
# REMOVED: player_rating_score due to unreliable 2024 data

def normalize_parameter(value, param_name):
    """Normalize different parameters to 0-1 scale"""
    
    if param_name == "elo_score":
        # Your elo scores are roughly 1200-2000 range
        return max(0, min(1, (value - 1200) / 800))
    
    elif param_name == "form_score":
        # Form scores are already 0-3 range, normalize to 0-1
        return max(0, min(1, value / 3.0))
    
    elif param_name == "squad_depth_score":
        # Squad depth scores roughly 3-7 range, normalize to 0-1  
        return max(0, min(1, (value - 3.0) / 4.0))
    
    elif param_name == "squad_value_score":
        # Squad value scores are already normalized 0-1 by the scraper
        return max(0, min(1, value))
    
    else:
        # Default: assume already normalized
        return max(0, min(1, value))

def fetch_team_strength_scores():
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")

    # Get all teams
    c.execute("SELECT id, name FROM teams")
    teams = c.fetchall()

    results = []

    for team_id, team_name in teams:
        # Fetch all parameters for this team
        c.execute("""
            SELECT parameter, value
            FROM team_parameters
            WHERE team_id = ?
        """, (team_id,))
        params = {row[0]: row[1] for row in c.fetchall()}

        # Calculate weighted strength score
        total_score = 0
        missing_params = []
        available_weight = 0

        for param_name, weight in WEIGHTS.items():
            if param_name in params and params[param_name] is not None:
                # Normalize the parameter value
                normalized_value = normalize_parameter(params[param_name], param_name)
                total_score += weight * normalized_value
                available_weight += weight
            else:
                missing_params.append(param_name)

        if available_weight > 0:
            # Scale up the score to account for missing parameters
            final_score = total_score * (sum(WEIGHTS.values()) / available_weight)
            
            # Display result
            if missing_params:
                results.append((team_name, round(final_score, 3), f"⚠️ Missing: {', '.join(missing_params)}"))
            else:
                results.append((team_name, round(final_score, 3), "✅ Complete"))
        else:
            results.append((team_name, "❌ No data", "Missing all parameters"))

    conn.close()
    return results

def display_detailed_breakdown():
    """Show detailed parameter breakdown for debugging"""
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")

    # Get all teams and their parameters
    c.execute("SELECT id, name FROM teams")
    teams = c.fetchall()

    print("\n🔍 DETAILED PARAMETER BREAKDOWN:\n")
    
    for team_id, team_name in teams:
        c.execute("""
            SELECT parameter, value
            FROM team_parameters
            WHERE team_id = ?
        """, (team_id,))
        params = {row[0]: row[1] for row in c.fetchall()}
        
        print(f"🏟️ {team_name}:")
        for param_name, weight in WEIGHTS.items():
            value = params.get(param_name, "Missing")
            if value != "Missing":
                normalized = normalize_parameter(value, param_name)
                contribution = weight * normalized
                print(f"   {param_name:<20}: {value:<8} -> {normalized:.3f} (weight: {weight:.1%}) = {contribution:.4f}")
            else:
                print(f"   {param_name:<20}: {value}")
        print()
    
    conn.close()

if __name__ == "__main__":
    results = fetch_team_strength_scores()
    
    # Sort by strength score (descending)
    valid_results = [(name, score, status) for name, score, status in results if isinstance(score, (int, float))]
    valid_results.sort(key=lambda x: x[1], reverse=True)
    
    print("\n⚽ PREMIER LEAGUE TEAM STRENGTH RANKINGS")
    print("="*60)
    
    for i, (team_name, score, status) in enumerate(valid_results, 1):
        print(f"{i:2d}. {team_name:<25} {score:.3f} {status}")
    
    # Show teams with missing data
    missing_data = [(name, score, status) for name, score, status in results if not isinstance(score, (int, float))]
    if missing_data:
        print(f"\n⚠️ Teams with missing data:")
        for team_name, score, status in missing_data:
            print(f"    {team_name:<25} {score} - {status}")
    
    print(f"\n💡 Showing detailed breakdown...")
    display_detailed_breakdown()