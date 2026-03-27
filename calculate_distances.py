import json
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

INPUT_FILE = "positions_gps.json"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi/2)**2 + cos(phi1)*cos(phi2)*sin(d_lambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Charger les positions
with open(INPUT_FILE) as f:
    positions = json.load(f)

# Trier globalement
positions.sort(key=lambda x: x['timestamp'])

results = []
trajet_index = 1
trajet_points = []
last_time = None
total_distance = 0.0

for i, pos in enumerate(positions):
    current_time = datetime.fromisoformat(pos['timestamp'])
    if last_time and (current_time - last_time).total_seconds() > 3600:
        # Interruption > 1h : clôturer le trajet
        if trajet_points:
            results.append({
                "jour": f"Trajet {trajet_index}",
                "distance_km": round(total_distance / 1000, 2)
            })
            trajet_index += 1
            trajet_points = []
            total_distance = 0.0

    if trajet_points:
        prev = trajet_points[-1]
        d = haversine(prev['lat'], prev['lon'], pos['lat'], pos['lon'])
        total_distance += d

    trajet_points.append(pos)
    last_time = current_time

# Ajouter le dernier trajet
if trajet_points:
    results.append({
        "jour": f"Trajet {trajet_index}",
        "distance_km": round(total_distance / 1000, 2)
    })

# Affichage + sauvegarde
print(json.dumps(results, indent=2, ensure_ascii=False))

with open("distances_par_jour.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

