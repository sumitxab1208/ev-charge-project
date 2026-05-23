from flask import (
    Flask, render_template, jsonify, request,
    redirect, session, flash
)
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ================= APP =================

app = Flask(__name__)
app.secret_key = "ev_secret_key_123"
DATABASE = "database.db"

# ================= AUTO INIT DB =================

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur  = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
        lat REAL, lng REAL, type TEXT, available INTEGER, price INTEGER)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
        email TEXT UNIQUE, password TEXT,
        wallet INTEGER DEFAULT 500, phone TEXT DEFAULT '', vehicle TEXT DEFAULT '')""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, station_name TEXT,
        booking_time TEXT DEFAULT (datetime('now','localtime')),
        slot TEXT DEFAULT '', duration INTEGER DEFAULT 1,
        kwh REAL DEFAULT 10, cost REAL DEFAULT 0)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER UNIQUE,
        username TEXT, station_name TEXT, rating INTEGER DEFAULT 5,
        comment TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now','localtime')))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
        action TEXT, detail TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')))""")
    # Safe column upgrades
    for col, defn in [("wallet","INTEGER DEFAULT 500"),("phone","TEXT DEFAULT ''"),("vehicle","TEXT DEFAULT ''")]:
        try: cur.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
        except: pass
    for col, defn in [("slot","TEXT DEFAULT ''"),("duration","INTEGER DEFAULT 1"),("kwh","REAL DEFAULT 10"),("cost","REAL DEFAULT 0")]:
        try: cur.execute(f"ALTER TABLE bookings ADD COLUMN {col} {defn}")
        except: pass
    # Seed stations if empty
    if cur.execute("SELECT COUNT(*) FROM stations").fetchone()[0] == 0:
        cur.executemany("INSERT INTO stations (name,lat,lng,type,available,price) VALUES (?,?,?,?,?,?)", [
            ("Jalandhar Central Station",31.3260,75.5762,"Fast",1,20),
            ("Model Town EV Hub",31.3201,75.5900,"Slow",0,10),
            ("Bus Stand Fast Charger",31.3256,75.5789,"Fast",1,25),
            ("GT Road Highway Station",31.3100,75.6000,"Fast",0,30),
            ("Mall Road Charging Point",31.3300,75.5700,"Slow",1,15),
            ("LPU Campus Charging Hub",31.2536,75.7033,"Fast",1,18),
            ("Railway Station Charger",31.3265,75.6200,"Slow",0,12),
            ("Phagwara Fast Charger",31.2206,75.7734,"Fast",1,22),
            ("Nakodar Road EV Stop",31.2900,75.6500,"Slow",1,8),
            ("Ludhiana NH-44 Hub",30.9010,75.8573,"Fast",1,28),
        ])
    conn.commit()
    conn.close()

init_db()

# ================= DB =================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ================= HOME =================

@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

# ================= STATIONS API =================

@app.route('/stations')
def stations():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM stations").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ================= REGISTER =================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        hashed   = generate_password_hash(password)
        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (username, email, password, wallet) VALUES (?, ?, ?, ?)",
                (username, email, hashed, 500)
            )
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            return render_template('register.html', error="⚠️ Username or email already exists.")
    return render_template('register.html')

# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user']    = user['username']
            session['user_id'] = user['id']
            return redirect('/')
        return render_template('login.html', error="❌ Invalid email or password.")
    return render_template('login.html')

# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ================= PROFILE =================

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    bookings = conn.execute(
        "SELECT * FROM bookings WHERE username=? ORDER BY id DESC LIMIT 5",
        (session['user'],)
    ).fetchall()
    total_bookings = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE username=?", (session['user'],)
    ).fetchone()[0]
    conn.close()
    return render_template('profile.html', user=user, bookings=bookings, total_bookings=total_bookings)

# ================= UPDATE PROFILE =================

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect('/login')
    phone = request.form.get('phone', '').strip()
    vehicle = request.form.get('vehicle', '').strip()
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET phone=?, vehicle=? WHERE id=?",
        (phone, vehicle, session['user_id'])
    )
    conn.commit()
    conn.close()
    return redirect('/profile')

# ================= WALLET TOPUP =================

