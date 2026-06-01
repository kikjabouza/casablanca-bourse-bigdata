# src/main.py
"""
Script principal de scraping du Casablanca Bourse
Scrape TOUTES les données des instruments et les stocke dans Cassandra
"""
import sys
import time
from typing import List, Dict
from datetime import datetime

from src.utils.logger import setup_logger, get_logger
from src.utils.config import Config
from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.storage.cassandra_client import CassandraClient

logger = get_logger(__name__)


class BourseScraperOrchestrator:
    """
    Orchestrateur principal qui coordonne tous les scrapers
    
    Responsabilités:
    - Scraper TOUTES les données des instruments
    - Stocker les résultats dans Cassandra
    - Pas d'orchestration Prefect (géré ultérieurement)
    """
    
    def __init__(self):
        self.config = Config()
        self.instruments_list_scraper = InstrumentsListScraper()
        self.instrument_details_scraper = InstrumentDetailsScraper()
        self.historical_data_scraper = HistoricalDataScraper()
        self.market_overview_scraper = MarketOverviewScraper(save_to_cassandra=True)
        self.cassandra = CassandraClient(test_mode=True)  # Mode test: JSON uniquement (pas Cassandra)
    
    def run_full_scraping(self):
        """
        Exécute le scraping complet de TOUTES les données
        Sans limites et sans orchestration Prefect
        """
        logger.info("=" * 80)
        logger.info("🚀 DÉMARRAGE DU SCRAPING COMPLET")
        logger.info("=" * 80)
        logger.info(f"Heure de démarrage: {datetime.now().isoformat()}")
        
        start_time = time.time()
        
        # Étape 1: Scraper la liste des instruments
        logger.info("\n" + "📋" * 40)
        logger.info("ÉTAPE 1: Récupération de la liste des instruments")
        logger.info("📋" * 40)
        
        instruments = self.instruments_list_scraper.scrape_instruments_list()
        
        if not instruments:
            logger.error("❌ Aucun instrument trouvé, arrêt du processus")
            return False
        
        logger.info(f"✅ {len(instruments)} instruments trouvés")
        
        # Étape 2: Scraper les détails statiques de TOUS les instruments
        logger.info("\n" + "📊" * 40)
        logger.info(f"ÉTAPE 2: Scraping des détails pour {len(instruments)} instruments")
        logger.info("📊" * 40)
        
        details_success = 0
        for i, instrument in enumerate(instruments, 1):
            ticker = instrument['ticker']
            try:
                logger.info(f"[{i}/{len(instruments)}] Scraping détails de {ticker}...")
                self.instrument_details_scraper.scrape_instrument(ticker)
                details_success += 1
                time.sleep(self.config.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"❌ Erreur pour {ticker}: {e}")
                time.sleep(self.config.REQUEST_DELAY * 2)  # Delay supplémentaire en cas d'erreur
        
        logger.info(f"✅ Détails scrapés: {details_success}/{len(instruments)} instruments")
        
        # Étape 3: Scraper les données historiques de TOUS les instruments
        logger.info("\n" + "📈" * 40)
        logger.info(f"ÉTAPE 3: Scraping des données historiques pour {len(instruments)} instruments")
        logger.info("📈" * 40)
        
        historical_success = 0
        for i, instrument in enumerate(instruments, 1):
            ticker = instrument['ticker']
            try:
                logger.info(f"[{i}/{len(instruments)}] Scraping historique de {ticker}...")
                self.historical_data_scraper.scrape_historical_data(ticker)
                historical_success += 1
                time.sleep(self.config.BULK_REQUEST_DELAY)
            except Exception as e:
                logger.error(f"❌ Erreur pour {ticker}: {e}")
                time.sleep(self.config.BULK_REQUEST_DELAY * 2)
        
        logger.info(f"✅ Historique scrapé: {historical_success}/{len(instruments)} instruments")
        
        # Étape 4: Scraper le market overview (indices, stats, top movers, etc.)
        logger.info("\n" + "🌍" * 40)
        logger.info("ÉTAPE 4: Scraping du market overview complet")
        logger.info("🌍" * 40)
        
        try:
            logger.info("Scraping du market overview...")
            overview_data = self.market_overview_scraper.scrape_market_overview(enrich_top_movers=True)
            if overview_data:
                logger.info("✅ Market overview scrapé avec succès")
            else:
                logger.error("⚠️  Market overview: aucune donnée retournée")
        except Exception as e:
            logger.error(f"❌ Erreur market overview: {e}")
        
        # Résumé final
        total_duration = time.time() - start_time
        logger.info("\n" + "=" * 80)
        logger.info("✅ SCRAPING COMPLET TERMINÉ")
        logger.info("=" * 80)
        logger.info(f"Durée totale: {total_duration/60:.2f} minutes")
        logger.info(f"Instruments traités: {len(instruments)}")
        logger.info(f"Heure de fin: {datetime.now().isoformat()}")
        
        return True
    
    def run_daily_update(self):
        """
        Exécute la mise à jour quotidienne des données
        Scrape les données de séance actualisées pour tous les instruments
        """
        logger.info("=" * 80)
        logger.info("🔄 DÉMARRAGE DE LA MISE À JOUR QUOTIDIENNE")
        logger.info("=" * 80)
        logger.info(f"Heure de démarrage: {datetime.now().isoformat()}")
        
        start_time = time.time()
        
        # Récupérer la liste des instruments
        logger.info("\nRécupération de la liste des instruments...")
        instruments = self.instruments_list_scraper.scrape_instruments_list()
        
        if not instruments:
            logger.error("❌ Aucun instrument trouvé, arrêt du processus")
            return False
        
        logger.info(f"✅ {len(instruments)} instruments trouvés")
        
        # Mise à jour des données de séance pour chaque instrument
        logger.info(f"\n🔄 Mise à jour des données de séance pour {len(instruments)} instruments")
        
        update_success = 0
        for i, instrument in enumerate(instruments, 1):
            ticker = instrument['ticker']
            try:
                logger.info(f"[{i}/{len(instruments)}] Mise à jour de {ticker}...")
                self.instrument_details_scraper.scrape_instrument(ticker)
                update_success += 1
                time.sleep(self.config.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"❌ Erreur pour {ticker}: {e}")
                time.sleep(self.config.REQUEST_DELAY * 2)
        
        logger.info(f"✅ Données mises à jour: {update_success}/{len(instruments)} instruments")
        
        # Mise à jour du market overview
        logger.info("\nMise à jour du market overview...")
        try:
            self.market_overview_scraper.scrape_market_overview(enrich_top_movers=True)
            logger.info("✅ Market overview mis à jour")
        except Exception as e:
            logger.error(f"⚠️  Erreur market overview: {e}")
        
        total_duration = time.time() - start_time
        logger.info("\n" + "=" * 80)
        logger.info("✅ MISE À JOUR QUOTIDIENNE TERMINÉE")
        logger.info("=" * 80)
        logger.info(f"Durée totale: {total_duration/60:.2f} minutes")
        logger.info(f"Heure de fin: {datetime.now().isoformat()}")
        
        return True
    
    def run_market_overview_only(self):
        """
        Scrape uniquement le market overview (indices, stats, top movers)
        Utilisation légère pour mise à jour rapide
        """
        logger.info("=" * 80)
        logger.info("🌍 SCRAPING DU MARKET OVERVIEW UNIQUEMENT")
        logger.info("=" * 80)
        
        try:
            overview_data = self.market_overview_scraper.scrape_market_overview(enrich_top_movers=True)
            if overview_data:
                logger.info("✅ Market overview scrapé avec succès")
                return True
            else:
                logger.error("❌ Aucune donnée retournée")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return False

def main():
    """
    Point d'entrée principal
    Usage:
        python -m src.main              # Scraping complet de toutes les données
        python -m src.main --daily      # Mise à jour quotidienne
        python -m src.main --overview   # Market overview uniquement
    """
    # Configurer les logs
    setup_logger()
    
    orchestrator = BourseScraperOrchestrator()
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] == '--daily':
            orchestrator.run_daily_update()
        elif sys.argv[1] == '--overview':
            orchestrator.run_market_overview_only()
        else:
            logger.error(f"Argument inconnu: {sys.argv[1]}")
            print("Usage: python -m src.main [--daily|--overview]")
            sys.exit(1)
    else:
        # Par défaut: scraping complet
        orchestrator.run_full_scraping()


if __name__ == "__main__":
    main()
