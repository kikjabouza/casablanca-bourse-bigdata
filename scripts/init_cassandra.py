"""
Initialisation du schéma Cassandra.
À exécuter APRÈS que le conteneur Cassandra soit démarré et en bonne santé.
Alternative au service cassandra-init du docker-compose.

Usage: python scripts/init_cassandra.py
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config import Config
from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

SCHEMA_FILE = ROOT / "cassandra" / "init.cql"


def init_cassandra() -> None:
    config = Config()

    try:
        from cassandra.cluster import Cluster
    except ImportError:
        logger.error(
            "cassandra-driver non installe. "
            "Installez Python 3.11 ou 3.12, puis: pip install cassandra-driver"
        )
        sys.exit(1)

    if not SCHEMA_FILE.exists():
        logger.error(f"Fichier schema introuvable: {SCHEMA_FILE}")
        sys.exit(1)

    logger.info(f"Connexion a Cassandra {config.CASSANDRA_HOST}:{config.CASSANDRA_PORT}...")

    cluster = None
    for attempt in range(1, 11):
        try:
            cluster = Cluster(
                contact_points=[config.CASSANDRA_HOST],
                port=config.CASSANDRA_PORT,
                connect_timeout=15,
            )
            session = cluster.connect()
            logger.info(f"Connexion reussie (tentative {attempt})")
            break
        except Exception as exc:
            logger.warning(f"Tentative {attempt}/10 echouee: {exc}")
            if attempt < 10:
                time.sleep(10)
    else:
        logger.error("Impossible de se connecter a Cassandra apres 10 tentatives")
        sys.exit(1)

    content = SCHEMA_FILE.read_text(encoding="utf-8")
    statements = [
        s.strip()
        for s in content.split(";")
        if s.strip() and not s.strip().startswith("--")
    ]

    logger.info(f"Execution de {len(statements)} instructions CQL...")
    ok = 0
    for stmt in statements:
        try:
            session.execute(stmt)
            ok += 1
        except Exception as exc:
            logger.warning(f"Instruction ignoree (peut etre normale): {exc}")

    logger.info(f"Schema initialise: {ok}/{len(statements)} instructions executees")
    cluster.shutdown()
    logger.info("Pret ! Lancez maintenant: python scripts/run_initial_load.py")


if __name__ == "__main__":
    init_cassandra()
