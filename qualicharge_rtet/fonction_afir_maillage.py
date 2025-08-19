# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions utilisées dans l'analyse du réseau des infrastructures IRVE.
"""
import geopandas as gpd
import networkx as nx
import geo_nx as gnx  # type: ignore

GEOM = "geometry"
NODE_ID = "node_id"
NATURE = "nature"
WEIGHT = "weight"
CORE = "core"


def troncons_non_mailles(
    g_tot: gnx.GeoGraph,
    gr_ext: gnx.GeoGraph,
    gr: gnx.GeoGraph,
    dispo: str,
    seuil: float,
    n_attribute: str = "dist_actives",
    stat_attribute: str = "station_irve",
) -> tuple[gnx.GeoGraph, gnx.GeoGraph]:
    """identifie les tronçons dont la distance entre les stations disponibles
    les plus proches est supérieure à 'seuil'"""
    stat_attribute = (
        stat_attribute if isinstance(stat_attribute, list) else [stat_attribute]
    )
    troncons_non_mailles = []
    gr_ext_indispo = nx.induced_subgraph(
        gr_ext, [nd for nd in gr_ext.nodes if not gr_ext.nodes[nd].get(dispo, True)]
    )
    gr_ext_st = nx.subgraph_view(
        gr_ext,
        filter_node=(
            lambda x: NATURE in gr_ext.nodes[x]
            and gr_ext.nodes[x][NATURE] in stat_attribute
        ),
    )

    is_dgr = isinstance(g_tot, gnx.geodigraph.GeoDiGraph)
    gr_rev = g_tot.reverse() if is_dgr else None
    for edge in gr.edges:
        distance_max = seuil - g_tot.edges[edge][WEIGHT]
        dist_inter_st = g_tot.weight_extend(
            edge,
            gr_ext_st,
            radius=distance_max,
            n_attribute=n_attribute,
            n_active=dispo,
            gr_rev=gr_rev,
        )
        if not dist_inter_st or dist_inter_st > seuil:
            troncons_non_mailles.append(edge)
    return gr_ext_indispo, gr.edge_subgraph(troncons_non_mailles)


def troncons_peu_mailles(
    gr_satur: gnx.GeoGraph, g_tot: gnx.GeoGraph, dispo: str
) -> gnx.GeoGraph:
    """complète gr_satur avec les tronçons allant jusqu'à une bifurcation ou une station disponible"""
    nd_sat = set(gr_satur.nodes())
    ed_extend = set(gr_satur.edges())
    for node in gr_satur.nodes():
        adjs = (
            set(
                nd
                for nd in g_tot.adj[node]
                if nd not in nd_sat
                and (dispo not in g_tot.nodes[nd] or g_tot.nodes[nd][dispo])
            )
            - nd_sat
        )
        while len(adjs) == 1:
            nd_sat.add(node)
            new_node = list(adjs)[0]
            ed_extend.add((node, new_node))
            node = new_node
            adjs = (
                set(
                    nd
                    for nd in g_tot.adj[node]
                    if nd not in nd_sat
                    and (dispo not in g_tot.nodes[nd] or g_tot.nodes[nd][dispo])
                )
                - nd_sat
            )
    return g_tot.edge_subgraph(ed_extend)


def aretes_adjacentes(
    node_index: int,
    nodes: gpd.GeoDataFrame,
    vertices: gpd.GeoDataFrame,
    distance: float,
    excl_list: list[int],
) -> gpd.GeoDataFrame:
    ext_vertices = vertices.drop(excl_list).copy()
    aretes_adj = ext_vertices[
        (ext_vertices["source"] == node_index) | (ext_vertices["target"] == node_index)
    ].copy()
    aretes_adj["ext"] = aretes_adj[["source", "target"]].apply(
        lambda row: row["target"] if row["target"] != node_index else row["source"], 1
    )
    aretes_adj = aretes_adj[aretes_adj["weight"] < distance]
    aretes_adj = (
        aretes_adj.reset_index()
        .merge(nodes.reset_index(), left_on="ext", right_on="node_id")
        .set_index("index")
    )
    aretes_adj["station"] = aretes_adj["nature"] == "station_irve"
    aretes_adj.loc[~aretes_adj["station"], "distance_restante"] = (
        distance - aretes_adj.loc[~aretes_adj["station"], "weight"]
    )
    # for _, row in aretes_adj[~aretes_adj["station"]].iterrows():
    #     print(aretes_adjacentes(row["fin"], row["distance_restante"]))
    return aretes_adj


def green_list(
    node: int,
    nodes: gpd.GeoDataFrame,
    vertices: gpd.GeoDataFrame,
    distance_restante: float,
    excl_list: list,
) -> list[int]:
    return_list = []
    adj = aretes_adjacentes(node, nodes, vertices, distance_restante, excl_list)
    return_list += adj[adj["station"]].index.to_list()
    for n, r in adj[~adj["station"]].iterrows():
        excl_list.append(n)
        recur_list = green_list(
            r["ext"], nodes, vertices, r["distance_restante"], excl_list
        )
        return_list += recur_list
        if len(recur_list) > 0:
            return_list.append(n)
    return return_list


def gr_maillage(
    gr_tot: gnx.GeoGraph,
    nodes: gpd.GeoDataFrame,
    vertices: gpd.GeoDataFrame,
    distance: float,
) -> gnx.GeoGraph:
    """identifie les tronçons dont la distance entre les stations disponibles
    les plus proches est supérieure à un seuil (méthode par noeud)"""
    edge_ids_old = []
    edge_ids = set()
    # excl_list = []
    for st in nodes[nodes["nature"] == "station_irve"].index:
        excl_list = []
        green_l = green_list(st, nodes, vertices, distance, excl_list)
        edge_ids_old += green_l
        edge_ids |= set(green_l)
        # edge_ids |= set(green_list(st, nodes, vertices, distance, excl_list))
    edge_ids = list(edge_ids)
    print(len(edge_ids), len(edge_ids_old))
    green_vert = [
        (src, tgt)
        for src, tgt in zip(
            vertices.loc[edge_ids, "source"], vertices.loc[edge_ids, "target"]
        )
    ]
    return nx.subgraph_view(gr_tot, filter_edge=(lambda x1, x2: (x1, x2) in green_vert))
