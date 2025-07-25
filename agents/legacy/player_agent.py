import sqlite3
import requests
import json
from datetime import datetime, timezone

# === Configuration ===
API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}
LEAGUE_ID = 39
SEASON = 2024

# Fallback average to use if no data is found (realistic player rating)
FALLBACK_AVERAGE = 7.0

# === Load Team API IDs ===
with open("agents/team_api_ids.json") as f:
    team_api_ids = json.load(f)

# === Fetch player rating score from API ===
def fetch_player_rating_score(api_team_id, team_name):
    """Fetch average player rating score for a team with improved error handling and season fallback"""
    
    # Try 2024 season first, then fall back to 2023 if no ratings found
    seasons_to_try = [2024, 2023]
    
    for season in seasons_to_try:
        params = {
            "team": api_team_id,
            "season": season,
            "page": 1
        }
        # Note: Omitting league parameter - including it causes ratings to return as None

        try:
            season_label = "current" if season == 2024 else "previous"
            print(f"🔍 Fetching player ratings for {team_name} (ID: {api_team_id}, {season_label} season)")
            response = requests.get(f"{BASE_URL}/players", headers=HEADERS, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ API returned status code {response.status_code} for {season} season")
                continue
            
            data = response.json()

            if "response" not in data or not data["response"]:
                print(f"   ❌ No player data returned for {season} season")
                continue

            print(f"   📊 Found {len(data['response'])} players in {season} season")
            
            ratings = []
            valid_players = 0
            
            for entry in data["response"]:
                player_name = entry.get("player", {}).get("name", "Unknown")
                stats = entry.get("statistics", [{}])[0] if entry.get("statistics") else {}
                
                # Try multiple paths for rating data
                rating = None
                minutes = 0
                
                # Check different possible rating locations
                if stats.get("games"):
                    rating = stats["games"].get("rating")
                    minutes = stats["games"].get("minutes", 0)
                
                # Fallback to direct rating field
                if not rating and "rating" in stats:
                    rating = stats.get("rating")
                
                # Additional fallback paths for rating
                if not rating:
                    # Try looking for rating in other possible locations
                    for key in ["rating", "average_rating", "overall_rating"]:
                        if key in stats and stats[key]:
                            rating = stats[key]
                            break
                
                # Validate rating and minutes - be more lenient
                if rating:
                    try:
                        rating_float = float(rating)
                        # More lenient validation: accept rating if valid float and reasonable range
                        if 1.0 <= rating_float <= 10.0:
                            # Accept players with any minutes > 0, or if minutes data is missing
                            if minutes > 0 or minutes == 0:  # Accept even if minutes is 0 or missing
                                ratings.append(rating_float)
                                valid_players += 1
                            else:
                                print(f"   ⚠️ Skipping {player_name}: negative minutes ({minutes})")
                        else:
                            print(f"   ⚠️ Skipping {player_name}: rating {rating_float} out of range (1.0-10.0)")
                    except (ValueError, TypeError):
                        print(f"   ⚠️ Skipping {player_name}: invalid rating format '{rating}'")

            # If we found ratings, use them
            if ratings:
                if valid_players < 3:  # Lower threshold - at least 3 players needed
                    print(f"   ⚠️ Warning: Very few players ({valid_players}) with valid ratings in {season}")
                elif valid_players < 8:  # Warn if still low but acceptable
                    print(f"   ⚠️ Warning: Limited player data ({valid_players} players) in {season} - consider data quality")
                
                average_rating = sum(ratings) / len(ratings)
                season_note = f" (from {season} season)" if season != 2024 else ""
                print(f"   📈 Average rating: {average_rating:.2f} from {valid_players} players{season_note}")
                
                return round(average_rating, 2)
            else:
                print(f"   ❌ No valid player ratings found in {season} season")
                continue
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error for {season} season: {e}")
            continue
        except Exception as e:
            print(f"   ❌ Error processing {season} season data: {e}")
            continue
    
    # If we get here, no season worked
    raise ValueError("No valid player ratings found in any season")

# === Update player rating scores in DB ===
def update_player_ratings():
    """Update player rating scores for all teams"""
    print("👥 Starting player rating score updates...")
    print(f"📅 Using season: {SEASON}")
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # Get all teams
    c.execute("SELECT name FROM teams ORDER BY name")
    teams = [row[0] for row in c.fetchall()]
    
    successful_updates = 0
    failed_updates = []

    for i, team in enumerate(teams, 1):
        print(f"\n[{i}/{len(teams)}] Processing {team}...")
        
        api_id = team_api_ids.get(team)
        if not api_id:
            print(f"❌ No API ID found for team: {team}")
            failed_updates.append((team, "No API ID"))
            continue

        try:
            score = fetch_player_rating_score(api_id, team)
            
            # Get team ID from database
            c.execute("SELECT id FROM teams WHERE name = ?", (team,))
            result = c.fetchone()
            if not result:
                raise ValueError(f"Team {team} not found in database")
            
            team_id = result[0]

            # Insert or update score
            c.execute("""
                INSERT INTO team_parameters (team_id, parameter, value, last_updated)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(team_id, parameter) DO UPDATE SET
                    value = excluded.value,
                    last_updated = excluded.last_updated
            """, (team_id, "player_rating_score", score, datetime.now(timezone.utc)))
            
            print(f"✅ {team}: {score}")
            successful_updates += 1

        except Exception as e:
            print(f"❌ Failed for {team}: {e}")
            print(f"↪️ Using fallback average: {FALLBACK_AVERAGE}")
            failed_updates.append((team, str(e)))
            
            # Still insert fallback value
            try:
                c.execute("SELECT id FROM teams WHERE name = ?", (team,))
                result = c.fetchone()
                if result:
                    team_id = result[0]
                    c.execute("""
                        INSERT INTO team_parameters (team_id, parameter, value, last_updated)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(team_id, parameter) DO UPDATE SET
                            value = excluded.value,
                            last_updated = excluded.last_updated
                    """, (team_id, "player_rating_score", FALLBACK_AVERAGE, datetime.now(timezone.utc)))
                    successful_updates += 1
            except Exception as fallback_error:
                print(f"❌ Even fallback failed: {fallback_error}")
            
        # Rate limiting protection
        if i % 5 == 0:  # Brief pause every 5 requests
            print("   ⏳ Brief pause to respect API limits...")
            import time
            time.sleep(1)

    # Commit all changes
    conn.commit()
    conn.close()
    
    # Summary reporting
    print(f"\n👥 PLAYER RATING UPDATE SUMMARY:")
    print(f"✅ Successful: {successful_updates}/{len(teams)} teams")
    
    if failed_updates:
        print(f"❌ Failed updates:")
        for team, error in failed_updates:
            print(f"   • {team}: {error}")
    else:
        print("🎉 All teams updated successfully!")
    
    return successful_updates == len(teams)

# === Run the agent ===
if __name__ == "__main__":
    success = update_player_ratings()
    if success:
        print("\n🎯 Ready to run main.py to see updated results!")
    else:
        print("\n⚠️  Some updates failed. Check errors above.")