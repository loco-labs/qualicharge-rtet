"""QualiCharge prefect indicators: state historicization.

E2: daily states of charge points in activity.
E3: daily states of stations in activity.
E6: daily states of pools.
"""

import json

#import os
from datetime import date, datetime, timedelta

import pandas as pd
from pandas import NamedAgg

# from prefect import flow, runtime, task
# from prefect.cache_policies import NONE
# from prefect.futures import wait
# from indicators.extract.utils import (
from utils import (
    filter_sessions_duration,
    get_chunks,
    # get_poc_station_for_day,
    # get_station_pool_for_day,
    to_sampled_sessions,
    to_sampled_state_grp,
    to_sampled_state_poc,
    to_sampled_statuses,
    to_state_grp,
    to_state_poc,
)

# from indicators.models import IndicatorPeriod, Level
# from indicators.types import Environment
# from indicators.utils import (
#    export_indicators,
#    get_period_start_from_pit,
# )

# HISTORY_STRATEGY_FIELD: str = "mean"
PERIOD = 288
CHUNK_SIZE: int = 200
SAMPLES: int = 288  # 5 min
SATURE_H: int = 45  # minimum duration (min) of saturation to have a saturated hour

ID_POC: str = "id_pdc_itinerance"
ID_STATION: str = "id_station_itinerance"
ID_POOL: str = "id_pool"
SATURATION_RATIO = 0.1
OVERLOAD_RATIO = 0.2
MAX_SESSION_DURATION_HOURS: float = 10


'''@task(task_run_name="read-S3-{bucket}-{day:%y-%m-%d}", cache_policy=NONE)
def read_s3_data(day: date, environment: str, bucket: str) -> pd.DataFrame:
    """Read S3 data for state historicization."""
    dir_path = f"{bucket}/{day.year}/{day.month}/{day.day}"
    file_path = f"{dir_path}/{environment}.parquet"
    s3_path = f"s3://{file_path}"
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", "")
    df = pd.read_parquet(
        s3_path,
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={"endpoint_url": s3_endpoint_url},
    )  # type: ignore[call-overload]
    return df
'''


