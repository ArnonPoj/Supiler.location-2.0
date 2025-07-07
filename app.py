from flask import Flask, render_template, request, jsonify
import psycopg2
import os
import folium
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
    # สร้างตารางถ้ายังไม่มี
    c.execute('''
        CREATE TABLE IF NOT EXISTS markers (
            id SERIAL PRIMARY KEY,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            title TEXT NOT NULL
        )
    ''')
    c.execute("ALTER TABLE markers ADD COLUMN IF NOT EXISTS olc TEXT;")
    c.execute("ALTER TABLE markers ADD COLUMN IF NOT EXISTS address TEXT;")
    c.execute("ALTER TABLE markers ADD COLUMN IF NOT EXISTS detail TEXT;")
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

@app.route('/markers')
def markers_api():
    markers = get_all_markers()
    data = []
    for m in markers:
        id, lat, lon, title, olc_code, address, detail = m
        data.append({
            'id': id,
            'lat': lat,
            'lon': lon,
            'title': title,
            'olc': olc_code,
            'address': address,
            'detail': detail,
        })
    return jsonify(data)

@app.route('/')
def index():
    markers = get_all_markers()
    if markers:
        start_lat, start_lon = markers[0][1], markers[0][2]
    else:
        start_lat, start_lon = 13.7563, 100.5018

    m = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    for mkr in markers:
        _, lat, lon, title, olc_code, address, detail = mkr
        popup_html = f"""
        <div style="min-width:200px;">
            <b>{title}</b><br>
            <b>OLC:</b> {olc_code or '-'}<br>
            <b>ที่อยู่:</b> {address or '-'}<br>
            <b>รายละเอียด:</b> {detail or '-'}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=title
        ).add_to(m)

    map_html = m._repr_html_()
    return render_template('map_folium.html', map_html=map_html)

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
