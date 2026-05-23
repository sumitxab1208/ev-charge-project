import sqlite3
import os

db_path = os.path.join(os.getcwd(), "database.db")
conn = sqlite3.connect(db_path)
cur  = conn.cursor()

# ================= STATIONS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS stations (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT,
    lat       REAL,
    lng       REAL,
    type      TEXT,
    available INTEGER,
    price     INTEGER
)
""")

# ================= USERS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email    TEXT UNIQUE,
    password TEXT,
    wallet   INTEGER DEFAULT 500,
    phone    TEXT DEFAULT '',
    vehicle  TEXT DEFAULT ''
)
""")

# Safely add new columns if they don't exist (handles old database)
for col, definition in [
    ("wallet",  "INTEGER DEFAULT 500"),
    ("phone",   "TEXT DEFAULT ''"),
    ("vehicle", "TEXT DEFAULT ''"),
]:
    try:
        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
    except:
        pass

# ================= BOOKINGS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT,
    station_name TEXT,
    booking_time TEXT DEFAULT (datetime('now','localtime')),
    slot         TEXT DEFAULT '',
    duration     INTEGER DEFAULT 1,
    kwh          REAL DEFAULT 10,
    cost         REAL DEFAULT 0
)
""")

# Safely add new booking columns
for col, definition in [
    ("slot",     "TEXT DEFAULT ''"),
    ("duration", "INTEGER DEFAULT 1"),
    ("kwh",      "REAL DEFAULT 10"),
    ("cost",     "REAL DEFAULT 0"),
]:
    try:
        cur.execute(f"ALTER TABLE bookings ADD COLUMN {col} {definition}")
    except:
        pass

# ================= REVIEWS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id   INTEGER UNIQUE,
    username     TEXT,
    station_name TEXT,
    rating       INTEGER DEFAULT 5,
    comment      TEXT DEFAULT '',
    created_at   TEXT DEFAULT (datetime('now','localtime'))
)
""")

# ================= ACTIVITY =================
cur.execute("""
CREATE TABLE IF NOT EXISTS activity (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT,
    action     TEXT,
    detail     TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime'))
)
""")

# ================= STATION DATA =================
# Only insert if table is empty
cur.execute("SELECT COUNT(*) FROM stations")
if cur.fetchone()[0] == 0:
    stations = [
        ("Jalandhar Central Station", 31.3260, 75.5762, "Fast", 1, 20),
        ("Model Town EV Hub",         31.3201, 75.5900, "Slow", 0, 10),
        ("Bus Stand Fast Charger",    31.3256, 75.5789, "Fast", 1, 25),
        ("GT Road Highway Station",   31.3100, 75.6000, "Fast", 0, 30),
        ("Mall Road Charging Point",  31.3300, 75.5700, "Slow", 1, 15),
        ("LPU Campus Charging Hub",   31.2536, 75.7033, "Fast", 1, 18),
        ("Railway Station Charger",   31.3265, 75.6200, "Slow", 0, 12),
        ("Phagwara Fast Charger",     31.2206, 75.7734, "Fast", 1, 22),
        ("Nakodar Road EV Stop",      31.2900, 75.6500, "Slow", 1,  8),
        ("Ludhiana NH-44 Hub",        30.9010, 75.8573, "Fast", 1, 28),
    ]
    cur.executemany(
        "INSERT INTO stations (name, lat, lng, type, available, price) VALUES (?, ?, ?, ?, ?, ?)",
        stations
    )
    print(f"✅ Inserted {len(stations)} stations.")
else:
    print("ℹ️  Stations already exist, skipping insert.")

conn.commit()
conn.close()
print("✅ Database ready with all tables and columns.")