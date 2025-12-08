# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions utilisées pour le calcul de la saturation.

Les fonctions d'évaluation de la saturation sont :
- transformation en une succession échantillonnée d'états des statuts (to_sampled_statuses) et sessions (to_sampled_sessions)
- assemblage des statuts et sessions échantillonnés pour obtenir l'état des pdc (to_sampled_state)
- génération de l'état global échantillonné d'un groupement de pdc (to_sampled_state_grp)
- génération des valeurs horaires des groupements de pdc (to_sampled_state_grp_h)
- création des données d'animation (features) des cartes (filter_animate, add_filter_animate)
- ajout d'une couche d'animation sur une carte (animate)
"""

import pandas as pd
import datetime
#import shapely
#import folium
#from folium.plugins import TimestampedGeoJson

ID_POC: str = "id_pdc_itinerance"
ID_STATION: str = "id_station_itinerance"

def to_sampled_statuses(
    data: pd.DataFrame,
    init_data: pd.DataFrame,
    timestamp: pd.Timestamp,
    echantillons: int,
) -> pd.DataFrame:
    """Génère les statuts échantillonnés pour une date donnée à partir d'un ensemble de statuts et de valeurs initiales.

    Les états de sortie ('etat_pdc') sont soit 'en_service', soit 'hors_service.
    La valeur 'inconnu' n'est pas prise en compte.'"""
    samples = pd.date_range(
        start=timestamp, end=timestamp + pd.Timedelta(days=1), periods=echantillons + 1
    )
    periode = pd.DataFrame({"periode": samples[0:echantillons]})
    state = pd.concat([data, init_data]).sort_values(
        by=["id_pdc_itinerance", "horodatage"]
    )
    state = state[(state["etat_pdc"] != "inconnu")]
    state["f_horodatage"] = list(state["horodatage"])[1 : len(state)] + [
        samples[echantillons]
    ]
    state["f_id_pdc_itinerance"] = list(state["id_pdc_itinerance"])[1 : len(state)] + [
        "aucun"
    ]

    crossed = pd.merge(state, periode, how="cross")
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


def to_sampled_sessions(
    data: pd.DataFrame,
    init_data: pd.DataFrame,
    timestamp: pd.Timestamp,
    echantillons: int,
) -> pd.DataFrame:
    """Génère les sessions échantillonnées pour une date donnée à partir d'un ensemble de sessions et de valeurs initiales.

    Les états de sortie ('occupation_pdc') sont soit 'occupe', soit 'f_libre.
    La valeur 'inconnu' n'est pas prise en compte."""
    samples = pd.date_range(
        start=timestamp, end=timestamp + pd.Timedelta(days=1), periods=echantillons + 1
    )
    periode = pd.DataFrame({"periode": samples[0:echantillons]})
    sessions = pd.concat([data, init_data]).sort_values(
        by=["id_pdc_itinerance", "start"]
    )
    sessions["occupation_pdc"] = "occupe"

    crossed = pd.merge(sessions, periode, how="cross")
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


def to_sampled_state_pdc(
    sessions: pd.DataFrame, statuses: pd.DataFrame
) -> pd.DataFrame:
    """Assemble les états issus des sessions et ceux issus des statuts.

    L'état 'occupe' des sessions est prioritaire à l'état des statuts.
    L'état 'f_libre' (non occupe) d'une session se traduit par l'état 'hors_service'
    si l'état du statut est 'hors_service' sinon par l'état 'libre'."""
    # ! les noms des états sont choisi pour que le tri alphabétique respecte l'ordre de priorité
    merged = pd.merge(
        sessions, statuses, how="outer", on=["id_pdc_itinerance", "periode"]
    ).fillna("aaa")
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


