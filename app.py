from flask import Flask, request, jsonify, render_template, render_template_string
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# ================== CONFIG ==================
POSITION_FILE = 'position.json'
HISTORY_FILE = 'positions_gps.json'
UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_PASSWORD = "tontonvelo"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================== ROUTES ==================

@app.route('/')
def index():
    return render_template('index.html')

VISITS_FILE = "visits.json"

@app.route("/log_visit")
def log_visit():
    # Récupère la date du jour
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Récupère l'adresse IP du client
    #user_ip = request.remote_addr
    user_ip = get_client_ip()
    if not user_ip:
      return jsonify(success=False, reason="local_ip")


    # Charge les données existantes
    if os.path.exists(VISITS_FILE):
        with open(VISITS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    # Initialise les stats du jour
    if today not in data:
        data[today] = {"total": 0, "uniques": []}

    # Incrémente total
    data[today]["total"] += 1

    # Ajoute IP si elle est unique
    if user_ip not in data[today]["uniques"]:
        data[today]["uniques"].append(user_ip)

    # Sauvegarde
    with open(VISITS_FILE, "w") as f:
        json.dump(data, f)

    return jsonify(success=True)

@app.route("/stats")
def stats():
    with open(VISITS_FILE) as f:
        data = json.load(f)
    return jsonify(data)  # ou générer du HTML si tu préfères

@app.route("/log_visit_upload")
def log_visit_upload():
    from datetime import datetime
    import json, os

    today = datetime.now().strftime("%Y-%m-%d")
    #ip = request.remote_addr
    ip = get_client_ip()
    if not ip:
        return jsonify(success=False, reason="local_ip")
    
    log_file = "upload_visits.json"

    if os.path.exists(log_file):
        with open(log_file) as f:
            data = json.load(f)
    else:
        data = {}

    if today not in data:
        data[today] = {"total": 0, "uniques": []}

    data[today]["total"] += 1
    if ip not in data[today]["uniques"]:
        data[today]["uniques"].append(ip)

    with open(log_file, "w") as f:
        json.dump(data, f)

    return jsonify(success=True)

@app.route("/visits_stats")
def visits_stats():
    if os.path.exists(VISITS_FILE):
        with open(VISITS_FILE) as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({})

@app.route("/upload_stats")
def upload_stats():
    log_file = "upload_visits.json"
    if os.path.exists(log_file):
        with open(log_file) as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({})
    
@app.route('/upload', methods=['GET', 'POST'])
def protected_upload():
    if request.method == "POST":
        if request.form.get("password") == UPLOAD_PASSWORD:
            # Sert le fichier HTML brut, sans passer par render_template
            with open("templates/upload.html", encoding="utf-8") as f:
                return f.read()
        else:
            return "<h2>❌ Mot de passe incorrect</h2><a href='/upload'>↩️ Réessayer</a>", 403

    return '''
    <form method="post">
        <h2> Accès protégé</h2>
        <input type="password" name="password" placeholder="Mot de passe" required>
        <button type="submit">Accéder</button>
    </form>
    '''

@app.route('/api/position', methods=['POST'])
def post_position():
    data = request.get_json()
    if not data or 'lat' not in data or 'lon' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    position = {
        'lat': data['lat'],
        'lon': data['lon'],
        'timestamp': datetime.utcnow().isoformat()
    }

    save_position(position)

    return jsonify({'status': 'ok'})

@app.route('/api/owntracks', methods=['POST'])
def post_owntracks():
    data = request.get_json()
    if not data or data.get('_type') != 'location':
        return jsonify({'error': 'Invalid OwnTracks payload'}), 400

    lat = data.get('lat')
    lon = data.get('lon')
    tst = data.get('tst')

    if lat is None or lon is None or tst is None:
        return jsonify({'error': 'Missing data in OwnTracks payload'}), 400

    dt = datetime.utcfromtimestamp(tst)
    timestamp = (dt - timedelta(hours=2)).isoformat() + 'Z'  # ← ici on enlève 2h

    position = {
        'lat': lat,
        'lon': lon,
        'timestamp': timestamp
    }

    save_position(position)

    return jsonify({'status': 'ok'})

@app.route('/api/position', methods=['GET'])
def get_position():
    if not os.path.exists(POSITION_FILE):
        return jsonify({'error': 'No position yet'}), 404
    with open(POSITION_FILE) as f:
        return jsonify(json.load(f))

@app.route('/api/position/history')
def get_position_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return jsonify(json.load(f))
    else:
        return jsonify([])

@app.route('/api/upload', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'Pas de fichier'}), 400

    photo = request.files['photo']
    lat = request.form.get('lat')
    lon = request.form.get('lon')

    if not lat or not lon:
        return jsonify({'error': 'Position GPS manquante'}), 400

    if photo and allowed_file(photo.filename):
        timestamp = (datetime.utcnow() + timedelta(hours=2)).isoformat() + 'Z'
        filename = datetime.utcnow().strftime('%Y%m%d%H%M%S') + '_' + photo.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(filepath)

        # Enregistre la position + photo
        entry = {
            'lat': float(lat),
            'lon': float(lon),
            'filename': filename,
            'timestamp': timestamp
        }

        photo_positions_file = 'photos.json'
        if os.path.exists(photo_positions_file):
            with open(photo_positions_file) as f:
                photos = json.load(f)
        else:
            photos = []

        photos.append(entry)
        with open(photo_positions_file, 'w') as f:
            json.dump(photos, f)

        return jsonify({'status': 'ok'})
    else:
        return jsonify({'error': 'Fichier invalide'}), 400

