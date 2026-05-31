## 📊 ÉTAT ACTUEL DE VOTRE PROJET

### ✅ Ce qui fonctionne parfaitement

| Composant                        | Statut          | Détails                                            |
| -------------------------------- | --------------- | -------------------------------------------------- |
| **Scraping détails instruments** | ✅ 100%         | Prix, variations, volumes pour MNG, BCP, ATW, etc. |
| **Scraping market overview**     | ✅ 100%         | MASI, MASI20, volume global, top 5 hausses/baisses |
| **Récupération des IDs**         | ✅ 100%         | Mapping ticker → ID pour tous les instruments      |
| **Tests unitaires (01-08)**      | ✅ 100%         | Tous les tests passent (sauf historique API)       |
| **Infrastructure Docker**        | ✅ Opérationnel | Cassandra, Trino, Metabase, Prefect tournent       |
| **Scripts de chargement**        | ✅ Fonctionnel  | `scripts/load_data.py` charge les détails          |
| **Fichiers JSON**                | ✅ Générés      | Données sauvegardées dans `tests/data/`            |

### ⚠️ Ce qui a des limitations

| Composant                   | Statut          | Cause                                                |
| --------------------------- | --------------- | ---------------------------------------------------- |
| **Données historiques**     | ❌ Bloqué       | API Bourse ferme la connexion (ConnectionResetError) |
| **Driver Cassandra Python** | ❌ Incompatible | Python 3.13 + cassandra-driver                       |
| **Prefect**                 | ⚠️ Partiel      | Installé mais conflit Pydantic                       |

### 🎯 Ce que vous avez comme données

```
✅ Données disponibles :
- Prix actuels de toutes les actions (détails)
- Variations quotidiennes
- Volumes échangés
- Capitalisations
- Top 5 hausses/baisses
- Indices MASI, MASI20, ESG
- Volume global du marché

❌ Données manquantes :
- Historique des prix (plusieurs années)
- Prix intraday (toutes les minutes)
```

---

## 🗺️ FEUILLE DE ROUTE POUR CONTINUER

### Phase 1 : Contourner l'API historique (Solution immédiate)

L'API historique bloque les connexions. Solution : scraper l'historique depuis les pages HTML des instruments.

```python
# scripts/fix_historical.py
"""
Script pour récupérer l'historique depuis le HTML (contournement API)
"""
import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_historical_from_html(ticker: str):
    """Scrape l'historique depuis le tableau HTML de la page instrument"""
    url = f"https://www.casablanca-bourse.com/fr/live-market/instruments/{ticker}"
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Chercher le tableau "Historique des cours et des volumes"
    # À implémenter avec BeautifulSoup

    return []

if __name__ == "__main__":
    data = scrape_historical_from_html("MNG")
    print(f"Récupéré {len(data)} jours")
```

### Phase 2 : Solution Cassandra (Alternative)

Puisque le driver Python est incompatible, utilisez **cqlsh** (CLI Cassandra) ou **Trino** comme pont.

#### Étape 2.1 : Créer les tables dans Cassandra via cqlsh

```bash
# Se connecter à Cassandra via Docker
docker exec -it cassandra cqlsh

# Exécuter les commandes suivantes
CREATE KEYSPACE IF NOT EXISTS bourse_data
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE bourse_data;

-- Table des instruments
CREATE TABLE IF NOT EXISTS instruments_static (
    ticker text PRIMARY KEY,
    isin text,
    sector text,
    listing_date date,
    shares_count bigint,
    nominal_value decimal,
    trading_cycle text,
    currency text,
    updated_at timestamp
);

-- Table des prix quotidiens
CREATE TABLE IF NOT EXISTS daily_prices (
    ticker text,
    date date,
    open_price decimal,
    high_price decimal,
    low_price decimal,
    close_price decimal,
    volume decimal,
    quantity int,
    trades_count int,
    market_cap decimal,
    variation decimal,
    var_ytd decimal,
    scraped_at timestamp,
    PRIMARY KEY (ticker, date)
);

-- Table des indices
CREATE TABLE IF NOT EXISTS daily_indices (
    index_name text,
    date date,
    value decimal,
    variation decimal,
    annual_variation decimal,
    updated_at timestamp,
    PRIMARY KEY (index_name, date)
);

-- Table des stats marché
CREATE TABLE IF NOT EXISTS market_stats (
    date date PRIMARY KEY,
    global_volume decimal,
    market_cap decimal,
    updated_at timestamp
);

-- Table des top movers
CREATE TABLE IF NOT EXISTS top_movers (
    date date,
    direction text,
    rank int,
    ticker text,
    company_name text,
    price decimal,
    variation decimal,
    updated_at timestamp,
    PRIMARY KEY (date, direction, rank)
);

-- Quitter cqlsh
exit;
```

#### Étape 2.2 : Insérer les données JSON dans Cassandra (via cqlsh)

```bash
# Script d'insertion depuis les fichiers JSON
# scripts/insert_to_cassandra.cql
```

### Phase 3 : Configurer Trino

#### Étape 3.1 : Vérifier le connecteur Cassandra

```bash
# Vérifier que Trino voit Cassandra
docker exec -it trino trino --execute "SHOW CATALOGS;"
# Doit afficher "cassandra"

# Tester la connexion
docker exec -it trino trino --catalog cassandra --execute "SHOW SCHEMAS;"
```

#### Étape 3.2 : Créer un fichier de propriétés si nécessaire

```bash
# Si le catalogue n'existe pas, le créer
docker exec -it trino bash
cat > /etc/trino/catalog/cassandra.properties << EOF
connector.name=cassandra
cassandra.contact-points=cassandra
cassandra.port=9042
cassandra.load-policy.dc-aware.local-dc=datacenter1
EOF
exit

# Redémarrer Trino
docker restart trino
```

