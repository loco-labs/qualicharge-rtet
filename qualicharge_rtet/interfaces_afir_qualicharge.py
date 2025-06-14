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
from qualicharge_rtet.fonction_afir import association_stations, propagation_attributs_core

GEOM = 'geometry'
NODE_ID = 'node_id'
NATURE = 'nature'
CORE = 'core'
ID_STATION_ITINERANCE = 'id_station_itinerance'
    
def creation_pandas_stations(data: str | pd.DataFrame, nature: str="station_irve", first_id: int=0, source: str='gireve', only_mandatory: bool=False) -> gpd.GeoDataFrame:
    """generation d'un DataFrame des stations
    
    Champs du DataFrame:
    - geometry : Point
    - amenageur (optionel): nom de l amenageur
    - operateur (optionnel): nom de l operateur
    - p_cum : puissance cumulée de la station
    - p_max : puissance maxi des points de recharge
    - node_id : numéro de node
    - id_station_itinerance : identifiant de la station
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
        stations[ID_STATION_ITINERANCE] = stations["id_station"]
        stations = gpd.GeoDataFrame(stations, crs=4326).to_crs(2154)
    elif source == 'qualicharge':
        csl = pd.read_csv(data, sep=",") if isinstance(data, str) else data
        geom = gpd.points_from_xy(csl.longitude, csl.latitude)
        stations = gpd.GeoDataFrame(csl, geometry=geom, crs=4326).to_crs(2154)
    stations[NODE_ID] = range(first_id, len(stations) + first_id)
    stations[NATURE] = nature        
    if only_mandatory:
            return stations[['p_cum', 'p_max', ID_STATION_ITINERANCE, GEOM, NODE_ID, NATURE]]
    return stations

def export_stations_parcs(graph: gnx.GeoGraph, only_mandatory:bool=False) -> pd.DataFrame:
    """Extraction et export des stations et parcs de recharge d'un graphe"""
    gr_stations = nx.subgraph_view(graph, filter_node=lambda x: graph.nodes[x][NATURE] == 'station_irve')
    stations = gr_stations.to_geopandas_nodelist()
    stations[CORE] = stations['node_id'].apply(get_rtet_attr_station, args=(graph, CORE))
    stations['parc_nature'] = stations['node_id'].apply(get_rtet_attr_station, args=(graph, NATURE))
    stations['parc_geometry'] = stations['node_id'].apply(get_rtet_attr_station, args=(graph, GEOM))
    stations['parc_id'] = stations['node_id'].apply(get_parc_id_station, args=(graph,))
    #stations['id_station_itinerance'] = stations['id_station']

    if only_mandatory:
        return stations[[ID_STATION_ITINERANCE, CORE, NODE_ID, 'parc_nature', 'parc_geometry', 'parc_id']]
    return stations

def filter_stations_parcs(rtet_edges: gpd.GeoDataFrame, rtet_nodes: gpd.GeoDataFrame, stations: pd.DataFrame, pmax: float=0, pcum: float=0, only_mandatory: bool=True) -> pd.DataFrame:
    """Extraction et export des stations et parcs de recharge d'un graphe"""

    # réseau rtet
    gr = gnx.from_geopandas_edgelist(rtet_edges, node_gdf= rtet_nodes, node_attr=True, edge_attr=True)
    
    # mise au format afir des stations
    first_id = max(gr.nodes) + 1
    stations_afir = creation_pandas_stations(stations, nature="station_irve", first_id=first_id, only_mandatory=only_mandatory, source="qualicharge")
    stations_afir_p = stations_afir[(stations_afir["p_max"] > pmax) & (stations_afir["p_cum"] > pcum)].reset_index()

    # réseau global
    gr_afir = association_stations(gr, stations_afir_p, only_mandatory=only_mandatory, log=True, id_station="id_station_itinerance") 
    propagation_attributs_core(gr_afir, "aire de recharge")
    
    # génération des stations liées au réseau RTET
    return export_stations_parcs(gr_afir, only_mandatory=only_mandatory)
