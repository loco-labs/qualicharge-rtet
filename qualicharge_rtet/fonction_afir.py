# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions utilisées dans l'analyse du réseau des infrastructures IRVE.
"""
import geopandas as gpd
import networkx as nx
import geo_nx as gnx

GEOM = "geometry"
NODE_ID = "node_id"
NATURE = "nature"
WEIGHT = "weight"
CORE = "core"


def insertion_noeuds(
    noeuds: gpd.GeoDataFrame,
    gr: gnx.GeoGraph,
    proxi: float,
    att_node: None | dict = None,
    troncons: None | list = None,
    adjust: bool = False,
) -> list[int]:
    """insere des 'noeuds' sur le graph 'gr' pour des troncons définis et retourne le graphe des 'noeuds'"""
    troncons = troncons if troncons is not None else gr.to_geopandas_edgelist()
    join = gpd.sjoin(
        noeuds, troncons.set_geometry(troncons.buffer(proxi))
    )  # filtrage des tronçons
    noeuds_ok = noeuds[noeuds.index.isin(join.index)].copy()
    noeuds_ok[NODE_ID] = range(max(gr.nodes) + 1, len(noeuds_ok) + max(gr.nodes) + 1)
    gs_noeuds = gnx.from_geopandas_nodelist(
        noeuds_ok, node_id=NODE_ID, node_attr=True
    )  # réseau des noeuds supplémentaires
    # à vectoriser
    added_nodes = []
    for noeud in gs_noeuds:
        geo_st = gs_noeuds.nodes[noeud][GEOM]
        id_edge = gr.find_nearest_edge(
            geo_st, proxi
        )  # recherche du troncon le plus proche
        att_noeud = (
            att_node
            if att_node is not None
            else {
                key: val
                for key, val in gs_noeuds.nodes[noeud].items()
                if key not in [NODE_ID, GEOM]
            }
        )
        dis = gr.insert_node(
            geo_st, noeud, id_edge, att_node=att_noeud, adjust=adjust
        )  # ajout du noeud
        if dis is not None:
            added_nodes.append(noeud)
    return added_nodes


def proximite(
    noeuds_ext: gpd.GeoDataFrame, cible: gpd.GeoDataFrame, proxi: float
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """sépare les noeuds proches (distance < proxi) et non proches"""
    st_join = gpd.sjoin(noeuds_ext, cible.set_geometry(cible.buffer(proxi)))
    st_ok = noeuds_ext.index.isin(st_join.index)
    return (noeuds_ext[st_ok], noeuds_ext[~st_ok])


def insertion_projection(
    nodes_ext: gpd.GeoDataFrame,
    node_attr: bool | str | list[str],
    edge_attr: None | dict,
    gr: gnx.GeoGraph,
    proxi: float,
    att_insert_node: None | dict,
) -> tuple[gnx.GeoGraph, list]:
    """création du graphe des stations avec projection sur des noeuds inserés dans le graphe 'gr'"""
    gr_ext = gnx.from_geopandas_nodelist(
        nodes_ext, node_id="node_id", node_attr=node_attr
    )
    stations = list(nodes_ext[NODE_ID])
    st_ko = []
    for station in stations:  # à vectoriser
        dist = gr_ext.project_node(station, gr, proxi, att_edge=edge_attr)
        if not dist:
            geo_st = gr_ext.nodes[station][GEOM]
            id_edge = gr.find_nearest_edge(geo_st, proxi)
            if not id_edge:
                st_ko.append(station)
                print("ko", station)
                continue
            # on ajoute un noeud et on crée le lien
            #id_node = max(max(gr.nodes) + 1, max(gr_ext.nodes) + 1)
            id_node = max(gr.nodes) + 1
            dis = gr.insert_node(
                geo_st, id_node, id_edge, att_node=att_insert_node, adjust=False
            )
            if dis is None:
                dist0 = geo_st.distance(gr.nodes[id_edge[0]][GEOM])
                dist1 = geo_st.distance(gr.nodes[id_edge[1]][GEOM])
                id_node = id_edge[0] if dist0 <= dist1 else id_edge[1]
            gr_ext.project_node(station, gr, 0, target_node=id_node, att_edge=edge_attr)
    return gr_ext, st_ko


def association_stations(
    gr: gnx.GeoGraph, stations_afir: gpd.GeoDataFrame, log: bool = False
) -> None | gnx.GeoGraph:
    """intègre les stations au graphe routier"""
    if gr is None or stations_afir is None:
        return None
    high_proxi_t = 100
    high_proxi_n = 300
    low_proxi = 2000

    noeuds = gr.to_geopandas_nodelist()
    noeuds_station = noeuds.loc[noeuds[NATURE] == "aire de service"]
    troncons = gr.to_geopandas_edgelist()
    troncons_hors_autoroute = troncons.loc[troncons[NATURE] == "troncon hors autoroute"]

    st_low_proxi, st_out = proximite(stations_afir, troncons, low_proxi)
    st_high_proxi_n, st_proxi_t = proximite(st_low_proxi, noeuds_station, high_proxi_n)
    #st_high_proxi_t, st_low_proxi = proximite(
    #    st_proxi_t, troncons_hors_autoroute, high_proxi_t
    #)
    if log: 
        print(
            "Nb stations (st, pre_st, ext, out, total) : ",
            len(st_high_proxi_n),
            len(st_proxi_t),
            #len(st_high_proxi_t),
            #len(st_low_proxi),
            len(st_out),
            len(stations_afir),
        )
    node_attr = ["amenageur", "operateur", "p_cum", "p_max", "id_station", NATURE]

    # IRVE très proches des stations
    edge_attr = {NATURE: "liaison aire de service"}
    gs_station, st_ko = gnx.project_graph(
        st_high_proxi_n, noeuds_station, high_proxi_n, node_attr, edge_attr
    )

    # IRVE proches d'un tronçon
    edge_attr = {NATURE: "liaison exterieur"}
    filter = (noeuds[NATURE] == "echangeur") | (noeuds[NATURE] == "rond-point")
    gs_externe, st_ko = gnx.project_graph(
        # st_low_proxi, noeuds.loc[filter], low_proxi, node_attr, edge_attr
        st_proxi_t, noeuds.loc[filter], low_proxi, node_attr, edge_attr
    )

    '''# IRVE très proches d'un tronçon
    edge_attr = {NATURE: "liaison aire de recharge"}
    att_node_insert = {NATURE: "aire de recharge"}
    gs_pre_station, st_ko = insertion_projection(
        st_high_proxi_t, node_attr, edge_attr, gr, high_proxi_t, att_node_insert
    )'''
    #return gnx.compose_all([gr, gs_externe, gs_pre_station, gs_station])
    return gnx.compose_all([gr, gs_externe, gs_station])

def propagation_attributs_core(gr: gnx.GeoGraph, nature: str) -> None:
    """propage l'attribut 'core' des tronçons sur les noeuds de type 'nature'"""
    for node in list(gr.nodes):
        if gr.nodes[node][NATURE] == nature:
            core = False
            for neighbors in gr.neighbors(node):
                if gr.edges[neighbors, node].get(CORE, False):
                    core = True
                    break
            gr.nodes[node][CORE] = core
    return

