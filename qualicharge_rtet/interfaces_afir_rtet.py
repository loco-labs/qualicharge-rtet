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