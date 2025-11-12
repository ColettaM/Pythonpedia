#-----------------------------------------------#
#          Service web Flask – Pythonpédia     
#-----------------------------------------------#

from flask import Flask, jsonify, render_template, request
import json, os
from dotenv import load_dotenv

#-----------------------------------------------#
# Configuration initiale
#-----------------------------------------------#
load_dotenv()  # Charge les variables d’environnement depuis le fichier .env

# Clé secrète d’administration
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "changeme")
print("Token admin chargé :", ADMIN_TOKEN)

# Fichier local contenant la base de données principale
DATA_FILE = "db.json"

# Création de l’application Flask
app = Flask(__name__)

#-----------------------------------------------#
# Fonctions utilitaires
#-----------------------------------------------#
def load_data():
    """Charge les données locales depuis le fichier JSON principal.
    Si le fichier n’existe pas, on renvoie une structure vide par défaut."""
    if not os.path.exists(DATA_FILE):
        return {"topics": {}, "annuaire": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

#-----------------------------------------------#
# Routes publiques – pages HTML
#-----------------------------------------------#
@app.route("/")
def home():
    """Page d’accueil principale."""
    return render_template("index.html")

@app.route("/ui")
def ui_page():
    """Page d’interface utilisateur."""
    return render_template("ui.html")

@app.route("/documentation")
def documentation_page():
    """Page affichant la documentation du projet."""
    return render_template("documentation.html")

#-----------------------------------------------#
# Routes API publiques (lecture seule)
#-----------------------------------------------#
@app.route("/ws/topics")
def get_topics():
    """Renvoie la liste de tous les sujets disponibles."""
    data = load_data()
    return jsonify(list(data.get("topics", {}).keys()))

@app.route("/ws/topic/<path:topic>")
def get_topic(topic):
    """Renvoie le contenu d’un sujet donné (ou erreur 404 si absent)."""
    data = load_data()
    topics = data.get("topics", {})
    if topic not in topics:
        return jsonify({"error": "Topic non trouvé"}), 404
    return jsonify(topics[topic])

@app.route("/ws/annuaire")
def get_annuaire():
    """Renvoie la liste actuelle des serveurs connus dans l’annuaire."""
    data = load_data()
    return jsonify(data.get("annuaire", []))

#-----------------------------------------------#
# Endpoint POST protégé : ajout d’un serveur
#-----------------------------------------------#
@app.post("/ws/annuaire")
def post_annuaire():
    """Ajoute un serveur à l’annuaire local.
    Cette route est protégée par une clé API d’administration."""
    
    # Vérification de la clé d’accès administrateur
    token = request.headers.get("X-API-Key") or request.args.get("token")
    if not token:
        return jsonify({"error": "Aucune clé administrateur fournie."}), 401
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Accès refusé : clé administrateur invalide."}), 403

    # Lecture du contenu JSON envoyé par le client
    data = load_data()
    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()

    # Validation de base
    if not url:
        return jsonify({"error": "Champ 'url' requis"}), 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error": "URL invalide (doit commencer par http:// ou https://)"}), 400

    # Mise à jour de l’annuaire (sans doublons)
    annuaire = set(data.get("annuaire", []))
    annuaire.add(url)
    data["annuaire"] = sorted(annuaire)

    # Sauvegarde du fichier JSON
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return jsonify({"ok": True, "annuaire": data["annuaire"]}), 201

#-----------------------------------------------#
# Endpoint privé : synchronisation / réplication
#-----------------------------------------------#
@app.post("/admin/sync")
def sync_now():
    """Déclenche manuellement une synchronisation locale.
    Cette route appelle la fonction enrichir() du module sync.py
    et est également protégée par la clé d’administration."""
    
    token = request.headers.get("X-API-Key") or request.args.get("token")
    if not token:
        return jsonify({"ok": False, "error": "Aucune clé administrateur fournie."}), 401
    if token != ADMIN_TOKEN:
        return jsonify({"ok": False, "error": "Clé administrateur invalide."}), 403

    import sync  # Import local pour éviter de charger inutilement le module
    try:
        sync.enrichir()
        return jsonify({"ok": True, "message": "Réplication terminée avec succès."}), 200
    except Exception as e:
        # Capture toute erreur de synchronisation
        return jsonify({"ok": False, "error": str(e)}), 500

#-----------------------------------------------#
# Lancement du serveur Flask
#-----------------------------------------------#
if __name__ == "__main__":
    # Le serveur écoute sur toutes les interfaces (port 8888)
    # Le mode debug=True est utile en développement mais à désactiver en production.
    app.run(host="0.0.0.0", port=8888, debug=True)
