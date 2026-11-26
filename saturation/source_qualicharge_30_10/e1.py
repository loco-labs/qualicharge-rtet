"""QualiCharge prefect indicators: extract.

E1: the list of stations of pools in activity.

data : id_pool
"""

import json
from datetime import date, datetime
from pathlib import Path

import geopandas as gpd  # type: ignore
import pandas as pd  # type: ignore

# from prefect import flow, runtime, task
# from indicators.extract.utils import get_poc_station_for_day
# from indicators.models import IndicatorPeriod, Level
# from indicators.types import Environment
from utils import (
    NaturePool,
    stations_echangeurs,
    #    POOLS_FILE,
    #    export_indicators,
    #    get_period_start_from_pit,
    #    init_pools,
)

# HISTORY_STRATEGY_FIELD: str = "mean"
PERIOD = "d"
POOLS_FILE = "../data_DMR/aires_dmr_2026-08-03.geojson"


def init_pools(
    file_path: Path, filter: NaturePool = NaturePool.AIRE
) -> gpd.GeoDataFrame:
    """Initialize pools from a geojson file."""
    return gpd.read_file(file_path).rename(columns={"id_aire": "id_pool"})


def read_statics(day: date) -> pd.DataFrame:
    """Read static data for pocs and stations."""
    date_statics = f"{day.day:02d}-{day.month:02d}-{day.year}"
    e5_str = pd.read_csv(f"../data_DMR_e2_e3/e5_{date_statics}.csv")["extras"][0]
    statics = pd.DataFrame(json.loads(e5_str))
    statics["unite"] = statics["id_pdc_itinerance"].str[:5]
    return statics


# @task
def get_station_pool_for_day(from_date: date) -> pd.DataFrame:
    """Get stations for a list of pools."""
    pools = init_pools(POOLS_FILE)
    # pdc_station = get_poc_station_for_day(from_date, environment)
    pdc_station = read_statics(from_date)
    stations_df = pdc_station.drop_duplicates(
        subset=["id_station_itinerance"]
    ).reset_index(drop=True)
    stations = gpd.GeoDataFrame(
        stations_df,
        geometry=gpd.points_from_xy(stations_df["longitude"], stations_df["latitude"]),
        crs="EPSG:4326",
    )

    aires = pools[pools["id_pool"].str[:1] == NaturePool.AIRE.value]
    aires_with_stations = gpd.sjoin(aires, stations, how="left", predicate="contains")

    echangeurs = pools[pools["id_pool"].str[:1] == NaturePool.ECHANGEUR.value]
    echangeurs_with_stations = stations_echangeurs(stations, echangeurs)

    pools_with_stations = pd.concat(
        [
            aires_with_stations[["id_pool", "id_station_itinerance"]],
            echangeurs_with_stations[["id_pool", "id_station_itinerance"]],
        ],
        ignore_index=True,
    )

    return pd.DataFrame(pools_with_stations).dropna().reset_index(drop=True)


# @flow(
#    flow_run_name="e1-d-00",  # -{start:%y-%m-%d}",
# )
def e1_national(
    start: date,
    # environment: Environment,
) -> pd.DataFrame:
    """Calculate e1 at the national level."""
    result = get_station_pool_for_day(start)
    indicators = {
        "target": "00",
        "value": len(result),
        "code": "e1",
        # "level": Level.NATIONAL,
        "period": PERIOD,
        "timestamp": start.isoformat(),
        "category": None,
        "extras": [
            {
                "id_station_itinerance": list(result["id_station_itinerance"]),
                "id_pool": list(result["id_pool"]),
            }
        ],
    }
    return pd.DataFrame(indicators)


# @flow(
#    flow_run_name="meta-e1-d",
# )
def e1(
    # environment: Environment,
    start: datetime | None = None,
    # offset: int = -1,
    # create_artifact: bool = False,
    # persist: bool = False,
) -> pd.DataFrame:
    """Run all e1 subflows."""
    # start = (
    #    datetime.now()
    #    if not offset and start is None
    #    else get_period_start_from_pit(start, offset, PERIOD)
    # )
    indicators = e1_national(start.date())  # , environment)
    description = f"e1 report at {start} (period: {PERIOD})"
    # flow_name = runtime.flow_run.name
    # export_indicators(
    #    indicators, environment, flow_name, description, create_artifact, persist
    # )
    return indicators
