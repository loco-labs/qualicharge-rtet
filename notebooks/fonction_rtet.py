# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions utilisées dans l'analyse du réseau RTET des infrastructure IRVE.
"""
import math
import pandas as pd
import numpy as np
import geopandas as gpd
import networkx as nx
import geo_nx as gnx
from geo_nx import cast_id

def insertion_noeuds(noeuds, gr, proxi, att_node):
    '''insertion de 'noeuds' sur le graph 'gr'et retourne le graphe des 'noeuds' '''
    troncons = gr.to_geopandas_edgelist()
    join = gpd.sjoin(noeuds, troncons.set_geometry(troncons.buffer(proxi))) # filtrage des tronçons
    noeuds_ok = noeuds[noeuds.index.isin(join.index)]
    gs_noeuds = gnx.from_geopandas_nodelist(noeuds_ok, node_attr=True) # réseau des noeuds supplémentaires
    # à vectoriser
    for noeuds in gs_noeuds:
        geo_st = gs_noeuds.nodes[noeuds]['geometry']
        id_edge = gr.find_nearest_edge(geo_st, proxi) # recherche du troncon le plus proche
        id_node = int(max(cast_id(gr.nodes, only_int=True)) + 1)
        gr.insert_node(geo_st, id_node, id_edge, att_node=att_node, adjust=False) # ajout du noeud     
    return gs_noeuds

def proximite(noeuds_ext, cible, proxi):
    '''sépare les noeuds proches (distance < proxi) et non proches''' 
    st_join = gpd.sjoin(noeuds_ext, cible.set_geometry(cible.buffer(proxi)))
    st_ok = noeuds_ext.index.isin(st_join.index)
    return (noeuds_ext[st_ok], noeuds_ext[~st_ok])

def insertion_projection(nodes_ext, node_attr, edge_attr, gr, proxi, att_insert_node):
    '''création du graphe des stations avec projection sur des noeuds inserés dans le graphe 'gr' '''
    gr_ext = gnx.from_geopandas_nodelist(nodes_ext, node_id='node_id', node_attr=node_attr)
    stations = list(nodes_ext['node_id'])
    st_ko =[]
    for station in stations: # à vectoriser
        dist = gr_ext.project_node(station, gr, proxi, att_edge=edge_attr)
        if not dist:
            geo_st = gr_ext.nodes[station]['geometry']
            id_edge = gr.find_nearest_edge(geo_st, proxi)
            if not id_edge: 
                st_ko.append(station)
                print('ko')
                continue 
            # on ajoute un noeud et on crée le lien 
            id_node = int(max(cast_id(gr.nodes, only_int=True)) + 1)
            dis = gr.insert_node(geo_st, id_node, id_edge, att_node=att_insert_node, adjust=False) 
            if not dis: # cas à clarifier  
                st_ko.append(station)
                print(id_node, id_edge, geo_st)
                continue
            gr_ext.project_node(station, gr, 0, target_node=id_node, att_edge=edge_attr)
    return gr_ext, st_ko

def analyse_saturation(gr_ext, gr, non_sature, seuil): 
    '''identifie les tronçons qui ont au moins un point à une distance supérieure à 'seuil' de la plus proche station non saturée''' 
    saturation = []
    gr_stat_satur = nx.subgraph_view(gr, filter_node=(lambda x: not gr.nodes[x].get(non_sature, True)))
    gr_ext_st = nx.subgraph_view(gr_ext, filter_node=(lambda x: isinstance(x, str) and x[:2] == 'st'))
    for edge in gr.edges:
        dist_inter_st = gr.weight_extend(edge, gr_ext_st, radius=seuil, n_attribute='dist_node_ext', n_active=non_sature)
        if not dist_inter_st or dist_inter_st > 2 * seuil :
            saturation.append(edge)
    # gr_satur = nx.subgraph_view(gr, filter_edge=(lambda x1, x2: (x1, x2) in saturation))
    gr_satur = gr.edge_subgraph(saturation)
    return gr_stat_satur, gr_satur

