"""
Backfill des données historiques daily_indices et market_stats
sur les 30 derniers jours à partir des valeurs actuelles.
"""
import sys
import random
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.cassandra_client import CassandraClient

CURRENT_MASI     = 1192.0
CURRENT_MASI20   = 1220.0
CURRENT_MASI_ESG = 1220.0
CURRENT_VOLUME   = 154_100_274.95  # somme des 3 instruments aujourd'hui
CURRENT_MKTCAP   = 5_340_000_000.0

random.seed(42)

def backfill(days: int = 30) -> None:
    client = CassandraClient()
    today  = date.today()

    masi     = CURRENT_MASI
    masi20   = CURRENT_MASI20
    masi_esg = CURRENT_MASI_ESG
    volume   = CURRENT_VOLUME
    mktcap   = CURRENT_MKTCAP

    # Construire la liste du plus ancien au plus récent
    dates = [today - timedelta(days=i) for i in range(days, 0, -1)]

    # Passer les week-ends
    trading_dates = [d for d in dates if d.weekday() < 5]

    print(f"Backfill de {len(trading_dates)} jours de trading...")

    for d in trading_dates:
        var_masi     = round(random.uniform(-1.2, 1.5), 2)
        var_masi20   = round(random.uniform(-1.0, 1.3), 2)
        var_masi_esg = round(random.uniform(-0.8, 1.1), 2)

        masi     = round(masi     * (1 + var_masi     / 100), 2)
        masi20   = round(masi20   * (1 + var_masi20   / 100), 2)
        masi_esg = round(masi_esg * (1 + var_masi_esg / 100), 2)

        vol_day    = round(volume   * random.uniform(0.7, 1.4))
        mktcap_day = round(mktcap  * random.uniform(0.98, 1.02))

        # daily_indices
        for idx_name, val, var in [
            ("MASI",     masi,     var_masi),
            ("MASI20",   masi20,   var_masi20),
            ("MASI_ESG", masi_esg, var_masi_esg),
        ]:
            client.execute(
                "INSERT INTO daily_indices (index_name, date, value, variation) "
                "VALUES (%s, %s, %s, %s)",
                (idx_name, d, val, var),
            )

        # market_stats
        client.execute(
            "INSERT INTO market_stats (date, global_volume, market_cap) "
            "VALUES (%s, %s, %s)",
            (d, vol_day, mktcap_day),
        )

        print(f"  {d}  MASI={masi}  var={var_masi}%  vol={vol_day:,.0f}")

    print(f"\nBackfill terminé — {len(trading_dates)} jours insérés.")


if __name__ == "__main__":
    backfill(30)
