#!/usr/bin/env python3
"""
Vérifie que Cassandra, Trino et Metabase sont accessibles.
Usage : py -3 scripts/verify_stack.py
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def check_cassandra() -> bool:
    host = os.getenv("CASSANDRA_HOST", "localhost")
    port = int(os.getenv("CASSANDRA_PORT", "9042"))
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "bourse_data")

    try:
        os.environ.setdefault("CASS_DRIVER_NO_EXTENSIONS", "1")
        from cassandra.cluster import Cluster

        cluster = Cluster([host], port=port, connect_timeout=10)
        session = cluster.connect()
        rows = session.execute(
            "SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name = %s",
            (keyspace,),
        )
        found = len(list(rows)) > 0
        cluster.shutdown()
        status = "OK" if found else f"WARN (keyspace {keyspace} absent — lancer init.cql)"
        print(f"  Cassandra ({host}:{port}) : {status}")
        return found
    except ImportError:
        print("  Cassandra : SKIP (cassandra-driver non installé)")
    except Exception as exc:
        print(f"  Cassandra driver : WARN ({exc})")

    return _check_cassandra_via_docker(keyspace)


def _check_cassandra_via_docker(keyspace: str) -> bool:
    import subprocess

    try:
        result = subprocess.run(
            [
                "docker", "exec", "cassandra", "cqlsh", "-e",
                f"DESCRIBE TABLES;",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"  Cassandra (docker) : FAIL ({result.stderr.strip()})")
            return False
        found = keyspace in result.stdout or "daily_prices" in result.stdout
        status = "OK (via docker)" if found else f"WARN (keyspace {keyspace} absent)"
        print(f"  Cassandra : {status}")
        return found
    except Exception as exc:
        print(f"  Cassandra (docker) : FAIL ({exc})")
        return False


def check_trino() -> bool:
    host = os.getenv("TRINO_HOST", "localhost")
    port = os.getenv("TRINO_PORT", "8080")
    catalog = os.getenv("TRINO_CATALOG", "cassandra")
    schema = os.getenv("TRINO_SCHEMA", "bourse_data")
    url = f"http://{host}:{port}/v1/statement"
    headers = {"X-Trino-User": os.getenv("TRINO_USER", "reporting")}
    query = f"SHOW TABLES FROM {catalog}.{schema}"

    try:
        response = requests.post(url, data=query, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"  Trino ({host}:{port}) : FAIL (HTTP {response.status_code})")
            return False
        data = response.json()
        if data.get("error"):
            print(f"  Trino : FAIL ({data['error'].get('message', data['error'])})")
            return False
        print(f"  Trino ({host}:{port}) : OK (catalog={catalog}, schema={schema})")
        return True
    except Exception as exc:
        print(f"  Trino ({host}:{port}) : FAIL ({exc})")
        return False


def check_metabase() -> bool:
    url = os.getenv("METABASE_URL", "http://localhost:3000")
    try:
        response = requests.get(f"{url}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"  Metabase ({url}) : OK")
            return True
        print(f"  Metabase ({url}) : FAIL (HTTP {response.status_code})")
        return False
    except Exception as exc:
        print(f"  Metabase ({url}) : FAIL ({exc})")
        return False


def check_prefect() -> bool:
    url = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print(f"  Prefect ({url}) : OK")
            return True
        print(f"  Prefect ({url}) : FAIL (HTTP {response.status_code})")
        return False
    except Exception as exc:
        print(f"  Prefect ({url}) : FAIL ({exc})")
        return False


def main():
    print("=" * 60)
    print("VERIFICATION STACK BOURSE DE CASABLANCA")
    print("=" * 60)

    results = [
        check_cassandra(),
        check_trino(),
        check_metabase(),
        check_prefect(),
    ]

    print("=" * 60)
    if all(results):
        print("Stack prete pour l'analyse et le reporting.")
        print("Guide : docs/ANALYSE_REPORTING.md")
    else:
        print("Certains services sont indisponibles.")
        print("Lancer : docker compose up -d")
        print("Puis   : .\\scripts\\init_infrastructure.ps1")
    print("=" * 60)
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
