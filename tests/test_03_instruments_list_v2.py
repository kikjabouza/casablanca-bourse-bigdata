"""
Test 3 BIS: Récupération de la liste des instruments via API
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

def test_instruments_list_via_api():
    """Teste la récupération de la liste via l'API JSON (plus fiable)"""
    print("\n" + "="*60)
    print("TEST 3 BIS: LISTE DES INSTRUMENTS VIA API JSON")
    print("="*60)
    
    # Lire les IDs déjà trouvés
    ids_file = Path(__file__).parent / "data" / "instruments_ids.json"
    if not ids_file.exists():
        print("❌ Aucun ID connu, lancez d'abord test_01")
        return None
    
    with open(ids_file, 'r', encoding='utf-8') as f:
        known_ids = json.load(f)
    
    print(f"\n📋 IDs récupérés: {len(known_ids)} instruments")
    
    # Liste des tickers à tester (ceux qu'on a déjà)
    test_tickers = list(known_ids.keys())
    
    if not test_tickers:
        print("❌ Aucun ID trouvé")
        return None
    
    instruments = []
    for ticker in test_tickers:
        instruments.append({
            'ticker': ticker,
            'name': ticker,
            'id': known_ids[ticker]
        })
    
    print(f"\n✅ {len(instruments)} instruments trouvés")
    
    # Afficher la liste
    print("\n📋 LISTE DES INSTRUMENTS:")
    print("-" * 50)
    for inst in instruments:
        print(f"   {inst['ticker']:6} (ID: {inst['id']})")
    
    # Sauvegarder
    output_file = Path(__file__).parent / "data" / "all_instruments.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(instruments, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Liste sauvegardée dans {output_file}")
    
    return instruments

if __name__ == "__main__":
    test_instruments_list_via_api()
