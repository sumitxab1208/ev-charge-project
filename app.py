from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    session,
    flash
)

import sqlite3
from datetime import datetime
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# ================= APP =================

app = Flask(__name__)
app.secret_key = "ev_secret_key_123"
DATABASE = "database.db"

# ================= DB CONNECTION =================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ================= HOME =================

@app.route('/')
def home():
    return render_template('index.html')

# ================= STATIONS API =================

@app.route('/stations')
def stations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stations")
    rows = cur.fetchall()
    conn.close()

    stations_data = []
    for row in rows:
        stations_data.append({
            "id":        row["id"],
            "name":      row["name"],
            "lat":       row["lat"],
            "lng":       row["lng"],
            "type":      row["type"],
            "available": row["available"],
            "price":     row["price"]
        })

    return jsonify(stations_data)

# ================= REGISTER =================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']
        hashed   = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed)
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
        email    = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user']    = user['username']
            session['user_id'] = user['id']
            return redirect('/')
        else:
            return render_template('login.html', error="❌ Invalid email or password.")

    return render_template('login.html')

# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ================= BOOK STATION =================

@app.route('/book/<station_name>')
def book_station(station_name):
    if 'user' not in session:
        return redirect('/login')

    username     = session['user']
    booking_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO bookings (username, station_name, booking_time) VALUES (?, ?, ?)",
        (username, station_name, booking_time)
    )
    conn.commit()
    conn.close()

    return redirect('/bookings')

# ================= BOOKINGS PAGE =================

@app.route('/bookings')
def bookings():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    conn = get_db_connection()
    cur  = conn.cursor()
    # Only show the logged-in user's own bookings
    cur.execute(
        "SELECT * FROM bookings WHERE username=? ORDER BY id DESC",
        (username,)
    )
    rows = cur.fetchall()
    conn.close()

    return render_template('bookings.html', bookings=rows, username=username)

# ================= CANCEL BOOKING (user) =================

@app.route('/cancel-booking/<int:id>')
def cancel_booking(id):
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    conn     = get_db_connection()
    cur      = conn.cursor()
    # Only allow users to cancel their own bookings
    cur.execute(
        "DELETE FROM bookings WHERE id=? AND username=?",
        (id, username)
    )
    conn.commit()
    conn.close()

    return redirect('/bookings')

# ================= FAVORITES PAGE =================

@app.route('/favourites')
def favourites():
    return render_template('favourites.html')

# ================= ADMIN DASHBOARD =================

@app.route('/admin')
def admin():
    # Basic admin guard — only 'admin' username
    if session.get('user') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM stations")
    total_stations = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cur.fetchone()[0]

    cur.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cur.fetchall()

    cur.execute("SELECT * FROM stations ORDER BY id ASC")
    all_stations = cur.fetchall()

    conn.close()

    return render_template(
        'admin.html',
        total_users=total_users,
        total_stations=total_stations,
        total_bookings=total_bookings,
        bookings=bookings,
        all_stations=all_stations
    )

# ================= DELETE BOOKING (admin) =================

@app.route('/delete-booking/<int:id>')
def delete_booking(id):
    if session.get('user') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')

# ================= TOGGLE STATION AVAILABILITY (admin) =================

@app.route('/toggle-station/<int:id>')
def toggle_station(id):
    if session.get('user') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT available FROM stations WHERE id=?", (id,))
    row = cur.fetchone()
    if row:
        new_val = 0 if row['available'] else 1
        cur.execute("UPDATE stations SET available=? WHERE id=?", (new_val, id))
        conn.commit()
    conn.close()

    return redirect('/admin')

# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)