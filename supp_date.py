import os
import json

# Dossier courant
dossier = "."

# Date cible à supprimer
date_cible = "2025-07-04"

# Parcours de tous les fichiers JSON du dossier
for nom_fichier in os.listdir(dossier):
    if nom_fichier.endswith(".json"):
        chemin_fichier = os.path.join(dossier, nom_fichier)

        with open(chemin_fichier, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"❌ Fichier illisible : {nom_fichier}")
                continue

        # Suppression récursive des éléments contenant la date cible
        def filtrer(obj):
            if isinstance(obj, list):
                return [filtrer(i) for i in obj if not contient_date(i)]
            elif isinstance(obj, dict):
                return {k: filtrer(v) for k, v in obj.items() if not contient_date(v)}
            return obj

        def contient_date(obj):
            if isinstance(obj, str) and date_cible in obj:
                return True
            elif isinstance(obj, dict):
                return any(contient_date(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(contient_date(i) for i in obj)
            return False

        data_filtré = filtrer(data)

        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(data_filtré, f, ensure_ascii=False, indent=2)

        print(f"✅ Fichier nettoyé : {nom_fichier}")

