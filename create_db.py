import sqlite3
import os

db_path = os.path.join(os.getcwd(), "database.db")

conn = sqlite3.connect(db_path)
cur  = conn.cursor()

# ================= STATIONS TABLE =================

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

# ================= USERS TABLE =================

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email    TEXT UNIQUE,
    password TEXT
)
""")

# ================= BOOKINGS TABLE =================

cur.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT,
    station_name TEXT,
    booking_time TEXT DEFAULT (datetime('now','localtime'))
)
""")

# ================= STATION DATA =================

cur.execute("DELETE FROM stations")

stations = [
    ("Jalandhar Central Station",   31.3260, 75.5762, "Fast", 1, 20),
    ("Model Town EV Hub",           31.3201, 75.5900, "Slow", 0, 10),
    ("Bus Stand Fast Charger",      31.3256, 75.5789, "Fast", 1, 25),
    ("GT Road Highway Station",     31.3100, 75.6000, "Fast", 0, 30),
    ("Mall Road Charging Point",    31.3300, 75.5700, "Slow", 1, 15),
    ("LPU Campus Charging Hub",     31.2536, 75.7033, "Fast", 1, 18),
    ("Railway Station Charger",     31.3265, 75.6200, "Slow", 0, 12),
    ("Phagwara Fast Charger",       31.2206, 75.7734, "Fast", 1, 22),
    ("Nakodar Road EV Stop",        31.2900, 75.6500, "Slow", 1, 8),
    ("Ludhiana NH-44 Hub",          30.9010, 75.8573, "Fast", 1, 28),
]

cur.executemany("""
    INSERT INTO stations (name, lat, lng, type, available, price)
    VALUES (?, ?, ?, ?, ?, ?)
""", stations)

conn.commit()
conn.close()

print("✅ Database created with", len(stations), "stations.")