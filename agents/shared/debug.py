import requests
import csv

# Try multiple possible URLs
URLS_TO_TRY = [
    "https://projects.fivethirtyeight.com/soccer-api/club/spi_global_rankings.csv",
    "https://raw.githubusercontent.com/fivethirtyeight/data/master/soccer-spi/spi_global_rankings.csv"
]

def debug_csv_structure():
    for i, url in enumerate(URLS_TO_TRY, 1):
        print(f"🔍 Trying URL {i}: {url}")
        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            decoded = response.content.decode("utf-8")
            
            # Check if it's HTML instead of CSV
            if decoded.strip().startswith('<!DOCTYPE') or decoded.strip().startswith('<html'):
                print(f"❌ URL {i} returned HTML instead of CSV")
                print(f"First 200 chars: {decoded[:200]}...")
                continue
                
            print(f"✅ Successfully fetched CSV from URL {i}")
            reader = csv.DictReader(decoded.splitlines())
            
            # Get the first row to see available columns
            first_row = next(reader)
            
            print("\n📋 Available columns:")
            for j, column in enumerate(first_row.keys()):
                print(f"  {j+1}. '{column}'")
            
            print(f"\n📊 Sample data from first row:")
            for key, value in first_row.items():
                print(f"  {key}: {value}")
            
            # Check if there are any columns that might be league-related
            print(f"\n🔍 Looking for league-related columns:")
            league_columns = [col for col in first_row.keys() if 'league' in col.lower()]
            if league_columns:
                for col in league_columns:
                    print(f"  Found: '{col}' = '{first_row[col]}'")
            else:
                print("  No columns with 'league' in the name found")
            
            # Look for Premier League teams
            print(f"\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 Looking for English Premier League teams...")
            reader = csv.DictReader(decoded.splitlines())  # Reset reader
            english_teams = []
            for row in reader:
                # Check if this might be an English team
                team_name = row.get('name', '')
                if any(team in team_name for team in ['Arsenal', 'Chelsea', 'Liverpool', 'Manchester', 'Tottenham']):
                    english_teams.append(row)
                    if len(english_teams) >= 5:  # Just show first 5
                        break
            
            if english_teams:
                print("  Found some English teams:")
                for team in english_teams:
                    print(f"    {team}")
            else:
                print("  No obvious English teams found")
            
            return  # Success, exit the function
            
        except requests.exceptions.RequestException as e:
            print(f"❌ URL {i} failed with error: {e}")
        except Exception as e:
            print(f"❌ URL {i} failed with unexpected error: {e}")
    
    print("\n❌ All URLs failed. The FiveThirtyEight API might be down or changed.")
    print("💡 Consider using alternative data sources or checking their website manually.")

if __name__ == "__main__":
    debug_csv_structure()