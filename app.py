from flask import Flask, render_template, request, jsonify
import psycopg2
import os
from openlocationcode import openlocationcode as olc

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
print("DATABASE_URL =", DATABASE_URL)  # Debug

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
            olc TEXT,
            address TEXT,
            detail TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_all_markers():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, title, olc, address, detail FROM markers")
    rows = c.fetchall()
    conn.close()
    return rows

def add_marker(lat, lon, title, olc_code=None, address=None, detail=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO markers (lat, lon, title, olc, address, detail)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (lat, lon, title, olc_code, address, detail))
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
    return render_template('map_leaflet.html')

@app.route('/markers')
def markers_api():
    markers = get_all_markers()
    data = []
    for m in markers:
        data.append({
            "id": m[0],
            "lat": m[1],
            "lon": m[2],
            "title": m[3],
            "olc": m[4],
            "address": m[5],
            "detail": m[6]
        })
    return jsonify(data)

@app.route('/add_marker', methods=['POST'])
def add_marker_api():
    data = request.json
    title = data.get('title')
    lat = data.get('lat')
    lon = data.get('lon')
    olc_code = data.get('olc', '').strip() or None
    address = data.get('address', '').strip() or None
    detail = data.get('detail', '').strip() or None

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

    add_marker(lat, lon, title, olc_code, address, detail)
    return {"message": "เพิ่มหมุดสำเร็จ"}, 200

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
