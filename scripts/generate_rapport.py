"""
Génère le rapport d'atelier complet en .docx.
Usage: py -3.13 scripts/generate_rapport.py
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ── Styles de page ───────────────────────────────────────────────────────────
section = doc.sections[0]
section.page_width  = Cm(21)
section.page_height = Cm(29.7)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.0)

# ── Helpers ──────────────────────────────────────────────────────────────────
NAVY  = RGBColor(0x1B, 0x2A, 0x4A)
TEAL  = RGBColor(0x2E, 0x86, 0xAB)
GOLD  = RGBColor(0xE8, 0xB8, 0x4B)
GRAY  = RGBColor(0x55, 0x55, 0x55)
BLACK = RGBColor(0x22, 0x22, 0x22)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xE8, 0xF4, 0xF8)

def set_cell_bg(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = NAVY
    # Bordure inférieure
    pPr = p._p.get_or_add_pPr()
    pb = OxmlElement('w:pBdr')
    bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single')
    bot.set(qn('w:sz'), '6')
    bot.set(qn('w:space'), '1')
    bot.set(qn('w:color'), '2E86AB')
    pb.append(bot)
    pPr.append(pb)
    return p

def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = TEAL
    return p

def h3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = NAVY
    return p

def body(text, bold=False, italic=False, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.size = Pt(11)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.3 + level * 0.25)
    run = p.add_run(text)
    run.font.size = Pt(11)
    return p

def code_block(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Inches(0.4)
    shading = OxmlElement('w:shd')
    shading.set(qn('w:val'), 'clear')
    shading.set(qn('w:color'), 'auto')
    shading.set(qn('w:fill'), 'E8F4F8')
    p._p.get_or_add_pPr().append(shading)
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0x1B, 0x2A, 0x4A)
    return p

def info_box(text, color_hex='E8F4F8', border_hex='2E86AB'):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.right_indent = Inches(0.3)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    shading = OxmlElement('w:shd')
    shading.set(qn('w:val'), 'clear')
    shading.set(qn('w:color'), 'auto')
    shading.set(qn('w:fill'), color_hex)
    p._p.get_or_add_pPr().append(shading)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.color.rgb = NAVY
    return p

def simple_table(headers, rows, col_widths=None):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    # En-tête
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        set_cell_bg(cell, '1B2A4A')
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = WHITE
        run.font.size = Pt(10.5)
    # Lignes
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i+1].cells[j]
            if i % 2 == 0:
                set_cell_bg(cell, 'E8F4F8')
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(10)
    if col_widths:
        for row in t.rows:
            for j, w in enumerate(col_widths):
                row.cells[j].width = Inches(w)
    doc.add_paragraph()
    return t

def page_break():
    doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════════
# PAGE DE TITRE
# ════════════════════════════════════════════════════════════════════════════════
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(60)
run = p.add_run("RAPPORT D'ATELIER BIG DATA")
run.bold = True
run.font.size = Pt(24)
run.font.color.rgb = NAVY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Pipeline de Collecte, Stockage et Visualisation")
run.font.size = Pt(18)
run.font.color.rgb = TEAL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Bourse de Casablanca (BVC)")
run.bold = True
run.font.size = Pt(16)
run.font.color.rgb = NAVY

doc.add_paragraph()

# Tableau infos groupe
t = doc.add_table(rows=7, cols=2)
t.style = 'Table Grid'
t.alignment = WD_TABLE_ALIGNMENT.CENTER
infos_page_titre = [
    ("Établissement",    "_________________________________"),
    ("Filière / Niveau", "_________________________________"),
    ("Groupe",          "_________________________________"),
    ("Membres",         "_________________________________\n_________________________________\n_________________________________"),
    ("Encadrant(e)",    "_________________________________"),
    ("Année académique","2025 – 2026"),
    ("Lien GitHub",     "_________________________________"),
]
for i, (k, v) in enumerate(infos_page_titre):
    set_cell_bg(t.rows[i].cells[0], 'E8F4F8')
    rk = t.rows[i].cells[0].paragraphs[0].add_run(k)
    rk.bold = True
    rk.font.size = Pt(11)
    rk.font.color.rgb = NAVY
    rv = t.rows[i].cells[1].paragraphs[0].add_run(v)
    rv.font.size = Pt(11)

for row in t.rows:
    row.cells[0].width = Inches(2.5)
    row.cells[1].width = Inches(10.0)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# TABLE DES MATIÈRES (manuelle)
# ════════════════════════════════════════════════════════════════════════════════
h1("Table des matières")
toc = [
    ("1.", "Introduction et contexte du projet", "3"),
    ("2.", "Architecture globale du pipeline", "4"),
    ("3.", "Phase 1 — Exploration du site BVC et des APIs", "5"),
    ("4.", "Phase 2 — Scrapers Python", "6"),
    ("5.", "Phase 3 — Tests unitaires", "8"),
    ("6.", "Phase 4 — Infrastructure Docker", "9"),
    ("7.", "Configuration Cassandra", "11"),
    ("8.", "Configuration Trino (moteur SQL)", "12"),
    ("9.", "Orchestration avec Prefect", "14"),
    ("10.", "Dashboard Metabase", "15"),
    ("11.", "Pipeline de synchronisation automatique", "17"),
    ("12.", "Configurations critiques et bugs résolus", "18"),
    ("13.", "Guide de reproduction (pas à pas)", "20"),
    ("14.", "Résultats et bilan", "22"),
]
for num, title, pg in toc:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(f"{num}  {title}")
    r1.font.size = Pt(11)
    r2 = p.add_run(f"  {'.' * (60 - len(num) - len(title))}  {pg}")
    r2.font.size = Pt(11)
    r2.font.color.rgb = GRAY

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 1. INTRODUCTION
# ════════════════════════════════════════════════════════════════════════════════
h1("1. Introduction et contexte du projet")

body(
    "Ce rapport documente la réalisation d'un pipeline Big Data complet dédié à la Bourse de "
    "Casablanca (BVC). L'objectif est de collecter automatiquement les données boursières "
    "publiques, de les stocker dans une base NoSQL, de les interroger via un moteur SQL distribué "
    "et de les visualiser dans un tableau de bord interactif en temps quasi-réel."
)

h2("Objectifs")
bullets_obj = [
    "Scraper automatiquement les instruments cotés, les cours de séance, les indices MASI/MASI20 et les top movers",
    "Stocker les données dans Apache Cassandra avec un schéma optimisé pour les time series",
    "Exposer les données via Trino (SQL distribué) sans duplication",
    "Orchestrer les flows de collecte avec Prefect (scheduling, retry, monitoring)",
    "Visualiser en temps réel dans un dashboard Metabase avec refresh toutes les 2 minutes",
    "Containeriser l'ensemble avec Docker Compose pour une reproductibilité complète",
]
for b in bullets_obj:
    bullet(b)

h2("Stack technique retenue")
simple_table(
    ["Composant", "Outil", "Version", "Rôle"],
    [
        ["Scraping", "Python + requests + BeautifulSoup4", "3.11 / 4.12", "Collecte données BVC"],
        ["Stockage", "Apache Cassandra", "4.1", "Base NoSQL time series"],
        ["Requêtes SQL", "Trino", "426", "Moteur SQL sur Cassandra"],
        ["Orchestration", "Prefect", "2.19.3", "Scheduling et monitoring flows"],
        ["Visualisation", "Metabase", "0.50.4", "Dashboard BI interactif"],
        ["Containerisation", "Docker Compose", "3.x", "Déploiement reproductible"],
    ],
    [2.5, 4.0, 1.5, 4.5]
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 2. ARCHITECTURE GLOBALE
# ════════════════════════════════════════════════════════════════════════════════
h1("2. Architecture globale du pipeline")

body(
    "Le pipeline suit un flux unidirectionnel depuis la source de données publique (BVC) "
    "jusqu'au tableau de bord Metabase. Chaque composant a un rôle clairement délimité "
    "et communique via des interfaces standardisées (CQL, JDBC, HTTP)."
)

h2("Flux de données")
code_block(
    "BVC Website (casablanca-bourse.com)\n"
    "   │\n"
    "   │  HTTP/HTTPS scraping (toutes les 2 min)\n"
    "   ▼\n"
    "scraper-worker [Docker]\n"
    "   ├── market_overview_flow  → daily_indices, market_stats, top_movers, intraday_indices\n"
    "   └── details_flow          → daily_prices, instruments_static (ATW, BCP, MNG)\n"
    "   │\n"
    "   │  CQL INSERT (cassandra-driver Python)\n"
    "   ▼\n"
    "Cassandra [Docker]  ← 8 tables, keyspace bourse_data\n"
    "   │\n"
    "   │  Lecture live à chaque requête (pas de cache)\n"
    "   ▼\n"
    "Trino [Docker]  ← connecteur Cassandra, port 8443 HTTPS\n"
    "   │\n"
    "   │  JDBC over SSL\n"
    "   ▼\n"
    "Metabase [Docker]  ← Dashboard, refresh auto 2 min\n"
    "   │\n"
    "   ▼\n"
    "Navigateur — Tableau de bord 'Marché Boursier Casablanca'"
)

h2("Principe de synchronisation")
body(
    "Un point central de l'architecture : Trino ne copie pas les données de Cassandra. "
    "Il agit comme une couche de traduction SQL → CQL. Chaque requête Metabase déclenche "
    "une lecture directe dans Cassandra via Trino. Cela garantit que les données affichées "
    "sont toujours à jour, sans mécanisme de synchronisation supplémentaire."
)
info_box(
    "⚡ Cassandra → Trino : aucune synchronisation à gérer. "
    "Trino lit en direct à chaque requête SQL envoyée par Metabase."
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 3. EXPLORATION DU SITE BVC ET APIs
# ════════════════════════════════════════════════════════════════════════════════
h1("3. Phase 1 — Exploration du site BVC et des APIs")

body(
    "Avant d'écrire le moindre scraper, il a été nécessaire d'analyser la structure "
    "du site casablanca-bourse.com pour identifier les sources de données disponibles, "
    "les formats utilisés et les contraintes techniques (authentification, rate limiting, SSL)."
)

h2("Sources identifiées")

h3("Pages HTML publiques")
bullet("/fr/live-market/overview — indices (MASI, MASI20, MASI_ESG), statistiques globales, top movers")
bullet("/fr/live-market/instruments/{ticker} — fiche complète d'un instrument (cours, infos statiques)")
bullet("/fr/live-market/indices/{slug} — valeur courante d'un indice")
body("Parsées avec BeautifulSoup4 en ciblant des classes CSS spécifiques (bg-gray-800, text-success-500, etc.).")

h3("APIs JSON (Next.js + Drupal)")
bullet("/api/proxy/fr/api/bourse_data/instrument — liste paginée de tous les instruments (page[limit], page[offset])")
bullet("/api/proxy/fr/api/bourse_data/market_watch — top movers avec paramètres de filtre")
bullet("/api/proxy/fr/api/bourse_data/instrument_history — historique OHLC par ticker et plage de dates")
bullet("/_next/data/{BUILD_ID}/fr/live-market/overview.json — données widget (volumes, capitalisations)")

h2("Contraintes techniques")
simple_table(
    ["Contrainte", "Observation", "Solution"],
    [
        ["SSL", "Certificat BVC non reconnu", "verify=False + urllib3.disable_warnings"],
        ["Headers", "Refus sans User-Agent navigateur", "Headers Chrome + Accept-Language fr-FR"],
        ["Pagination", "API limitée à 250 résultats/page", "Boucle offset incrémental jusqu'à liste vide"],
        ["Rate limiting", "Pas de limitation détectée", "Pause REQUEST_DELAY=0.5s par sécurité"],
        ["Format dates", "DD/MM/YYYY dans listing_date", "datetime.strptime avec fallback multi-formats"],
        ["BUILD_ID Next.js", "ID changeant périodiquement", "Variable NEXT_BUILD_ID dans .env"],
    ],
    [2.5, 4.5, 5.5]
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 4. SCRAPERS PYTHON
# ════════════════════════════════════════════════════════════════════════════════
h1("4. Phase 2 — Scrapers Python")

body(
    "Quatre scrapers ont été développés, chacun ciblant un type de données. "
    "Tous suivent le même patron : requête HTTP → parsing → sauvegarde Cassandra (no-op si mode stub)."
)

h2("4.1 InstrumentsListScraper")
body("Fichier : src/scrapers/instruments_list_scraper.py")
bullet("Scrape la liste complète des instruments cotés à la BVC")
bullet("Stratégie : appel API JSON en premier (_scrape_from_api), fallback HTML si l'API échoue")
bullet("Pagination : loop sur offset jusqu'à retour liste vide")
bullet("Tables Cassandra alimentées : instruments (ticker, name, url)")

h2("4.2 InstrumentDetailsScraper")
body("Fichier : src/scrapers/instrument_details_scraper.py")
bullet("Scrape la fiche complète d'un instrument donné (par ticker)")
bullet("Parsing HTML via HTMLParser : informations statiques (ISIN, secteur, date cotation) + données de séance (OHLC, volume, variation)")
bullet("Gestion du format de date listing_date : DD/MM/YYYY → objet date Python (multi-format)")
bullet("Tables Cassandra alimentées : instruments_static, daily_prices")
info_box("Note : instruments_static n'a PAS de colonne company_name. Le nom de la société est dans la table instruments (colonne name).")

h2("4.3 MarketOverviewScraper")
body("Fichier : src/scrapers/market_overview_scraper.py")
bullet("Cœur du pipeline temps réel — exécuté toutes les 2 minutes")
bullet("Extrait : indices MASI/MASI20/MASI_ESG, volume global, capitalisation, top 5 hausses, top 5 baisses")
bullet("Double source : HTML principal + widget API JSON (fallback si HTML incomplet)")
bullet("Sauvegarde un snapshot intraday horodaté (HH:MM) pour la courbe temps réel")
bullet("Tables Cassandra alimentées : daily_indices, market_stats, top_movers, intraday_indices")

h2("4.4 HistoricalDataScraper")
body("Fichier : src/scrapers/historical_data_scraper.py")
bullet("Scrape l'historique OHLC via l'API JSON /instrument_history")
bullet("Paramètres : ticker, start_date, end_date (format YYYY-MM-DD)")
bullet("Calcule adjusted_close avec le ratio ajustement (splits/dividendes)")
bullet("Table Cassandra alimentée : historical_prices")

h2("CassandraClient — Client dual-mode")
body("Fichier : src/storage/cassandra_client.py")
body(
    "Le client Cassandra supporte deux modes via la variable CASSANDRA_STUB :"
)
code_block(
    "CASSANDRA_STUB=true  → mode stub : tous les INSERT sont des no-ops (pour les tests)\n"
    "CASSANDRA_STUB=false → connexion réelle à Cassandra (pour la production)\n\n"
    "Si cassandra-driver n'est pas installé (Python 3.13), bascule automatiquement en stub."
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 5. TESTS UNITAIRES
# ════════════════════════════════════════════════════════════════════════════════
h1("5. Phase 3 — Tests unitaires")

body(
    "Les tests vérifient le bon fonctionnement des scrapers sans nécessiter "
    "de Cassandra ni de Docker. Ils s'exécutent en mode stub Cassandra."
)

h2("Stratégie de test")
bullet("CASSANDRA_STUB=true : aucune écriture en base, tests purement fonctionnels")
bullet("Tests contre le vrai site BVC : les données réelles sont récupérées et validées")
bullet("Résultats sauvegardés en JSON dans tests/data/ pour inspection manuelle")

h2("Fichiers de test")
simple_table(
    ["Fichier", "Ce qui est testé"],
    [
        ["test_instruments_list.py", "Liste non vide · ticker alphanumérique · URL valide · > 50 instruments"],
        ["test_instrument_details.py", "Cours > 0 · variation dans [-30%, +30%] · date = aujourd'hui"],
        ["test_market_overview.py", "MASI présent · value > 0 · top_gainers ≥ 1 entrée"],
        ["test_historical_data.py", "OHLC cohérent (low ≤ open ≤ close ≤ high) · dates triées"],
    ],
    [4.0, 8.5]
)

h2("Lancement des tests")
code_block(
    "# Activer l'environnement Python 3.11\n"
    ".\\venv\\Scripts\\Activate.ps1\n\n"
    "# Tous les tests avec rapport détaillé\n"
    "pytest tests/ -v\n\n"
    "# Test de scraping manuel avec export JSON\n"
    "python tests/run_all_tests.py --overview    # market overview\n"
    "python tests/run_all_tests.py --details     # détails ATW\n"
    "python tests/run_all_tests.py --historical  # historique 30j ATW"
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 6. INFRASTRUCTURE DOCKER
# ════════════════════════════════════════════════════════════════════════════════
h1("6. Phase 4 — Infrastructure Docker")

body(
    "L'ensemble du projet tourne dans 5 conteneurs Docker orchestrés par docker-compose. "
    "Un sixième conteneur (cassandra-init) s'exécute une seule fois au démarrage pour initialiser le schéma."
)

h2("Conteneurs et leurs rôles")
simple_table(
    ["Conteneur", "Image", "Port(s)", "Rôle", "Persistance"],
    [
        ["cassandra", "cassandra:4.1", "9042", "Base NoSQL, keyspace bourse_data", "Volume cassandra-data"],
        ["cassandra-init", "cassandra:4.1", "—", "Init schéma CQL (one-shot)", "Aucune"],
        ["trino", "trinodb/trino:426", "8080/8443", "Moteur SQL, connecteur Cassandra", "Aucune"],
        ["prefect-server", "prefecthq/prefect:2.19.3-python3.11", "4200", "UI + API Prefect", "Volume prefect-data"],
        ["scraper-worker", "Dockerfile.worker (python:3.11)", "—", "Prefect serve() + scraping", "Mount projet"],
        ["metabase", "metabase/metabase:v0.50.4", "3000", "Dashboard BI", "Volume metabase-data"],
    ],
    [2.5, 3.5, 1.5, 3.5, 2.0]
)

h2("Dépendances entre services")
code_block(
    "cassandra         ← aucune dépendance\n"
    "cassandra-init    ← attend cassandra (healthy)\n"
    "trino             ← attend cassandra (healthy)\n"
    "prefect-server    ← aucune dépendance\n"
    "scraper-worker    ← attend cassandra (healthy) + prefect-server (started)\n"
    "metabase          ← attend trino (healthy)"
)

h2("Point critique : CASSANDRA_HOST")
info_box(
    "Dans Docker, chaque conteneur a son propre réseau interne. "
    "Le hostname 'localhost' dans un conteneur = l'intérieur de ce conteneur, PAS le PC hôte. "
    "Le scraper-worker doit donc utiliser CASSANDRA_HOST=cassandra (nom du service Docker). "
    "Cette variable est injectée via docker-compose environment, sans modifier le fichier .env "
    "utilisé par les scripts Python lancés directement sur le PC."
)

h2("Commandes de gestion")
code_block(
    "# Construire l'image du worker (première fois ou après modification)\n"
    "docker-compose build scraper-worker\n\n"
    "# Démarrer toute la stack\n"
    "docker-compose up -d\n\n"
    "# Vérifier l'état\n"
    "docker-compose ps\n\n"
    "# Logs en direct d'un service\n"
    "docker logs scraper-worker --follow\n\n"
    "# Arrêter sans supprimer les données\n"
    "docker-compose down\n\n"
    "# Arrêter ET supprimer les données (ATTENTION)\n"
    "docker-compose down -v"
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 7. CASSANDRA
# ════════════════════════════════════════════════════════════════════════════════
h1("7. Configuration Cassandra")

h2("Schéma des données (8 tables)")
body("Fichier : cassandra/init.cql — exécuté automatiquement par cassandra-init au premier démarrage.")

tables_cass = [
    ("instruments", "ticker (PK)", "name, url, updated_at", "Liste de tous les cotés BVC"),
    ("instruments_static", "ticker (PK)", "isin, sector, listing_date, shares_count, nominal_value, trading_cycle, currency", "Données statiques"),
    ("daily_prices", "ticker + date (PK)", "open/high/low/close, volume, quantity, trades_count, market_cap, variation, var_ytd", "Prix de séance"),
    ("historical_prices", "ticker + date (PK)", "OHLC, volume, adjusted_close, ratio", "Historique OHLC ajusté"),
    ("daily_indices", "index_name + date (PK)", "value, variation, annual_variation", "MASI / MASI20 / MASI_ESG"),
    ("market_stats", "date (PK)", "global_volume, market_cap", "Totaux du marché"),
    ("top_movers", "date + direction + rank (PK)", "ticker, company_name, price, variation", "Top 5 hausses/baisses"),
    ("intraday_indices", "index_name + date + timestamp (PK)", "value, scraped_at", "Snapshots 2 min"),
]
simple_table(
    ["Table", "Clé primaire", "Colonnes", "Usage"],
    tables_cass,
    [2.8, 2.8, 4.5, 3.0]
)

h2("Vérification manuelle")
code_block(
    "docker exec -it cassandra cqlsh\n\n"
    "USE bourse_data;\n"
    "DESCRIBE TABLES;\n"
    "SELECT COUNT(*) FROM instruments;\n"
    "SELECT COUNT(*) FROM daily_prices;\n"
    "SELECT * FROM daily_indices WHERE index_name='MASI' LIMIT 5;\n"
    "SELECT * FROM intraday_indices LIMIT 10;"
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 8. TRINO
# ════════════════════════════════════════════════════════════════════════════════
h1("8. Configuration Trino (moteur SQL)")

body(
    "Trino est un moteur de requêtes SQL distribué. Il ne stocke aucune donnée : "
    "il traduit les requêtes SQL reçues de Metabase en opérations CQL Cassandra, "
    "lit les résultats, les formate et les renvoie. Chaque requête Metabase déclenche "
    "une lecture fraîche dans Cassandra."
)

h2("Fichiers de configuration")

h3("trino/etc/config.properties")
code_block(
    "coordinator=true\n"
    "node-scheduler.include-coordinator=true\n"
    "http-server.http.port=8080\n"
    "discovery.uri=http://localhost:8080\n"
    "http-server.authentication.type=PASSWORD\n"
    "http-server.authentication.allow-insecure-over-http=true\n"
    "http-server.https.enabled=true\n"
    "http-server.https.port=8443\n"
    "http-server.https.keystore.path=/etc/trino/trino.jks\n"
    "http-server.https.keystore.key=trino123\n"
    "internal-communication.shared-secret=<base64>\n"
    "protocol.v1.alternate-header-name=Presto"
)

h3("trino/catalog/cassandra.properties")
code_block(
    "connector.name=cassandra\n"
    "cassandra.contact-points=cassandra\n"
    "cassandra.native-protocol-port=9042\n"
    "cassandra.load-policy.use-dc-aware=true\n"
    "cassandra.load-policy.dc-aware.local-dc=datacenter1"
)

h2("Problèmes résolus — Trino")
simple_table(
    ["Problème", "Cause", "Solution"],
    [
        ["Trino crash au démarrage", "cassandra.load-policy.use-datacenter invalide en Trino 426", "Remplacer par use-dc-aware=true + dc-aware.local-dc=datacenter1"],
        ["Unauthorized (Metabase)", "shared-secret manquant avec auth PASSWORD", "Ajouter internal-communication.shared-secret=<base64>"],
        ["Prepared statement not found", "Driver Presto envoie X-Presto-* mais Trino 426 attend X-Trino-*", "protocol.v1.alternate-header-name=Presto"],
        ["SSL truststore rejeté", "Certificat auto-signé non reconnu par le driver JDBC", "SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit"],
    ],
    [3.5, 5.0, 4.0]
)

h2("Certificat SSL (JKS)")
body(
    "Trino utilise un certificat auto-signé (trino.jks). Ce certificat a été importé "
    "dans un truststore Java (/tmp/ts.jks) dans le conteneur Metabase. Metabase utilise "
    "ce truststore via les Additional JDBC Options pour valider la connexion SSL."
)
code_block(
    "# Dans le conteneur Metabase — commande d'import :\n"
    "keytool -import -alias trino -file /tmp/trino.crt -keystore /tmp/ts.jks \\\n"
    "        -storepass changeit -noprompt\n\n"
    "# JDBC Options dans Metabase :\n"
    "SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit"
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 9. PREFECT
# ════════════════════════════════════════════════════════════════════════════════
h1("9. Orchestration avec Prefect")

body(
    "Prefect 2.x est la couche d'orchestration du pipeline. Il gère le scheduling, "
    "l'exécution, le retry automatique et le monitoring des flows de scraping."
)

h2("Composants Prefect")
bullet("prefect-server (Docker, port 4200) : API REST + interface web. Stocke l'historique des runs dans SQLite. NE réalise pas l'exécution des flows — il planifie uniquement.")
bullet("scraper-worker (Docker) : lance prefect serve() qui enregistre les deployments ET exécute les flows selon leur schedule. Pas de worker séparé nécessaire avec serve().")

h2("Flows déployés")
simple_table(
    ["Flow", "Fichier", "Schedule", "Tables alimentées"],
    [
        ["market_overview_flow", "flows/market_overview_flow.py", "Toutes les 2 minutes", "daily_indices, market_stats, top_movers, intraday_indices"],
        ["details_flow", "flows/details_flow.py", "Toutes les 15 minutes", "daily_prices, instruments_static"],
        ["instruments_flow", "flows/instruments_flow.py", "Lun–Ven 18h00", "instruments"],
        ["historical_daily_flow", "flows/historical_flow.py", "Lun–Ven 19h00", "historical_prices"],
    ],
    [3.2, 4.0, 2.5, 4.0]
)

h2("scripts/serve_flows.py — Point d'entrée du worker")
code_block(
    "from prefect import serve\n"
    "from flows.market_overview_flow import market_overview_flow\n"
    "from flows.details_flow import details_flow\n\n"
    "market_deployment = market_overview_flow.to_deployment(\n"
    "    name='market-overview-2min',\n"
    "    interval=timedelta(minutes=2),\n"
    ")\n"
    "details_deployment = details_flow.to_deployment(\n"
    "    name='details-15min',\n"
    "    interval=timedelta(minutes=15),\n"
    ")\n"
    "serve(market_deployment, details_deployment)"
)

h2("Interface Prefect")
bullet("URL : http://localhost:4200")
bullet("Deployments : voir les 2 flows enregistrés et leur schedule")
bullet("Flow Runs : historique de chaque exécution avec statut (succès/échec) et logs")
bullet("Déclencher manuellement : cliquer sur un deployment → 'Run' → 'Quick Run'")

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 10. METABASE
# ════════════════════════════════════════════════════════════════════════════════
h1("10. Dashboard Metabase")

body(
    "Metabase est l'outil de visualisation Business Intelligence. Il se connecte à Trino "
    "via JDBC et envoie des requêtes SQL standard pour chaque carte du dashboard."
)

h2("Configuration de la connexion")
simple_table(
    ["Champ Metabase", "Valeur"],
    [
        ["Type de base de données", "Presto (driver JDBC Facebook)"],
        ["Afficher le nom", "Bourse Casablanca"],
        ["Hôte", "trino"],
        ["Port", "8443"],
        ["Catalog", "cassandra"],
        ["Schema", "bourse_data"],
        ["Nom d'utilisateur", "admin"],
        ["Mot de passe", "trino123"],
        ["SSL", "✅ Coché"],
        ["Additional JDBC options", "SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit"],
    ],
    [5.0, 9.0]
)

h2("12 requêtes du dashboard")
simple_table(
    ["#", "Nom", "Visualisation", "Page"],
    [
        ["1", "Top 10 — Volume du jour", "Tableau", "1"],
        ["2", "Performance sectorielle — 30j", "Barres (X=sector, Y=variation_moy)", "1"],
        ["3", "MASI — Évolution 30 jours", "Courbe (X=date, Y=valeur_masi)", "1"],
        ["4", "KPI — MASI / Variation / Volume / Capitalisation", "4 cartes Nombre", "1"],
        ["5", "Top 5 Hausses", "Tableau", "1"],
        ["6", "Top 5 Baisses", "Tableau", "1"],
        ["7", "Répartition Marché — Camembert", "Camembert (hausse/baisse/stable)", "1"],
        ["8", "Volume quotidien — 30j", "Courbe aire (X=date, Y=volume_M)", "1"],
        ["9", "MASI — Intraday temps réel", "Courbe (X=HH:MM, Y=valeur)", "1 & 2"],
        ["10", "Capitalisation par secteur", "Barres horizontales", "1"],
        ["11", "Historique OHLC — {{ticker}}", "Courbe 90 jours", "2"],
        ["12", "Fiche Instrument — {{ticker}}", "Tableau (cours + infos)", "2"],
    ],
    [0.5, 5.0, 4.5, 1.5]
)

h2("Rafraîchissement automatique")
body(
    "Dans le dashboard Metabase, activer : icône horloge (en haut à droite) → 2 minutes. "
    "Chaque refresh envoie les 12 requêtes SQL à Trino qui lit les données fraîches de Cassandra."
)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 11. PIPELINE DE SYNCHRONISATION
# ════════════════════════════════════════════════════════════════════════════════
h1("11. Pipeline de synchronisation automatique")

body(
    "Une fois docker-compose up -d lancé, tout le pipeline tourne de façon autonome "
    "sans intervention manuelle. Voici ce qui se passe toutes les 2 minutes :"
)

steps_pipeline = [
    ("1", "scraper-worker", "market_overview_flow se déclenche (Prefect schedule)"),
    ("2", "MarketOverviewScraper", "Requête HTTP vers casablanca-bourse.com/fr/live-market/overview"),
    ("3", "Parsing", "BeautifulSoup extrait MASI, MASI20, stats, top movers"),
    ("4", "CassandraClient", "INSERT dans daily_indices, market_stats, top_movers, intraday_indices"),
    ("5", "Metabase", "Refresh automatique → envoie requêtes SQL à Trino"),
    ("6", "Trino", "Traduit SQL en CQL, lit Cassandra, renvoie les résultats"),
    ("7", "Dashboard", "Cartes mises à jour : MASI, volume, top movers actualisés"),
]
simple_table(
    ["Étape", "Acteur", "Action"],
    steps_pipeline,
    [1.0, 3.5, 9.0]
)

h2("Toutes les 15 minutes (en plus)")
bullet("details_flow scrape ATW, BCP, MNG sur /fr/live-market/instruments/{ticker}")
bullet("Met à jour daily_prices (cours de séance) et instruments_static (secteur, ISIN, etc.)")

h2("Chaque jour (Lun–Ven)")
bullet("18h00 : instruments_flow scrape la liste complète — INSERT uniquement si changements")
bullet("19h00 : historical_daily_flow ajoute le dernier jour OHLC pour ATW, BCP, MNG")

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 12. CONFIGURATIONS CRITIQUES ET BUGS RÉSOLUS
# ════════════════════════════════════════════════════════════════════════════════
h1("12. Configurations critiques et bugs résolus")

body(
    "Cette section documente les problèmes rencontrés lors de la mise en place du pipeline "
    "et les solutions appliquées. Elle est utile pour comprendre les choix de configuration."
)

bugs = [
    (
        "Trino crash au démarrage (connecteur Cassandra)",
        "Le fichier cassandra.properties utilisait cassandra.load-policy.use-datacenter "
        "qui est invalide en Trino 426.",
        "Remplacer par :\n"
        "  cassandra.load-policy.use-dc-aware=true\n"
        "  cassandra.load-policy.dc-aware.local-dc=datacenter1\n"
        "(Noms trouvés en lisant le bytecode de trino-cassandra-426.jar)"
    ),
    (
        "internal-communication.shared-secret manquant",
        "Avec http-server.authentication.type=PASSWORD, Trino exige un shared-secret "
        "pour les communications internes. Sans lui, Trino refuse de démarrer.",
        "Générer une clé base64 et ajouter :\n"
        "  internal-communication.shared-secret=<valeur_base64>"
    ),
    (
        "Prepared statement not found (Metabase → Trino)",
        "Le driver JDBC Presto (Facebook) envoie des headers X-Presto-* mais Trino 426 "
        "attend X-Trino-*. Cela cause une erreur lors de l'exécution des requêtes préparées.",
        "Ajouter dans config.properties :\n"
        "  protocol.v1.alternate-header-name=Presto"
    ),
    (
        "SSL truststore Metabase",
        "Trino utilise un certificat auto-signé. Le driver JDBC Presto ne peut pas "
        "le valider sans truststore explicite.",
        "1. Exporter le certificat Trino\n"
        "2. L'importer dans /tmp/ts.jks dans le conteneur Metabase\n"
        "3. Additional JDBC options : SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit"
    ),
    (
        "ModuleNotFoundError: No module named 'src'",
        "Les fichiers flows/*.py importent src.scrapers.* mais quand ils sont exécutés "
        "directement (python flows/xxx.py), le répertoire parent n'est pas dans sys.path.",
        "Ajouter en haut de chaque flow file :\n"
        "  import sys\n"
        "  from pathlib import Path\n"
        "  sys.path.insert(0, str(Path(__file__).parent.parent))"
    ),
    (
        "listing_date format DD/MM/YYYY",
        "Le site BVC retourne les dates de cotation au format '06/07/2004' mais "
        "Cassandra attend un objet date Python.",
        "Dans cassandra_client.py, parse avec fallback multi-formats :\n"
        "  for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):\n"
        "      listing_date = datetime.strptime(raw_date, fmt).date()"
    ),
    (
        "Column 'ist.company_name' cannot be resolved",
        "La table instruments_static n'a pas de colonne company_name. "
        "Ce champ est dans la table instruments (colonne name).",
        "Modifier la Requête 12 Fiche Instrument :\n"
        "  LEFT JOIN cassandra.bourse_data.instruments i ON dp.ticker = i.ticker\n"
        "  → sélectionner i.name AS societe"
    ),
    (
        "CASSANDRA_HOST=localhost dans Docker",
        "Dans le conteneur scraper-worker, localhost = l'intérieur du conteneur, "
        "pas le PC hôte. Cassandra est inaccessible.",
        "Dans docker-compose.yml, section environment du scraper-worker :\n"
        "  CASSANDRA_HOST=cassandra   (hostname Docker interne)"
    ),
]

for i, (title, cause, fix) in enumerate(bugs):
    h3(f"{'.'*(0)} {title}")
    p = doc.add_paragraph()
    r = p.add_run("Cause : ")
    r.bold = True
    r.font.color.rgb = RGBColor(0xCC, 0x33, 0x33)
    p.add_run(cause).font.size = Pt(11)
    p2 = doc.add_paragraph()
    r2 = p2.add_run("Solution : ")
    r2.bold = True
    r2.font.color.rgb = RGBColor(0x2E, 0x86, 0x2E)
    code_block(fix)

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 13. GUIDE DE REPRODUCTION
# ════════════════════════════════════════════════════════════════════════════════
h1("13. Guide de reproduction (pas à pas)")

body(
    "Cette section permet à toute personne disposant du code source de reproduire "
    "intégralement le projet sur sa machine Windows."
)

h2("Prérequis")
simple_table(
    ["Outil", "Version", "Lien"],
    [
        ["Docker Desktop", "4.x+", "https://www.docker.com/products/docker-desktop/"],
        ["Python", "3.11 ou 3.12 (⚠ pas 3.13)", "https://www.python.org/downloads/"],
        ["Git", "Quelconque", "https://git-scm.com/"],
    ],
    [2.5, 2.5, 8.5]
)

h2("Étape 1 — Installer les dépendances Python")
code_block(
    "# Cloner le projet\n"
    "git clone [LIEN_GITHUB] Projet_BD\n"
    "cd Projet_BD\n\n"
    "# Environnement virtuel Python 3.11\n"
    "py -3.11 -m venv venv\n"
    ".\\venv\\Scripts\\Activate.ps1\n\n"
    "# Dépendances\n"
    "pip install -r requirements.txt"
)

h2("Étape 2 — Configurer .env")
code_block(
    "copy .env.example .env\n"
    "# Vérifier les valeurs par défaut (aucune modification nécessaire)"
)

h2("Étape 3 — Démarrer la stack Docker")
code_block(
    "# Construire le scraper-worker (première fois uniquement)\n"
    "docker-compose build scraper-worker\n\n"
    "# Démarrer tous les conteneurs\n"
    "docker-compose up -d\n\n"
    "# Attendre ~90s que Cassandra soit healthy\n"
    "docker-compose ps   # vérifier que tout est UP"
)

h2("Étape 4 — Vérifier la stack")
code_block(
    "python scripts/verify_stack.py\n"
    "# Résultat attendu :\n"
    "# [OK] Cassandra accessible\n"
    "# [OK] Trino accessible\n"
    "# [OK] Prefect Server accessible\n"
    "# [OK] Metabase accessible"
)

h2("Étape 5 — Tests (optionnel)")
code_block("pytest tests/ -v")

h2("Étape 6 — Chargement initial des données")
code_block(
    "# Instruments + 1 an historique OHLC (5-20 min)\n"
    "python scripts/run_initial_load.py\n\n"
    "# Backfill 30 jours indices et stats\n"
    "python scripts/backfill_indices.py"
)

h2("Étape 7 — Vérifier le scraping automatique")
code_block(
    "# Le scraper-worker tourne déjà depuis docker-compose up -d\n"
    "docker logs scraper-worker --follow\n"
    "# Voir aussi : http://localhost:4200/deployments"
)

h2("Étape 8 — Configurer Metabase → Trino")
bullet("Ouvrir http://localhost:3000 et créer un compte admin")
bullet("Ajouter base de données → Presto → remplir les champs (voir section 10)")
bullet("Additional JDBC options : SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit")
bullet("Sauvegarder et attendre la synchronisation")

h2("Étape 9 — Créer les 12 requêtes et le dashboard")
bullet("Suivre le guide guide_dash_metabase.md (12 requêtes SQL détaillées)")
bullet("Assembler en dashboard 2 pages (Page 1 : Vue générale, Page 2 : Analyse par instrument)")
bullet("Activer refresh automatique 2 minutes")

page_break()

# ════════════════════════════════════════════════════════════════════════════════
# 14. RÉSULTATS ET BILAN
# ════════════════════════════════════════════════════════════════════════════════
h1("14. Résultats et bilan")

h2("Fonctionnalités livrées")
simple_table(
    ["Fonctionnalité", "Statut", "Détails"],
    [
        ["Scraping BVC (liste instruments)", "✅ Opérationnel", "80+ instruments cotés"],
        ["Scraping prix de séance", "✅ Opérationnel", "ATW, BCP, MNG — toutes les 15 min"],
        ["Scraping indices MASI/MASI20", "✅ Opérationnel", "Toutes les 2 minutes"],
        ["Historique OHLC 1 an", "✅ Opérationnel", "ATW, BCP, MNG — 365 jours"],
        ["Snapshots intraday", "✅ Opérationnel", "1 point toutes les 2 minutes"],
        ["Cassandra (8 tables)", "✅ Opérationnel", "Keyspace bourse_data, volume persistant"],
        ["Trino SQL sur Cassandra", "✅ Opérationnel", "Port 8443 HTTPS, auth PASSWORD"],
        ["Prefect orchestration", "✅ Opérationnel", "2 deployments, UI http://localhost:4200"],
        ["Dashboard Metabase", "✅ Opérationnel", "2 pages, 12 requêtes, refresh 2 min"],
        ["Containerisation Docker", "✅ Opérationnel", "docker-compose up -d lance tout"],
    ],
    [5.5, 2.2, 5.8]
)

h2("Compétences Big Data mobilisées")
bullet("Ingénierie des données : scraping, parsing, normalisation, gestion des formats")
bullet("Bases NoSQL : modélisation Cassandra, partition keys, clustering columns")
bullet("SQL distribué : requêtes multi-tables via connecteur Cassandra, gestion SSL/auth")
bullet("Orchestration : flows Prefect, scheduling, retry, monitoring")
bullet("Visualisation BI : dashboard Metabase, filtres dynamiques {{ticker}}, KPIs")
bullet("DevOps : Docker Compose, volumes, réseaux inter-conteneurs, Dockerfile custom")

h2("Perspectives d'évolution")
bullet("Apache Kafka : pipeline streaming temps réel pour les ticks de cours")
bullet("Alertes Prefect : notification email si variation MASI > seuil configurable")
bullet("Extension à 100+ instruments : optimiser le scraping avec async/ThreadPool")
bullet("Apache Spark : calculs statistiques sur l'historique (moyennes mobiles, corrélations)")
bullet("Tests d'intégration : vérifier le flux complet BVC → Cassandra → Trino → Metabase")

doc.add_paragraph()
info_box(
    "Ce rapport constitue à la fois une documentation technique du projet et un guide "
    "d'atelier permettant de reproduire le pipeline complet à partir du code source. "
    "Pour toute question : [EMAIL_GROUPE] · Lien GitHub : [LIEN_GITHUB]"
)

# ── Sauvegarde ────────────────────────────────────────────────────────────────
output = "Rapport_Atelier_BigData_Bourse_Casablanca.docx"
doc.save(output)
print(f"[OK] Rapport généré : {output}")
print(f"     14 sections · Guide de reproduction inclus")
