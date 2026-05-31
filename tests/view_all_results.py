"""
Visualise tous les résultats des tests
"""

import json
from pathlib import Path


def view_all_results():
    """Affiche un résumé de tous les résultats sauvegardés"""
    print("\n" + "="*70)
    print("📊 VISUALISATION DE TOUS LES RÉSULTATS")
    print("="*70)
    
    data_dir = Path(__file__).parent / "data"
    
    if not data_dir.exists():
        print("❌ Dossier data/ non trouvé. Lancez d'abord les tests.")
        return
    
    # 1. IDs des instruments
    print("\n" + "─"*70)
    print("1️⃣ INSTRUMENTS IDs")
    print("─"*70)
    ids_file = data_dir / "instruments_ids.json"
    if ids_file.exists():
        with open(ids_file, 'r', encoding='utf-8') as f:
            ids = json.load(f)
        print(f"\n✅ {len(ids)} instruments trouvés:")
        for ticker, id_val in ids.items():
            print(f"   {ticker:6} -> ID: {id_val}")
    else:
        print("❌ Fichier non trouvé")
    
    # 2. Liste des instruments
    print("\n" + "─"*70)
    print("2️⃣ LISTE DES INSTRUMENTS (API)")
    print("─"*70)
    all_inst_file = data_dir / "all_instruments.json"
    if all_inst_file.exists():
        with open(all_inst_file, 'r', encoding='utf-8') as f:
            instruments = json.load(f)
        print(f"\n✅ {len(instruments)} instruments:")
        for inst in instruments:
            print(f"   {inst['ticker']:6} (ID: {inst['id']})")
    else:
        print("❌ Fichier non trouvé - Lancez test_03_instruments_list_v2.py")
    
    # 3. Détails MNG
    print("\n" + "─"*70)
    print("3️⃣ DÉTAILS INSTRUMENT (MNG)")
    print("─"*70)
    details_file = data_dir / "MNG_details.json"
    if details_file.exists():
        with open(details_file, 'r', encoding='utf-8') as f:
            details = json.load(f)
        print(f"\n✅ Informations pour {details.get('ticker')}:")
        print(f"   ISIN: {details.get('isin')}")
        print(f"   Secteur: {details.get('sector')}")
        print(f"   Cours actuel: {details.get('current_price')} MAD")
        print(f"   Variation: {details.get('variation')}%")
        print(f"   Capitalisation: {details.get('market_cap'):,.0f} MAD")
        print(f"   Volume: {details.get('volume'):,.0f} MAD")
    else:
        print("❌ Fichier non trouvé")
    
    # 4. Données historiques MNG
    print("\n" + "─"*70)
    print("4️⃣ HISTORIQUE INSTRUMENT (MNG)")
    print("─"*70)
    hist_file = data_dir / "MNG_historical.json"
    if hist_file.exists():
        with open(hist_file, 'r', encoding='utf-8') as f:
            hist = json.load(f)
        print(f"\n✅ {len(hist)} jours historiques:")
        print(f"   Période: {hist[0].get('date')} à {hist[-1].get('date')}")
        closes = [h.get('close_price', 0) for h in hist if h.get('close_price') is not None]
        if closes:
            print(f"   Prix min: {min(closes):.2f} MAD")
            print(f"   Prix max: {max(closes):.2f} MAD")
            print(f"   Moyenne: {sum(closes)/len(closes):.2f} MAD")
            print(f"   Variation: {((closes[-1] - closes[0]) / closes[0] * 100):.2f}%")
    else:
        print("❌ Fichier non trouvé")
    
    # 5. MASI temps réel
    print("\n" + "─"*70)
    print("5️⃣ MASI TEMPS RÉEL")
    print("─"*70)
    masi_file = data_dir / "masi_realtime.json"
    if masi_file.exists():
        with open(masi_file, 'r', encoding='utf-8') as f:
            masi = json.load(f)
        print(f"\n✅ {len(masi.get('points', []))} points MASI sauvegardés:")
        for point in masi.get('points', [])[:3]:
            print(f"   {point.get('index_name')}: {point.get('value'):.2f} pts ({point.get('timestamp')})")
    else:
        print("❌ Fichier non trouvé - Lancez test_06_masi_realtime.py")
    
    # 6. Market overview
    print("\n" + "─"*70)
    print("6️⃣ MARKET OVERVIEW")
    print("─"*70)
    for market_file_name in ("market_overview_complete.json", "market_overview.json"):
        market_file = data_dir / market_file_name
        if not market_file.exists():
            continue

        with open(market_file, "r", encoding="utf-8") as handle:
            market = json.load(handle)

        print(f"\n✅ Market overview ({market_file_name}) du {market.get('date')}:")

        print("\n   Indices:")
        for name, idx_data in market.get("indices", {}).items():
            print(
                f"      {name}: {idx_data.get('value')} "
                f"({idx_data.get('variation')}%, YTD: {idx_data.get('annual_variation')}%)"
            )

        print("\n   Futures MASI20:")
        for future in market.get("futures", []):
            print(
                f"      {future.get('name')}: {future.get('value')} "
                f"({future.get('variation')}%)"
            )

        print("\n   Stats globales:")
        stats = market.get("market_stats", {})
        print(f"      Volume: {stats.get('global_volume', 0):,.0f} MAD")
        print(f"      Capitalisation: {stats.get('market_cap', 0):,.0f} MAD")

        gainers = market.get("top_gainers") or market.get("top_movers", {}).get("top_gainers", [])
        losers = market.get("top_losers") or market.get("top_movers", {}).get("top_losers", [])

        print(f"\n   Top Gainers ({len(gainers)}):")
        for mover in gainers[:5]:
            print(
                f"      {mover.get('ticker')}: {mover.get('price')} MAD "
                f"(+{mover.get('variation')}%)"
            )

        print(f"\n   Top Losers ({len(losers)}):")
        for mover in losers[:5]:
            print(
                f"      {mover.get('ticker')}: {mover.get('price')} MAD "
                f"({mover.get('variation')}%)"
            )
        break
    else:
        print("❌ Fichier non trouvé - Lancez test_07_market_overview.py ou test_08_market_overview_complete.py")
    
    # Résumé global
    print("\n" + "="*70)
    print("📈 RÉSUMÉ GLOBAL")
    print("="*70)
    
    files = list(data_dir.glob("*.json"))
    print(f"\n✅ {len(files)} fichiers de données sauvegardés:")
    total_size = 0
    for f in sorted(files):
        size = f.stat().st_size
        total_size += size
        print(f"   {f.name:30} ({size:>8} bytes)")
    
    print(f"\n💾 Taille totale: {total_size:,.0f} bytes ({total_size/1024:.1f} KB)")
    print("\n" + "="*70)


if __name__ == "__main__":
    view_all_results()