@app.route('/api/photos')
def get_photo_positions():
    photo_positions_file = 'photos.json'
    if os.path.exists(photo_positions_file):
        with open(photo_positions_file) as f:
            return jsonify(json.load(f))
    else:
        return jsonify([])

@app.route('/api/distances')
def api_distances():
    if os.path.exists("distances_par_jour.json"):
        with open("distances_par_jour.json", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify([])


# ================== UTILS ==================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_position(position):
    # Sauvegarde la dernière position connue
    with open(POSITION_FILE, 'w') as f:
        json.dump(position, f)

    # Ajout à l'historique
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    else:
        history = []

    history.append(position)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)
        
    calculate_distances_by_day()
        
def calculate_distances_by_day():
    from collections import defaultdict
    from math import radians, sin, cos, sqrt, atan2

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371e3  # rayon Terre en mètres
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        d_phi = radians(lat2 - lat1)
        d_lambda = radians(lon2 - lon1)

        a = sin(d_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    if not os.path.exists(HISTORY_FILE):
        return

    with open(HISTORY_FILE) as f:
        positions = json.load(f)

    positions_by_day = defaultdict(list)
    for pos in positions:
        day = pos['timestamp'].split("T")[0]
        positions_by_day[day].append(pos)

    results = []
    for day, points in positions_by_day.items():
        points.sort(key=lambda x: x['timestamp'])
        total_distance = 0.0
        for i in range(1, len(points)):
            lat1, lon1 = points[i-1]['lat'], points[i-1]['lon']
            lat2, lon2 = points[i]['lat'], points[i]['lon']
            total_distance += haversine(lat1, lon1, lat2, lon2)
        results.append({
            "jour": day,
            "distance_km": round(total_distance / 1000, 2)
        })

    with open("distances_par_jour.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def get_client_ip():
    # Essaye de récupérer l’IP réelle via les headers (reverse proxy)
    if "X-Forwarded-For" in request.headers:
        ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
    else:
        ip = request.remote_addr

    # Ignore les IPs locales pour les stats
    if ip.startswith("127.") or ip.startswith("172.") or ip.startswith("192.168.") or ip == "localhost":
        return None
    return ip

# ================ DÉMARRAGE SERVEUR =================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
