# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions utilisées pour le calcul de la saturation.

Les étapes d'évaluation de la saturation sont :
- transformation en une succession échantillonnée d'états des statuts (to_sampled_statuses) et sessions (to_sampled_sessions)
- assemblage des statuts et sessions échantillonnés pour obtenir l'état des pdc (to_sampled_state)
- génération de l'état global échantillonné d'un groupement de pdc (to_sampled_state_grp)
- génération des valeurs horaires des groupements de pdc (to_sampled_state_grp_h)
"""

import geopandas as gpd
import pandas as pd
import shapely
import folium
from folium.plugins import TimestampedGeoJson

def to_sampled_statuses(data: pd.DataFrame, init_data: pd.DataFrame, timestamp: pd.Timestamp, echantillons: int) -> pd.DataFrame:
    """Génère les statuts échantillonnés pour une date donnée à partir d'un ensemble de statuts et de valeurs initiales. 
    
    Les états de sortie ('etat_pdc') sont soit 'en_service', soit 'hors_service. 
    La valeur 'inconnu' n'est pas prise en compte.'"""
    samples = pd.date_range(start=timestamp, end=timestamp+pd.Timedelta(days=1), periods=echantillons+1)
    periode = pd.DataFrame( {'periode': samples[0:echantillons]})
    state = pd.concat([data, init_data]).sort_values(by=['id_pdc_itinerance', 'horodatage'])
    state = state[(state['etat_pdc'] != 'inconnu')]
    state['f_horodatage'] = list(state['horodatage'])[1:len(state)] + [samples[echantillons]]
    state['f_id_pdc_itinerance'] = list(state['id_pdc_itinerance'])[1:len(state)] + ['aucun']
    
    crossed = pd.merge(state, periode, how='cross')
    sampled = crossed[((crossed['id_pdc_itinerance'].eq(crossed['f_id_pdc_itinerance'])) &
                 (crossed['periode'] >= crossed['horodatage']) &
                 (crossed['periode'] < crossed['f_horodatage'])) |
                (~(crossed['id_pdc_itinerance'].eq(crossed['f_id_pdc_itinerance'])) &
                 (crossed['periode'] >= crossed['horodatage']))]
    sampled = sampled[['periode', 'etat_pdc', 'id_pdc_itinerance']]
    
    return sampled.sort_values(by=['id_pdc_itinerance', 'periode']).reset_index(drop=True)

def to_sampled_sessions(data: pd.DataFrame, init_data: pd.DataFrame, timestamp: pd.Timestamp, echantillons: int) -> pd.DataFrame:
    """Génère les sessions échantillonnées pour une date donnée à partir d'un ensemble de sessions et de valeurs initiales.
    
    Les états de sortie ('occupation_pdc') sont soit 'occupe', soit 'f_libre. 
    La valeur 'inconnu' n'est pas prise en compte."""
    null_date = pd.Timestamp('2000-01-01T00:00:00+02:00')
    samples = pd.date_range(start=timestamp, end=timestamp+pd.Timedelta(days=1), periods=echantillons+1)
    periode = pd.DataFrame( {'periode': samples[0:echantillons]})
    sessions = pd.concat([data, init_data]).sort_values(by=['id_pdc_itinerance', 'start'])
    sessions['occupation_pdc'] = 'occupe'
    
    crossed = pd.merge(sessions, periode, how='cross')
    sampled = crossed[((crossed['periode'] >= crossed['start']) &
                       (crossed['periode'] < crossed['end']))]
    sampled = sampled[['periode', 'occupation_pdc', 'id_pdc_itinerance']]
    non_occupe = pd.merge(periode, pd.DataFrame({'id_pdc_itinerance': sessions['id_pdc_itinerance'].unique()}), how='cross')
    sampled = pd.merge(non_occupe, sampled, how='left', on=['id_pdc_itinerance', 'periode']).fillna("f_libre")
    
    return sampled.sort_values(by=['id_pdc_itinerance', 'periode']).reset_index(drop=True)

