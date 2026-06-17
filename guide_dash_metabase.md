# Guide — Dashboard Metabase : Marché Boursier Casablanca

## Prérequis

- Metabase accessible sur `http://localhost:3000`
- Source de données **Bourse Casablanca** (Presto → Trino) déjà configurée
- Fichier `sql/queries.sql` disponible dans le projet

---

## Étape 1 — Créer les requêtes SQL sauvegardées

Pour chaque requête ci-dessous : **Nouvelle requête SQL** → sélectionner la source
**Bourse Casablanca** → coller le SQL → cliquer **Visualiser** → **Enregistrer**.

---

### Requête 1 — Top 10 instruments par volume

**Nom à donner :** `Top 10 — Volume du jour`
**Visualisation :** Tableau

```sql
SELECT
    dp.ticker,
    ist.sector,
    dp.close_price      AS cours_cloture,
    dp.variation        AS variation_pct,
    dp.volume           AS volume_mad,
    dp.market_cap       AS capitalisation
FROM cassandra.bourse_data.daily_prices dp
LEFT JOIN cassandra.bourse_data.instruments_static ist
    ON dp.ticker = ist.ticker
WHERE dp.date = current_date
ORDER BY dp.volume DESC
LIMIT 10;
```

---

### Requête 2 — Performance sectorielle (30 jours)

**Nom à donner :** `Performance sectorielle — 30j`
**Visualisation :** Graphique en barres (X = sector, Y = variation_moyenne_pct)

```sql
SELECT
    ist.sector,
    ROUND(AVG(dp.variation), 2)     AS variation_moyenne_pct,
    ROUND(SUM(dp.volume) / 1e9, 2)  AS volume_total_milliards,
    COUNT(DISTINCT dp.ticker)       AS nb_instruments
FROM cassandra.bourse_data.daily_prices dp
LEFT JOIN cassandra.bourse_data.instruments_static ist
    ON dp.ticker = ist.ticker
WHERE dp.date >= DATE_ADD('day', -30, current_date)
  AND ist.sector IS NOT NULL
GROUP BY ist.sector
ORDER BY variation_moyenne_pct DESC;
```

---

### Requête 3 — Évolution MASI (30 jours)

**Nom à donner :** `MASI — Évolution 30 jours`
**Visualisation :** Courbe (X = date, Y = valeur_masi)

```sql
SELECT
    date,
    ROUND(value, 2)     AS valeur_masi,
    ROUND(variation, 2) AS variation_pct
FROM cassandra.bourse_data.daily_indices
WHERE index_name = 'MASI'
  AND date >= DATE_ADD('day', -30, current_date)
ORDER BY date ASC;
```

---

### Requête 4 — KPI résumé du jour

**Nom à donner :** `KPI — Résumé du jour`
**Visualisation :** 5 cartes KPI séparées (une par métrique)

```sql
SELECT
    ms.date,
    ROUND(di_masi.value, 2)            AS masi,
    ROUND(di_masi.variation, 2)        AS masi_var_pct,
    ROUND(di_m20.value, 2)             AS masi20,
    ROUND(ms.global_volume / 1e9, 2)   AS volume_milliards,
    ROUND(ms.market_cap / 1e9, 2)      AS capitalisation_milliards
FROM cassandra.bourse_data.market_stats ms
LEFT JOIN cassandra.bourse_data.daily_indices di_masi
    ON ms.date = di_masi.date AND di_masi.index_name = 'MASI'
LEFT JOIN cassandra.bourse_data.daily_indices di_m20
    ON ms.date = di_m20.date AND di_m20.index_name = 'MASI20'
WHERE ms.date = current_date
LIMIT 1;
```

** MASI ESG intraday (temps réel) — à ajouter en plus du KPI MASI quotidien **

```sql
  SELECT
      value       AS valeur_masi_esg,
      timestamp   AS heure_utc,
      scraped_at  AS scrape_a
  FROM cassandra.bourse_data.intraday_indices
  WHERE index_name = 'MASI_ESG'
    AND date = current_date
  ORDER BY timestamp DESC
  LIMIT 1
```

