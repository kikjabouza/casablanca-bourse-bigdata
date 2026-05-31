# src/storage/cassandra_client.py
"""
Client Cassandra avec fallback pour Python 3.13+
"""

import os
import logging
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)

class CassandraClient:
    """Client Cassandra avec support pour environnement de test"""
    
    def __init__(self, test_mode: bool = True):
        """
        Args:
            test_mode: True = mode test (pas de connexion réelle)
                      False = mode production (tentative de connexion)
        """
        self.config = Config()
        self.test_mode = test_mode
        self.session = None
        
        # En mode test, on ne tente pas la connexion
        if test_mode:
            logger.info("🔧 Mode TEST: Cassandra désactivé (driver incompatible Python 3.13)")
            return
        
        # En mode production, on essaie la connexion
        self._connect_production()
    
    def _connect_production(self):
        """Tente une connexion réelle à Cassandra (peut échouer sur Python 3.13)"""
        try:
            # Vérifier si on est explicitement en production
            if os.getenv('ENVIRONMENT') != 'production':
                logger.warning("⚠️ Mode production non activé. Utilisation du mode test.")
                self.test_mode = True
                return
            
            # Tentative d'import conditionnel
            try:
                from cassandra.cluster import Cluster
                from cassandra.auth import PlainTextAuthProvider
            except ImportError as e:
                logger.warning(f"⚠️ Driver Cassandra non disponible: {e}")
                logger.info("💡 Installez avec: pip install cassandra-driver")
                self.test_mode = True
                return
            
            cluster = Cluster(
                [self.config.CASSANDRA_HOST],
                port=self.config.CASSANDRA_PORT,
                connect_timeout=10
            )
            self.session = cluster.connect()
            # Créer une fonction row_factory simple
            def dict_factory(row, *args):
                return dict(row._asdict())
            self.session.row_factory = dict_factory
            logger.info(f"✅ Connecté à Cassandra sur {self.config.CASSANDRA_HOST}")
            
        except Exception as e:
            logger.warning(f"⚠️ Connexion Cassandra impossible: {e}")
            logger.info("🔄 Basculement en mode test (fichiers JSON uniquement)")
            self.test_mode = True
    
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
    
    def close(self):
        """Ferme la connexion"""
        if self.session and not self.test_mode:
            self.session.shutdown()
            logger.info("Connexion Cassandra fermée")