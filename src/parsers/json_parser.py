from typing import Any, Dict, List

from src.utils.logger import get_logger

logger = get_logger(__name__)


class JSONParser:
    """Parseur pour les réponses JSON des APIs de casablanca-bourse.com."""

    @staticmethod
    def parse_instrument_history(api_response: Dict[str, Any], ticker: str) -> List[Dict[str, Any]]:
        """
        Parse la réponse de l'API instrument_history.
        Retourne une liste d'enregistrements OHLC + volume.
        """
        records = []
        for item in api_response.get("data", []):
            attrs = item.get("attributes", {})
            close = attrs.get("closingPrice")
            if close is None:
                continue

            records.append(
                {
                    "ticker": ticker,
                    "date": attrs.get("created"),
                    "close_price": float(close),
                    "open_price": float(attrs["openingPrice"]) if attrs.get("openingPrice") else None,
                    "high_price": float(attrs["highPrice"]) if attrs.get("highPrice") else None,
                    "low_price": float(attrs["lowPrice"]) if attrs.get("lowPrice") else None,
                    "volume": float(attrs["cumulVolumeEchange"]) if attrs.get("cumulVolumeEchange") else None,
                    "ratio": float(attrs["ratioConsolide"]) if attrs.get("ratioConsolide") else 1.0,
                }
            )

        logger.debug(f"Parse {len(records)} enregistrements historiques pour {ticker}")
        return records

    @staticmethod
    def extract_pagination_info(api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations de pagination de la réponse API."""
        meta = api_response.get("meta", {})
        links = api_response.get("links", {})
        return {
            "total_count": meta.get("count", 0),
            "next_page": links.get("next", {}).get("href") if isinstance(links.get("next"), dict) else None,
        }
