"""
Verification de l'état de la stack complète.
Teste la connectivité de chaque service Docker.

Usage: python scripts/verify_stack.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import requests

from src.utils.config import Config


def check_cassandra(config: Config) -> bool:
    print("  [Cassandra]...")
    try:
        from cassandra.cluster import Cluster
        cluster = Cluster(
            contact_points=[config.CASSANDRA_HOST],
            port=config.CASSANDRA_PORT,
            connect_timeout=5,
        )
        session = cluster.connect()
        rows = list(session.execute("SELECT cluster_name FROM system.local"))
        cluster_name = rows[0][0] if rows else "?"
        cluster.shutdown()
        print(f"  [OK] Cassandra accessible (cluster: {cluster_name})")
        return True
    except ImportError:
        print("  [WARN] cassandra-driver non installe (Python 3.13 incompatible)")
        return False
    except Exception as exc:
        print(f"  [FAIL] Cassandra: {exc}")
        return False


def check_trino(config: Config) -> bool:
    print("  [Trino]...")
    try:
        resp = requests.get(
            f"http://{config.TRINO_HOST}:{config.TRINO_PORT}/v1/info", timeout=5
        )
        if resp.status_code == 200:
            version = resp.json().get("nodeVersion", {}).get("version", "?")
            print(f"  [OK] Trino accessible (version: {version})")
            return True
        print(f"  [FAIL] Trino status HTTP: {resp.status_code}")
        return False
    except Exception as exc:
        print(f"  [FAIL] Trino: {exc}")
        return False


def check_prefect(config: Config) -> bool:
    print("  [Prefect]...")
    try:
        resp = requests.get(f"{config.PREFECT_API_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("  [OK] Prefect Server accessible -> http://localhost:4200")
            return True
        print(f"  [FAIL] Prefect status HTTP: {resp.status_code}")
        return False
    except Exception as exc:
        print(f"  [FAIL] Prefect: {exc}")
        return False


def check_metabase() -> bool:
    print("  [Metabase]...")
    try:
        resp = requests.get("http://localhost:3000/api/health", timeout=10)
        if resp.status_code == 200:
            print("  [OK] Metabase accessible -> http://localhost:3000")
            return True
        print(f"  [FAIL] Metabase status HTTP: {resp.status_code}")
        return False
    except Exception as exc:
        print(f"  [FAIL] Metabase: {exc}")
        return False


def check_bourse_website() -> bool:
    print("  [Site Bourse de Casablanca]...")
    try:
        resp = requests.get(
            "https://www.casablanca-bourse.com/fr/live-market/overview",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
            verify=False,
        )
        if resp.status_code == 200:
            print("  [OK] Site casablanca-bourse.com accessible")
            return True
        print(f"  [FAIL] Site status HTTP: {resp.status_code}")
        return False
    except Exception as exc:
        print(f"  [FAIL] Site Bourse: {exc}")
        return False


def main() -> int:
    config = Config()

    print("\n" + "=" * 60)
    print("  VERIFICATION DE LA STACK")
    print("=" * 60)

    results = {
        "cassandra": check_cassandra(config),
        "trino": check_trino(config),
        "prefect": check_prefect(config),
        "metabase": check_metabase(),
        "bourse_website": check_bourse_website(),
    }

    print("\n" + "=" * 60)
    ok = [k for k, v in results.items() if v]
    fail = [k for k, v in results.items() if not v]

    if not fail:
        print("  STATUT: STACK COMPLETEMENT OPERATIONNELLE")
    else:
        print(f"  STATUT: SERVICES EN ERREUR -> {', '.join(fail)}")
        if "bourse_website" not in fail:
            print("  NOTE: Le site de la bourse est accessible -> tests possibles")
        print("\n  Pour demarrer les services Docker:")
        print("    docker-compose up -d")

    print("=" * 60)
    return 0 if not fail else 1


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    sys.exit(main())
