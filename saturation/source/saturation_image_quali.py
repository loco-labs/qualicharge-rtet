"""
Ce module contient les fonctions utilisées pour le calcul de la saturation.
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd
from pandas import NamedAgg

#import shapely
#import folium
#from folium.plugins import TimestampedGeoJson

ID_POC: str = "id_pdc_itinerance"
ID_STATION: str = "id_station_itinerance"
MAX_SESSION_DURATION_HOURS: float = 10
START_FULL_USE = 0.99
END_FULL_USE = 0.8

# fonctions de utils

def hysteresis(x: pd.Series, low_hysteresis_level: float, high_hysteresis_level: float) -> pd.Series:
    """Apply hysteresis to a Series with given low and high hysteresis levels."""
    high = x >= high_hysteresis_level
    low_or_high = (x < low_hysteresis_level) | high
    ind_low_or_high = np.nonzero(low_or_high)[0]
    if not ind_low_or_high.size:  # prevent index error if ind_low_or_high is empty
        return None
    cnt = np.cumsum(low_or_high)
    return np.where(cnt, high[ind_low_or_high[cnt - 1]], False)

def maxi_periode_PU(state_grp: pd.DataFrame, group_name: str) -> pd.DataFrame:
    '''Calculate de PU periode with the maximum duration.'''
    df = state_grp.sort_values(by=[group_name, 'periode']).reset_index(drop=True)

    groups = df["occupe"].ne(
        df.groupby(group_name)["occupe"].shift()
    ).groupby(df[group_name]).cumsum()

    valid_groups = df[df["occupe"]].assign(valid_group=groups[df["occupe"]])

    maxi_period = valid_groups.groupby([group_name, "valid_group"]).agg(
            start=("periode", "first"),
            end=("periode", "last"),
        )
    maxi_period['duration'] = maxi_period['end'] - maxi_period['start']
    maxi_period = maxi_period.loc[
        maxi_period.groupby(level=0)["duration"].idxmax()
    ]
    return maxi_period

def to_sampled_statuses(
    data: pd.DataFrame,
    init_data: pd.DataFrame,
    timestamp: pd.Timestamp,
    samples_per_day: int,
    min_duration: timedelta = timedelta(),
) -> pd.DataFrame:
    """Generate sampled statuses for a given date.

    Generation is based on a set of statuses and initial values.
    The output states ('etat_pdc') are either 'en_service' or 'hors_service'.
    The 'inconnu' value is not taken into account.
    """
    samples = pd.date_range(
        start=timestamp,
        end=timestamp + pd.Timedelta(days=1),
        periods=samples_per_day + 1,
    )
    periode = pd.DataFrame({"periode": samples[0:samples_per_day]})
    state = pd.concat([data, init_data]).sort_values(
        by=["id_pdc_itinerance", "horodatage"]
    )
    state = state[(state["etat_pdc"] != "inconnu")]
    #state["f_horodatage"] = list(state["horodatage"])[1 : len(state)] + [
    #    samples[samples_per_day]
    #]
    #state["f_id_pdc_itinerance"] = list(state["id_pdc_itinerance"])[1 : len(state)] + [
    #    "aucun"
    #]
    state["f_horodatage"] = state["horodatage"].shift(-1)
    state.loc[state.index[-1], "f_horodatage"] = samples[samples_per_day]
    state["f_id_pdc_itinerance"] = state["id_pdc_itinerance"].shift(-1)
    state.loc[state.index[-1], "f_id_pdc_itinerance"] = "aucun"
    # remove statuses with short duration
    state["duration"] = state["f_horodatage"] - state["horodatage"]
    filtered_state = state[
        (state["duration"] > min_duration)
        | (state["id_pdc_itinerance"] != state["f_id_pdc_itinerance"])
    ].copy()
    filtered_state["f_horodatage"] = list(filtered_state["horodatage"])[
        1 : len(filtered_state)
    ] + [samples[samples_per_day]]
    filtered_state["f_id_pdc_itinerance"] = list(filtered_state["id_pdc_itinerance"])[
        1 : len(filtered_state)
    ] + ["aucun"]

    # create sampled statuses
    crossed = pd.merge(filtered_state, periode, how="cross")
    sampled = crossed[
        (
            (crossed["id_pdc_itinerance"].eq(crossed["f_id_pdc_itinerance"]))
            & (crossed["periode"] >= crossed["horodatage"])
            & (crossed["periode"] < crossed["f_horodatage"])
        )
        | (
            ~(crossed["id_pdc_itinerance"].eq(crossed["f_id_pdc_itinerance"]))
            & (crossed["periode"] >= crossed["horodatage"])
        )
    ]
    sampled = sampled[["periode", "etat_pdc", "id_pdc_itinerance"]]

    return sampled.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


def to_sampled_sessions(  # noqa: PLR0913
    data: pd.DataFrame,
    init_data: pd.DataFrame,
    timestamp: pd.Timestamp,
    samples_per_day: int,
    min_duration: timedelta = timedelta(),
    max_duration: timedelta = timedelta(hours=24)
    # latency: timedelta = timedelta()
) -> pd.DataFrame:
    """Generate sampled sessions for a given date.

    Generation is based on a set of sessions and initial values.
    Input data: set of sessions and initial values.
    The output states ('occupation_pdc') are either 'occupe' or 'libre'.
    The 'inconnu' value is not taken into account.
    """
    # add a latency for full_use
    #if latency:
    #    data = data.assign(end=data['end']+latency)

    # init variables
    samples = pd.date_range(
        start=timestamp,
        end=timestamp + pd.Timedelta(days=1),
        periods=samples_per_day + 1,
    )
    periode = pd.DataFrame({"periode": samples[0:samples_per_day]})
    sessions = pd.concat([data, init_data]).sort_values(
        by=["id_pdc_itinerance", "start"]
    )
    # remove invalid sessions : duplicates, short duration, long duration
    unic = ["start", "end", "id_pdc_itinerance"]
    sessions["duration"] = sessions["end"] - sessions["start"]
    filtered_sessions = (
        sessions[
            (sessions["duration"] > min_duration)
            & (sessions["duration"] < max_duration)
        ]
        .copy()
        .drop_duplicates(subset=unic)
    )

    # create sampled sessions
    filtered_sessions["occupation_pdc"] = "occupe"
    crossed = pd.merge(filtered_sessions, periode, how="cross")
    sampled = crossed[
        (
            (crossed["periode"] >= crossed["start"])
            & (crossed["periode"] < crossed["end"])
        )
    ]
    sampled = sampled[["periode", "occupation_pdc", "id_pdc_itinerance"]]
    non_occupe = pd.merge(
        periode,
        pd.DataFrame({"id_pdc_itinerance": sessions["id_pdc_itinerance"].unique()}),
        how="cross",
    )
    sampled = pd.merge(
        non_occupe, sampled, how="left", on=["id_pdc_itinerance", "periode"]
    ).fillna("f_libre")

    return sampled.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


def to_sampled_state_poc(
    sessions: pd.DataFrame, statuses: pd.DataFrame
) -> pd.DataFrame:
    """Combine the states derived from sessions with those derived from statuses.

    The session 'occupe' state takes precedence over the status state.
    A session's 'f_libre' (not occupied) state translates to the 'hors_service' state if
    the status state is 'hors_service'; otherwise, it translates to the 'libre' state.
    """
    merged = pd.merge(
        sessions, statuses, how="outer", on=["id_pdc_itinerance", "periode"]
    ).fillna("aaa")

    # ! The state names are chosen so that alphabetical sorting respects
    # the order of priority.
    merged["state"] = (
        merged[["etat_pdc", "occupation_pdc"]]
        .agg("max", axis=1)
        .replace("en_service", "libre")
    )
    merged = merged[["id_pdc_itinerance", "periode", "state"]].replace(
        "f_libre", "libre"
    )

    return merged.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


def to_state_poc_d(state_poc: pd.DataFrame, samples_per_day: int) -> pd.DataFrame:
    """Generate daily states for the charge points based on their sampled state.

    The time spent in each state is returne d in minutes.
    """
    sampled = state_poc[["id_pdc_itinerance", "state"]].reset_index()
    sampled["occupe"] = sampled["state"] == "occupe"
    sampled["hors_service"] = sampled["state"] == "hors_service"
    sampled["libre"] = sampled["state"] == "libre"

    state_d = sampled.groupby(["id_pdc_itinerance"]).agg("sum").reset_index()

    for etat in ["occupe", "hors_service", "libre"]:
        state_d[etat] = state_d[etat] * 60 * 24 / samples_per_day

    return state_d[["id_pdc_itinerance", "occupe", "hors_service", "libre"]]


def to_sampled_state_grp(
    state_poc: pd.DataFrame,
    pdc_group: pd.DataFrame,
    group_name: str,
    saturation_ratio: float,
    overload_ratio: float,
    add_full_use: bool = False,
) -> pd.DataFrame:
    """Generate the aggregated states of a set of charge points.

    "surcharge" occurs when the number of charge points falls below 'overload_ratio'
    value, and "sature" occurs below 'saturation_ratio' value.
    Each state is represented by a boolean value as well as an aggregated numeric value
    ('hs': 1, 'inactif': 2, 'actif': 3, 'surcharge': 4, 'sature': 5).
    """
    returned_fields = [
                group_name,
                "periode",
                "occupe",
                "hors_service",
                "libre",
                "pleine_utilisation",
                "nb_pdc",
                "hs",
                "inactif",
                "pu",
                "sature",
                "surcharge",
                "actif",
                "state",
            ]
    nb_pdc = (
        pdc_group.groupby([group_name])
        .count()
        .rename(columns={"id_pdc_itinerance": "nb_pdc"})
    )
    merged = pd.merge(state_poc, pdc_group, how="left", on="id_pdc_itinerance")
    merged["occupe"] = merged["state"] == "occupe"
    merged["hors_service"] = merged["state"] == "hors_service"
    merged["libre"] = merged["state"] == "libre"
    # add a 5 min interval for 'pleine utilisation'
    occupe_hs = merged['occupe'] | merged['hors_service']
    merged['pleine_utilisation'] = occupe_hs | occupe_hs.shift(fill_value=False)

    grouped = (
        merged[[group_name, "periode", "occupe", "hors_service", "libre", "pleine_utilisation"]]
        .groupby([group_name, "periode"])
        .sum()
        .reset_index()
    )
    grouped = pd.merge(grouped, nb_pdc, how="left", on=group_name)

    grouped["hs"] = ((grouped["libre"] + grouped["occupe"]) == 0) & (
        grouped["hors_service"] > 0
    )
    grouped["inactif"] = ~grouped["hs"] & (grouped["occupe"] == 0)
    grouped["sature"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & (grouped["libre"] / grouped["nb_pdc"] < saturation_ratio)
    )
    grouped["surcharge"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & ~grouped["sature"]
        & (grouped["libre"] / grouped["nb_pdc"] < overload_ratio)
    )
    grouped["actif"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & ~grouped["sature"]
        & ~grouped["surcharge"]
    )
    grouped["state"] = (
        grouped["hs"]
        + grouped["inactif"] * 2
        + grouped["actif"] * 3
        + grouped["surcharge"] * 4
        + grouped["sature"] * 5
    )

    if add_full_use:
        not_full_use = 0
        maybe_full_use = 0.5
        full_use = 1

        full_use_rate = grouped["pleine_utilisation"] / grouped["nb_pdc"]
        tmp_full_use = pd.cut(
            full_use_rate,
            [-np.inf, END_FULL_USE, START_FULL_USE, np.inf],
            labels=[not_full_use, maybe_full_use, full_use],
        )
        grouped["pu"] = tmp_full_use.where(
            tmp_full_use != maybe_full_use,
            np.where(
                hysteresis(tmp_full_use.values, maybe_full_use, full_use),
                full_use,
                not_full_use,
            ),
        ).astype("bool")
    else :
        grouped["pu"] = False

    return grouped[returned_fields]



def to_state_grp_h(
    state_grp: pd.DataFrame,
    group_name: str,
    samples_per_day: int,
    duree_etat_min: float,
) -> pd.DataFrame:
    """Generate hourly states based on the sampled state of a set of charge points.

    The time spent in each state is returned in minutes.
    Two boolean hourly states, 'sature_h' and 'surcharge_h', are calculated based on a
    threshold for the time spent in the state.
    """
    sample_duration = 24 * 60 / samples_per_day
    state_fields_h = ["hs", "inactif", "pu_cum", "sature_cum", "surcharge", "actif"]

    sampled = state_grp.reset_index()
    sampled["periode_h"] = sampled["periode"].dt.hour
    sampled["periode_d"] = sampled["periode"].dt.date
    grouped = sampled.groupby([group_name, "nb_pdc", "periode_d", "periode_h"])
    sampled_h = grouped.agg(
        hs=NamedAgg("hs", "sum"),
        inactif=NamedAgg("inactif", "sum"),
        sature_cum=NamedAgg("sature", "sum"),
        pu_cum=NamedAgg("pu", "sum"),
        surcharge=NamedAgg("surcharge", "sum"),
        actif=NamedAgg("actif", "sum"),
    ) * sample_duration

    sampled_h["sature_h"] = (sampled_h["sature_cum"] + sampled_h["hs"]) >= duree_etat_min
    sampled_h["surcharge_h"] = ~sampled_h["sature_h"] & (
        (sampled_h["surcharge"] + sampled_h["sature_cum"] + sampled_h["hs"])
        >= duree_etat_min
    )
    return sampled_h.reset_index()[[group_name, "periode_d", "periode_h", "nb_pdc"] + state_fields_h + ["sature_h", "surcharge_h"]]


def to_state_grp_d(
    state_grp_h: pd.DataFrame,
    group_name: str,
) -> pd.DataFrame:
    """Generate daily states from the hourly state of a set of charge points.

    The time spent in each state is returned in minutes.
    """
    grouped = state_grp_h.groupby([group_name, "periode_d"])
    state_grp_d = grouped.agg(
        nb_pdc=NamedAgg("nb_pdc", "max"),
        nb_h=NamedAgg("periode", "count"),
        hs=NamedAgg("hs", "sum"),
        inactif=NamedAgg("inactif", "sum"),
        sature_cum=NamedAgg("sature", "sum"),
        sature_max=NamedAgg("sature", "max"),
        surcharge=NamedAgg("surcharge", "sum"),
        actif=NamedAgg("actif", "sum"),
    ).reset_index()

    return state_grp_d

# fonctions de e2_e3

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
    min_duration = timedelta (minutes=24 * 60 / samples_per_day)
    max_duration = timedelta (hours=MAX_SESSION_DURATION_HOURS)
    timestamp = pd.Timestamp(day.isoformat() + "T00:00:00+00:00")
    pocs_with_sessions = sessions[ID_POC].unique()
    pocs_with_statuses = statuses[ID_POC].unique()

    attributes_statuses = [ID_POC, "horodatage", "etat_pdc"]
    statuses = statuses[attributes_statuses].copy()
    statuses["horodatage"] = statuses["horodatage"].astype("datetime64[s, UTC]")
    
    attributes_sessions = [ID_POC, "start", "end"]
    sessions = sessions[attributes_sessions].copy()
    sessions["start"] = sessions["start"].astype("datetime64[s, UTC]")
    sessions["end"] = sessions["end"].astype("datetime64[s, UTC]")

    init_statuses = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=-1)] * len(pocs_with_statuses),
            "etat_pdc": ["en_service"] * len(pocs_with_statuses),
            "id_pdc_itinerance": pocs_with_statuses,
        }
    )
    init_statuses["horodatage"] = pd.to_datetime(init_statuses["horodatage"], utc=True)
    sampled_statuses = to_sampled_statuses(
        statuses, init_statuses, timestamp, samples_per_day, min_duration=min_duration
    )

    init_sessions = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=-2)] * len(pocs_with_sessions),
            "end": [timestamp + pd.Timedelta(hours=-1)] * len(pocs_with_sessions),
            "id_pdc_itinerance": pocs_with_sessions,
        }
    )
    sampled_sessions = to_sampled_sessions(
        sessions, init_sessions, timestamp, samples_per_day, min_duration=min_duration, max_duration=max_duration
    )

    return to_sampled_state_poc(sampled_sessions, sampled_statuses)