> Pour chaque métrique (masi, masi_var_pct, volume_milliards, capitalisation_milliards) :
> cliquer sur **Visualiser** → choisir **Nombre** → enregistrer sous un nom distinct
> 6 KPIs: `KPI — Résumé du jour`,`KPI — MASI`, `KPI — MASI20`, `KPI — Capitalisation`, `KPI — Volume`, `KPI — MASI VAR PCT`.

---

### Requête 5 — Top 5 hausses du jour

**Nom à donner :** `Top 5 Hausses`
**Visualisation :** Tableau

```sql
SELECT rank, ticker, company_name, price AS cours, variation AS variation_pct
FROM cassandra.bourse_data.top_movers
WHERE date = current_date
  AND direction = 'up'
ORDER BY rank ASC;
```

---

### Requête 6 — Top 5 baisses du jour

**Nom à donner :** `Top 5 Baisses`
**Visualisation :** Tableau

```sql
SELECT rank, ticker, company_name, price AS cours, variation AS variation_pct
FROM cassandra.bourse_data.top_movers
WHERE date = current_date
  AND direction = 'down'
ORDER BY rank ASC;

```

---

### Requête 7 — Répartition hausses / baisses / stables

**Nom à donner :** `Répartition Marché — Camembert`
**Visualisation :** Camembert

```sql
  SELECT 'En hausse' AS statut, COUNT(*) AS nombre
  FROM cassandra.bourse_data.daily_prices
  WHERE date = current_date AND variation > 0

  UNION ALL

  SELECT 'En baisse' AS statut, COUNT(*) AS nombre
  FROM cassandra.bourse_data.daily_prices
  WHERE date = current_date AND variation < 0

  UNION ALL

  SELECT 'Stables' AS statut, COUNT(*) AS nombre
  FROM cassandra.bourse_data.daily_prices
  WHERE date = current_date AND variation = 0;
```

> Après **Visualiser** → cliquer sur l'icône de graphique → choisir **Camembert**.
> Assigner : Dimension = nom de la colonne, Métrique = valeur.

---

### Requête 8 — Tendance volume quotidien (30 jours)

**Nom à donner :** `Volume quotidien — 30j`
**Visualisation :** Courbe (X = date, Y = volume_millions_mad)

```sql
SELECT
    date,
    ROUND(global_volume / 1e6, 0) AS volume_millions_mad
FROM cassandra.bourse_data.market_stats
WHERE date >= DATE_ADD('day', -30, current_date)
ORDER BY date ASC;
```

---

### Requête 9 — MASI intraday (temps réel)

**Nom à donner :** `MASI — Intraday temps réel`
**Visualisation :** Courbe (X = timestamp, Y = valeur_masi)

```sql
SELECT
    timestamp,
    ROUND(value, 2) AS valeur_masi
FROM cassandra.bourse_data.intraday_indices
WHERE index_name = 'MASI'
  AND date = current_date
ORDER BY timestamp ASC;
```

---

### Requête 10 — Capitalisation par secteur

**Nom à donner :** `Capitalisation par secteur`
**Visualisation :** Barres horizontales ou Camembert

```sql
SELECT
    ist.sector,
    ROUND(SUM(dp.market_cap) / 1e9, 2) AS capitalisation_milliards,
    COUNT(DISTINCT dp.ticker)           AS nb_instruments
FROM cassandra.bourse_data.daily_prices dp
LEFT JOIN cassandra.bourse_data.instruments_static ist
    ON dp.ticker = ist.ticker
WHERE dp.date = current_date
  AND ist.sector IS NOT NULL
GROUP BY ist.sector
ORDER BY capitalisation_milliards DESC;
```

---

### Requête 11 — Évolution historique OHLC par instrument

**Nom à donner :** `Historique OHLC — {{ticker}}`
**Visualisation :** Courbe (X = date, Y = cloture)

