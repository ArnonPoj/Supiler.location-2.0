from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from openlocationcode import openlocationcode as olc

app = Flask(__name__)

DB_PATH = 'markers.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            title TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_all_markers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, title FROM markers")
    rows = c.fetchall()
    conn.close()
    return rows

def add_marker(lat, lon, title):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO markers (lat, lon, title) VALUES (?, ?, ?)", (lat, lon, title))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('map_folium.html')

@app.route('/markers')
def markers_api():
    markers = get_all_markers()
    data = [{"id": m[0], "lat": m[1], "lon": m[2], "title": m[3]} for m in markers]
    return jsonify(data)

@app.route('/add_marker', methods=['POST'])
def add_marker_api():
    data = request.json
    title = data.get('title')
    lat = data.get('lat')
    lon = data.get('lon')
    olc_code = data.get('olc', '').strip()

    if olc_code:
        try:
            if not olc.isFull(olc_code):
                ref_lat, ref_lon = 13.7563, 100.5018
                recovered = olc.recoverNearest(olc_code, ref_lat, ref_lon)
                decoded = olc.decode(recovered)
            else:
                decoded = olc.decode(olc_code)
            lat = decoded.latitudeCenter
            lon = decoded.longitudeCenter
        except Exception as e:
            return {"error": f"OLC ไม่ถูกต้อง: {str(e)}"}, 400
    else:
        try:
            lat = float(lat)
            lon = float(lon)
        except:
            return {"error": "พิกัดละติจูดลองจิจูดไม่ถูกต้อง"}, 400

    if not title:
        return {"error": "กรุณากรอกชื่อสถานที่"}, 400

    add_marker(lat, lon, title)
    return {"message": "เพิ่มหมุดสำเร็จ"}, 200

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
