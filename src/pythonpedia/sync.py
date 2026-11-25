#-----------------------------------------------------------#
# Client privé d’enrichissement – Pythonpédia
#-----------------------------------------------------------#
# Ce script interroge les autres serveurs connus de l’annuaire
# pour fusionner leurs topics dans la base locale.
#----------------------------------------------- ------------#

import requests
import json
import socket
from urllib.parse import quote

# Fichier JSON local servant de base de données
from .paths import DATA_FILE

#-----------------------------------------------------------#
# Fonctions utilitaires 
#-----------------------------------------------------------#
def load_data():
    """Charge les données locales depuis db.json."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    """Sauvegarde les données locales dans db.json avec indentation."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

#-----------------------------------------------------------#
# Fusion de données : intégration des topics distants
#-----------------------------------------------------------#
def merge_topics(local_topics, remote_topics):
    """
    Fusionne les topics d’un serveur distant dans la base locale.
    - Ne supprime jamais les données existantes.
    - Évite les doublons en utilisant des ensembles (set).
    - Trie les URLs pour garder une structure stable.
    """
    for topic_name, items in remote_topics.items():
        # Crée le topic local s’il n’existe pas encore
        local_topic = local_topics.setdefault(topic_name, {})
        for item_name, urls in items.items():
            local_urls = set(local_topic.get(item_name, []))
            merged = sorted(local_urls.union(urls))
            local_topic[item_name] = merged
    return local_topics

#-----------------------------------------------------------#
# Fonction principale : enrichissement / réplication
#-----------------------------------------------------------#
def enrichir():
    """
    Explore les serveurs listés dans l’annuaire et fusionne leurs topics.
    - Évite de contacter sa propre adresse IP ou localhost.
    - Découvre de nouveaux serveurs au fur et à mesure (auto-expansion).
    - Gère les erreurs réseau sans interrompre le processus global.
    """

    # Chargement des données locales
    data = load_data()
    known_servers = list(data.get("annuaire", []))
    local_topics = data.setdefault("topics", {})

    # Détection de l’adresse IP locale pour éviter l’auto-contact
    try:
        own_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        own_ip = None
    print(f"Adresse locale détectée : {own_ip}")

    visited = set()       # Serveurs déjà contactés
    newly_found = set()   # Nouveaux serveurs découverts pendant la réplication

    # Boucle principale : exploration récursive des serveurs connus
    while known_servers:
        server = known_servers.pop(0)
        if server in visited:
            continue
        visited.add(server)

        # Évite les serveurs locaux (localhost ou IP personnelle)
        if "localhost" in server or "127.0.0.1" in server:
            continue
        if own_ip and own_ip in server:
            continue

        print(f"\n🔄 Contact de {server} ...")
        try:
            # --- Étape 1 : récupération de la liste des topics ---
            resp = requests.get(f"{server}/ws/topics", timeout=6)
            resp.raise_for_status()
            topics = resp.json()

            # --- Étape 2 : fusion des contenus de chaque topic ---
            for t in topics:
                r2 = requests.get(f"{server}/ws/topic/{quote(t, safe='')}", timeout=6)
                r2.raise_for_status()
                remote_topic = {t: r2.json()}
                local_topics = merge_topics(local_topics, remote_topic)
                print(f"  ➕ fusion du topic '{t}' ({len(r2.json())} items)")

            # --- Étape 3 : récupération de l’annuaire distant ---
            try:
                ann = requests.get(f"{server}/ws/annuaire", timeout=6)
                ann.raise_for_status()
                remote_annuaire = ann.json()

                # Ajoute les nouveaux serveurs valides (hors localhost)
                for s in remote_annuaire:
                    if any(x in s for x in ["localhost", "127.0.0.1"]):
                        continue
                    if own_ip and own_ip in s:
                        continue
                    if s not in visited and s not in known_servers:
                        print(f" Nouveau serveur découvert : {s}")
                        newly_found.add(s)
                        known_servers.append(s)

            except Exception as e:
                print(f" Annuaire inaccessible sur {server}: {e}")

        except Exception as e:
            print(f"Erreur avec {server}: {e}")

    #-----------------------------------------------------------#
    # Étape finale : sauvegarde et affichage des résultats
    #-----------------------------------------------------------#
    if newly_found:
        data["annuaire"].extend(sorted(newly_found))
        print(f"\n {len(newly_found)} nouveaux serveurs ajoutés à l’annuaire.")

    data["topics"] = local_topics
    save_data(data)
    print("\n✅ Base locale mise à jour avec succès !")

#-----------------------------------------------------------#
# Exécution directe du module
#-----------------------------------------------------------#
if __name__ == "__main__":
    enrichir()
