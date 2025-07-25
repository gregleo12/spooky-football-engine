import sqlite3

premier_league_teams = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
    "Liverpool", "Luton Town", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest", "Sheffield United",
    "Tottenham Hotspur", "West Ham United", "Wolverhampton Wanderers"
]

conn = sqlite3.connect("db/football_strength.db")
c = conn.cursor()

# Enable foreign key constraints (good practice)
c.execute("PRAGMA foreign_keys = ON;")

for team in premier_league_teams:
    c.execute("INSERT OR IGNORE INTO teams (name) VALUES (?)", (team,))

conn.commit()
conn.close()
print("✅ All Premier League teams added.")
