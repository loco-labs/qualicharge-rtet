
# -*- coding: utf-8 -*-
"""
Ce module contient la classe Afir .
"""
import networkx as nx
import geo_nx as gnx
from fonction_rtet import association_stations

GEOM = 'geometry'
NODE_ID = 'node_id'
NATURE = 'nature'
WEIGHT = 'weight'
CORE = 'core'


class Afir():
    """La classe Afir est associée aux indicateurs AFIR du réseau RTE-T..

    *instance methods*

    - `insert_node`

    """

    def __init__(self, rtet, stations, central=True, pcum=400, pmax=150, dist=60):
        """The initialization of an Afir scenario includes :
        - GeoGraph is identical to a Graph initialization.
        (with the addition of the creation of a 'crs' attribute - default : None).

        The 'geometry' attribute is mandatory for the GeoGraph methods (eg. to_geopandas_edgelist)

        Examples
        --------
        Create an empty graph structure (a "null graph") with no nodes and no edges.

        >>> G = nx.Graph()
        """
        self.stations = stations[(stations["p_max"] > pmax) & (
            stations["p_cum"] > pcum)].reset_index()
        self.central = central
        self.pcum = pcum
        self.pmax = pmax
        self.dist = dist
        if central:
            sub = nx.subgraph_view(
                rtet, filter_edge=lambda x, y: rtet[x][y][CORE])
            rtet_core = nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))
            self.rtet = gnx.GeoGraph(rtet_core)
        else:
            self.rtet = rtet
        self.reseau = association_stations(self.rtet, self.stations)

    @property
    def gr_all(self):
        sub = nx.subgraph_view(self.rtet, filter_edge=(
            lambda x, y: self.rtet[x][y][NATURE][:7] == 'troncon'))
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_autoroute(self):
        sub = nx.subgraph_view(self.rtet, filter_edge=(
            lambda x, y: self.rtet[x][y][NATURE] == 'troncon autoroute'))
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_hors_autoroute(self):
        sub = nx.subgraph_view(self.rtet, filter_edge=(
            lambda x, y: self.rtet[x][y][NATURE] == 'troncon hors autoroute'))
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_rtet_central(self):
        sub = nx.subgraph_view(self.rtet, filter_edge=(
            lambda x, y: self.rtet[x][y]["core"]))
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_rtet_global(self):
        sub = nx.subgraph_view(self.rtet, filter_edge=(
            lambda x, y: not self.rtet[x][y]["core"]))
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_aire_service(self):
        return nx.subgraph_view(self.reseau, filter_node=(
            lambda x: self.reseau.nodes[x][NATURE] == 'aire de service'))

    @property
    def gr_echangeur(self):
        return nx.subgraph_view(self.reseau, filter_node=(
            lambda x: self.reseau.nodes[x][NATURE] == 'echangeur'))

    @property
    def gr_rond_point(self):
        return nx.subgraph_view(self.reseau, filter_node=(
            lambda x: self.reseau.nodes[x][NATURE] == 'rond-point'))

    @property
    def gs_all(self):
        return nx.subgraph_view(self.reseau, filter_node=(
            lambda x: self.reseau.nodes[x][NATURE] == "station_irve"))

    @property
    def gs_station(self):
        return nx.subgraph_view(self.reseau, filter_node=(
            lambda x: self.reseau.nodes[x][NATURE] == "station_irve" and
            self.reseau.edges[x, list(self.reseau.adj[x])[0]]
            [NATURE] == 'liaison aire de service'))

    @property
    def gs_pre_station(self):
        return nx.subgraph_view(self.reseau, filter_node=(
            lambda x: self.reseau.edges[x, list(self.reseau.adj[x])[0]]
            [NATURE] == 'liaison aire de recharge' and 
            self.reseau.nodes[x][NATURE] == "station_irve"))
 
    @property
    def gs_externe(self):
        return nx.subgraph_view(self.reseau, filter_node=(
            lambda x: self.reseau.edges[x, list(self.reseau.adj[x])[0]]
            [NATURE] == 'liaison exterieur' and 
            self.reseau.nodes[x][NATURE] == "station_irve"))

    def gp_trajet(self, source, target, graph=True):
        path = nx.shortest_path(self.reseau, source=source, target=target, weight='weight')
        if not graph:
            return path
        return nx.subgraph_view(self.reseau, filter_edge=(
            lambda x, y: x in path and y in path and 
            abs(path.index(y) - path.index(x)) == 1),
            filter_node=lambda x: x in path)