def to_sampled_state_pdc(sessions: pd.DataFrame, statuses: pd.DataFrame) -> pd.DataFrame:
    """Assemble les états issus des sessions et ceux issus des statuts.
    
    L'état 'occupe' des sessions est prioritaire à l'état des statuts.
    L'état 'f_libre' (non occupe) d'une session se traduit par l'état 'hors_service' 
    si l'état du statut est 'hors_service' sinon par l'état 'libre'."""
    merged = pd.merge(sessions, statuses, how='outer', on=['id_pdc_itinerance', 'periode']).fillna('aaa')
    merged['state'] = merged[['etat_pdc', 'occupation_pdc']].agg('max', axis=1).replace('en_service', 'libre')
    merged = merged[['id_pdc_itinerance', 'periode', 'state']].replace('f_libre', 'libre')
    
    return merged.sort_values(by=['id_pdc_itinerance', 'periode']).reset_index(drop=True)

def to_sampled_state_grp(state_pdc: pd.DataFrame, pdc_group: pd.DataFrame, group_name: str) -> pd.DataFrame:
    """Génère l'état d'un ensemble de pdc à partir de l'état de chaque pdc.

    La surcharge est activée à moins de 20% de pdc libres et la saturation à moins de 10%.
    Chaque état est restitué par un booléen ainsi que par une valeur aggrégée numérique 
    ('hs': 1, 'inactif': 2, 'actif': 3, 'surcharge': 4, 'sature': 5)."""
    nb_pdc = pdc_group.groupby([group_name]).count().rename(columns={'id_pdc_itinerance': 'nb_pdc'})
    merged =  pd.merge(state_pdc, pdc_group, how='left', on='id_pdc_itinerance')
    merged['occupe'] = merged['state'] == 'occupe'
    merged['hors_service'] = merged['state'] == 'hors_service'
    merged['libre'] = merged['state'] == 'libre'
    print(len(state_pdc), len(merged))
    
    grouped = merged[[group_name, 'periode', 'occupe', 'hors_service', 'libre']].groupby([group_name, 'periode']).sum().reset_index()
    grouped = pd.merge(grouped, nb_pdc, how='left', on=group_name)

    grouped['hs'] = (grouped['libre'] + grouped['occupe'] == 0) & (grouped['hors_service'] > 0)
    grouped['inactif'] = ~grouped['hs'] & (grouped['occupe'] == 0)
    grouped['sature'] = ~grouped['hs'] & ~grouped['inactif'] & (grouped['libre']/grouped['nb_pdc'] < 0.1)
    grouped['surcharge'] = ~grouped['hs'] & ~grouped['inactif'] & ~grouped['sature'] & (grouped['libre']/grouped['nb_pdc'] < 0.2)
    grouped['actif'] = ~grouped['hs'] & ~grouped['inactif'] & ~grouped['sature'] & ~grouped['surcharge']
    grouped['state'] = grouped['hs'] + grouped['inactif'] * 2 + grouped['actif'] * 3 + grouped['surcharge'] * 4 + grouped['sature'] * 5

    
    return grouped

def to_sampled_state_grp_h(state_grp: pd.DataFrame, group_name: str, echantillons: int, duree_etat_min: float) -> pd.DataFrame:
    """Génère les états horaires à partir de l'état échantillonné d'un ensemble de pdc.
    
    Le temps passé dans chaque état est restitué en minutes.
    Deux états horaires booléens 'sature_h' et 'surcharge_h' sont calculé à partir d'un seuil de temps passé dans l'état."""
    nb_ech_hour = echantillons / 24
    # print(echantillons, nb_ech_hour)
    
    sampled = state_grp.reset_index()
    sampled['periode_h'] = sampled['periode'].dt.hour
    sampled['periode'] = sampled['periode'].dt.date
    
    sampled_h = sampled.groupby([group_name, 'periode', 'periode_h']).agg('sum')
    sampled_h = sampled_h / nb_ech_hour
    for etat in ['hs', 'inactif', 'sature', 'surcharge', 'actif']:
        sampled_h[etat] = sampled_h[etat] * 60
    sampled_h['nb_pdc'] = sampled_h['nb_pdc'].astype('int')
    
    #sampled_h['sature_h'] = sampled_h['sature'] > duree_etat_min
    sampled_h['sature_h'] = (sampled_h['sature'] + sampled_h['hs']) > duree_etat_min
    #sampled_h['surcharge_h'] = ~sampled_h['sature_h'] & ((sampled_h['surcharge'] + sampled_h['sature']) > duree_etat_min)
    sampled_h['surcharge_h'] = ~sampled_h['sature_h'] & ((sampled_h['surcharge'] + sampled_h['sature'] + sampled_h['hs']) > duree_etat_min)
    
    return sampled_h[['nb_pdc', 'hs', 'inactif', 'sature', 'surcharge', 'actif', 'sature_h', 'surcharge_h']]


