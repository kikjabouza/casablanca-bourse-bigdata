"""
Script pour exécuter tous les tests séquentiellement
"""

import subprocess
import sys
from pathlib import Path


def run_test(script_name):
    """Exécute un script de test"""
    print(f"\n{'🚀'*40}")
    print(f"EXÉCUTION DE {script_name}")
    print(f"{'🚀'*40}")
    
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / script_name)],
        capture_output=False,
        text=True
    )
    
    return result.returncode == 0


def main():
    """Exécute tous les tests dans l'ordre"""
    
    tests = [
        "test_01_get_instrument_id.py",
        "test_03_instruments_list.py",
        "test_02_historical_data.py",
        "test_04_instrument_details.py",
        "test_05_full_workflow.py",
        "test_06_masi_realtime.py",
        "test_07_market_overview.py"
    ]
    
    print("\n" + "="*60)
    print("🏃 LANCEMENT DE TOUS LES TESTS")
    print("="*60)
    
    results = {}
    
    for test in tests:
        success = run_test(test)
        results[test] = success
        
        if not success:
            print(f"\n❌ Test {test} échoué. Arrêt de l'exécution.")
            break
        
        input("\nAppuyez sur Entrée pour continuer au test suivant...")
    
    # Résumé final
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    for test, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test}")
    
    print("\n💡 Les fichiers de données sont dans tests/data/")


if __name__ == "__main__":
    main()
