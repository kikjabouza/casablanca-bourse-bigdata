# 📈 Bourse de Casablanca — Pipeline Big Data

> Projet académique — Module Big Data  
> Scraping quotidien des cotations boursières, orchestration, stockage distribué et reporting financier.
> Bourse de Casablanca
> Scraping quotidien des cotations de la Bourse de Casablanca avec BeautifulSoup.
> Orchestration Prefect, stockage haute disponibilité dans Cassandra, requêtage SQL fédéré avec Trino sur Cassandra, et reporting financier (volumes, performances sectorielles) sur Metabase.
> Technologies :

## Web scraping → Prefect → Cassandra → Trino → Metabase

## 👥 Équipe & Responsabilités

| Membre      | Rôle                                      | Dossier/Fichiers                                       |
| ----------- | ----------------------------------------- | ------------------------------------------------------ |
| **Khadija** | Scraping & Validation des données         | `src/scraper.py`, `src/validator.py`, `tests/`         |
| **Joyce**   | Infrastructure Docker, Cassandra, Prefect | `docker-compose.yml`, `flows/`, `cassandra/`, `trino/` |
| **Riad**    | Requêtes SQL & Dashboards Metabase        | `sql/queries.sql`, dashboard Metabase                  |

---

## 🏗️ Architecture du Pipeline

```
Site Bourse de Casablanca
        │
        ▼
  [Scraper Python]        ← Khadija  (BeautifulSoup + Pydantic)
  src/scraper.py
        │
        ▼
  [Prefect Flow]          ← Joyce    (Orchestration + scheduling 18h/jour)
  flows/daily_scrape.py
        │
        ▼
  [Cassandra]             ← Joyce    (Stockage haute disponibilité)
  keyspace: bourse
  table: cotations
        │
        ▼
  [Trino]                 ← Riad     (Moteur SQL fédéré sur Cassandra)
  sql/queries.sql
        │
        ▼
  [Metabase]              ← Riad     (Dashboard de reporting financier)
  http://localhost:3000
```

---

## Vue globale du pipeline

À la fin du projet, voici ce qui se passera chaque jour :
08:00 ou 18:00 (heure programmée)

       Prefect
          │
          ▼
     scraper.py
          │
          ▼

Récupération des cotations
│
▼
Validation / Nettoyage
│
▼
Insertion Cassandra
│
▼
Historisation
│
▼
Trino
│
▼
Requêtes SQL
│
▼
Metabase
│
▼
Dashboard

## 📁 Structure du Projet

```
casablanca-bourse-bigdata/
│
├── src/                          # Scraping & validation — Khadija
│   ├── scraper.py                #   Fonction scrape_cotations()
│   └── validator.py              #   Modèle Pydantic Cotation
│
├── flows/                        # Orchestration Prefect — Joyce
│   └── daily_scrape.py           #   Flow quotidien (déclenché à 18h)
│
├── cassandra/                    # Base de données — Joyce
│   └── init.cql                  #   Schéma keyspace + table cotations
│
├── trino/                        # Moteur SQL fédéré — Joyce
│   └── catalog/
│       └── cassandra.properties  #   Connecteur Trino → Cassandra
│
├── sql/                          # Requêtes KPIs — Riad
│   └── queries.sql               #   Top volumes, secteurs, évolutions...
│
├── docs/                         # Documentation & ressources
│   └── architecture.png          #   Schéma du pipeline (optionnel)
│
├── tests/                        # Tests unitaires — Khadija
│   └── test_scraper.py           #   Cas normaux, valeurs manquantes, timeout
│
├── docker-compose.yml            # Lance tous les services en une commande
├── requirements.txt              # Dépendances Python
├── .env.example                  # Modèle de variables d'environnement (à copier en .env)
├── .env                          # Variables locales — NE PAS committer (dans .gitignore)
├── .gitignore                    # Fichiers exclus du dépôt Git
└── README.md                     # Ce fichier
```

---

## 🚀 Lancer le Projet (démarrage rapide)

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré
- Python 3.11+

### 1. Cloner le dépôt

```bash
git clone https://github.com/kikjabouza/casablanca-bourse-bigdata.git
cd casablanca-bourse-bigdata
git checkout branch YOUR_BRANCH_NAME  # Khadija : khadija, Joyce : joyce, Riad : riad
```

### 2. Installer les dépendances Python

```bash
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Lancer tous les services Docker

```bash
docker-compose up -d
```

Vérifier que tout tourne :

```bash
docker-compose ps
```

| Service    | URL                   | Description          |
| ---------- | --------------------- | -------------------- |
| Prefect UI | http://localhost:4200 | Monitoring des flows |
| Trino UI   | http://localhost:8080 | Interface SQL        |
| Metabase   | http://localhost:3000 | Dashboards           |
| Cassandra  | localhost:9042        | Base de données      |

### 4. Initialiser le schéma Cassandra

```bash
docker exec -it cassandra cqlsh -f /cassandra/init.cql
```

### 5. Déclencher le scraping manuellement (pour tester)

```bash
python flows/daily_scrape.py
```

### 6. Vérifier les données dans Cassandra

```bash
docker exec -it cassandra cqlsh -e "SELECT COUNT(*) FROM bourse.cotations;"
```

---

## 🗃️ Schéma de la Base Cassandra

**Keyspace :** `bourse`  
**Table :** `cotations`

| Colonne          | Type   | Description                             |
| ---------------- | ------ | --------------------------------------- |
| `valeur`         | TEXT   | Nom de l'entreprise (clé de partition)  |
| `date_scrape`    | DATE   | Date de la cotation (clé de clustering) |
| `cours`          | DOUBLE | Cours de clôture (MAD)                  |
| `variation`      | DOUBLE | Variation journalière (%)               |
| `volume`         | BIGINT | Volume échangé                          |
| `capitalisation` | DOUBLE | Capitalisation boursière (MAD)          |
| `secteur`        | TEXT   | Secteur d'activité                      |

---

## 📊 KPIs Disponibles dans Metabase

1. **Top 10 valeurs** par volume du jour
2. **Performance sectorielle** — variation moyenne sur 30 jours
3. **Évolution d'une valeur** dans le temps (ex: Attijariwafa)
4. **Répartition haussiers / baissiers / stables** du jour

---

## 🔄 Workflow Git

Chaque membre travaille sur sa propre branche :

```bash
# Khadija
git checkout -b khadija/scraping

# Joyce
git checkout -b joyce/infrastructure

# Riad
git checkout -b riad/reporting
```

Pour merger sur `main` : créer une Pull Request sur GitHub, un autre membre relit avant de merger.

---

## ⚠️ Points d'attention

- Le scraping tourne **automatiquement à 18h** via Prefect (après la clôture de la bourse)
- Ne jamais committer le fichier `.env` (il contient des secrets) — utiliser `.env.example` comme modèle
- Si Metabase ne liste pas Trino nativement, utiliser le connecteur **Starburst** (compatible)

---

## 📚 Technologies utilisées

| Technologie      | Version | Rôle                       |
| ---------------- | ------- | -------------------------- |
| Python           | 3.11    | Langage principal          |
| BeautifulSoup4   | 4.12    | Parsing HTML               |
| Prefect          | 2.x     | Orchestration & scheduling |
| Apache Cassandra | 4.1     | Stockage distribué         |
| Trino            | latest  | Moteur SQL fédéré          |
| Metabase         | latest  | Reporting & dashboards     |
| Docker Compose   | v3      | Conteneurisation           |
