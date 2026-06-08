import sqlite3
from main import scrape_data

all_players, all_values, all_clubs, all_logos, all_player_images = scrape_data()  # scrapes fresh data

conn = sqlite3.connect("nike_liga.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS players")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        value INTEGER,
        club TEXT,
        logo_url TEXT,
        player_img_url TEXT,
        scraped_at DATE DEFAULT (date('now'))
    )
""")

#cursor.execute("DELETE FROM players")  # clear old data before inserting fresh

for name, value, club, logo, player_img in zip(all_players, all_values, all_clubs, all_logos, all_player_images):
    cursor.execute(
        "INSERT INTO players (name, value, club, logo_url, player_img_url) VALUES (?, ?, ?, ?, ?)",
        (name, int(value), club, logo, player_img)
    )

conn.commit()
conn.close()
print(f"Saved {len(all_players)} players to nike_liga.db")