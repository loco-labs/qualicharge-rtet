# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 21:22:32 2024

@author: a lab in the Air
"""

import json
from shapely import LineString, Point
import numpy as np
import geopandas as gpd
import pandas as pd
import geo_nx as gnx 
import networkx as nx 
from networkx.utils import graphs_equal

from geo_nx import geom_to_crs, cast_id
from fonction_rtet import insertion_noeuds, proximite, insertion_projection

version = 'V1'
data_path = '../data/'
rtet_path = '../rtet/'
refnat = {'tiles': 'cartodbpositron', 'location': [46.3, 2.3], 'zoom_start': 7}

rtet = gpd.read_file(data_path + "roads_GL2017_Council_FR/roads_GL2017_Council_FR.shp").to_crs(2154)
rtet.loc[rtet["NATIONALRO"] == "N29", "NATIONALRO"] = "A29"
rtet.loc[rtet["ID"] == "25111", "NATIONALRO"] = "A63"
autoroute = rtet['NATIONALRO'].map(str).str.startswith('A')
rtet['nature'] = 'troncon hors autoroute'
rtet.loc[autoroute, 'nature'] = 'troncon autoroute'
gr = gnx.from_geopandas_edgelist(rtet, edge_attr=["CORE_NETWO", "CORRIDORS", "INTROADNUM", "NATIONALRO", "GEO_LENGTH", "ID", "geometry", "nature"])
nx.set_node_attributes(gr, "connecteur", name="nature")

sg = nx.subgraph_view(gr, filter_edge=lambda x,y: gr[x][y]["nature"] == 'troncon autoroute')
gr_autoroute =  nx.induced_subgraph(sg, nx.utils.flatten(sg.edges()))

sg = nx.subgraph_view(gr, filter_edge=lambda x,y: gr[x][y]["nature"] == 'troncon hors autoroute')
gr_hors_autoroute =  nx.induced_subgraph(sg, nx.utils.flatten(sg.edges()))

asfa = pd.read_csv(data_path + "asfa.csv")
asfa = pd.concat([asfa, pd.json_normalize(asfa['dict'].map(lambda x: str.replace(x, '"', "")).map(lambda x: str.replace(x, "'", '"')).map(json.loads))], axis=1)
del asfa['Unnamed: 0']
del asfa['dict']
asfa['geometry'] = asfa['coords'].map(json.loads).map(lambda x: [x[1], x[0]]).map(Point)
asfa['nature'] = 'aire de service'
asfa.drop_duplicates(subset=['geometry'], inplace=True)
asfa_gpd = gpd.GeoDataFrame(asfa, crs='4326').to_crs(2154)

proxi_geo = 100 # distance maximale au réseau routier 
noeuds_as = asfa_gpd.loc[asfa_gpd['type']=='AS', ['nom', 'nature', 'geometry', 'roadname']].copy()
gs_noeuds_as = insertion_noeuds(noeuds_as, gr, proxi_geo, adjust=False)

param_exp_ech = {'n_name': 'echangeurs', 'n_color': 'blue', 'n_marker_kwds': {'radius': 3, 'fill': True}}
param_exp_rp = {'n_name': 'rond-points', 'n_color': 'purple', 'n_marker_kwds': {'radius': 3, 'fill': True}}
param_exp_as = {'n_name': 'aire de service', 'n_color': 'red', 'n_marker_kwds': {'radius': 3, 'fill': True}}
param_exp_gr = {'e_name': 'edges', 'n_name': 'nodes', 'e_popup': ['weight', 'source', 'target', "CORE_NETWO", "NATIONALRO"], 
                'e_tooltip': ["source", "target", "nature"], 'n_tooltip': ["node_id", "nature"], 'n_marker_kwds': {'radius': 1, 'fill': False}}
#carte = gs_noeuds_ech.explore(refmap=refnat, edges=False, **param_exp_ech)
#carte = gs_noeuds_rp.explore(refmap=carte, edges=False, **param_exp_rp)
carte = gs_noeuds_as.explore(refmap=refnat, edges=False, **param_exp_as)
carte = gr.explore(refmap=carte, layercontrol=True, n_color='black', **param_exp_gr)
carte.save('ma_carte.html')