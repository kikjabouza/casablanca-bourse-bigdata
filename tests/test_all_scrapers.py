"""
Test Global: Exécuter tous les tests des scrapers à la fois
Lance les 4 scrapers principaux en séquence avec rapports détaillés
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger, get_logger

# Importer les tests finaux
from tests.test_03_instruments_list_v2 import test_instruments_list_via_api
from tests.test_04_instrument_details import test_instrument_details
from tests.test_02_historical_data import test_historical_data
from tests.test_08_market_overview_complete import test_market_overview_complete

setup_logger()
logger = get_logger(__name__)

# Configuration des données de résultats
RESULTS_FILE = Path(__file__).parent / "data" / "all_tests_results.json"


def run_all_tests():
    """
    Lance tous les tests des scrapers
    """
    print("\n" + "=" * 80)
    print("🚀 EXÉCUTION COMPLÈTE DE TOUS LES TESTS DES SCRAPERS")
    print("=" * 80)
    
    start_time = datetime.now()
    results = {
        "timestamp": start_time.isoformat(),
        "tests": {},
        "summary": {}
    }
    
    # Test 1: Instruments List
    print("\n" + "🔷" * 40)
    print("TEST 1/4: LISTE DES INSTRUMENTS")
    print("🔷" * 40)
    try:
        test_start = time.time()
        instruments = test_instruments_list_via_api()
        test_duration = time.time() - test_start
        
        if instruments:
            results["tests"]["instruments_list"] = {
                "status": "✅ SUCCÈS",
                "count": len(instruments),
                "duration_seconds": test_duration,
                "tickers": [i['ticker'] for i in instruments]
            }
            print(f"⏱️  Durée: {test_duration:.2f}s")
        else:
            results["tests"]["instruments_list"] = {
                "status": "❌ ÉCHOUÉ",
                "error": "Aucun instrument retourné",
                "duration_seconds": test_duration
            }
    except Exception as e:
        results["tests"]["instruments_list"] = {
            "status": "❌ ERREUR",
            "error": str(e),
            "duration_seconds": time.time() - test_start
        }
        print(f"❌ ERREUR: {e}")
    
    # Test 2: Instrument Details
    print("\n" + "🔶" * 40)
    print("TEST 2/4: DÉTAILS DES INSTRUMENTS")
    print("🔶" * 40)
    try:
        test_start = time.time()
        details = test_instrument_details("MNG")
        test_duration = time.time() - test_start
        
        if details:
            results["tests"]["instrument_details"] = {
                "status": "✅ SUCCÈS",
                "ticker": "MNG",
                "fields": len(details),
                "duration_seconds": test_duration
            }
            print(f"⏱️  Durée: {test_duration:.2f}s")
        else:
            results["tests"]["instrument_details"] = {
                "status": "❌ ÉCHOUÉ",
                "error": "Aucun détail retourné",
                "duration_seconds": test_duration
            }
    except Exception as e:
        results["tests"]["instrument_details"] = {
            "status": "❌ ERREUR",
            "error": str(e),
            "duration_seconds": time.time() - test_start
        }
        print(f"❌ ERREUR: {e}")
    
    # Test 3: Historical Data
    print("\n" + "🔵" * 40)
    print("TEST 3/4: DONNÉES HISTORIQUES")
    print("🔵" * 40)
    try:
        test_start = time.time()
        historical = test_historical_data("MNG", limit_days=30)
        test_duration = time.time() - test_start
        
        if historical:
            results["tests"]["historical_data"] = {
                "status": "✅ SUCCÈS",
                "ticker": "MNG",
                "records_count": len(historical),
                "duration_seconds": test_duration
            }
            print(f"⏱️  Durée: {test_duration:.2f}s")
        else:
            results["tests"]["historical_data"] = {
                "status": "❌ ÉCHOUÉ",
                "error": "Aucune donnée retournée",
                "duration_seconds": test_duration
            }
    except Exception as e:
        results["tests"]["historical_data"] = {
            "status": "❌ ERREUR",
            "error": str(e),
            "duration_seconds": time.time() - test_start
        }
        print(f"❌ ERREUR: {e}")
    
    # Test 4: Market Overview
    print("\n" + "🟢" * 40)
    print("TEST 4/4: MARKET OVERVIEW COMPLET")
    print("🟢" * 40)
    try:
        test_start = time.time()
        market_data = test_market_overview_complete()
        test_duration = time.time() - test_start
        
        if market_data:
            results["tests"]["market_overview"] = {
                "status": "✅ SUCCÈS",
                "indices_count": len(market_data.get("indices", {})),
                "futures_count": len(market_data.get("futures", [])),
                "top_gainers": len(market_data.get("top_gainers", [])),
                "top_losers": len(market_data.get("top_losers", [])),
                "duration_seconds": test_duration
            }
            print(f"⏱️  Durée: {test_duration:.2f}s")
        else:
            results["tests"]["market_overview"] = {
                "status": "❌ ÉCHOUÉ",
                "error": "Aucune donnée retournée",
                "duration_seconds": test_duration
            }
    except Exception as e:
        results["tests"]["market_overview"] = {
            "status": "❌ ERREUR",
            "error": str(e),
            "duration_seconds": time.time() - test_start
        }
        print(f"❌ ERREUR: {e}")
    
    # Calcul du résumé
    total_duration = (datetime.now() - start_time).total_seconds()
    successful_tests = sum(1 for t in results["tests"].values() if "SUCCÈS" in t["status"])
    total_tests = len(results["tests"])
    
    results["summary"] = {
        "total_tests": total_tests,
        "successful": successful_tests,
        "failed": total_tests - successful_tests,
        "success_rate": f"{(successful_tests/total_tests)*100:.1f}%",
        "total_duration_seconds": total_duration
    }
    
    # Affichage du résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)
    print(f"Tests exécutés: {total_tests}")
    print(f"Succès: {successful_tests}")
    print(f"Échoués: {total_tests - successful_tests}")
    print(f"Taux de réussite: {results['summary']['success_rate']}")
    print(f"Durée totale: {total_duration:.2f}s")
    
    # Détails de chaque test
    print("\n" + "-" * 80)
    print("DÉTAILS DES TESTS")
    print("-" * 80)
    for test_name, test_result in results["tests"].items():
        status = test_result["status"]
        duration = test_result.get("duration_seconds", 0)
        print(f"{test_name:30} | {status:15} | Durée: {duration:.2f}s")
        
        if "error" in test_result:
            print(f"  └─ Erreur: {test_result['error']}")
        else:
            # Afficher les détails spécifiques
            for key, value in test_result.items():
                if key not in ["status", "duration_seconds"]:
                    print(f"  └─ {key}: {value}")
    
    # Sauvegarder les résultats
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Résultats complets sauvegardés dans {RESULTS_FILE}")
    
    print("\n" + "=" * 80)
    if successful_tests == total_tests:
        print("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
    else:
        print(f"⚠️  {total_tests - successful_tests} test(s) ont échoué")
    print("=" * 80 + "\n")
    
    return results


if __name__ == "__main__":
    run_all_tests()
