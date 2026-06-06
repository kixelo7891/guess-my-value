import sqlite3
from main import scrape_data

all_players, all_values = scrape_data()  # scrapes fresh data

conn = sqlite3.connect(r"C:\Users\igoro\PycharmProjects\GuessMyValueNikeLiga\nike_liga.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        value INTEGER,
        scraped_at DATE DEFAULT (date('now'))
    )
""")

cursor.execute("DELETE FROM players")  # clear old data before inserting fresh

for name, value in zip(all_players, all_values):
    cursor.execute("INSERT INTO players (name, value) VALUES (?, ?)", (name, int(value)))

conn.commit()
conn.close()
print(f"Saved {len(all_players)} players to nike_liga.db")