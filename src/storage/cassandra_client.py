# src/storage/cassandra_client.py
"""
Client Cassandra avec fallback pour Python 3.13+
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)

class CassandraClient:
    """
    Client Cassandra pour stockage des données scrapées
    
    Modes:
    - test_mode=True: stockage JSON uniquement (tests unitaires)
    - test_mode=False: tentative connexion Cassandra réelle (production)
    """
    
    def __init__(self, test_mode: bool = False):
        """
        Args:
            test_mode: 
                True = mode test (pas de connexion réelle, fichiers JSON uniquement)
                False = mode production (tentative de connexion Cassandra)
        """
        self.config = Config()
        self.test_mode = test_mode
        self.session = None
        
        # Créer le dossier de stockage JSON
        self.json_storage_dir = Path(__file__).parent.parent.parent / "tests" / "data"
        self.json_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # En mode test, on désactive Cassandra
        if test_mode:
            logger.info(f"🔧 Mode TEST: Cassandra désactivé (données stockées dans {self.json_storage_dir})")
            return
        
        # En mode production, on essaie la connexion
        self._connect_production()
    
    def _connect_production(self):
        """Tente une connexion réelle à Cassandra"""
        try:
            logger.info("🔄 Mode PRODUCTION: Tentative de connexion à Cassandra...")
            
            # Tentative d'import conditionnel du driver Cassandra
            try:
                from cassandra.cluster import Cluster
                from cassandra.auth import PlainTextAuthProvider
            except ImportError as e:
                logger.warning(f"⚠️ Driver Cassandra non disponible: {e}")
                logger.info("💡 Pour une connexion réelle: pip install cassandra-driver")
                self.test_mode = True
                return
            
            # Essayer de se connecter
            cluster = Cluster(
                [self.config.CASSANDRA_HOST],
                port=self.config.CASSANDRA_PORT,
                connect_timeout=10
            )
            self.session = cluster.connect()
            
            # Configurer row_factory simple
            def dict_factory(row, *args):
                return dict(row._asdict()) if hasattr(row, '_asdict') else row
            
            self.session.row_factory = dict_factory
            logger.info(f"✅ Connecté à Cassandra sur {self.config.CASSANDRA_HOST}:{self.config.CASSANDRA_PORT}")

            self._ensure_keyspace()
            self._load_schema_if_available()

        except Exception as e:
            logger.warning(f"⚠️ Connexion Cassandra impossible: {e}")
            logger.info("🔄 Basculement en mode test (données en fichiers JSON)")
            self.test_mode = True
    
    def _ensure_keyspace(self):
        """Crée le keyspace si nécessaire et positionne la session dessus."""
        keyspace = self.config.CASSANDRA_KEYSPACE
        query = f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': 1 }}
        """
        self.session.execute(query)
        self.session.set_keyspace(keyspace)

    def _load_schema_if_available(self):
        """Charge les instructions CQL du fichier init.cql si présent."""
        schema_file = Path(__file__).resolve().parents[2] / "cassandra" / "init.cql"
        if not schema_file.exists():
            logger.warning(f"⚠️ Fichier de schéma introuvable: {schema_file}")
            return

        logger.info(f"📄 Chargement du schéma Cassandra depuis {schema_file}")
        content = schema_file.read_text(encoding="utf-8")
        statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
        for statement in statements:
            if statement.startswith("--"):
                continue
            try:
                self.session.execute(statement)
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de l'exécution du schéma Cassandra: {e}\nStatement: {statement[:120]}...")

    def execute(self, query: str, params: tuple = None) -> List[Dict]:
        """Exécute une requête (simulée en mode test)"""
        if self.test_mode:
            logger.debug(f"[TEST] Query: {query[:100]}...")
            if params:
                logger.debug(f"[TEST] Params: {params}")
            return []
        else:
            if params:
                result = self.session.execute(query, params)
            else:
                result = self.session.execute(query)
            return list(result)
    
    def execute_simple(self, query: str, params: tuple = None):
        """Exécute une requête sans retour (simulée en mode test)"""
        if self.test_mode:
            logger.debug(f"[TEST] Execute: {query[:100]}...")
        else:
            if params:
                self.session.execute(query, params)
            else:
                self.session.execute(query)
    
    def save_instrument_json(self, ticker: str, data: Dict) -> str:
        """
        Sauvegarde les données d'un instrument en JSON (mode test uniquement)
        Retourne le chemin du fichier
        """
        if not self.test_mode:
            return None
        
        file_path = self.json_storage_dir / f"{ticker}_details.json"
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.debug(f"💾 Données sauvegardées: {file_path}")
        return str(file_path)
    
    def close(self):
        """Ferme la connexion"""
        if self.session and not self.test_mode:
            self.session.shutdown()
            logger.info("Connexion Cassandra fermée")