@app.route('/wallet-topup', methods=['POST'])
def wallet_topup():
    if 'user' not in session:
        return redirect('/login')
    amount = int(request.form.get('amount', 0))
    if amount > 0:
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET wallet = wallet + ? WHERE id=?",
            (amount, session['user_id'])
        )
        conn.execute(
            "INSERT INTO activity (username, action, detail) VALUES (?, ?, ?)",
            (session['user'], 'wallet_topup', f'Added ₹{amount} to wallet')
        )
        conn.commit()
        conn.close()
    return redirect('/profile')

# ================= SMART BOOK (with slot + duration) =================

@app.route('/smart-book/<station_name>', methods=['GET', 'POST'])
def smart_book(station_name):
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()
    station = conn.execute("SELECT * FROM stations WHERE name=?", (station_name,)).fetchone()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()

    if not station:
        conn.close()
        return redirect('/')

    if request.method == 'POST':
        slot     = request.form.get('slot', '')
        duration = int(request.form.get('duration', 1))
        kwh      = float(request.form.get('kwh', 10))
        cost     = round(station['price'] * kwh, 2)

        if user['wallet'] < cost:
            conn.close()
            return render_template('smart_book.html',
                station=dict(station), user=dict(user),
                error=f"❌ Insufficient wallet balance. Need ₹{cost}, have ₹{user['wallet']}.")

        booking_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

        conn.execute(
            "INSERT INTO bookings (username, station_name, booking_time, slot, duration, kwh, cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session['user'], station_name, booking_time, slot, duration, kwh, cost)
        )
        conn.execute(
            "UPDATE users SET wallet = wallet - ? WHERE id=?",
            (cost, session['user_id'])
        )
        conn.execute(
            "UPDATE stations SET available=0 WHERE name=?", (station_name,)
        )
        conn.execute(
            "INSERT INTO activity (username, action, detail) VALUES (?, ?, ?)",
            (session['user'], 'booking', f'Booked {station_name} for {duration}h — ₹{cost}')
        )
        conn.commit()
        conn.close()
        return redirect('/bookings')

    conn.close()
    return render_template('smart_book.html', station=dict(station), user=dict(user), error=None)

# ================= OLD BOOK (keep for backward compat) =================

@app.route('/book/<station_name>')
def book_station(station_name):
    return redirect(f'/smart-book/{station_name}')

# ================= BOOKINGS =================

@app.route('/bookings')
def bookings():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM bookings WHERE username=? ORDER BY id DESC",
        (session['user'],)
    ).fetchall()
    conn.close()
    return render_template('bookings.html', bookings=rows, username=session['user'])

# ================= CANCEL BOOKING =================

@app.route('/cancel-booking/<int:id>')
def cancel_booking(id):
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    booking = conn.execute("SELECT * FROM bookings WHERE id=? AND username=?",
                           (id, session['user'])).fetchone()
    if booking:
        # Refund wallet
        conn.execute(
            "UPDATE users SET wallet = wallet + ? WHERE username=?",
            (booking['cost'] or 0, session['user'])
        )
        # Re-enable station
        conn.execute(
            "UPDATE stations SET available=1 WHERE name=?", (booking['station_name'],)
        )
        conn.execute("DELETE FROM bookings WHERE id=?", (id,))
        conn.execute(
            "INSERT INTO activity (username, action, detail) VALUES (?, ?, ?)",
            (session['user'], 'cancel', f'Cancelled booking at {booking["station_name"]}')
        )
        conn.commit()
    conn.close()
    return redirect('/bookings')

# ================= FAVOURITES =================

@app.route('/favourites')
def favourites():
    if 'user' not in session:
        return redirect('/login')
    return render_template('favourites.html')

# ================= ACTIVITY FEED API =================

@app.route('/api/activity')
def activity_feed():
    if 'user' not in session:
        return jsonify([])
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM activity WHERE username=? ORDER BY id DESC LIMIT 10",
        (session['user'],)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ================= WALLET API =================

@app.route('/api/wallet')
def wallet_balance():
    if 'user' not in session:
        return jsonify({'balance': 0})
    conn = get_db_connection()
    user = conn.execute("SELECT wallet FROM users WHERE id=?", (session['user_id'],)).fetchone()
    conn.close()
    return jsonify({'balance': user['wallet'] if user else 0})

# ================= REVIEW =================