# all_state_h:pd.DataFrame, animate_state_h: pd.DataFrame
def animate_features(state_station_h:pd.DataFrame, surcharge: pd.DataFrame, stations_parcs: pd.DataFrame, colors:list, sizes:dict, period_min:int) -> list[dict]:
    """Génère les features utilisées pour l'animation temporelle des stations saturées.

    Une couleur est affectée pour chacun des deux états.
    La taille des points est choisie en fonction du nombre de pdc.
    L'animation démarre après l'heure définie par period_min."""
    def set_color(row:pd.Series)-> str:
        match [bool(row['sature_h']), bool(row['surcharge_h'])]:
            case [True, _]:
                return colors[0]
            case [_, True]: 
                return colors[1]
            case _:
                return 'white'
    def set_radius(nb_pdc:int)-> int:
        if nb_pdc < min(sizes['nb_pdc']):
            return min(sizes['radius'])
        if nb_pdc > max(sizes['nb_pdc']):
            return max(sizes['radius'])
        return sizes['radius'][1]
    surcharge_f = surcharge[surcharge['periode_h'] > period_min]        
    state_station_h_f = state_station_h[state_station_h['periode_h'] > period_min]
    stations_surcharge = surcharge_f['id_station_itinerance'].unique()
    surcharge_station_h = state_station_h_f[state_station_h_f['id_station_itinerance'].isin(stations_surcharge)]
    surcharge_station_h = pd.merge(surcharge_station_h, stations_parcs[['id_station_itinerance', 'parc_id', 'operateur', 'parc_nature', 'geometry']], how='left', on='id_station_itinerance')
    #surcharge_station_h['periode_iso'] = (surcharge_station_h["periode"].astype('datetime64[s]') + pd.Timedelta("1 hour") * surcharge_station_h["periode_h"] ).astype('str')
    surcharge_station_h['coordinates'] = surcharge_station_h['geometry'].apply(lambda x: shapely.get_coordinates(x).tolist()[0])
    
    surcharge_station_h['color'] = surcharge_station_h[['sature_h', 'surcharge_h']].apply(set_color, axis=1)
    surcharge_station_h['radius'] = surcharge_station_h['nb_pdc'].apply(set_radius)

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": row[1]["coordinates"],
            },
            "properties": {
                "time": row[1]["periode_iso"],
                "icon": "circle",
                "style": {
                    "color": row[1]["color"],
                    "weight": 0,
                    "radius": row[1]["radius"],
                    "fillOpacity": 0 if row[1]["color"] == "white" else 1
                },     
            },
        }
        for row in surcharge_station_h.iterrows()
    ]
    return features

def animate(refmap:folium.Map | dict, features:list[dict], **param):
    """Ajoute une couche d'animation temporelle sur une carte."""
    param = {
        "period": "PT1H",
        "auto_play": False,
        "loop": False,
        "max_speed": 1,
        "loop_button": True,
        "date_options": "YYYY/MM/DD-HH",
        "time_slider_drag_update": True,
        "duration": "PT0H"
    } | param
    refmap = folium.Map(**refmap) if isinstance(refmap, dict) else refmap
    folium.plugins.TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        **param
    ).add_to(refmap)
    return refmap