def filter_statuses_sessions(
    sessions: pd.DataFrame, statuses: pd.DataFrame, statics: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter statuses and sessions with statics data."""
    sessions = sessions[sessions[ID_POC].isin(statics[ID_POC])].copy()
    active_poc = sessions[ID_POC].unique()
    statuses = statuses[statuses[ID_POC].isin(active_poc)].copy()
    return (statuses, sessions)


def get_sampled_state_poc(
    day: date,
    samples_per_day: int,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
) -> pd.DataFrame:
    """Extract complete POC with sessions and statuses."""
    print(len(sessions), len(statuses))
    min_duration = timedelta(minutes=24 * 60 / samples_per_day)
    timestamp = pd.Timestamp(day.isoformat() + "T00:00:00+00:00")
    pocs_with_sessions = pd.Series(sessions[ID_POC].unique())
    pocs_with_statuses = pd.Series(statuses[ID_POC].unique())
    all_pocs = (
        pd.concat([pocs_with_sessions, pocs_with_statuses])
        .drop_duplicates()
        .reset_index(drop=True)
    )

    attributes_statuses = [ID_POC, "horodatage", "etat_pdc", "occupation_pdc"]
    statuses = statuses[attributes_statuses].copy()
    statuses["horodatage"] = statuses["horodatage"].astype("datetime64[s, UTC]")

    attributes_sessions = [ID_POC, "start", "end"]
    sessions = sessions[attributes_sessions].copy()
    sessions["start"] = sessions["start"].astype("datetime64[s, UTC]")
    sessions["end"] = sessions["end"].astype("datetime64[s, UTC]")

    init_start_statuses = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=-1)] * len(all_pocs),
            "etat_pdc": ["en_service"] * len(all_pocs),
            "occupation_pdc": ["libre"] * len(all_pocs),
            "id_pdc_itinerance": all_pocs,
        }
    )
    init_end_statuses = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=1)] * len(all_pocs),
            "etat_pdc": ["en_service"] * len(all_pocs),
            "occupation_pdc": ["libre"] * len(all_pocs),
            "id_pdc_itinerance": all_pocs,
        }
    )
    init_statuses = pd.concat([init_start_statuses, init_end_statuses])
    init_statuses["horodatage"] = pd.to_datetime(init_statuses["horodatage"], utc=True)
    sampled_statuses = to_sampled_statuses(
        statuses, init_statuses, timestamp, samples_per_day, min_duration=min_duration
    )

    init_sessions = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=-2)] * len(all_pocs),
            "end": [timestamp + pd.Timedelta(hours=-1)] * len(all_pocs),
            "id_pdc_itinerance": all_pocs,
        }
    )
    sampled_sessions = to_sampled_sessions(
        sessions,
        init_sessions,
        timestamp,
        samples_per_day,
    )

    return to_sampled_state_poc(sampled_sessions, sampled_statuses)


# @task(task_run_name="sampled_chunk-{day:%y-%m-%d}", cache_policy=NONE)
def get_state_poc_for_chunk(
    day: date,
    samples_per_day: int,
    statics_chunk: pd.DataFrame,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate state_poc for a chunk."""
    statuses_chunk, sessions_chunk = filter_statuses_sessions(
        sessions, statuses, statics_chunk
    )
    sampled_state_poc_chunk = get_sampled_state_poc(
        day,
        samples_per_day,
        sessions_chunk,
        statuses_chunk,
    )
    state_poc_chunk = to_state_poc(sampled_state_poc_chunk, samples_per_day)
    return (sampled_state_poc_chunk, state_poc_chunk)

#@task(task_run_name="to_state_chunk-{day:%y-%m-%d}", cache_policy=NONE)
def to_state(  # noqa: PLR0913
    statics: pd.DataFrame,
    chunk: pd.DataFrame,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
    day: date,
    samples_per_day: int,
    add_pool: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convert the data to a state representation."""
    statics_chunk = statics[statics[ID_POC].isin(chunk[ID_POC])]
    sampled_state_poc, state_poc = get_state_poc_for_chunk(
        day, samples_per_day, statics_chunk, sessions, statuses
    )
    state_station = to_state_grp(
        to_sampled_state_grp(
            sampled_state_poc[sampled_state_poc[ID_POC].isin(chunk[ID_POC])],
            chunk[[ID_POC, ID_STATION]],
            ID_STATION,
            SATURATION_RATIO,
            OVERLOAD_RATIO,
            add_full_use=True,
            add_latency=True,
        ),  # type: ignore[call-overload]
        ID_STATION,
        samples_per_day,
    )
    state_pool = (
        to_state_grp(
            to_sampled_state_grp(
                sampled_state_poc[sampled_state_poc[ID_POC].isin(chunk[ID_POC])],
                chunk[[ID_POC, ID_POOL]],
                ID_POOL,
                SATURATION_RATIO,
                OVERLOAD_RATIO,
                add_full_use=True,
                add_latency=True,
            ),  # type: ignore[call-overload]
            ID_POOL,
            samples_per_day,
        )
        if add_pool
        else pd.DataFrame()
    )
    return (state_poc, state_station, state_pool)

def to_state_with_details(  # noqa: PLR0913
    statics: pd.DataFrame,
    chunk: pd.DataFrame,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
    day: date,
    samples_per_day: int,
    add_pool: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convert the data to a state representation."""
    statics_chunk = statics[statics[ID_POC].isin(chunk[ID_POC])]
    sampled_state_poc, state_poc = get_state_poc_for_chunk(
        day, samples_per_day, statics_chunk, sessions, statuses
    )
    sampled_state_station = to_sampled_state_grp(
        sampled_state_poc[sampled_state_poc[ID_POC].isin(chunk[ID_POC])],
        chunk[[ID_POC, ID_STATION]],
        ID_STATION,
        SATURATION_RATIO,
        OVERLOAD_RATIO,
        add_full_use=True,
        add_latency=True,
    )  # type: ignore[call-overload]
    state_station = to_state_grp(
        sampled_state_station,
        ID_STATION,
        samples_per_day,
    )
    state_pool = (
        to_state_grp(
            to_sampled_state_grp(
                sampled_state_poc[sampled_state_poc[ID_POC].isin(chunk[ID_POC])],
                chunk[[ID_POC, ID_POOL]],
                ID_POOL,
                SATURATION_RATIO,
                OVERLOAD_RATIO,
                add_full_use=True,
                add_latency=True,
            ),  # type: ignore[call-overload]
            ID_POOL,
            samples_per_day,
        )
        if add_pool
        else pd.DataFrame()
    )
    return (state_poc, state_station, state_pool, sampled_state_poc, sampled_state_station)


# @flow(flow_run_name="meta-e2-d")
def e2(  # noqa: PLR0913
    # environment: Environment,
    state_poc: pd.DataFrame,
    sessions_poc: pd.DataFrame,
    day: date,
    # create_artifact: bool,
    # persist: bool,
) -> pd.DataFrame:
    """Run e2 subflow."""
    full_state_poc = pd.merge(state_poc, sessions_poc, on=ID_POC, how="left").fillna(0)
    indicators_e2 = pd.DataFrame(
        {
            "target": "00",
            "value": len(full_state_poc),
            "code": "e2",
            # "level": Level.NATIONAL,
            "period": PERIOD,
            "timestamp": day.isoformat(),
            "category": None,
            "extras": [
                {
                    "id_pdc_itinerance": list(full_state_poc[ID_POC]),
                    "occupe": list(full_state_poc["occupe"]),
                    "occupe_max": list(full_state_poc["occupe_max"]),
                    "hors_service": list(full_state_poc["hors_service"]),
                    "libre": list(full_state_poc["libre"]),
                    "pseudo_libre": list(full_state_poc["pseudo_libre"]),
                    "pseudo_occupe": list(full_state_poc["pseudo_occupe"]),
                    "sessions_nb": list(full_state_poc["sessions_nb"]),
                    "energy_cum": list(full_state_poc["energy_cum"]),
                }
            ],
        }
    )
    desc_e2 = f"e2 report at {day} (period: {PERIOD})"
    # flow_name_e2 = "e2-" + runtime.flow_run.name
    # export_indicators(
    #    indicators_e2, environment, flow_name_e2, desc_e2, create_artifact, persist
    # )
    return indicators_e2


# @flow(flow_run_name="meta-e3-d")
def e3(  # noqa: PLR0913
    # environment: Environment,
    state_station: pd.DataFrame,
    info_sessions_stations: pd.DataFrame,
    day: date,
    # create_artifact: bool,
    # persist: bool,
) -> pd.DataFrame:
    """Run e3 subflow."""
    # state_station = to_state_grp(sampled_state_station, ID_STATION, SAMPLES)
    full_state_station = pd.merge(
        state_station, info_sessions_stations, on=ID_STATION, how="left"
    ).fillna(0)
    indicators_e3 = pd.DataFrame(
        {
            "target": "00",
            "value": len(full_state_station),
            "code": "e3",
            # "level": Level.NATIONAL,
            "period": PERIOD,
            "timestamp": day.isoformat(),
            "category": None,
            "extras": [
                {
                    "id_station_itinerance": list(full_state_station[ID_STATION]),
                    "nb_pdc": list(full_state_station["nb_pdc"]),
                    "hs": list(full_state_station["hs"]),
                    "inactif": list(full_state_station["inactif"]),
                    "sature_cum": list(full_state_station["sature_cum"]),
                    "sature_max": list(full_state_station["sature_max"]),
                    "surcharge": list(full_state_station["surcharge"]),
                    "actif": list(full_state_station["actif"]),
                    "pu_cum": list(full_state_station["pu_cum"]),
                    "pu_max": list(full_state_station["pu_max"]),
                    "pu_len": list(full_state_station["pu_len"]),
                    "sessions_nb": list(full_state_station["sessions_nb"]),
                    "energy_cum": list(full_state_station["energy_cum"]),
                }
            ],
        }
    )

    desc_e3 = f"e3 report at {day} (period: {PERIOD})"
    # flow_name_e3 = "e3-" + runtime.flow_run.name
    # export_indicators(
    #    indicators_e3, environment, flow_name_e3, desc_e3, create_artifact, persist
    # )
    return indicators_e3


# @flow(flow_run_name="meta-e6-d")
def e6(  # noqa: PLR0913
    # environment: Environment,
    state_pool: pd.DataFrame,
    info_sessions_pools: pd.DataFrame,
    day: date,
    # create_artifact: bool,
    # persist: bool,
) -> pd.DataFrame:
    """Run e6 subflow."""
    full_state_pool = pd.merge(
        state_pool, info_sessions_pools, on=ID_POOL, how="left"
    ).fillna(0)
    indicators_e6 = pd.DataFrame(
        {
            "target": "00",
            "value": len(full_state_pool),
            "code": "e6",
            # "level": Level.NATIONAL,
            "period": PERIOD,
            "timestamp": day.isoformat(),
            "category": None,
            "extras": [
                {
                    "id_pool": list(full_state_pool[ID_POOL]),
                    "nb_pdc": list(full_state_pool["nb_pdc"]),
                    "hs": list(full_state_pool["hs"]),
                    "inactif": list(full_state_pool["inactif"]),
                    "sature_cum": list(full_state_pool["sature_cum"]),
                    "sature_max": list(full_state_pool["sature_max"]),
                    "surcharge": list(full_state_pool["surcharge"]),
                    "actif": list(full_state_pool["actif"]),
                    "pu_cum": list(full_state_pool["pu_cum"]),
                    "pu_max": list(full_state_pool["pu_max"]),
                    "pu_len": list(full_state_pool["pu_len"]),
                    "sessions_nb": list(full_state_pool["sessions_nb"]),
                    "energy_cum": list(full_state_pool["energy_cum"]),
                }
            ],
        }
    )
    desc_e6 = f"e6 report at {day} (period: {PERIOD})"
    # flow_name_e6 = "e6-" + runtime.flow_run.name
    # export_indicators(
    #    indicators_e6, environment, flow_name_e6, desc_e6, create_artifact, persist
    # )
    return indicators_e6

def read_statics(day: date, min_power: float) -> pd.DataFrame:
    """Read static data for pocs and stations."""
    date_statics = f"{day.day:02d}-{day.month:02d}-{day.year}"
    e5_str = pd.read_csv(f"../data_DMR_e2_e3/e5_{date_statics}.csv")["extras"][0]
    statics = pd.DataFrame(json.loads(e5_str))
    statics["unite"] = statics["id_pdc_itinerance"].str[:5]
    return statics[statics["puissance_nominale"] >= min_power]

def read_statics_pools(day:date, min_power: float) -> pd.DataFrame:
    """Read static data for stations and pools."""
    e1_statics = pd.read_csv("../source/tests_DMR/aires_pdc_2026-07-25.csv")[[ID_POOL, ID_STATION]].drop_duplicates()
    return e1_statics

#@flow(flow_run_name="meta-e2e3e6-d")
def e2_e3_e6(  # noqa: PLR0913
    #environment: Environment,
    min_power: float,
    day: date,
    #offset: int = -1,
    chunk_size: int = CHUNK_SIZE,
    samples_per_day: int = SAMPLES,
    #create_artifact: bool = False,
    #persist: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run all e2, e3, and e6 subflows."""
    # common to indicators e2 and e3
    date_file = f"{day.year}{day.month:02d}{day.day:02d}"
    data_quali = "../data/"
    min_duration = timedelta(minutes=24 * 60 / samples_per_day)
    max_duration = timedelta(hours=MAX_SESSION_DURATION_HOURS)

    e1_statics = read_statics_pools(day, min_power)

    statuses = pd.read_parquet(data_quali + "qualicharge-" + date_file + "/statuses/production.parquet", engine="pyarrow")
    sessions_s3 = pd.read_parquet(data_quali + "qualicharge-" + date_file + "/sessions/production.parquet", engine="pyarrow")
    sessions = filter_sessions_duration(
        sessions_s3, min_duration=min_duration, max_duration=max_duration
    )
    statics = read_statics(day, min_power)
    statics = statics[statics["puissance_nominale"] >= min_power]
    pools_statics = read_statics_pools(day, min_power) 
    pools_stations = pools_statics[[ID_POOL, ID_STATION]].drop_duplicates()
    pools_stations_pocs = pools_statics.merge(statics, on=ID_STATION, how="left")

    sessions_poc = (
        sessions.groupby(ID_POC)
        .agg(
            sessions_nb=NamedAgg("energy", "count"),
            energy_cum=NamedAgg("energy", "sum"),
        )
        .reset_index()
    )
    # chunk calculation for pools and stations
    chunks_pools = get_chunks(pools_stations_pocs, ID_POOL, chunk_size)
    futures_pools = [
        to_state(statics, chunk, sessions, statuses, day, samples_per_day)
        for chunk in chunks_pools
    ]
    # wait(futures_pools)

    statics_no_pools = statics[~statics[ID_POC].isin(pools_stations_pocs[ID_POC])]
    chunks_no_pools = get_chunks(statics_no_pools, ID_STATION, chunk_size)
    futures_no_pools = [
        to_state(
            statics_no_pools,
            chunk,
            sessions,
            statuses,
            day,
            samples_per_day,
            add_pool=False,
        )
        for chunk in chunks_no_pools
    ]
    # wait(futures_no_pools)

    # e2 indicator
    state_poc = pd.concat(
            [
                pd.concat([future[0] for future in futures_pools], ignore_index=True),
                pd.concat([future[0] for future in futures_no_pools], ignore_index=True),
            ],
            ignore_index=True,
        )
    indicators_e2 = e2(
        # environment,
        state_poc,
        sessions_poc,
        day,
        # create_artifact,
        # persist,
    )
    # e3 indicator
    state_station = pd.concat(
        [
            pd.concat([future[1] for future in futures_pools], ignore_index=True),
            pd.concat([future[1] for future in futures_no_pools], ignore_index=True),
        ],
        ignore_index=True
    )
    sessions_stations = pd.merge(
        statics[[ID_POC, ID_STATION]], sessions_poc, on=ID_POC, how="left"
    ).fillna(0)
    info_sessions_stations = (
        sessions_stations[[ID_STATION, "sessions_nb", "energy_cum"]]
        .groupby(ID_STATION)
        .sum()
        .reset_index()
    )
    indicators_e3 = e3(
        #environment,
        state_station,
        info_sessions_stations,
        day,
        #create_artifact,
        #persist,
    )
    # e6 indicator
    state_pool = pd.concat([future[2] for future in futures_pools], ignore_index=True)
    sessions_pools = pd.merge(
        pools_stations_pocs[[ID_POOL, ID_POC]], sessions_poc, on=ID_POC, how="left"
    ).fillna(0)
    info_sessions_pools = (
        sessions_pools[[ID_POOL, "sessions_nb", "energy_cum"]]
        .groupby(ID_POOL)
        .sum()
        .reset_index()
    )
    indicators_e6 = e6(
        #environment,
        state_pool,
        info_sessions_pools,
        day,
        #create_artifact,
        #persist,
    )
    #return (indicators_e2, indicators_e3, indicators_e6)
    return (state_poc, state_station, state_pool)

def e2_e3_e6_with_details(  # noqa: PLR0913
    #environment: Environment,
    min_power: float,
    day: date,
    chunk_size: int = CHUNK_SIZE,
    samples_per_day: int = SAMPLES,
    list_station: list = [],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run all e2, e3, and e6 subflows."""
    # common to indicators e2 and e3
    date_file = f"{day.year}{day.month:02d}{day.day:02d}"
    data_quali = "../data/"
    min_duration = timedelta(minutes=24 * 60 / samples_per_day)
    max_duration = timedelta(hours=MAX_SESSION_DURATION_HOURS)

    #e1_statics = read_statics_pools(day, min_power)

    statuses = pd.read_parquet(data_quali + "qualicharge-" + date_file + "/statuses/production.parquet", engine="pyarrow")
    sessions_s3 = pd.read_parquet(data_quali + "qualicharge-" + date_file + "/sessions/production.parquet", engine="pyarrow")
    sessions = filter_sessions_duration(
        sessions_s3, min_duration=min_duration, max_duration=max_duration
    )
    statics = read_statics(day, min_power)
    statics = statics[statics["puissance_nominale"] >= min_power]
    if list_station :
        statics = statics[statics[ID_STATION].isin(list_station)]
    pools_statics = read_statics_pools(day, min_power) 
    #pools_stations = pools_statics[[ID_POOL, ID_STATION]].drop_duplicates()
    pools_stations_pocs = pools_statics.merge(statics, on=ID_STATION, how="left")

    sessions_poc = (
        sessions.groupby(ID_POC)
        .agg(
            sessions_nb=NamedAgg("energy", "count"),
            energy_cum=NamedAgg("energy", "sum"),
        )
        .reset_index()
    )
    # chunk calculation for pools and stations
    chunks_pools = get_chunks(pools_stations_pocs, ID_POOL, chunk_size)
    print("chunks_pools ", chunks_pools)
    futures_pools = [
        to_state_with_details(statics, chunk, sessions, statuses, day, samples_per_day)
        for chunk in chunks_pools
    ]
    # wait(futures_pools)

    statics_no_pools = statics[~statics[ID_POC].isin(pools_stations_pocs[ID_POC])]
    chunks_no_pools = get_chunks(statics_no_pools, ID_STATION, chunk_size)
    print("chunks_no_pools ", chunks_no_pools)
    futures_no_pools = [
        to_state_with_details(
            statics_no_pools,
            chunk,
            sessions,
            statuses,
            day,
            samples_per_day,
            add_pool=False,
        )
        for chunk in chunks_no_pools
    ]
    # wait(futures_no_pools)
    futures = futures_no_pools + futures_pools
    #print("future0 ", futures[0])
    #print("future-1 ", futures[-1])
    # e2 indicator
    state_poc = pd.concat([future[0] for future in futures], ignore_index=True)
    sampled_state_poc = pd.concat([future[3] for future in futures], ignore_index=True)
    
    # e3 indicator
    state_station = pd.concat([future[1] for future in futures], ignore_index=True),
    sampled_state_station = pd.concat([future[4] for future in futures], ignore_index=True),

    # e6 indicator
    state_pool = pd.concat([future[2] for future in futures_pools], ignore_index=True)
    return (state_poc, state_station, state_pool, sampled_state_poc, sampled_state_station)
