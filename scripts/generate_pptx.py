"""
Génère la présentation PowerPoint du projet Big Data Bourse de Casablanca.
Usage: py -3.13 scripts/generate_pptx.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Palette de couleurs soft & professionnelles ──────────────────────────────
NAVY       = RGBColor(0x1B, 0x2A, 0x4A)   # bleu marine foncé
TEAL       = RGBColor(0x2E, 0x86, 0xAB)   # bleu-vert accent principal
MINT       = RGBColor(0xA8, 0xDA, 0xDC)   # bleu clair secondaire
SAND       = RGBColor(0xF4, 0xF1, 0xEB)   # fond crème chaud
GOLD       = RGBColor(0xE8, 0xB8, 0x4B)   # accent or/jaune
DARK_GRAY  = RGBColor(0x3D, 0x3D, 0x3D)   # texte principal
MID_GRAY   = RGBColor(0x7A, 0x7A, 0x8C)   # texte secondaire
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BLUE = RGBColor(0xE8, 0xF4, 0xF8)   # fond carte légère
GREEN_OK   = RGBColor(0x4C, 0xAF, 0x50)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]  # layout vide

# ── Helpers ──────────────────────────────────────────────────────────────────

def bg(slide, color: RGBColor):
    """Colorier le fond de la slide."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def box(slide, x, y, w, h, fill_color=None, border_color=None, border_width=Pt(0)):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = border_width
    else:
        shape.line.fill.background()
    return shape

def txt(slide, text, x, y, w, h, size=18, bold=False, color=DARK_GRAY,
        align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb

def card(slide, x, y, w, h, title, body, title_color=TEAL, bg_color=WHITE):
    box(slide, x, y, w, h, fill_color=bg_color, border_color=MINT, border_width=Pt(1.5))
    txt(slide, title, x+0.12, y+0.1, w-0.24, 0.35, size=13, bold=True, color=title_color)
    txt(slide, body, x+0.12, y+0.45, w-0.24, h-0.55, size=10.5, color=DARK_GRAY, wrap=True)

def divider(slide, x, y, w, color=TEAL):
    ln = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Pt(2))
    ln.fill.solid()
    ln.fill.fore_color.rgb = color
    ln.line.fill.background()

def header_bar(slide, title, subtitle=None):
    box(slide, 0, 0, 13.33, 1.15, fill_color=NAVY)
    txt(slide, title, 0.35, 0.1, 10, 0.58, size=26, bold=True, color=WHITE)
    if subtitle:
        txt(slide, subtitle, 0.35, 0.65, 10, 0.4, size=13, color=MINT, italic=True)

def slide_num(slide, n, total):
    txt(slide, f"{n} / {total}", 12.0, 7.1, 1.2, 0.35, size=10, color=MID_GRAY, align=PP_ALIGN.RIGHT)

TOTAL = 14

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITRE
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)

# Bande décorative
box(s, 0, 2.7, 13.33, 0.06, fill_color=GOLD)

