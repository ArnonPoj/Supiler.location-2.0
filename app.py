from flask import Flask, render_template, request, jsonify
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL ยังไม่ถูกตั้งใน environment variable")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS markers (
            id SERIAL PRIMARY KEY,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            title TEXT NOT NULL,
            address TEXT,
            detail TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_all_markers():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, title, address, detail FROM markers")
    rows = c.fetchall()
    conn.close()
    return rows

def add_marker(lat, lon, title, address=None, detail=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO markers (lat, lon, title, address, detail)
        VALUES (%s, %s, %s, %s, %s)
    """, (lat, lon, title, address, detail))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('map_leaflet.html')

@app.route('/markers')
def markers_api():
    markers = get_all_markers()
    return jsonify([
        {
            'id': m[0], 'lat': m[1], 'lon': m[2],
            'title': m[3], 'address': m[4], 'detail': m[5]
        }
        for m in markers
    ])

@app.route('/add_marker', methods=['POST'])
def add_marker_api():
    data = request.get_json()
    title = data.get('title')
    address = data.get('address', '').strip() or None
    detail = data.get('detail', '').strip() or None
    lat = data.get('lat')
    lon = data.get('lon')

    if not title:
        return {"error": "กรุณากรอกชื่อสถานที่"}, 400

    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return {"error": "พิกัดไม่ถูกต้อง"}, 400

    add_marker(lat, lon, title, address, detail)
    return {"message": "เพิ่มหมุดสำเร็จ"}, 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