def propagation_attributs_edges(gr: gnx.GeoGraph)-> None:
    """crée les attributs 'core' et 'noeud autoroute' des noeuds à partir des tronçons"""
    for node in list(gr.nodes):
        core = False
        for neighbors in gr.neighbors(node):
            if gr.edges[neighbors, node].get(CORE, False):
                core = True
                break
        gr.nodes[node][CORE] = core
        if gr.nodes[node][NATURE] == 'noeud rtet':
            autoroute = True
            for neighbors in gr.neighbors(node):
                if gr.edges[neighbors, node][NATURE] != 'troncon autoroute':
                    autoroute = False
                    break
            if autoroute:
                gr.nodes[node][NATURE] = 'noeud autoroute'
    for edge in list(gr.edges):
        if gr.edges[edge][NATURE] == 'liaison aire':
            core = gr.nodes[edge[0]].get(CORE, False) or gr.nodes[edge[1]].get(CORE, False)
            gr.edges[edge][CORE] = gr.nodes[edge[0]][CORE] = gr.nodes[edge[1]][CORE] = core
    return

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
            gr_rev=gr_rev
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

def get_rtet_attr_station(node, gr_station: gnx.GeoGraph, attr: str) -> bool:
    """restitue la valeur d'un attribut du RTET"""
    return gr_station.nodes[list(gr_station.neighbors(node))[0]][attr]

def get_parc_id_station(node, gr_station: gnx.GeoGraph=None) -> bool:
    """restitue l'Id du parc associé à la station"""
    return 'parc ' + str(list(gr_station.neighbors(node))[0])

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