@app.route('/review/<int:booking_id>', methods=['POST'])
def add_review(booking_id):
    if 'user' not in session:
        return redirect('/login')
    rating  = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()
    conn = get_db_connection()
    booking = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if booking and booking['username'] == session['user']:
        conn.execute(
            "INSERT OR REPLACE INTO reviews (booking_id, username, station_name, rating, comment) VALUES (?, ?, ?, ?, ?)",
            (booking_id, session['user'], booking['station_name'], rating, comment)
        )
        conn.commit()
    conn.close()
    return redirect('/bookings')

# ================= ADMIN =================

@app.route('/admin')
def admin():
    if session.get('user') != 'admin':
        return redirect('/')
    conn = get_db_connection()
    total_users    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_stations = conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    revenue        = conn.execute("SELECT SUM(cost) FROM bookings").fetchone()[0] or 0
    bookings       = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
    all_stations   = conn.execute("SELECT * FROM stations ORDER BY id ASC").fetchall()
    all_users      = conn.execute("SELECT id, username, email, wallet, phone, vehicle FROM users ORDER BY id ASC").fetchall()
    conn.close()
    return render_template('admin.html',
        total_users=total_users,
        total_stations=total_stations,
        total_bookings=total_bookings,
        revenue=round(revenue, 2),
        bookings=bookings,
        all_stations=all_stations,
        all_users=all_users
    )

# ================= ADMIN — ADD STATION =================

@app.route('/admin/add-station', methods=['POST'])
def add_station():
    if session.get('user') != 'admin':
        return redirect('/')
    name      = request.form['name'].strip()
    lat       = float(request.form['lat'])
    lng       = float(request.form['lng'])
    stype     = request.form['type']
    available = int(request.form.get('available', 1))
    price     = int(request.form['price'])
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO stations (name, lat, lng, type, available, price) VALUES (?, ?, ?, ?, ?, ?)",
        (name, lat, lng, stype, available, price)
    )
    conn.commit()
    conn.close()
    return redirect('/admin')

# ================= ADMIN — EDIT STATION =================

@app.route('/admin/edit-station/<int:id>', methods=['POST'])
def edit_station(id):
    if session.get('user') != 'admin':
        return redirect('/')
    name      = request.form['name'].strip()
    stype     = request.form['type']
    available = int(request.form.get('available', 1))
    price     = int(request.form['price'])
    conn = get_db_connection()
    conn.execute(
        "UPDATE stations SET name=?, type=?, available=?, price=? WHERE id=?",
        (name, stype, available, price, id)
    )
    conn.commit()
    conn.close()
    return redirect('/admin')

# ================= ADMIN — DELETE STATION =================

@app.route('/admin/delete-station/<int:id>')
def delete_station(id):
    if session.get('user') != 'admin':
        return redirect('/')
    conn = get_db_connection()
    conn.execute("DELETE FROM stations WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ================= ADMIN — DELETE BOOKING =================

@app.route('/delete-booking/<int:id>')
def delete_booking(id):
    if session.get('user') != 'admin':
        return redirect('/')
    conn = get_db_connection()
    conn.execute("DELETE FROM bookings WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ================= ADMIN — TOGGLE STATION =================

@app.route('/toggle-station/<int:id>')
def toggle_station(id):
    if session.get('user') != 'admin':
        return redirect('/')
    conn = get_db_connection()
    row = conn.execute("SELECT available FROM stations WHERE id=?", (id,)).fetchone()
    if row:
        conn.execute("UPDATE stations SET available=? WHERE id=?",
                     (0 if row['available'] else 1, id))
        conn.commit()
    conn.close()
    return redirect('/admin')

# ================= ADMIN — DELETE USER =================

@app.route('/admin/delete-user/<int:id>')
def delete_user(id):
    if session.get('user') != 'admin':
        return redirect('/')
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ================= ADMIN — STATS API =================

@app.route('/api/admin/stats')
def admin_stats():
    if session.get('user') != 'admin':
        return jsonify({})
    conn = get_db_connection()
    bookings_per_day = conn.execute("""
        SELECT DATE(booking_time) as day, COUNT(*) as count
        FROM bookings GROUP BY DATE(booking_time) ORDER BY day DESC LIMIT 7
    """).fetchall()
    top_stations = conn.execute("""
        SELECT station_name, COUNT(*) as count
        FROM bookings GROUP BY station_name ORDER BY count DESC LIMIT 5
    """).fetchall()
    conn.close()
    return jsonify({
        'bookings_per_day': [dict(r) for r in bookings_per_day],
        'top_stations': [dict(r) for r in top_stations]
    })

# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)