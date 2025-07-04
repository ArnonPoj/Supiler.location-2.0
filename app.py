from flask import Flask, render_template, request, jsonify
import sqlite3
import folium
import os

app = Flask(__name__)

DB_PATH = 'markers.db'
MAP_HTML_PATH = 'static/map.html'

# สร้างฐานข้อมูลและตารางถ้ายังไม่มี
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            title TEXT,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ดึงหมุดทั้งหมดจาก DB
def get_all_markers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, title, description FROM markers")
    rows = c.fetchall()
    conn.close()
    return rows

# เพิ่มหมุดใหม่
def add_marker(lat, lon, title=None, description=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO markers (lat, lon, title, description) VALUES (?, ?, ?, ?)", (lat, lon, title, description))
    conn.commit()
    conn.close()

# สร้างแผนที่ Folium จากหมุดใน DB แล้วเซฟไฟล์ HTML
def create_map():
    markers = get_all_markers()
    if markers:
        # ใช้ตำแหน่งหมุดแรกเป็นจุดศูนย์กลางแผนที่
        start_lat, start_lon = markers[0][1], markers[0][2]
    else:
        # ถ้าไม่มีหมุดเลย ให้ตั้งค่ากลางแผนที่เป็นกรุงเทพ (ตัวอย่าง)
        start_lat, start_lon = 13.7563, 100.5018

    m = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    for mkr in markers:
        _, lat, lon, title, desc = mkr
        popup_text = f"<b>{title or 'No title'}</b><br>{desc or ''}"
        folium.Marker(location=[lat, lon], popup=popup_text).add_to(m)

    # สร้างไฟล์ HTML ใน static/
    m.save(MAP_HTML_PATH)

@app.route('/')
def index():
    # สร้างแผนที่ก่อนแสดง
    create_map()
    return render_template('map_folium.html')

@app.route('/api/markers', methods=['GET', 'POST'])
def api_markers():
    if request.method == 'POST':
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')
        title = data.get('title')
        description = data.get('description')

        if lat is None or lon is None:
            return jsonify({'error': 'lat and lon required'}), 400
        
        add_marker(lat, lon, title, description)
        create_map()  # สร้างแผนที่ใหม่หลังเพิ่มหมุด
        return jsonify({'message': 'Marker added successfully'})

    else:  # GET
        markers = get_all_markers()
        result = []
        for mkr in markers:
            id_, lat, lon, title, desc = mkr
            result.append({'id': id_, 'lat': lat, 'lon': lon, 'title': title, 'description': desc})
        return jsonify(result)

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True)
