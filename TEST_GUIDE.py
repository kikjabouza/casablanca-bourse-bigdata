#!/usr/bin/env python3
"""
Guide interactif de test des modifications

Lance les différents tests et valide les modifications du projet
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
TESTS_DIR = PROJECT_ROOT / "tests"
DATA_DIR = TESTS_DIR / "data"


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title):
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)


def check_files_exist():
    """Vérifie que les fichiers attendus existent et les obsolètes sont supprimés"""
    print_section("✓ Vérification des fichiers")
    
    # Fichiers qui ne doivent PAS exister
    obsolete_files = [
        "src/scrapers/masi_realtime_scraper.py",
        "tests/test_01_get_instrument_id.py",
        "tests/test_03_instruments_list.py",
        "tests/test_05_full_workflow.py",
        "tests/test_06_masi_realtime.py",
        "tests/test_scrapers.py",
        "tests/view_all_results.py",
    ]
    
    obsolete_found = []
    for file in obsolete_files:
        if (PROJECT_ROOT / file).exists():
            obsolete_found.append(file)
    
    if obsolete_found:
        print(f"❌ Fichiers obsolètes trouvés:")
        for f in obsolete_found:
            print(f"   - {f}")
        return False
    else:
        print("✅ Tous les fichiers obsolètes ont été supprimés")
    
    # Fichiers qui DOIVENT exister
    required_files = [
        "tests/test_03_instruments_list_v2.py",
        "tests/test_04_instrument_details.py",
        "tests/test_02_historical_data.py",
        "tests/test_08_market_overview_complete.py",
        "tests/test_all_scrapers.py",
        "src/main.py",
        "scripts/scrape.py",
        "scripts/verify_stack.py",
        "scripts/init_infrastructure.ps1",
        "cassandra/data/README.md",
        "MODIFICATIONS.md",
    ]
    
    missing_files = []
    for file in required_files:
        if not (PROJECT_ROOT / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Fichiers manquants:")
        for f in missing_files:
            print(f"   - {f}")
        return False
    else:
        print(f"✅ Tous les {len(required_files)} fichiers attendus sont présents")
    
    return True


def test_imports():
    """Teste que les imports fonctionnent"""
    print_section("✓ Vérification des imports")
    
    try:
        from src.main import BourseScraperOrchestrator
        print("✅ BourseScraperOrchestrator importé")
        
        from src.storage.cassandra_client import CassandraClient
        print("✅ CassandraClient importé")
        
        from src.scrapers.market_overview_scraper import MarketOverviewScraper
        print("✅ MarketOverviewScraper importé")
        
        # Vérifier que masi_realtime n'existe plus
        try:
            from src.scrapers.masi_realtime_scraper import MASIRealtimeScraper
            print("❌ masi_realtime_scraper devrait être supprimé!")
            return False
        except ImportError:
            print("✅ masi_realtime_scraper supprimé avec succès")
        
        return True
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_cassandra_modes():
    """Teste les modes test/production de Cassandra"""
    print_section("✓ Vérification des modes Cassandra")
    
    try:
        from src.storage.cassandra_client import CassandraClient
        
        # Mode test
        client_test = CassandraClient(test_mode=True)
        if client_test.test_mode:
            print("✅ Mode test activé correctement")
        else:
            print("❌ Mode test ne fonctionne pas")
            return False
        
        # Mode production
        client_prod = CassandraClient(test_mode=False)
        print(f"✅ Mode production: test_mode={client_prod.test_mode}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_main_methods():
    """Teste que main.py a les bonnes méthodes"""
    print_section("✓ Vérification des méthodes de BourseScraperOrchestrator")
    
    try:
        from src.main import BourseScraperOrchestrator
        
        orchestrator = BourseScraperOrchestrator()
        
        methods = [
            'run_full_scraping',
            'run_daily_update',
            'run_market_overview_only'
        ]
        
        for method in methods:
            if hasattr(orchestrator, method):
                print(f"✅ Méthode '{method}' existe")
            else:
                print(f"❌ Méthode '{method}' manquante")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def check_test_data():
    """Vérifie que les fichiers de résultats de test existent"""
    print_section("✓ Vérification des résultats de test")
    
    expected_data_files = [
        "all_instruments.json",
        "MNG_details.json",
        "MNG_historical.json",
        "market_overview_complete.json",
    ]
    
    found_files = []
    missing_files = []
    
    for file in expected_data_files:
        file_path = DATA_DIR / file
        if file_path.exists():
            found_files.append(file)
        else:
            missing_files.append(file)
    
    if found_files:
        print(f"✅ Fichiers de test trouvés ({len(found_files)}):")
        for f in found_files:
            print(f"   - {f}")
    
    if missing_files:
        print(f"⚠️  Fichiers de test manquants ({len(missing_files)}) - lancer les tests pour générer:")
        for f in missing_files:
            print(f"   - {f}")
    
    return True


def check_cassandra_data_dir():
    """Vérifie la structure du dossier cassandra/data"""
    print_section("✓ Vérification du dossier cassandra/data")
    
    cassandra_data = PROJECT_ROOT / "cassandra" / "data"
    
    if cassandra_data.exists():
        print(f"✅ Dossier cassandra/data existe")
        
        if (cassandra_data / "README.md").exists():
            print(f"✅ cassandra/data/README.md existe")
        else:
            print(f"❌ cassandra/data/README.md manquant")
            return False
        
        return True
    else:
        print(f"❌ Dossier cassandra/data manquant")
        return False


def run_test_suite():
    """Lance le test global de tous les scrapers"""
    print_section("🚀 Exécution du test global (test_all_scrapers.py)")
    print("⏳ Ceci peut prendre quelques minutes...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "test_all_scrapers.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=300
        )
        
        print(result.stdout.decode('utf-8'))
        
        if result.returncode == 0:
            print("✅ Tests exécutés avec succès")
            
            # Vérifier les résultats
            results_file = DATA_DIR / "all_tests_results.json"
            if results_file.exists():
                with open(results_file) as f:
                    results = json.load(f)
                print(f"\n📊 Résumé des tests:")
                print(f"   Tests réussis: {results['summary'].get('successful', 0)}")
                print(f"   Tests échoués: {results['summary'].get('failed', 0)}")
                print(f"   Taux de réussite: {results['summary'].get('success_rate', 'N/A')}")
            
            return True
        else:
            print(f"❌ Tests échoués (code: {result.returncode})")
            print(result.stderr.decode('utf-8'))
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout lors de l'exécution des tests")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def generate_summary(results):
    """Génère un résumé des tests"""
    print_header("📋 RÉSUMÉ DES VÉRIFICATIONS")
    
    checks = [
        ("Fichiers", results.get('files', False)),
        ("Imports", results.get('imports', False)),
        ("Modes Cassandra", results.get('cassandra_modes', False)),
        ("Méthodes main.py", results.get('main_methods', False)),
        ("Dossier cassandra/data", results.get('cassandra_data_dir', False)),
        ("Test suite", results.get('test_suite', None)),
    ]
    
    passed = sum(1 for _, result in checks if result is True)
    failed = sum(1 for _, result in checks if result is False)
    skipped = sum(1 for _, result in checks if result is None)
    
    print("\n")
    for name, result in checks:
        if result is True:
            print(f"  ✅ {name}")
        elif result is False:
            print(f"  ❌ {name}")
        else:
            print(f"  ⏭️  {name} (non exécuté)")
    
    print("\n" + "-" * 80)
    print(f"✅ Réussi: {passed}")
    print(f"❌ Échoué: {failed}")
    print(f"⏭️  Skippé: {skipped}")
    
    if failed == 0:
        print("\n🎉 TOUTES LES VÉRIFICATIONS SONT PASSÉES!")
        return True
    else:
        print(f"\n⚠️  {failed} vérification(s) ont échoué")
        return False


def main():
    print_header("🧪 GUIDE DE TEST - MODIFICATIONS DU PROJET")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Projet: {PROJECT_ROOT}")
    
    results = {}
    
    # Test 1: Fichiers
    results['files'] = check_files_exist()
    
    # Test 2: Imports
    results['imports'] = test_imports()
    
    # Test 3: Modes Cassandra
    results['cassandra_modes'] = test_cassandra_modes()
    
    # Test 4: Méthodes main.py
    results['main_methods'] = test_main_methods()
    
    # Test 5: Dossier cassandra/data
    results['cassandra_data_dir'] = check_cassandra_data_dir()
    
    # Test 6: Vérifier les données de test
    check_test_data()
    
    # Test 7: Optionnel - Exécuter le test suite
    print_section("🚀 TESTS OPTIONNELS")
    user_input = input("Voulez-vous exécuter le test global (test_all_scrapers.py)? [y/n]: ").strip().lower()
    
    if user_input in ['y', 'yes', 'o', 'oui']:
        results['test_suite'] = run_test_suite()
    else:
        print("Test suite ignoré (utilisez: python tests/test_all_scrapers.py)")
        results['test_suite'] = None
    
    # Résumé
    success = generate_summary(results)
    
    print_header("📚 DOCUMENTATION")
    print("""
Voir pour plus d'informations:
  - MODIFICATIONS.md        - Documentation complète des changements
  - src/main.py            - Code de scraping principal
  - tests/test_all_scrapers.py - Test global
  - cassandra/data/README.md   - Stockage intermédiaire
  
Commandes utiles:
  python -m src.main              # Scraping complet
  python -m src.main --daily      # Mise à jour quotidienne
  python -m src.main --overview   # Market overview uniquement
  python tests/test_all_scrapers.py  # Tous les tests
  python scripts/verify_stack.py   # Vérifier Cassandra/Trino/Metabase
    """)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