### Phase 4 : Configurer Metabase

#### Étape 4.1 : Accéder à Metabase

```bash
# Ouvrir dans le navigateur
http://localhost:3000
```

#### Étape 4.2 : Configuration initiale

1. Créer un compte admin (email: admin@example.com, password: admin123)
2. Ajouter une base de données :
   - Type: **Trino** (ou **Starburst** si Trino n'apparaît pas)
   - Host: `trino`
   - Port: `8080`
   - Catalog: `cassandra`
   - Schema: `bourse_data`
   - Username: `trino` (ou laisser vide)
   - Cliquer sur **Save**

#### Étape 4.3 : Créer des dashboards

```sql
-- Dashboard 1: Vue Marché (à exécuter dans Metabase)
SELECT
    date,
    global_volume as "Volume Global (MAD)",
    market_cap as "Capitalisation (MAD)"
FROM market_stats
ORDER BY date DESC
LIMIT 1;

-- Dashboard 2: Top Performances
SELECT
    ticker as "Action",
    company_name as "Société",
    price as "Prix (MAD)",
    variation as "Variation %"
FROM top_movers
WHERE date = (SELECT MAX(date) FROM top_movers)
  AND direction = 'up'
ORDER BY rank;

-- Dashboard 3: Indices
SELECT
    index_name as "Indice",
    value as "Valeur",
    variation as "Var. %"
FROM daily_indices
WHERE date = (SELECT MAX(date) FROM daily_indices);
```

### Phase 5 : Orchestration avec Prefect (Alternative)

Puisque Prefect a des conflits, utilisez **cron** ou **Task Scheduler** pour l'instant.

#### Étape 5.1 : Script de mise à jour quotidienne

```python
# scripts/daily_update.py
"""
Script pour mise à jour quotidienne (à exécuter via cron)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.utils.logger import setup_logger
import time

setup_logger()

def daily_update():
    """Met à jour les données quotidiennes"""
    print("🔄 Démarrage mise à jour quotidienne...")

    # 1. Mettre à jour le market overview
    print("📊 Mise à jour market overview...")
    overview = MarketOverviewScraper().scrape_market_overview()

    # 2. Mettre à jour les détails des instruments
    print("📈 Mise à jour des instruments...")
    tickers = ['MNG', 'BCP', 'ATW', 'IAM', 'AGM']  # À étendre

    for ticker in tickers:
        print(f"  - {ticker}...")
        InstrumentDetailsScraper().scrape_instrument(ticker)
        time.sleep(1)

    print("✅ Mise à jour terminée")

if __name__ == "__main__":
    daily_update()
```

#### Étape 5.2 : Planification avec cron (Linux/Mac) ou Task Scheduler (Windows)

**Windows Task Scheduler** :

```powershell
# Créer une tâche planifiée
schtasks /create /tn "BourseDailyUpdate" /tr "python C:\...\scripts\daily_update.py" /sc daily /st 17:00
```

### Phase 6 : Solution de replis pour l'historique

Si l'API historique reste bloquée, utilisez une source alternative :

#### Option A : Yahoo Finance (API gratuite)

```python
import yfinance as yf

def get_historical_from_yahoo(ticker: str):
    """Récupère l'historique depuis Yahoo Finance"""
    # Mapper ticker Bourse de Casablanca → Yahoo ticker
    yahoo_map = {'MNG': 'MNG.CA', 'BCP': 'BCP.CA'}
    yahoo_ticker = yahoo_map.get(ticker, f"{ticker}.CA")
    data = yf.download(yahoo_ticker, period="5y")
    return data
```

#### Option B : Fichiers CSV pré-téléchargés

- Télécharger manuellement l'historique depuis le site
- Les convertir en CSV
- Les importer dans Cassandra

---

## 📋 CHECKLIST DES PROCHAINES ACTIONS

### Action immédiate (aujourd'hui)

- [ ] Lancer `python scripts/load_data.py --all` pour charger TOUS les détails
- [ ] Vérifier que tous les fichiers JSON sont générés
- [ ] Accéder à Metabase (http://localhost:3000)
- [ ] Créer les premières visualisations

### Action à court terme (cette semaine)

- [ ] Créer les tables Cassandra via `docker exec -it cassandra cqlsh`
- [ ] Configurer Trino pour voir Cassandra
- [ ] Connecter Metabase à Trino
- [ ] Créer 3-4 dashboards

### Action à moyen terme (prochaine semaine)

- [ ] Configurer la mise à jour quotidienne (cron/Task Scheduler)
- [ ] Résoudre le problème de l'API historique (contournement HTML)
- [ ] Ajouter les données historiques

### Action à long terme

- [ ] Migrer vers Prefect (quand compatible Python 3.13)
- [ ] Automatiser complètement le pipeline
- [ ] Ajouter des alertes (variations anormales)

---

## 🚀 COMMANDE À LANCER MAINTENANT

```powershell
# 1. Charger tous les instruments (détails seulement)
python scripts/load_data.py --all

# 2. Vérifier les résultats
python -c "
import json
from pathlib import Path
data_dir = Path('tests/data')
json_files = list(data_dir.glob('*_details.json'))
print(f'✅ {len(json_files)} instruments chargés')
for f in json_files[:5]:
    with open(f) as fp:
        data = json.load(fp)
        print(f'   - {data.get(\"ticker\")}: {data.get(\"current_price\")} MAD')
"

# 3. Ouvrir Metabase
start http://localhost:3000
```

**Voulez-vous lancer `python scripts/load_data.py --all` maintenant ?**
