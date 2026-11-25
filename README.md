# Pythonpédia

**Mini encyclopédie distribuée sur le langage Python**
Projet de TP – Master 2 Data Science – Université d’Angers (2025–2026)

---

## Description du projet

**Pythonpédia** est une encyclopédie en ligne consacrée au **langage Python**, construite de manière **distribuée** entre plusieurs serveurs du réseau universitaire.

Chaque serveur héberge une partie de la base de connaissances sur Python :
- des **topics** représentant les grands thèmes du langage (ex. : types, fonctions, POO, multithreading) ;
- des **items** à l’intérieur de chaque topic (ex. : définition, exemple, tutoriel, bonne pratique, piège) ;
- et des **URLs** pointant vers des ressources externes fiables (documentation officielle, tutoriels, forums, etc.).

L’objectif est de créer une **encyclopédie collaborative sur Python**, où chaque serveur contribue à enrichir le savoir commun.
Chaque instance expose une **API REST publique** permettant de partager ses données, et peut se synchroniser automatiquement avec les autres serveurs connus.

---

## Structure du projet

```
pythonpedia/
├─ app.py                  # Service web Flask (API publique + admin)
├─ sync.py                 # Script de réplication automatique
├─ db.json                 # Base locale des topics + annuaire
├─ .env.example            # Modèle de configuration locale
├─ templates/
│   ├─ index.html          # Page d’accueil et documentation API
│   ├─ ui.html             # Interface interactive (topics + annuaire)
│   └─ documentation.html  # Documentation technique du projet
└─ static/
    ├─ style.css           # Feuille de style
    └─ style1.css
```

---

## Installation et lancement

### 1️- Prérequis

* Python 3.10+
* Bibliothèques : `flask`, `requests`, `python-dotenv`

### 2️- Installation

```bash
git clone https://github.com/ColettaM/Pythonpedia.git
cd Pythonpedia

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)

# Installer les dépendances
python -m pip install -r requirements.txt
```

### 3️- Fichier `.env`

Copie `.env.example` vers `.env`, puis renseigne une clé locale unique. Tu peux en générer une avec `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

```
ADMIN_TOKEN=VOTRE_TOKEN
```

La lecture des pages et de l’API fonctionne sans clé. La clé active les actions d’administration.

---

## Lancer le serveur

```bash
python app.py
```

> Le service est accessible à l’adresse :
> [http://localhost:8888/](http://localhost:8888/)

---

## Interface Web

| Page             | Description                                                            |
| ---------------- | ---------------------------------------------------------------------- |
| `/`              | Page d’accueil (présentation + documentation de l’API)                 |
| `/ui`            | Interface interactive pour naviguer dans les topics, items et serveurs |
| `/documentation` | Documentation technique du projet                                      |

---

##  API REST publique

### 🔹 Liste des topics

**GET `/ws/topics`**

```json
["types", "fonctions", "multithreading", "POO"]
```

### 🔹 Détails d’un topic

**GET `/ws/topic/<topic>`**

```json
{
  "exemple": ["https://realpython.com/..."],
  "définition": ["https://docs.python.org/..."]
}
```

### 🔹 Liste des serveurs connus

**GET `/ws/annuaire`**

```json
[
  "http://172.20.45.142:8888",
  "http://172.20.45.149:8888"
]
```

---

## Endpoints protégés (clé API requise)

Ces routes nécessitent un **header HTTP** :

```
X-API-Key: VOTRE_TOKEN
```

> (ou la valeur que tu as mise dans ton fichier `.env`)

### Ajouter un serveur à l’annuaire

**POST `/ws/annuaire`**

```bash
curl -X POST http://localhost:8888/ws/annuaire \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_TOKEN" \
  -d '{"url": "http://172.20.45.150:8888"}'
```

**Réponse :**

```json
{"ok": true, "annuaire": ["http://172.20.45.142:8888", "http://172.20.45.150:8888"]}
```

---

### Lancer la réplication manuelle

**POST `/admin/sync`**

Déclenche la fonction `sync.enrichir()` qui interroge les serveurs connus pour :

* Récupérer leurs topics et URLs
* Fusionner les données locales sans doublon
* Mettre à jour l’annuaire

```bash
curl -X POST http://localhost:8888/admin/sync \
  -H "X-API-Key: VOTRE_TOKEN"
```

**Réponse :**

```json
{"ok": true, "message": "Réplication terminée avec succès."}
```

---

## Réplication automatique (script `sync.py`)

Le script `sync.py` peut être exécuté manuellement :

```bash
python sync.py
```

Il :

1. Charge les serveurs connus depuis `db.json`.
2. Interroge chaque serveur `/ws/topics` et `/ws/topic/<topic>`.
3. Fusionne les données (sans doublon) dans la base locale.
4. Met à jour la liste des serveurs (`/ws/annuaire`).

Le même processus est déclenché par l’API `POST /admin/sync`.

---

## Sécurité

* Les actions sensibles sont protégées par un **token administrateur**.
* Le token est stocké **dans le fichier `.env`** (jamais en clair dans le code).
* L’interface `/ui` permet à l’administrateur d’entrer ce token pour accéder aux fonctions d’ajout et de réplication.

---

## Structure de la base (`db.json`)

Exemple :

```json
{
  "topics": {
    "fonctions": {
      "définition": ["https://docs.python.org/fr/3/tutorial/controlflow.html#defining-functions"],
      "exemple": ["https://realpython.com/defining-your-own-python-function/"],
      "bonne pratique": ["https://peps.python.org/pep-0008/"]
    },
    "POO": {
      "tuto": ["https://realpython.com/python3-object-oriented-programming/"],
      "exemple": ["https://docs.python.org/fr/3/tutorial/classes.html"]
    }
  },
  "annuaire": [
    "http://172.20.45.142:8888",
    "http://172.20.45.149:8888"
  ]
}
```

---

## Découverte de nouveaux serveurs

Les serveurs sont généralement découverts :

1. Par **propagation** (lors de la réplication : récupération des `/ws/annuaire` distants)
2. Ou manuellement (via l’interface `/ui` → “Ajouter un serveur”)
3. Optionnellement, en scannant un sous-réseau ou via mDNS (bonus)

---

## Auteur

**Coletta Moutsiha**
Master 2 – Data Science
Université d’Angers – Année 2025–2026

---
