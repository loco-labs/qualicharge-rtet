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


def creation_reseau_rtet(shp_file):
    rtet = gpd.read_file(shp_file).to_crs(2154)
    rtet.loc[rtet["NATIONALRO"] == "N29", "NATIONALRO"] = "A29"
    rtet.loc[rtet["ID"] == "25111", "NATIONALRO"] = "A63"
    
    rtet['core'] = rtet["CORE_NETWO"] == '1'
    autoroute = rtet['NATIONALRO'].map(str).str.startswith('A')
    rtet['nature'] = 'troncon hors autoroute'
    rtet.loc[autoroute, 'nature'] = 'troncon autoroute'
    
    gr = gnx.from_geopandas_edgelist(rtet, edge_attr=["CORRIDORS", "INTROADNUM", "NATIONALRO", "ID", "geometry", "nature", "core"])
    gr.erase_linear_nodes(keep_attr=['nature', 'core'])
    nx.set_node_attributes(gr, "connecteur", name="nature")
    return gr

def creation_pandas_aires(file):
    asfa = pd.read_csv(file)
    asfa = pd.concat([asfa, pd.json_normalize(asfa['dict'].map(lambda x: str.replace(x, '"', "")).map(lambda x: str.replace(x, "'", '"')).map(json.loads))], axis=1)
    del asfa['Unnamed: 0']
    del asfa['dict']
    asfa['geometry'] = asfa['coords'].map(json.loads).map(lambda x: [x[1], x[0]]).map(Point)
    asfa['nature'] = 'aire de service'
    asfa.drop_duplicates(subset=['geometry'], inplace=True)
    return gpd.GeoDataFrame(asfa, crs='4326').to_crs(2154)
    
def creation_pandas_stations(file, pmax, pcum, max_id):
    # Chargement des points de recharge de la consolidation Gireve
    csl = pd.read_csv(file, sep=";", encoding="latin")
    csl["puissance_nominale"] = csl["puissance_nominale"].astype(float)
    
    # Les stations respectant les critères AFIR sont obtenues après un groupby sur les coordonnées
    stations = csl.groupby("coordonneesXY").agg(
        p_max = ("puissance_nominale", "max"), 
        p_cum = ("puissance_nominale", "sum"),
        id_station = ("id_pdc_regroupement", "first"),
        amenageur = ("nom_amenageur", "first"),
        operateur = ("nom_operateur", "first"))
    stations_afir = stations[(stations["p_max"] > pmax) & (stations["p_cum"] > pcum)].copy().reset_index()
    stations_afir['geometry'] = stations_afir["coordonneesXY"].apply(lambda x: Point(str.split(x, ',')))
    stations_afir = gpd.GeoDataFrame(stations_afir, crs=4326).to_crs(2154)
    stations_afir['node_id'] = range(max_id + 1, len(stations_afir) + max_id + 1)
    stations_afir['nature'] = 'station_irve'
    return stations_afir