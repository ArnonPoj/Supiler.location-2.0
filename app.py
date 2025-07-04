from flask import Flask, render_template, request, redirect
import folium
import sqlite3
import os

app = Flask(__name__)

DB_FILE = 'markers.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            lat REAL,
            lng REAL
        )
    ''')
    conn.commit()
    conn.close()

def get_all_markers():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT name, lat, lng FROM markers')
    rows = c.fetchall()
    conn.close()
    return rows

def add_marker(name, lat, lng):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO markers (name, lat, lng) VALUES (?, ?, ?)', (name, lat, lng))
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        lat = float(request.form['lat'])
        lng = float(request.form['lng'])
        add_marker(name, lat, lng)
        return redirect('/')

    # 1. สร้าง folium map
    m = folium.Map(location=[13.75, 100.5], zoom_start=6)

    # 2. ดึง marker ทั้งหมดจาก DB
    for name, lat, lng in get_all_markers():
        folium.Marker([lat, lng], popup=name).add_to(m)

    # 3. Save เป็น HTML แล้วแสดงผ่าน iframe
    map_path = 'static/map.html'
    m.save(map_path)
    return render_template('map_folium.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
