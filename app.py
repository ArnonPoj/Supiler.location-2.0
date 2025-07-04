from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import folium
import os

app = Flask(__name__)

DB_PATH = 'markers.db'
MAP_HTML_PATH = 'static/map.html'

# 🧱 สร้างตาราง markers ถ้ายังไม่มี
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

# 📥 อ่านหมุดทั้งหมด
def get_all_markers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, title, description FROM markers")
    rows = c.fetchall()
    conn.close()
    return rows

# ➕ เพิ่มหมุด
def add_marker(lat, lon, title=None, description=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO markers (lat, lon, title, description) VALUES (?, ?, ?, ?)",
              (lat, lon, title, description))
    conn.commit()
    conn.close()

# 🗺️ สร้างแผนที่จากหมุดในฐานข้อมูล
def create_map():
    markers = get_all_markers()
    if markers:
        start_lat, start_lon = markers[0][1], markers[0][2]
    else:
        start_lat, start_lon = 13.7563, 100.5018  # กรุงเทพฯ

    m = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    for mkr in markers:
        _, lat, lon, title, desc = mkr
        popup_text = f"<b>{title or 'No title'}</b><br>{desc or ''}"
        folium.Marker(location=[lat, lon], popup=popup_text).add_to(m)

    m.save(MAP_HTML_PATH)

# 🌐 เส้นทางหลัก: แสดงฟอร์ม + แผนที่
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form.get('name')
        lat = request.form.get('lat')
        lon = request.form.get('lng')

        if not lat or not lon or not title:
            return "กรุณากรอกข้อมูลให้ครบ", 400

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return "ละติจูดและลองจิจูดต้องเป็นตัวเลข", 400

        add_marker(lat, lon, title)
        create_map()
        return redirect(url_for('index'))

    create_map()
    return render_template('map_folium.html')

# 🚀 จุดเริ่มต้น
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))  # ✅ Render จะส่ง PORT มาให้
    app.run(host='0.0.0.0', port=port, debug=True)  # ✅ ต้องฟังที่ 0.0.0.0
