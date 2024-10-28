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

GEOM = 'geometry'
NODE_ID = 'node_id'
NATURE = 'nature'
WEIGHT = 'weight'

def insertion_noeuds(noeuds, gr, proxi, att_node=None, troncons=None, adjust=False):
    '''insere des 'noeuds' sur le graph 'gr' pour des troncons définis et retourne le graphe des 'noeuds' '''
    troncons = troncons if troncons is not None else gr.to_geopandas_edgelist()
    join = gpd.sjoin(noeuds, troncons.set_geometry(troncons.buffer(proxi))) # filtrage des tronçons
    noeuds_ok = noeuds[noeuds.index.isin(join.index)].copy()
    noeuds_ok[NODE_ID] = range(max(gr.nodes)+1, len(noeuds_ok)+max(gr.nodes)+1)
    gs_noeuds = gnx.from_geopandas_nodelist(noeuds_ok, node_id=NODE_ID, node_attr=True) # réseau des noeuds supplémentaires
    # à vectoriser
    for noeud in gs_noeuds:
        geo_st = gs_noeuds.nodes[noeud][GEOM]
        id_edge = gr.find_nearest_edge(geo_st, proxi) # recherche du troncon le plus proche
        att_node = att_node if att_node is not None else {key: val for key, val in gs_noeuds.nodes[noeud].items() if key not in [NODE_ID, GEOM]}
        gr.insert_node(geo_st, noeud, id_edge, att_node=att_node, adjust=adjust) # ajout du noeud
    return gs_noeuds

def proximite(noeuds_ext, cible, proxi):
    '''sépare les noeuds proches (distance < proxi) et non proches''' 
    st_join = gpd.sjoin(noeuds_ext, cible.set_geometry(cible.buffer(proxi)))
    st_ok = noeuds_ext.index.isin(st_join.index)
    return (noeuds_ext[st_ok], noeuds_ext[~st_ok])

def insertion_projection(nodes_ext, node_attr, edge_attr, gr, proxi, att_insert_node):
    '''création du graphe des stations avec projection sur des noeuds inserés dans le graphe 'gr' '''
    gr_ext = gnx.from_geopandas_nodelist(nodes_ext, node_id='node_id', node_attr=node_attr)
    stations = list(nodes_ext[NODE_ID])
    st_ko =[]
    for station in stations: # à vectoriser
        dist = gr_ext.project_node(station, gr, proxi, att_edge=edge_attr)
        if not dist:
            geo_st = gr_ext.nodes[station][GEOM]
            id_edge = gr.find_nearest_edge(geo_st, proxi)
            if not id_edge: 
                st_ko.append(station)
                print('ko')
                continue 
            # on ajoute un noeud et on crée le lien 
            id_node = max(max(gr.nodes) + 1, max(gr_ext.nodes) + 1)
            dis = gr.insert_node(geo_st, id_node, id_edge, att_node=att_insert_node, adjust=False) 
            if not dis: # cas à clarifier  
                st_ko.append(station)
                print(id_node, id_edge, geo_st)
                continue
            gr_ext.project_node(station, gr, 0, target_node=id_node, att_edge=edge_attr)
    return gr_ext, st_ko

def troncons_non_mailles(g_tot, gr_ext, gr, dispo, seuil, n_attribute='dist_actives', stat_attribute='station_irve'): 
    '''identifie les tronçons dont la distance entre les stations disponibles les plus proches est supérieure à 'seuil' ''' 
    troncons_non_mailles = []
    gr_ext_indispo = nx.induced_subgraph(gr_ext, [nd for nd in gr_ext.nodes if not gr_ext.nodes[nd].get(dispo, True)])
    gr_ext_st = nx.subgraph_view(gr_ext, filter_node=(lambda x: NATURE in gr_ext.nodes[x] and gr_ext.nodes[x][NATURE] == stat_attribute))
    for edge in gr.edges:
        distance_max = seuil - g_tot.edges[edge][WEIGHT]
        dist_inter_st = g_tot.weight_extend(edge, gr_ext_st, radius=distance_max, n_attribute=n_attribute, n_active=dispo)
        if not dist_inter_st or dist_inter_st > seuil :
            troncons_non_mailles.append(edge)
    return gr_ext_indispo, gr.edge_subgraph(troncons_non_mailles)

def troncons_peu_mailles(gr_satur, g_tot, dispo):
    '''complète gr_satur avec les tronçons allant jusqu'à une bifurcation ou une station disponible'''
    nd_sat = set(gr_satur.nodes())
    ed_extend = set(gr_satur.edges())
    for node in gr_satur.nodes():
        adjs = set(nd for nd in g_tot.adj[node] 
                   if nd not in nd_sat and (dispo not in g_tot.nodes[nd] or g_tot.nodes[nd][dispo])
                  ) - nd_sat
        while len(adjs) == 1:
            nd_sat.add(node)
            new_node = list(adjs)[0]
            ed_extend.add((node, new_node))
            node = new_node
            adjs = set(nd for nd in g_tot.adj[node] 
                       if nd not in nd_sat and (dispo not in g_tot.nodes[nd] or g_tot.nodes[nd][dispo])
                      ) - nd_sat
    return g_tot.edge_subgraph(ed_extend)

def aretes_adjacentes(node_index, nodes, vertices, distance, excl_list):
    ext_vertices = vertices.drop(excl_list).copy()
    aretes_adj = ext_vertices[(ext_vertices["source"] == node_index) | (ext_vertices["target"] == node_index)].copy()
    aretes_adj["ext"] = aretes_adj[["source", "target"]].apply(lambda row: row["target"] if row["target"] != node_index else row["source"], 1)
    aretes_adj = aretes_adj[aretes_adj["weight"] < distance]
    aretes_adj = aretes_adj.reset_index().merge(nodes.reset_index(), left_on="ext", right_on="node_id").set_index("index")
    aretes_adj["station"] = aretes_adj["nature"] == "station_irve" 
    aretes_adj.loc[~aretes_adj["station"], "distance_restante"] = distance - aretes_adj.loc[~aretes_adj["station"], "weight"]
    # for _, row in aretes_adj[~aretes_adj["station"]].iterrows():
    #     print(aretes_adjacentes(row["fin"], row["distance_restante"]))
    return aretes_adj
    
def green_list(node, nodes, vertices, distance_restante, excl_list):
    return_list = []
    adj = aretes_adjacentes(node, nodes, vertices, distance_restante, excl_list)
    return_list += adj[adj["station"]].index.to_list()
    for n, r in adj[~adj["station"]].iterrows():
        excl_list.append(n)
        recur_list = green_list(r["ext"], nodes, vertices, r["distance_restante"], excl_list)
        return_list += recur_list
        if len(recur_list) > 0: return_list.append(n)
    return return_list

def gr_maillage(gr_tot, nodes, vertices, distance: float = 60000.0):
    #edge_ids = []
    edge_ids = set()
    #excl_list = []    
    for st in nodes[nodes["nature"] == "station_irve"].index:
        excl_list = []
        #edge_ids+= green_list(st, nodes, vertices, distance, excl_list)
        edge_ids |= set(green_list(st, nodes, vertices, distance, excl_list))
    edge_ids = list(edge_ids)
    green_vert = [(src, tgt) for src, tgt in zip(vertices.loc[edge_ids, "source"], vertices.loc[edge_ids, "target"])]
    return nx.subgraph_view(gr_tot, filter_edge=(lambda x1, x2: (x1, x2) in green_vert))