def to_sampled_state_grp(
    state_pdc: pd.DataFrame,
    pdc_group: pd.DataFrame,
    group_name: str,
    pourcent_sature: float,
    pourcent_surcharge: float,
) -> pd.DataFrame:
    """Génère le cumul du nombre de pdc par état et l'état d'un ensemble de pdc à partir de l'état de chaque pdc.

    La surcharge est activée à moins de 20% de pdc libres et la saturation à moins de 10%.
    Chaque état est restitué par un booléen ainsi que par une valeur aggrégée numérique
    ('hs': 1, 'inactif': 2, 'actif': 3, 'surcharge': 4, 'sature': 5)."""
    nb_pdc = (
        pdc_group.groupby([group_name])
        .count()
        .rename(columns={"id_pdc_itinerance": "nb_pdc"})
    )
    merged = pd.merge(state_pdc, pdc_group, how="left", on="id_pdc_itinerance")
    merged["occupe"] = merged["state"] == "occupe"
    merged["hors_service"] = merged["state"] == "hors_service"
    merged["libre"] = merged["state"] == "libre"
    print(len(state_pdc), len(merged))

    grouped = (
        merged[[group_name, "periode", "occupe", "hors_service", "libre"]]
        .groupby([group_name, "periode"])
        .sum()
        .reset_index()
    )
    grouped = pd.merge(grouped, nb_pdc, how="left", on=group_name)

    grouped["hs"] = (grouped["libre"] + grouped["occupe"] == 0) & (
        grouped["hors_service"] > 0
    )
    grouped["inactif"] = ~grouped["hs"] & (grouped["occupe"] == 0)
    grouped["sature"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & (grouped["libre"] / grouped["nb_pdc"] < pourcent_sature)
    )
    grouped["surcharge"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & ~grouped["sature"]
        & (grouped["libre"] / grouped["nb_pdc"] < pourcent_surcharge)
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

    return grouped[
        [
            group_name,
            "periode",
            "occupe",
            "hors_service",
            "libre",
            "nb_pdc",
            "hs",
            "inactif",
            "sature",
            "surcharge",
            "actif",
            "state",
        ]
    ]


def to_sampled_state_grp_h(
    state_grp: pd.DataFrame, group_name: str, echantillons: int, duree_etat_min: float
) -> pd.DataFrame:
    """Génère les états horaires à partir de l'état échantillonné d'un ensemble de pdc.

    Le temps passé dans chaque état est restitué en minutes.
    Deux états horaires booléens 'sature_h' et 'surcharge_h' sont calculé à partir d'un seuil de temps passé dans l'état.
    """
    nb_ech_hour = echantillons / 24

    sampled = state_grp.reset_index()
    sampled["periode_h"] = sampled["periode"].dt.hour
    sampled["periode"] = sampled["periode"].dt.date

    sampled_h = sampled.groupby([group_name, "periode", "periode_h"]).agg("sum")
    sampled_h = sampled_h / nb_ech_hour
    for etat in ["hs", "inactif", "sature", "surcharge", "actif"]:
        sampled_h[etat] = sampled_h[etat] * 60
    sampled_h["nb_pdc"] = sampled_h["nb_pdc"].astype("int")

    sampled_h["sature_h"] = (sampled_h["sature"] + sampled_h["hs"]) >= duree_etat_min
    sampled_h["surcharge_h"] = ~sampled_h["sature_h"] & (
        (sampled_h["surcharge"] + sampled_h["sature"] + sampled_h["hs"])
        >= duree_etat_min
    )

    sampled_h = sampled_h.reset_index()
    sampled_h["periode_iso"] = (
        sampled_h["periode"].astype("datetime64[s]")
        + pd.Timedelta("1 hour") * sampled_h["periode_h"]
    ).astype("str")
    sampled_h["periode_paris"] = (
        pd.to_datetime(sampled_h["periode_iso"])
        .dt.tz_localize("UTC")
        .dt.tz_convert("Europe/Paris")
        .astype("str")
    )

    return sampled_h[
        [
            group_name,
            "periode",
            "periode_h",
            "nb_pdc",
            "hs",
            "inactif",
            "sature",
            "surcharge",
            "actif",
            "sature_h",
            "surcharge_h",
            "periode_iso",
            "periode_paris",
        ]
    ]

def sampled_state_poc(
    day: datetime.date,
    samples_per_day: int,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
    statics: pd.DataFrame,
) -> pd.DataFrame:
    """Extract complete POC with sessions and statuses."""
    timestamp = pd.Timestamp(day.isoformat() + "T00:00:00+00:00")
    pocs_with_sessions = sessions[ID_POC].unique()
    pocs_with_statuses = statuses[ID_POC].unique()
    pocs_ids = set(pocs_with_sessions).intersection(set(pocs_with_statuses))

    attributes_sessions = [ID_POC, "start", "end"]
    attributes_statuses = [ID_POC, "horodatage", "etat_pdc"]
    # statuses = statuses[statuses[ID_POC].isin(pocs_ids)][attributes_sessions]
    statuses = statuses[attributes_statuses]
    # sessions = sessions[sessions[ID_POC].isin(pocs_ids)][attributes_statuses]
    sessions = sessions[attributes_sessions]
    sessions["start"] = sessions["start"].astype("datetime64[s, UTC]")
    sessions["end"] = sessions["end"].astype("datetime64[s, UTC]")

    pocs_stations = statics[statics[ID_POC].isin(pocs_with_sessions)]
    pocs = pocs_stations[ID_POC].unique()
    stations = pocs_stations[ID_STATION].unique()

    init = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=-1)] * len(pocs_with_statuses),
            "etat_pdc": ["en_service"] * len(pocs_with_statuses),
            "id_pdc_itinerance": pocs_with_statuses,
        }
    )
    sampled_statuses = to_sampled_statuses(statuses, init, timestamp, samples_per_day)
    print("status : ", len(sampled_statuses)) 

    init = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(days=-1)] * len(pocs_with_sessions),
            "end": [timestamp + pd.Timedelta(hours=-1)] * len(pocs_with_sessions),
            "id_pdc_itinerance": pocs_with_sessions,
        }
    )
    sampled_sessions = to_sampled_sessions(sessions, init, timestamp, samples_per_day)
    print("sessions : ", len(sampled_sessions))
    sampled_state_poc = to_sampled_state_pdc(sampled_sessions, sampled_statuses)
    print("state : ", len(sampled_state_poc))
    return sampled_state_poc