# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions d'interface utilisées dans l'analyse du réseau RTET des infrastructure IRVE.
"""
import json
import pandas as pd
import numpy as np
import geopandas as gpd
import networkx as nx
import geo_nx as gnx
from shapely import Point
from qualicharge_rtet.fonction_afir import get_rtet_attr_station, get_parc_id_station

GEOM = 'geometry'
NODE_ID = 'node_id'
NATURE = 'nature'
WEIGHT = 'weight'
CORE = 'core'

def creation_reseau_rtet(shp_file):
    rtet = gpd.read_file(shp_file).to_crs(2154)
    rtet.loc[rtet["NATIONALRO"] == "N29", "NATIONALRO"] = "A29"
    rtet.loc[rtet["ID"] == "25111", "NATIONALRO"] = "A63"
    
    rtet[CORE] = rtet["CORE_NETWO"] == '1'
    autoroute = rtet['NATIONALRO'].map(str).str.startswith('A')
    rtet[NATURE] = 'troncon hors autoroute'
    rtet.loc[autoroute, NATURE] = 'troncon autoroute'
    
    gr = gnx.from_geopandas_edgelist(rtet, edge_attr=["CORRIDORS", "INTROADNUM", "NATIONALRO", "ID", GEOM, NATURE, CORE])
    gr.erase_linear_nodes(keep_attr=[NATURE, CORE])
    nx.set_node_attributes(gr, "noeud rtet", name=NATURE)
    return gr

def creation_pandas_aires(file):
    asfa = pd.read_csv(file)
    asfa = pd.concat([asfa, pd.json_normalize(asfa['dict'].map(
        lambda x: str.replace(x, '"', "")).map(
        lambda x: str.replace(x, "'", '"')).map(json.loads))], axis=1)
    del asfa['Unnamed: 0']
    del asfa['dict']
    asfa[GEOM] = asfa['coords'].map(json.loads).map(lambda x: [x[1], x[0]]).map(Point)
    asfa[NATURE] = 'aire de service'
    #asfa.drop_duplicates(subset=[GEOM], inplace=True)
    return gpd.GeoDataFrame(asfa, crs='4326').to_crs(2154)
    
def creation_pandas_stations(data: str | pd.DataFrame, nature="station_irve", first_id=0, source='gireve') -> pd.DataFrame:
    """generation d'un DataFrame des stations
    
    Champs du DataFrame:
    - geometry : Point
    - amenageur : nom de l amenageur
    - operateur : nom de l operateur
    - p_cum : puissance cumulée de la station
    - p_max : puissance maxi des points de recharge
    - node_id : numéro de node
    - id_station : identifiant de la station
    - nature : type de station
    """
    if source == 'gireve':
        # Chargement des points de recharge de la consolidation Gireve
        csl = pd.read_csv(data, sep=";", encoding="latin") if isinstance(data, str) else data
        if csl["puissance_nominale"].dtype != np.dtype('float64'):
            csl["puissance_nominale"] = csl["puissance_nominale"].str.replace(',', '.').astype(float)
        
        # Les stations respectant les critères AFIR sont obtenues après un groupby sur les coordonnées
        stations_csl = csl.groupby("coordonneesXY").agg(
            p_max = ("puissance_nominale", "max"), 
            p_cum = ("puissance_nominale", "sum"),
            id_station = ("id_pdc_regroupement", "first"),
            amenageur = ("nom_amenageur", "first"),
            operateur = ("nom_operateur", "first"))
        stations = stations_csl.reset_index()
        stations[GEOM] = stations["coordonneesXY"].apply(lambda x: Point(str.split(x, ',')))
        stations = gpd.GeoDataFrame(stations, crs=4326).to_crs(2154)
    elif source == 'qualicharge':
        csl = pd.read_csv(data, sep=",") if isinstance(data, str) else data
        geom = gpd.points_from_xy(csl.longitude, csl.latitude)
        stations = gpd.GeoDataFrame(csl, geometry=geom, crs=4326).to_crs(2154)
    stations[NODE_ID] = range(first_id, len(stations) + first_id)
    stations[NATURE] = nature        
        
    return stations[['p_cum', 'p_max', 'id_station', 'operateur', 'amenageur', GEOM, NODE_ID, NATURE]]

def export_stations_parcs(graph: gnx.GeoGraph, simple:bool=False) -> pd.DataFrame:
    """Extraction et export des stations et parcs de recharge d'un graphe"""
    gr_stations = nx.subgraph_view(graph, filter_node=lambda x: graph.nodes[x][NATURE] == 'station_irve')
    stations = gr_stations.to_geopandas_nodelist()
    stations[CORE] = stations['node_id'].apply(get_rtet_attr_station, args=(graph, CORE))
    stations['parc_nature'] = stations['node_id'].apply(get_rtet_attr_station, args=(graph, NATURE))
    stations['parc_geometry'] = stations['node_id'].apply(get_rtet_attr_station, args=(graph, GEOM))
    stations['parc_id'] = stations['node_id'].apply(get_parc_id_station, args=(graph,))
    stations['id_station_itinerance'] = stations['id_station']

    if simple:
        return stations[['id_station_itinerance', CORE, NODE_ID, 'parc_nature', 'parc_geometry', 'parc_id']]
    return stations
