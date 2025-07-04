from flask import Flask, render_template, request, jsonify
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
            title TEXT NOT NULL
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

def decode_olc(code, ref_lat=13.7563, ref_lon=100.5018):
    plus_code = code.split()[0].strip()
    if not olc.isFull(plus_code):
        recovered = olc.recoverNearest(plus_code, ref_lat, ref_lon)
        decoded = olc.decode(recovered)
    else:
        decoded = olc.decode(plus_code)
    return decoded.latitudeCenter, decoded.longitudeCenter

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
            lat, lon = decode_olc(olc_code)
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
