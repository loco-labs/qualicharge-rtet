# -*- coding: utf-8 -*-
"""
Ce module contient la classe Afir .
"""
import copy
import networkx as nx
import geo_nx as gnx
from qualicharge_rtet.fonction_afir import association_stations
from qualicharge_rtet.fonction_afir_maillage import (
    troncons_non_mailles,
    troncons_peu_mailles,
)

GEOM = "geometry"
NODE_ID = "node_id"
NATURE = "nature"
WEIGHT = "weight"
CORE = "core"


class Afir:
    """La classe Afir est associée aux indicateurs AFIR du réseau RTE-T..

    *instance methods*

    - `insert_node`

    """

    def __init__(
        self, rtet=None, stations=None, central=True, pcum=400, pmax=150, dist=60, log=False
    ):
        """The initialization of an Afir scenario includes :
        - GeoGraph is identical to a Graph initialization.
        (with the addition of the creation of a 'crs' attribute - default : None).

        The 'geometry' attribute is mandatory for the GeoGraph methods (eg. to_geopandas_edgelist)

        Examples
        --------
        Create an empty graph structure (a "null graph") with no nodes and no edges.

        >>> G = nx.Graph()
        """
        self._rtet = None
        self._stations = None
        self._reseau = None
        self._central = central
        self._pcum = pcum
        self._pmax = pmax
        self._dist = dist

        self.set_rtet(rtet, log=log)
        self.set_stations(stations, log=log)

    def set_rtet(self, rtet, log=False):
        if not rtet:
            return
        rtet = copy.deepcopy(rtet)
        if not self._central:
            self._rtet = rtet
        else:
            sub = nx.subgraph_view(rtet, filter_edge=lambda x, y: rtet[x][y][CORE])
            rtet_core = nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))
            self._rtet = gnx.GeoGraph(rtet_core)
        self._reseau = association_stations(self._rtet, self._stations, log=log)
        return

    def set_stations(self, stations, log=False):
        if stations is not None:
            self._stations = stations[
                (stations["p_max"] > self._pmax) & (stations["p_cum"] > self._pcum)
            ].reset_index()
            self._reseau = association_stations(self._rtet, self._stations,log=log)

    def set_reseau(self, reseau):
        self._reseau = reseau

    @property
    def rtet(self):
        return self._rtet

    @property
    def size_rtet(self):
        return self._rtet.size(weight=WEIGHT)

    @property
    def stations(self):
        return self._stations

    @property
    def reseau(self):
        return self._reseau

    @property
    def central(self):
        return self._central

    @property
    def pcum(self):
        return self._pcum

    @property
    def pmax(self):
        return self._pmax

    @property
    def dist(self):
        return self._dist

    @property
    def gr_all(self):
        sub = nx.subgraph_view(
            self._rtet,
            filter_edge=(lambda x, y: self._rtet[x][y][NATURE][:7] == "troncon"),
        )
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_autoroute(self):
        sub = nx.subgraph_view(
            self._rtet,
            filter_edge=(lambda x, y: self._rtet[x][y][NATURE] == "troncon autoroute"),
        )
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_hors_autoroute(self):
        sub = nx.subgraph_view(
            self._rtet,
            filter_edge=(
                lambda x, y: self._rtet[x][y][NATURE] == "troncon hors autoroute"
            ),
        )
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_rtet_central(self):
        sub = nx.subgraph_view(
            self._rtet, filter_edge=(lambda x, y: self._rtet[x][y]["core"])
        )
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_rtet_global(self):
        return self.gr_all
        # sub = nx.subgraph_view(self._rtet, filter_edge=(
        #    lambda x, y: not self._rtet[x][y]["core"]))
        # return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))

    @property
    def gr_aire_service(self):
        return nx.subgraph_view(
            self._reseau,
            filter_node=(lambda x: self._reseau.nodes[x][NATURE] == "aire de service"),
        )

    @property
    def gr_echangeur(self):
        return nx.subgraph_view(
            self._reseau,
            filter_node=(lambda x: self._reseau.nodes[x][NATURE] == "echangeur"),
        )

    @property
    def gr_rond_point(self):
        return nx.subgraph_view(
            self._reseau,
            filter_node=(lambda x: self._reseau.nodes[x][NATURE] == "rond-point"),
        )

    @property
    def gs_all(self):
        return nx.subgraph_view(
            self._reseau,
            filter_node=(lambda x: self._reseau.nodes[x][NATURE] == "station_irve"),
        )

    @property
    def gs_station(self):
        return nx.subgraph_view(
            self.reseau,
            filter_node=(
                lambda x: self._reseau.nodes[x][NATURE] == "station_irve"
                and self._reseau.edges[x, list(self._reseau.adj[x])[0]][NATURE]
                == "liaison aire de service"
            ),
        )

    @property
    def gs_pre_station(self):
        return nx.subgraph_view(
            self._reseau,
            filter_node=(
                lambda x: self._reseau.edges[x, list(self._reseau.adj[x])[0]][NATURE]
                == "liaison aire de recharge"
                and self._reseau.nodes[x][NATURE] == "station_irve"
            ),
        )

    @property
    def gs_externe(self):
        return nx.subgraph_view(
            self._reseau,
            filter_node=(
                lambda x: self._reseau.edges[x, list(self._reseau.adj[x])[0]][NATURE]
                == "liaison exterieur"
                and self._reseau.nodes[x][NATURE] == "station_irve"
            ),
        )
    def indicateur_afir(self, etendu=False, dispo="dispo"):
        l_rtet = self.size_rtet
        l_non_afir = self.gr_non_maille(etendu=etendu, dispo=dispo).size(weight=WEIGHT)
        return {'ratio afir': (1 - l_non_afir / l_rtet),
                'distance rtet': l_rtet,
                'distance restante': l_non_afir}

    def gr_non_maille(self, etendu=False, dispo="dispo"):
        '''
        - un tronçon est non maillé s'il existe un point de ce tronçon situé 
        à une distance de la plus proche station supérieure à un seuil,
        - un tronçon est peu maillé s'il est sur la même branche (ensemble de 
        tronçons entre deux stations disponibles ou bifurcations) qu'un tronçon maillé.

        Parameters
        ----------
        etendu : booleen, optional
            tronçpon peu maillé si True, sinon tronçon non maillés. 
            The default is False.
        dispo : string, optional
            Attribut booléen. S'il est faux, la station est indisponible.
            The default is "dispo".

        Returns
        -------
        GeoGraph
            Graphe des troncons non ou peu maillés .
        '''
        dist_actives = "dist_actives"
        non_maille = troncons_non_mailles(
            self.reseau,
            self.gs_all,
            self.gr_all,
            dispo,
            self.dist,
            n_attribute=dist_actives,
            stat_attribute="station_irve",
        )[1]
        self.gr_all.remove_attribute(dist_actives, edges=False)
        if etendu:
            return troncons_peu_mailles(non_maille, self.reseau, dispo)
        return non_maille

    def gp_trajet(self, source, target, graph=True):
        path = nx.shortest_path(
            self._reseau, source=source, target=target, weight="weight"
        )
        if not graph:
            return path
        return nx.subgraph_view(
            self._reseau,
            filter_edge=(
                lambda x, y: x in path
                and y in path
                and abs(path.index(y) - path.index(x)) == 1
            ),
            filter_node=lambda x: x in path,
        )