```sql
SELECT
    date,
    open_price      AS ouverture,
    high_price      AS plus_haut,
    low_price       AS plus_bas,
    close_price     AS cloture,
    volume
FROM cassandra.bourse_data.historical_prices
WHERE ticker = {{ticker}}
ORDER BY date DESC
LIMIT 90;
```

> `{{ticker}}` est un **filtre Metabase** : Metabase génère automatiquement un champ
> de saisie dans le dashboard pour filtrer par instrument.

---

### Requête 12 — Fiche instrument (cours + stats)

**Nom à donner :** `Fiche Instrument — {{ticker}}`
**Visualisation :** Tableau

```sql
 SELECT
      dp.ticker,
      i.name           AS societe,
      ist.sector,
      ist.isin,
      dp.close_price   AS cours_cloture,
      dp.open_price    AS cours_ouverture,
      dp.high_price    AS plus_haut,
      dp.low_price     AS plus_bas,
      dp.variation     AS variation_pct,
      dp.volume        AS volume_mad,
      dp.market_cap    AS capitalisation
  FROM cassandra.bourse_data.daily_prices dp
  LEFT JOIN cassandra.bourse_data.instruments_static ist
      ON dp.ticker = ist.ticker
  LEFT JOIN cassandra.bourse_data.instruments i
      ON dp.ticker = i.ticker
  WHERE dp.ticker = {{ticker}}
    AND dp.date = current_date;
```

---

## Étape 2 — Créer le Dashboard

Aller dans **Dashboards** → **Nouveau tableau de bord** :

- **Nom :** `Marché Boursier — Casablanca`
- **Description :** `Suivi en temps réel des indices boursiers, cours et volumes de la Bourse de Casablanca (BVC) — données collectées toutes les 2 minutes et enrichies quotidiennement via pipeline Big Data (Cassandra · Trino · Prefect).`

---

## Étape 3 — Page 1 : Vue Générale des KPIs

Cliquer sur **+** pour ajouter des questions au dashboard.

### Disposition recommandée

```
┌─────────────────────────────────────────────────────────────────────┐
│  KPI — MASI      │  KPI — Var%     │  KPI — Volume  │  KPI — Capi  │
├──────────────────┴─────────────────┴────────────────┴──────────────┤
│                                                                     │
│            MASI — Évolution 30 jours  (Courbe)                     │
│                                                                     │
├───────────────────────────────────┬─────────────────────────────────┤
│  Performance sectorielle (Barres) │  Répartition Marché (Camembert) │
├───────────────────────────────────┴─────────────────────────────────┤
│  Top 5 Hausses (Tableau)          │  Top 5 Baisses (Tableau)        │
├───────────────────────────────────┴─────────────────────────────────┤
│                                                                     │
│            Volume quotidien — 30j  (Courbe aire)                   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Capitalisation par secteur (Barres horizontales)                   │
├─────────────────────────────────────────────────────────────────────┤
│  Top 10 — Volume du jour (Tableau)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Questions à ajouter (dans l'ordre)

| Position                 | Question sauvegardée             | Type de visualisation |
| ------------------------ | -------------------------------- | --------------------- |
| Ligne 1 (4 colonnes)     | `KPI — MASI`                     | Nombre                |
| Ligne 1 (4 colonnes)     | `KPI — Variation %`              | Nombre                |
| Ligne 1 (4 colonnes)     | `KPI — Volume`                   | Nombre                |
| Ligne 1 (4 colonnes)     | `KPI — Capitalisation`           | Nombre                |
| Ligne 2 (pleine largeur) | `MASI — Évolution 30 jours`      | Courbe                |
| Ligne 3 (moitié gauche)  | `Performance sectorielle — 30j`  | Barres                |
| Ligne 3 (moitié droite)  | `Répartition Marché — Camembert` | Camembert             |
| Ligne 4 (moitié gauche)  | `Top 5 Hausses`                  | Tableau               |
| Ligne 4 (moitié droite)  | `Top 5 Baisses`                  | Tableau               |
| Ligne 5 (pleine largeur) | `Volume quotidien — 30j`         | Courbe                |
| Ligne 6 (pleine largeur) | `Capitalisation par secteur`     | Barres horiz.         |
| Ligne 7 (pleine largeur) | `Top 10 — Volume du jour`        | Tableau               |

---

## Étape 4 — Page 2 : Vue par Instrument (avec filtre)

### Ajouter une 2ème page au dashboard

Dans le dashboard, cliquer sur **+** à côté du nom de la page (en haut) → **Ajouter une page** → nommer `Analyse par Instrument`.

### Ajouter le filtre

1. Cliquer sur l'icône **filtre** (🔽) en haut du dashboard
2. **Ajouter un filtre** → Type : **Texte ou catégorie** → **Est**
3. Nommer le filtre : `Instrument (Ticker)`
4. Connecter ce filtre à chaque question contenant `{{ticker}}` :
   - Cliquer sur chaque carte → icône engrenage → associer le champ `ticker`

### Disposition recommandée

```
┌─────────────────────────────────────────────────────────────────────┐
│  Filtre : Instrument (Ticker)  [ATW ▼]                              │
├─────────────────────────────────────────────────────────────────────┤
│  Fiche Instrument — {{ticker}}  (Tableau — cours du jour)           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│         Historique OHLC — {{ticker}}  (Courbe 90 jours)            │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│         MASI — Intraday temps réel  (Courbe du jour)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Questions à ajouter

