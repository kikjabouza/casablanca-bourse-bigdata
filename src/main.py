# src/main.py
import sys
import time
from typing import List, Dict
from src.utils.logger import setup_logger, get_logger
from src.utils.config import Config
from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.market_overview_scraper import MarketOverviewScraper

logger = get_logger(__name__)

class BourseScraperOrchestrator:
    """Orchestrateur principal qui coordonne tous les scrapers"""
    
    def __init__(self):
        self.config = Config()
        self.instruments_list_scraper = InstrumentsListScraper()
        self.instrument_details_scraper = InstrumentDetailsScraper()
        self.historical_data_scraper = HistoricalDataScraper()
        self.market_overview_scraper = MarketOverviewScraper()
    
    def run_full_initial_load(self):
        """
        Exécute le chargement initial complet de toutes les données
        """
        logger.info("=" * 60)
        logger.info("Démarrage du chargement initial complet")
        logger.info("=" * 60)
        
        # Étape 1: Scraper la liste des instruments
        logger.info("\n📋 Étape 1: Récupération de la liste des instruments")
        instruments = self.instruments_list_scraper.scrape_instruments_list()
        
        if not instruments:
            logger.error("Aucun instrument trouvé, arrêt du processus")
            return
        
        # Étape 2: Pour chaque instrument, scraper les détails statiques
        logger.info(f"\n📊 Étape 2: Scraping des détails pour {len(instruments)} instruments")
        for i, instrument in enumerate(instruments, 1):
            ticker = instrument['ticker']
            logger.info(f"  [{i}/{len(instruments)}] Traitement de {ticker}")
            
            self.instrument_details_scraper.scrape_instrument(ticker)
            time.sleep(self.config.REQUEST_DELAY)
        
        # Étape 3: Scraper les données historiques
        logger.info(f"\n📈 Étape 3: Scraping des données historiques")
        for i, instrument in enumerate(instruments, 1):
            ticker = instrument['ticker']
            logger.info(f"  [{i}/{len(instruments)}] Historique pour {ticker}")
            
            self.historical_data_scraper.scrape_historical_data(ticker)
            time.sleep(self.config.BULK_REQUEST_DELAY)
        
        # Étape 4: Scraper le market overview
        logger.info("\n🌍 Étape 4: Scraping du market overview")
        self.market_overview_scraper.scrape_market_overview()
        
        logger.info("\n✅ Chargement initial complet terminé avec succès!")
    
    def run_daily_update(self):
        """
        Exécute la mise à jour quotidienne (seulement les dernières données)
        """
        logger.info("=" * 60)
        logger.info("Démarrage de la mise à jour quotidienne")
        logger.info("=" * 60)
        
        # Récupérer la liste des instruments depuis Cassandra (ou re-scraper)
        instruments = self.instruments_list_scraper.scrape_instruments_list()
        
        if not instruments:
            logger.error("Aucun instrument trouvé, arrêt du processus")
            return
        
        # Mise à jour des données de séance pour chaque instrument
        logger.info(f"\n🔄 Mise à jour des données pour {len(instruments)} instruments")
        for i, instrument in enumerate(instruments, 1):
            ticker = instrument['ticker']
            logger.info(f"  [{i}/{len(instruments)}] Mise à jour de {ticker}")
            
            self.instrument_details_scraper.scrape_instrument(ticker)
            time.sleep(self.config.REQUEST_DELAY)
        
        # Mise à jour du market overview
        logger.info("\n🌍 Mise à jour du market overview")
        self.market_overview_scraper.scrape_market_overview()
        
        logger.info("\n✅ Mise à jour quotidienne terminée avec succès!")

def main():
    """Point d'entrée principal"""
    # Configurer les logs
    setup_logger()
    
    orchestrator = BourseScraperOrchestrator()
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1 and sys.argv[1] == '--daily':
        orchestrator.run_daily_update()
    else:
        orchestrator.run_full_initial_load()

if __name__ == "__main__":
    main()