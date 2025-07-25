import sqlite3

conn = sqlite3.connect("db/football_strength.db")
c = conn.cursor()

# Enable foreign keys
c.execute("PRAGMA foreign_keys = ON;")

# Drop tables if re-running clean
c.execute("DROP TABLE IF EXISTS team_parameters")
c.execute("DROP TABLE IF EXISTS teams")

# Create teams table with UUID primary key
c.execute("""
CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
)
""")

# Create parameters table with UUID foreign key
c.execute("""
CREATE TABLE IF NOT EXISTS team_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT NOT NULL,
    parameter TEXT NOT NULL,
    value REAL,
    last_updated DATETIME,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    UNIQUE(team_id, parameter)
)
""")

conn.commit()
conn.close()
print("✅ DB with UUIDs created.")