| Question sauvegardée            | Type    | Filtre connecté      |
| ------------------------------- | ------- | -------------------- |
| `Fiche Instrument — {{ticker}}` | Tableau | Oui → champ `ticker` |
| `Historique OHLC — {{ticker}}`  | Courbe  | Oui → champ `ticker` |
| `MASI — Intraday temps réel`    | Courbe  | Non (fixé sur MASI)  |

### Utilisation du filtre

Saisir le ticker de l'un des 10 instruments suivis :

| Ticker | Société                   |
| ------ | ------------------------- |
| ATW    | Attijariwafa Bank         |
| BCP    | Banque Centrale Populaire |
| IAM    | Itissalat Al-Maghrib      |
| MNG    | Managem                   |
| ADH    | Douja Prom Addoha         |
| CIH    | CIH Bank                  |
| ALM    | Aluminium du Maroc        |
| DHO    | Delta Holding             |
| HPS    | HPS                       |
| ATH    | Auto Hall                 |

---

## Étape 5 — Paramètres finaux du dashboard

1. Cliquer **Sauvegarder** en haut à droite
2. Activer **Rafraîchissement automatique** : cliquer sur l'icône horloge → **2 minutes**
3. Passer en **mode plein écran** pour affichage en salle : icône ⛶

---

## Récapitulatif des questions créées

| #   | Nom                                    | Page        | Visualisation |
| --- | -------------------------------------- | ----------- | ------------- |
| 1   | Top 10 — Volume du jour                | Page 1      | Tableau       |
| 2   | Performance sectorielle — 30j          | Page 1      | Barres        |
| 3   | MASI — Évolution 30 jours              | Page 1      | Courbe        |
| 4   | KPI — MASI / Variation / Volume / Capi | Page 1      | Nombres (×4)  |
| 5   | Top 5 Hausses                          | Page 1      | Tableau       |
| 6   | Top 5 Baisses                          | Page 1      | Tableau       |
| 7   | Répartition Marché — Camembert         | Page 1      | Camembert     |
| 8   | Volume quotidien — 30j                 | Page 1      | Courbe        |
| 9   | MASI — Intraday temps réel             | Pages 1 & 2 | Courbe        |
| 10  | Capitalisation par secteur             | Page 1      | Barres horiz. |
| 11  | Historique OHLC — {{ticker}}           | Page 2      | Courbe        |
| 12  | Fiche Instrument — {{ticker}}          | Page 2      | Tableau       |
