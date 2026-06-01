"""
Script utilitaire pour vérifier l'intégrité de la stack (Cassandra, Trino, Metabase)

Usage: python scripts/verify_stack.py
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)


def check_cassandra() -> bool:
    """Vérifie la connexion à Cassandra"""
    host = os.getenv("CASSANDRA_HOST", "localhost")
    port = int(os.getenv("CASSANDRA_PORT", "9042"))
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "bourse_data")

    try:
        os.environ.setdefault("CASS_DRIVER_NO_EXTENSIONS", "1")
        from cassandra.cluster import Cluster

        cluster = Cluster([host], port=port, connect_timeout=10)
        session = cluster.connect()
        rows = session.execute(f"SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name='{keyspace}'")
        
        if rows:
            logger.info(f"✅ Cassandra: Keyspace '{keyspace}' trouvé")
            session.shutdown()
            return True
        else:
            logger.warning(f"⚠️  Cassandra: Keyspace '{keyspace}' non trouvé")
            return False
            
    except ImportError:
        logger.warning("⚠️  Cassandra driver non installé")
        return False
    except Exception as e:
        logger.error(f"❌ Cassandra: Erreur de connexion - {e}")
        return False


def check_trino() -> bool:
    """Vérifie la connexion à Trino"""
    host = os.getenv("TRINO_HOST", "localhost")
    port = int(os.getenv("TRINO_PORT", "8080"))
    url = f"http://{host}:{port}/ui"
    
    try:
        response = requests.head(url, timeout=5)
        if response.status_code < 500:
            logger.info("✅ Trino: Accessible")
            return True
        else:
            logger.warning(f"⚠️  Trino: Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Trino: Non accessible - {e}")
        return False


def check_metabase() -> bool:
    """Vérifie la connexion à Metabase"""
    host = os.getenv("METABASE_HOST", "localhost")
    port = int(os.getenv("METABASE_PORT", "3000"))
    url = f"http://{host}:{port}/api/health"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Metabase: Accessible")
            return True
        else:
            logger.warning(f"⚠️  Metabase: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Metabase: Non accessible - {e}")
        return False


def main():
    logger.info("=" * 60)
    logger.info("Vérification de la stack")
    logger.info("=" * 60)
    
    results = {
        "Cassandra": check_cassandra(),
        "Trino": check_trino(),
        "Metabase": check_metabase()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("Résumé:")
    for service, status in results.items():
        status_text = "✅ OK" if status else "❌ KO"
        logger.info(f"  {service:20} {status_text}")
    logger.info("=" * 60)
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
