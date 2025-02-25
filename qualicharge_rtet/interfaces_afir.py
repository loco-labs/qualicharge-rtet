# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions d'interface utilisées dans l'analyse du réseau RTET des infrastructure IRVE.
"""
import json
import pandas as pd
import geopandas as gpd
import networkx as nx
import geo_nx as gnx
from shapely import Point

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
    
    #tot = 0
    #list_nodes = list(gr.nodes)
    for node in list(gr.nodes):
        autoroute = True
        for neighbors in gr.neighbors(node):
            if gr.edges[neighbors, node]['nature'] != 'troncon autoroute':
                autoroute = False
                break
        if autoroute:
            #nx.set_node_attributes(gr, "noeud autoroute", name=NATURE)
            gr.nodes[node][NATURE] = 'noeud autoroute'
            #tot += 1
    #print(tot)
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
        csl["puissance_nominale"] = csl["puissance_nominale"].astype(float)
        
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