txt(s, "PIPELINE BIG DATA", 1.0, 0.8, 11.5, 0.8, size=38, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(s, "Bourse de Casablanca — Collecte, Stockage & Visualisation en Temps Réel",
    1.0, 1.55, 11.5, 0.6, size=17, color=MINT, align=PP_ALIGN.CENTER, italic=True)

# Boîte centrale
box(s, 1.5, 2.9, 10.33, 2.85, fill_color=RGBColor(0x23, 0x3A, 0x5E), border_color=TEAL, border_width=Pt(1.5))

infos = [
    ("Données sources", "casablanca-bourse.com — 80+ instruments cotés"),
    ("Stack technique", "Python · Cassandra · Trino · Prefect · Metabase · Docker"),
    ("Fréquence", "Collecte toutes les 2 minutes · Dashboard temps réel"),
    ("Périmètre", "Instruments, indices MASI/MASI20, top movers, historique OHLC"),
]
for i, (k, v) in enumerate(infos):
    yy = 3.05 + i * 0.6
    txt(s, f"  {k}", 1.65, yy, 3.2, 0.38, size=12, bold=True, color=GOLD)
    txt(s, v, 4.85, yy, 6.7, 0.38, size=12, color=WHITE)

txt(s, "Projet Big Data — Semestre 8 · 2025–2026", 1.0, 6.6, 11.5, 0.5,
    size=12, color=MID_GRAY, align=PP_ALIGN.CENTER)
slide_num(s, 1, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — ARCHITECTURE GLOBALE
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Architecture Globale du Pipeline", "Flux de données de la source à la visualisation")

components = [
    (0.25,  "BVC\nWebsite",    TEAL,  "casablanca-\nbourse.com"),
    (2.45,  "Scrapers\nPython", RGBColor(0x4C,0x72,0xB0), "4 scrapers\nBeautifulSoup"),
    (4.65,  "Cassandra",       RGBColor(0x1E,0x8B,0x8B), "8 tables\nbourse_data"),
    (6.85,  "Trino",           RGBColor(0x8A,0x2B,0xE2), "Connecteur\nCassandra"),
    (9.05,  "Metabase",        GOLD,  "Dashboard\n2 pages"),
]

for cx, label, color, sub in components:
    box(s, cx, 2.0, 1.9, 1.9, fill_color=color)
    txt(s, label, cx+0.05, 2.15, 1.8, 0.8, size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txt(s, sub, cx+0.05, 2.9, 1.8, 0.7, size=10, color=WHITE, align=PP_ALIGN.CENTER)

# Flèches entre blocs
arrows = [(2.15, 2.85), (4.35, 2.85), (6.55, 2.85), (8.75, 2.85)]
for ax, ay in arrows:
    txt(s, "→", ax, ay, 0.3, 0.3, size=20, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

# Labels sous les flèches
arrow_labels = ["HTTP\nscraping", "CQL\nINSERT", "SQL\nquery live", "JDBC\nSSL"]
for i, (ax, ay) in enumerate(arrows):
    txt(s, arrow_labels[i], ax-0.05, 3.1, 0.4, 0.5, size=8, color=MID_GRAY, align=PP_ALIGN.CENTER)

# Prefect et scraper-worker
box(s, 2.45, 4.2, 6.3, 1.05, fill_color=RGBColor(0xF0,0xF7,0xFF), border_color=TEAL, border_width=Pt(1.2))
txt(s, "Orchestration Prefect + scraper-worker (Docker)", 2.6, 4.3, 6.0, 0.4, size=12, bold=True, color=NAVY)
txt(s, "market_overview_flow  toutes les 2 min  ·  details_flow  toutes les 15 min",
    2.6, 4.65, 6.0, 0.45, size=10.5, color=DARK_GRAY)

divider(s, 0.35, 5.45, 12.6)

cards_bottom = [
    ("Collecte", "Scraping HTTP\n+ parsing HTML/JSON"),
    ("Stockage", "Cassandra NoSQL\n8 tables CQL"),
    ("Requêtes", "Trino SQL distribué\nConnecteur Cassandra"),
    ("Orchestration", "Prefect 2.x\nFlows + schedules"),
    ("Visualisation", "Metabase\nDashboard temps réel"),
]
for i, (t, b) in enumerate(cards_bottom):
    cx = 0.35 + i * 2.54
    box(s, cx, 5.6, 2.4, 1.6, fill_color=LIGHT_BLUE, border_color=MINT, border_width=Pt(1))
    txt(s, t, cx+0.1, 5.68, 2.2, 0.38, size=12, bold=True, color=TEAL)
    txt(s, b, cx+0.1, 6.05, 2.2, 0.9, size=10, color=DARK_GRAY, wrap=True)

slide_num(s, 2, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — EXPLORATION DU SITE BVC ET APIs
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Phase 1 — Exploration du Site BVC et des APIs", "Ingénierie inverse pour identifier les sources de données")

txt(s, "Le site casablanca-bourse.com expose deux types de sources :",
    0.4, 1.3, 12.5, 0.45, size=13, color=DARK_GRAY)

sources = [
    ("Pages HTML publiques",
     "• /fr/live-market/overview — indices, stats, top movers\n"
     "• /fr/live-market/instruments/{ticker} — fiche instrument\n"
     "• /fr/live-market/indices/MASI — valeur indice\n"
     "Parsées avec BeautifulSoup4 (sélecteurs CSS ciblés)"),
    ("API JSON (Next.js / Drupal)",
     "• /api/proxy/fr/api/bourse_data/instrument — liste paginée\n"
     "• /api/proxy/fr/api/bourse_data/market_watch — top movers API\n"
     "• /api/proxy/fr/api/bourse_data/instrument_history — OHLC\n"
     "• /_next/data/{BUILD_ID}/fr/live-market/overview.json — widget data\n"
     "Consommées en JSON avec requests"),
    ("Données extraites",
     "• Instruments : ticker, nom, ISIN, secteur, date cotation\n"
     "• Prix de séance : open/high/low/close, volume, variation%\n"
     "• Indices : MASI, MASI20, MASI_ESG (valeur + variation)\n"
     "• Top 5 hausses / Top 5 baisses du jour\n"
     "• Historique OHLC (jusqu'à 365 jours)"),
]
for i, (t, b) in enumerate(sources):
    cx = 0.35 + i * 4.3
    box(s, cx, 1.85, 4.1, 4.6, fill_color=WHITE, border_color=TEAL, border_width=Pt(1.5))
    txt(s, t, cx+0.15, 1.95, 3.8, 0.45, size=13, bold=True, color=TEAL)
    divider(s, cx+0.15, 2.42, 3.8, MINT)
    txt(s, b, cx+0.15, 2.55, 3.8, 3.8, size=10.5, color=DARK_GRAY, wrap=True)

box(s, 0.35, 6.6, 12.65, 0.62, fill_color=LIGHT_BLUE, border_color=MINT, border_width=Pt(1))
txt(s, "⚠  Headers HTTP indispensables : User-Agent Chrome + Accept-Language fr-FR · SSL verify=False (certificat BVC non reconnu)",
    0.55, 6.68, 12.2, 0.42, size=11, color=NAVY, italic=True)
slide_num(s, 3, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — SCRAPERS PYTHON
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Phase 2 — Scrapers Python", "4 scrapers spécialisés → sauvegarde directe dans Cassandra")

scrapers = [
    ("InstrumentsListScraper", "src/scrapers/instruments_list_scraper.py",
     "Scrape la liste complète des instruments cotés\n"
     "API JSON paginée (/instrument)\n"
     "Fallback HTML si l'API échoue\n"
     "→ Table : instruments"),
    ("InstrumentDetailsScraper", "src/scrapers/instrument_details_scraper.py",
     "Scrape la fiche complète d'un instrument\n"
     "Parsing HTML : infos statiques + cours de séance\n"
     "Gestion listing_date (format DD/MM/YYYY → date Python)\n"
     "→ Tables : instruments_static, daily_prices"),
    ("MarketOverviewScraper", "src/scrapers/market_overview_scraper.py",
     "Scrape la page overview toutes les 2 minutes\n"
     "Indices MASI/MASI20/MASI_ESG + stats globales\n"
     "Top 5 hausses et baisses (HTML + API fallback)\n"
     "→ Tables : daily_indices, market_stats, top_movers, intraday_indices"),
    ("HistoricalDataScraper", "src/scrapers/historical_data_scraper.py",
     "Scrape l'historique OHLC via API JSON\n"
     "Paramètres : ticker + date_start + date_end\n"
     "Ajustement ratio splits/dividendes\n"
     "→ Table : historical_prices"),
]

for i, (name, path, desc) in enumerate(scrapers):
    row = i // 2
    col = i % 2
    cx = 0.35 + col * 6.5
    cy = 1.35 + row * 2.75
    box(s, cx, cy, 6.2, 2.55, fill_color=WHITE, border_color=TEAL, border_width=Pt(1.5))
    txt(s, name, cx+0.15, cy+0.08, 5.9, 0.4, size=13, bold=True, color=NAVY)
    txt(s, path, cx+0.15, cy+0.45, 5.9, 0.28, size=9, color=MID_GRAY, italic=True)
    divider(s, cx+0.15, cy+0.75, 5.9, MINT)
    txt(s, desc, cx+0.15, cy+0.88, 5.9, 1.55, size=10.5, color=DARK_GRAY, wrap=True)

slide_num(s, 4, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — TESTS UNITAIRES
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Phase 3 — Tests Unitaires", "Validation des scrapers avec pytest + mode stub Cassandra")

txt(s, "Stratégie de test", 0.4, 1.3, 12.5, 0.42, size=16, bold=True, color=NAVY)

box(s, 0.35, 1.75, 12.65, 1.85, fill_color=WHITE, border_color=MINT, border_width=Pt(1))
strategy = (
    "Mode stub Cassandra (CASSANDRA_STUB=true) : tous les CQL INSERT sont des no-ops, aucune infrastructure requise pour les tests.\n"
    "Les scrapers sont testés contre le vrai site BVC — les données réelles sont capturées en JSON dans tests/data/\n"
    "Pytest fixtures : session HTTP mockée pour isoler le parsing du réseau"
)
txt(s, strategy, 0.5, 1.85, 12.3, 1.65, size=11, color=DARK_GRAY, wrap=True)

test_files = [
    ("test_instruments_list.py", "Vérifie : liste non vide · ticker alphanumérique · URL valide"),
    ("test_instrument_details.py", "Vérifie : cours > 0 · variation dans [-30%, +30%] · date aujourd'hui"),
    ("test_market_overview.py", "Vérifie : MASI présent · value > 0 · top_gainers ≥ 1 entrée"),
    ("test_historical_data.py", "Vérifie : OHLC cohérent (low ≤ open ≤ close ≤ high) · dates triées"),
]
txt(s, "Fichiers de test", 0.4, 3.7, 12.5, 0.42, size=14, bold=True, color=NAVY)
for i, (f, desc) in enumerate(test_files):
    cy = 4.15 + i * 0.58
    box(s, 0.35, cy, 12.65, 0.52, fill_color=LIGHT_BLUE if i % 2 == 0 else WHITE,
        border_color=MINT, border_width=Pt(0.5))
    txt(s, f, 0.5, cy+0.07, 3.8, 0.38, size=11, bold=True, color=TEAL)
    txt(s, desc, 4.3, cy+0.07, 8.5, 0.38, size=11, color=DARK_GRAY)

txt(s, "pytest tests/ -v    →  Tous les tests passent en mode stub sans Cassandra ni Docker",
    0.4, 6.6, 12.5, 0.5, size=12, bold=True, color=NAVY, italic=True)
slide_num(s, 5, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — STACK DOCKER
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Phase 4 — Stack Docker", "5 conteneurs orchestrés par docker-compose")

containers = [
    ("cassandra", "Cassandra 4.1", "9042",
     "Base de données NoSQL\nKeyspace bourse_data\n8 tables CQL\nVolume persistant",
     RGBColor(0x1E,0x8B,0x8B)),
    ("trino", "Trino 426", "8080/8443",
     "Moteur SQL distribué\nConnecteur Cassandra\nHTTPS + auth PASSWORD\nJKS keystore SSL",
     RGBColor(0x8A,0x2B,0xE2)),
    ("prefect-server", "Prefect 2.19", "4200",
     "UI orchestration\nPlanification des flows\nHistorique des runs\nSQLite backend",
     TEAL),
    ("scraper-worker", "Python 3.11", "—",
     "Prefect serve()\nmarket_overview 2 min\ndetails_flow 15 min\nCassandraHost=cassandra",
     RGBColor(0x4C,0x72,0xB0)),
    ("metabase", "Metabase 0.50", "3000",
     "Dashboard BI\nConnexion Presto JDBC\nSSL truststore JKS\nRefresh auto 2 min",
     GOLD),
]

for i, (cname, image, port, desc, color) in enumerate(containers):
    cx = 0.3 + i * 2.58
    box(s, cx, 1.35, 2.4, 0.52, fill_color=color)
    txt(s, cname, cx+0.08, 1.4, 2.25, 0.38, size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    box(s, cx, 1.88, 2.4, 3.65, fill_color=WHITE, border_color=color, border_width=Pt(1.5))
    txt(s, image, cx+0.1, 1.95, 2.2, 0.35, size=11, bold=True, color=color)
    txt(s, f"Port : {port}", cx+0.1, 2.3, 2.2, 0.3, size=10, color=MID_GRAY)
    divider(s, cx+0.1, 2.62, 2.2, MINT)
    txt(s, desc, cx+0.1, 2.72, 2.2, 2.7, size=10, color=DARK_GRAY, wrap=True)

box(s, 0.3, 5.6, 12.75, 1.62, fill_color=LIGHT_BLUE, border_color=TEAL, border_width=Pt(1))
txt(s, "Points de configuration critiques :", 0.5, 5.68, 12.3, 0.38, size=12, bold=True, color=NAVY)
critical = (
    "• cassandra-init : conteneur one-shot qui exécute init.cql au premier démarrage (crée keyspace + tables)\n"
    "• scraper-worker : CASSANDRA_HOST=cassandra (réseau Docker) ≠ localhost (PC hôte) — variable injectée via docker-compose\n"
    "• Trino SSL : certificat auto-signé trino.jks · auth PASSWORD · shared-secret requis · protocol Presto compatible"
)
txt(s, critical, 0.5, 6.0, 12.3, 1.1, size=10.5, color=DARK_GRAY, wrap=True)
slide_num(s, 6, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — CASSANDRA : SCHÉMA ET MODÈLE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Cassandra — Schéma des Données", "8 tables CQL dans le keyspace bourse_data")

tables = [
    ("instruments",        "ticker ★",              "name, url, updated_at",             "Liste de tous les cotés BVC"),
    ("instruments_static", "ticker ★",              "isin, sector, listing_date,\nnominal_value, trading_cycle", "Données statiques par instrument"),
    ("daily_prices",       "ticker ★  date ★",      "open/high/low/close, volume,\nvariation, market_cap, var_ytd", "Prix de séance (1 ligne/jour)"),
    ("historical_prices",  "ticker ★  date ★",      "OHLC, volume,\nadjusted_close, ratio", "Historique OHLC ajusté ATW/BCP/MNG"),
    ("daily_indices",      "index_name ★  date ★",  "value, variation,\nannual_variation", "MASI / MASI20 / MASI_ESG par jour"),
    ("market_stats",       "date ★",                "global_volume, market_cap",          "Totaux du marché par jour"),
    ("top_movers",         "date ★  direction ★  rank ★", "ticker, company_name,\nprice, variation", "Top 5 hausses et baisses"),
    ("intraday_indices",   "index_name ★  date ★  timestamp ★", "value, scraped_at",    "Snapshots MASI toutes les 2 min"),
]

txt(s, "★ = clé primaire (partition key + clustering columns)", 0.35, 1.28, 12.5, 0.35, size=10.5, color=MID_GRAY, italic=True)

header_cols = ["Table", "Clé primaire", "Colonnes principales", "Usage"]
col_w = [2.5, 2.4, 3.4, 3.9]
col_x = [0.35, 2.85, 5.25, 8.65]
row_h = 0.58

# En-tête tableau
for j, (h, cw, cx) in enumerate(zip(header_cols, col_w, col_x)):
    box(s, cx, 1.65, cw-0.05, 0.42, fill_color=NAVY)
    txt(s, h, cx+0.08, 1.68, cw-0.2, 0.35, size=11, bold=True, color=WHITE)

for i, (tname, pk, cols, usage) in enumerate(tables):
    cy = 2.1 + i * row_h
    row_bg = LIGHT_BLUE if i % 2 == 0 else WHITE
    for j, (val, cw, cx) in enumerate(zip([tname, pk, cols, usage], col_w, col_x)):
        box(s, cx, cy, cw-0.05, row_h-0.04, fill_color=row_bg, border_color=MINT, border_width=Pt(0.5))
        fc = TEAL if j == 0 else DARK_GRAY
        txt(s, val, cx+0.08, cy+0.05, cw-0.2, row_h-0.1, size=9.5, color=fc, bold=(j==0))

slide_num(s, 7, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — TRINO : CONFIGURATION ET RÔLE
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Trino — Moteur SQL sur Cassandra", "Requêtes SQL standard sur données NoSQL Cassandra")

txt(s, "Rôle de Trino", 0.4, 1.28, 12.5, 0.4, size=15, bold=True, color=NAVY)
txt(s, "Trino est un moteur de requêtes SQL distribué. Il traduit les requêtes SQL de Metabase en "
       "opérations CQL Cassandra en temps réel, sans copier ni cacher les données.",
    0.4, 1.65, 12.5, 0.55, size=12, color=DARK_GRAY)

configs = [
    ("config.properties\n(trino/etc/)", WHITE,
     "coordinator=true\nhttp-server.https.port=8443\n"
     "http-server.authentication.type=PASSWORD\n"
     "internal-communication.shared-secret=...\n"
     "protocol.v1.alternate-header-name=Presto"),
    ("cassandra.properties\n(trino/catalog/)", WHITE,
     "connector.name=cassandra\n"
     "cassandra.contact-points=cassandra\n"
     "cassandra.native-protocol-port=9042\n"
     "cassandra.load-policy.use-dc-aware=true\n"
     "cassandra.load-policy.dc-aware.local-dc=datacenter1"),
]

for i, (title, bg_c, code) in enumerate(configs):
    cx = 0.35 + i * 5.2
    box(s, cx, 2.35, 4.9, 2.85, fill_color=NAVY)
    txt(s, title, cx+0.15, 2.42, 4.6, 0.45, size=12, bold=True, color=GOLD)
    txt(s, code, cx+0.15, 2.88, 4.6, 2.2, size=10, color=MINT, wrap=True)

box(s, 10.6, 2.35, 2.55, 2.85, fill_color=WHITE, border_color=GOLD, border_width=Pt(1.5))
txt(s, "Bugs résolus", 10.75, 2.42, 2.25, 0.38, size=11, bold=True, color=GOLD)
bugs = [
    "❌ use-datacenter\n✅ use-dc-aware",
    "❌ Pas de shared-secret\n✅ Requis avec PASSWORD",
    "❌ X-Trino-* headers\n✅ alternate-header\n   =Presto",
]
for i, b in enumerate(bugs):
    txt(s, b, 10.75, 2.85 + i*0.78, 2.25, 0.72, size=9.5, color=DARK_GRAY, wrap=True)

divider(s, 0.35, 5.35, 12.65)
txt(s, "Pourquoi SSL sur le port 8443 ?", 0.4, 5.45, 12.5, 0.38, size=13, bold=True, color=NAVY)
ssl_text = (
    "Metabase utilise le driver JDBC Presto (Facebook) qui impose une connexion sécurisée. "
    "Trino génère un certificat auto-signé (trino.jks). Ce certificat est importé dans un truststore "
    "Java (/tmp/ts.jks) accessible au conteneur Metabase, et référencé via "
    "SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit dans les Additional JDBC Options."
)
txt(s, ssl_text, 0.4, 5.82, 12.5, 1.3, size=11, color=DARK_GRAY, wrap=True)
slide_num(s, 8, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — PREFECT : ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Prefect — Orchestration des Flows", "Scheduling, monitoring et retry automatique")

txt(s, "Prefect 2.x : Flows et Deployments", 0.4, 1.28, 12.5, 0.4, size=15, bold=True, color=NAVY)

flows = [
    ("market_overview_flow", "Toutes les 2 min",
     "flows/market_overview_flow.py",
     "Scrape MASI/MASI20, stats, top movers\n"
     "Snapshot intraday horodaté (HH:MM)\n"
     "Task : retries=3, delay=15s"),
    ("details_flow", "Toutes les 15 min",
     "flows/details_flow.py",
     "Scrape ATW, BCP, MNG (3 tickers)\n"
     "Mise à jour daily_prices + instruments_static\n"
     "Pause 1s entre instruments"),
    ("instruments_flow", "Lun–Ven 18h00",
     "flows/instruments_flow.py",
     "Scrape liste complète des cotés\n"
     "INSERT uniquement si changements détectés\n"
     "(ticker inconnu ou nom/url modifié)"),
    ("historical_daily_flow", "Lun–Ven 19h00",
     "flows/historical_flow.py",
     "Ajout du dernier jour OHLC\n"
     "pour les 3 instruments suivis\n"
     "Exécution unique : historical_initial_flow (1 an)"),
]
for i, (name, sched, path, desc) in enumerate(flows):
    row, col = i // 2, i % 2
    cx, cy = 0.35 + col * 6.5, 1.85 + row * 2.55
    box(s, cx, cy, 6.2, 2.4, fill_color=WHITE, border_color=TEAL, border_width=Pt(1.5))
    box(s, cx, cy, 6.2, 0.52, fill_color=TEAL)
    txt(s, name, cx+0.12, cy+0.07, 4.2, 0.38, size=12, bold=True, color=WHITE)
    box(s, cx+4.35, cy+0.07, 1.7, 0.35, fill_color=GOLD)
    txt(s, sched, cx+4.38, cy+0.09, 1.6, 0.3, size=9.5, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    txt(s, path, cx+0.12, cy+0.6, 5.9, 0.28, size=9, color=MID_GRAY, italic=True)
    txt(s, desc, cx+0.12, cy+0.9, 5.9, 1.4, size=10.5, color=DARK_GRAY, wrap=True)

box(s, 0.35, 6.92, 12.65, 0.45, fill_color=LIGHT_BLUE, border_color=TEAL, border_width=Pt(1))
txt(s, "scraper-worker lance prefect serve() au démarrage → enregistre automatiquement les deployments et exécute les flows selon leur schedule · UI : http://localhost:4200",
    0.5, 6.97, 12.3, 0.35, size=10.5, color=NAVY, italic=True)
slide_num(s, 9, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — METABASE : DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Metabase — Dashboard Bourse de Casablanca", "2 pages · 12 requêtes SQL · Refresh automatique toutes les 2 minutes")

txt(s, "Page 1 — Vue Générale du Marché", 0.4, 1.3, 8.5, 0.4, size=14, bold=True, color=NAVY)

layout_lines = [
    "┌──────────┬──────────┬──────────┬──────────┐",
    "│ KPI MASI │ KPI Var% │ KPI Vol. │ KPI Capi │  ← 4 cartes Nombre",
    "├──────────┴──────────┴──────────┴──────────┤",
    "│       MASI — Évolution 30 jours (courbe)  │",
    "├─────────────────────┬─────────────────────┤",
    "│ Perf. sectorielle   │ Répartition Marché  │",
    "│ (barres)            │ (camembert)         │",
    "├─────────────────────┼─────────────────────┤",
    "│ Top 5 Hausses       │ Top 5 Baisses       │",
    "├─────────────────────┴─────────────────────┤",
    "│    Volume quotidien 30j (courbe aire)      │",
    "│    Capitalisation par secteur (barres)     │",
    "│    Top 10 Volume du jour (tableau)         │",
    "└────────────────────────────────────────────┘",
]
box(s, 0.35, 1.72, 7.6, 5.5, fill_color=NAVY)
for i, line in enumerate(layout_lines):
    txt(s, line, 0.45, 1.8 + i*0.37, 7.4, 0.38, size=9.5, color=MINT, wrap=False)

txt(s, "Page 2 — Analyse par Instrument", 8.1, 1.3, 5.1, 0.4, size=14, bold=True, color=NAVY)
p2_items = [
    ("Filtre", "{{ticker}} — saisir ATW, BCP ou MNG"),
    ("Fiche", "Tableau : cours, secteur, ISIN, OHLC du jour"),
    ("Historique", "Courbe OHLC sur 90 jours"),
    ("Intraday", "Courbe MASI toutes les 2 minutes"),
]
for i, (k, v) in enumerate(p2_items):
    cy = 1.78 + i * 0.72
    box(s, 8.1, cy, 5.1, 0.65, fill_color=LIGHT_BLUE, border_color=TEAL, border_width=Pt(1))
    txt(s, k, 8.25, cy+0.06, 1.2, 0.38, size=11, bold=True, color=TEAL)
    txt(s, v, 9.45, cy+0.06, 3.6, 0.5, size=10.5, color=DARK_GRAY, wrap=True)

box(s, 8.1, 4.8, 5.1, 2.42, fill_color=WHITE, border_color=GOLD, border_width=Pt(1.5))
txt(s, "Connexion Metabase → Trino", 8.25, 4.88, 4.8, 0.38, size=12, bold=True, color=GOLD)
conn = [
    "Type         : Presto (driver JDBC Facebook)",
    "Hôte         : trino   Port : 8443",
    "Catalog      : cassandra",
    "Schema       : bourse_data",
    "SSL          : ✅ coché",
    "JDBC options : SSLTrustStorePath=/tmp/ts.jks",
    "               &SSLTrustStorePassword=changeit",
]
for i, line in enumerate(conn):
    txt(s, line, 8.25, 5.25 + i*0.28, 4.8, 0.28, size=9.5, color=DARK_GRAY)
slide_num(s, 10, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — PIPELINE DE SYNCHRONISATION
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Pipeline de Synchronisation Complet", "De la source à l'affichage — sans aucune étape manuelle")

steps = [
    (TEAL,  "1", "BVC Website",        "casablanca-bourse.com\nHTTP/HTTPS public"),
    (RGBColor(0x4C,0x72,0xB0), "2", "Scrapers Python", "requests + BeautifulSoup\nHTML + API JSON"),
    (RGBColor(0x1E,0x8B,0x8B), "3", "Cassandra",       "CQL INSERT\n8 tables"),
    (RGBColor(0x8A,0x2B,0xE2), "4", "Trino",            "SQL live\nPas de cache"),
    (GOLD,  "5", "Metabase",           "JDBC SSL\nRefresh 2 min"),
]

for i, (color, num, name, detail) in enumerate(steps):
    cx = 0.5 + i * 2.48
    box(s, cx, 1.5, 2.15, 2.0, fill_color=color)
    txt(s, num, cx+0.08, 1.55, 0.5, 0.55, size=22, bold=True, color=WHITE)
    txt(s, name, cx+0.08, 2.05, 2.0, 0.55, size=13, bold=True, color=WHITE)
    txt(s, detail, cx+0.08, 2.58, 2.0, 0.8, size=10, color=WHITE, wrap=True)
    if i < 4:
        txt(s, "→", cx+2.15, 2.2, 0.35, 0.55, size=22, bold=True, color=NAVY)

freq_labels = [
    ("", ""),
    ("Toutes les\n2 min (overview)\n15 min (details)", TEAL),
    ("Immédiat\naprès chaque\nscraping", RGBColor(0x1E,0x8B,0x8B)),
    ("Live à chaque\nrequête SQL\n(pas de sync)", RGBColor(0x8A,0x2B,0xE2)),
    ("Refresh\nauto toutes\nles 2 min", GOLD),
]
for i, (label, color) in enumerate(freq_labels):
    if label:
        cx = 0.5 + i * 2.48
        box(s, cx, 3.6, 2.15, 1.15, fill_color=LIGHT_BLUE, border_color=color, border_width=Pt(1.2))
        txt(s, label, cx+0.1, 3.65, 1.95, 1.05, size=10, color=color, bold=True, wrap=True, align=PP_ALIGN.CENTER)

divider(s, 0.35, 4.9, 12.65)

key_points = [
    ("Pas de synchronisation Cassandra→Trino",
     "Trino lit directement dans Cassandra à chaque requête. Zéro délai, zéro cache à invalider."),
    ("Scraper-worker autonome",
     "Démarre avec docker-compose up -d. Préfect serve() enregistre les deployments et exécute les flows sans intervention."),
    ("Haute disponibilité",
     "restart: unless-stopped sur tous les services. En cas de crash, Docker redémarre automatiquement."),
]
for i, (t, b) in enumerate(key_points):
    cx = 0.35 + i * 4.35
    box(s, cx, 5.05, 4.2, 2.2, fill_color=WHITE, border_color=TEAL, border_width=Pt(1.2))
    txt(s, t, cx+0.12, 5.12, 3.96, 0.45, size=11, bold=True, color=TEAL)
    txt(s, b, cx+0.12, 5.57, 3.96, 1.55, size=10.5, color=DARK_GRAY, wrap=True)
slide_num(s, 11, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — CONFIGURATIONS CLÉS ET BUGS RÉSOLUS
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Configurations Clés & Problèmes Résolus", "Problèmes rencontrés et solutions appliquées")

issues = [
    ("Cassandra connector crash (Trino 426)",
     "CAUSE : cassandra.load-policy.use-datacenter invalide en Trino 426\n"
     "FIX   : use-dc-aware=true + dc-aware.local-dc=datacenter1"),
    ("shared-secret manquant",
     "CAUSE : http-server.authentication.type=PASSWORD exige shared-secret\n"
     "FIX   : internal-communication.shared-secret=<base64>"),
    ("Prepared statement not found",
     "CAUSE : Driver Presto envoie X-Presto-* mais Trino attend X-Trino-*\n"
     "FIX   : protocol.v1.alternate-header-name=Presto"),
    ("SSL truststore Metabase",
     "CAUSE : Certificat auto-signé non reconnu par le driver JDBC\n"
     "FIX   : SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit"),
    ("ModuleNotFoundError: src",
     "CAUSE : flows/*.py exécutés hors de la racine du projet\n"
     "FIX   : sys.path.insert(0, str(Path(__file__).parent.parent))"),
    ("listing_date format DD/MM/YYYY",
     "CAUSE : BVC retourne '06/07/2004', Cassandra attend un objet date Python\n"
     "FIX   : datetime.strptime avec fallback multi-formats"),
    ("company_name inexistant",
     "CAUSE : instruments_static n'a pas de colonne company_name\n"
     "FIX   : LEFT JOIN instruments i → i.name AS societe"),
    ("CASSANDRA_HOST=localhost en Docker",
     "CAUSE : localhost dans Docker = l'intérieur du conteneur, pas le PC\n"
     "FIX   : CASSANDRA_HOST=cassandra dans docker-compose environment"),
]

for i, (title, detail) in enumerate(issues):
    row, col = i // 2, i % 2
    cx = 0.35 + col * 6.5
    cy = 1.35 + row * 1.52
    box(s, cx, cy, 6.2, 1.42, fill_color=WHITE, border_color=RGBColor(0xFF,0x6B,0x6B), border_width=Pt(1.2))
    txt(s, f"⚡ {title}", cx+0.12, cy+0.07, 5.96, 0.38, size=11, bold=True, color=RGBColor(0xCC,0x33,0x33))
    txt(s, detail, cx+0.12, cy+0.48, 5.96, 0.88, size=9.5, color=DARK_GRAY, wrap=True)

slide_num(s, 12, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — RÉSULTATS ET DÉMO
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, SAND)
header_bar(s, "Résultats — Pipeline Opérationnel", "Données collectées et visualisées en temps réel")

txt(s, "Ce qui tourne en production", 0.4, 1.3, 12.5, 0.42, size=15, bold=True, color=NAVY)

results = [
    ("Collecte", GREEN_OK,
     "80+ instruments cotés BVC\nATW · BCP · MNG : données complètes\nHistorique OHLC 365 jours\nIntraday snapshots toutes les 2 min"),
    ("Cassandra", GREEN_OK,
     "8 tables opérationnelles\nKeyspace bourse_data\nDonnées persistées sur volume Docker\nBackfill 30 jours d'indices historiques"),
    ("Trino", GREEN_OK,
     "Port 8443 HTTPS + auth PASSWORD\nConnecteur Cassandra fonctionnel\n12 requêtes SQL validées\nCompatibilité Presto JDBC résolue"),
    ("Metabase", GREEN_OK,
     "Dashboard 2 pages opérationnel\nKPIs · Courbes · Barres · Camembert\nFiltre {{ticker}} sur Page 2\nRefresh automatique 2 minutes"),
    ("Prefect", GREEN_OK,
     "2 deployments enregistrés\nUI http://localhost:4200\nHistorique des runs visible\nRetry automatique (3 tentatives)"),
]

for i, (title, color, body) in enumerate(results):
    cx = 0.35 + (i % 3) * 4.3 if i < 3 else 2.5 + ((i-3) % 2) * 4.3
    cy = 1.82 if i < 3 else 4.42
    w = 4.1
    box(s, cx, cy, w, 2.38, fill_color=WHITE, border_color=color, border_width=Pt(2))
    box(s, cx, cy, w, 0.48, fill_color=color)
    txt(s, f"✓  {title}", cx+0.12, cy+0.06, w-0.24, 0.36, size=13, bold=True, color=WHITE)
    txt(s, body, cx+0.12, cy+0.58, w-0.24, 1.7, size=10.5, color=DARK_GRAY, wrap=True)

slide_num(s, 13, TOTAL)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — CONCLUSION
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
box(s, 0, 0, 13.33, 0.06, fill_color=GOLD)
box(s, 0, 7.44, 13.33, 0.06, fill_color=GOLD)

txt(s, "Conclusion & Perspectives", 1.0, 0.5, 11.5, 0.7, size=28, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(s, "Un pipeline Big Data complet de la collecte à la visualisation",
    1.0, 1.15, 11.5, 0.5, size=14, color=MINT, align=PP_ALIGN.CENTER, italic=True)

summary = [
    ("Compétences mises en œuvre",
     "Web scraping · NoSQL (Cassandra) · SQL distribué (Trino)\n"
     "Orchestration (Prefect) · BI (Metabase) · Containerisation (Docker)"),
    ("Architecture réplicable",
     "Code source disponible · Guide de lancement complet\n"
     "docker-compose up -d suffit pour tout démarrer"),
    ("Perspectives d'évolution",
     "Ajouter Kafka pour streaming temps réel\n"
     "Alertes Prefect par email (cours anormal)\n"
     "Étendre à 100+ instruments"),
]

for i, (t, b) in enumerate(summary):
    cx = 0.5 + i * 4.22
    box(s, cx, 1.9, 4.1, 2.5, fill_color=RGBColor(0x23,0x3A,0x5E), border_color=TEAL, border_width=Pt(1.5))
    txt(s, t, cx+0.15, 1.98, 3.8, 0.42, size=12, bold=True, color=GOLD)
    txt(s, b, cx+0.15, 2.42, 3.8, 1.88, size=11, color=WHITE, wrap=True)

stack_items = ["Python 3.11", "Cassandra 4.1", "Trino 426", "Prefect 2.19", "Metabase 0.50", "Docker Compose"]
txt(s, "Stack complète :", 1.0, 4.6, 3.0, 0.4, size=13, bold=True, color=MINT)
for i, item in enumerate(stack_items):
    cx = 1.0 + i * 2.02
    box(s, cx, 5.05, 1.9, 0.52, fill_color=TEAL)
    txt(s, item, cx+0.08, 5.1, 1.75, 0.4, size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

txt(s, "Projet réalisé dans le cadre du cours Big Data — Semestre 8 · 2025–2026",
    1.0, 5.8, 11.5, 0.42, size=12, color=MID_GRAY, align=PP_ALIGN.CENTER)
txt(s, "Code source : [lien GitHub]  ·  Guide : GUIDE_LANCEMENT.md",
    1.0, 6.2, 11.5, 0.42, size=12, color=MINT, align=PP_ALIGN.CENTER, italic=True)
slide_num(s, 14, TOTAL)

# ── Sauvegarde ────────────────────────────────────────────────────────────────
output = "Presentation_BigData_Bourse_Casablanca.pptx"
prs.save(output)
print(f"[OK] Présentation générée : {output}")
print(f"     {TOTAL} slides · Palette Navy/Teal/Gold")
