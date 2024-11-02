
# -*- coding: utf-8 -*-
"""
Ce module contient la classe Afir .
"""
import json
import pandas as pd
import geopandas as gpd
import networkx as nx
import geo_nx as gnx
from shapely import Point
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
    def __init__(self, rtet, stations, central=True, pcum=400, pmax=150, dist=60 ):
        """The initialization of an Afir scenario includes :
        - GeoGraph is identical to a Graph initialization.
        (with the addition of the creation of a 'crs' attribute - default : None).

        The 'geometry' attribute is mandatory for the GeoGraph methods (eg. to_geopandas_edgelist)

        Examples
        --------
        Create an empty graph structure (a "null graph") with no nodes and no edges.

        >>> G = nx.Graph()
        """
        self.stations = stations[(stations["p_max"] > pmax) & (stations["p_cum"] > pcum)].reset_index()
        self.central = central
        self.pcum = pcum
        self.pmax = pmax
        self.dist = dist
        if central:
            sub = nx.subgraph_view(rtet, filter_edge=lambda x,y: rtet[x][y][CORE]==True)
            rtet_core = nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))
            self.rtet =  gnx.GeoGraph(rtet_core)
        else:
            self.rtet = rtet
        self.reseau = association_stations(self.rtet, self.stations) 
    
    @property 
    def gr_rtet(self):
        filter_edge = lambda x,y: self.rtet[x][y][NATURE][:7] == 'troncon'
        sub = nx.subgraph_view(self.rtet, filter_edge=filter_edge)
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))    

    @property 
    def gr_autoroute(self):
        filter_edge = lambda x,y: self.rtet[x][y][NATURE] == 'troncon autoroute'
        sub = nx.subgraph_view(self.rtet, filter_edge=filter_edge)
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))    
    
    @property 
    def gr_hors_autoroute(self):
        filter_edge = lambda x,y: self.rtet[x][y][NATURE] == 'troncon hors autoroute'
        sub = nx.subgraph_view(self.rtet, filter_edge=filter_edge)
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))        
    
    @property 
    def gr_rtet_central(self):
        filter_edge=lambda x,y: self.rtet[x][y]["core"]
        sub = nx.subgraph_view(self.rtet, filter_edge=filter_edge)
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))  
    
    @property 
    def gr_rtet_global(self):
        filter_edge=lambda x,y: not self.rtet[x][y]["core"]
        sub = nx.subgraph_view(self.rtet, filter_edge=filter_edge)
        return nx.induced_subgraph(sub, nx.utils.flatten(sub.edges()))  
    
    @property 
    def gr_aire_service(self):
        filter_node=lambda x: self.reseau.nodes[x]["nature"] == 'aire de service'
        return nx.subgraph_view(self.reseau, filter_node=filter_node)
    
    @property 
    def gr_echangeur(self):
        filter_node=lambda x: self.reseau.nodes[x]["nature"] == 'echangeur'
        return nx.subgraph_view(self.reseau, filter_node=filter_node)

    @property 
    def gr_rond_point(self):
        filter_node=lambda x: self.reseau.nodes[x]["nature"] == 'rond-point'
        return nx.subgraph_view(self.reseau, filter_node=filter_node)
    
    @property 
    def gs_station(self):
        filter_node=lambda x: self.reseau[x][list(self.reseau.adj[x])[0]]["nature"] == 'liaison aire de service'
        return nx.subgraph_view(self.reseau, filter_node=filter_node)
    
    @property 
    def gs_pre_station(self):
        filter_node=lambda x: self.reseau[x][list(self.reseau.adj[x])[0]]["nature"] == 'liaison aire de recharge'
        return nx.subgraph_view(self.reseau, filter_node=filter_node)

    @property 
    def gs_externe(self):
        filter_node=lambda x: self.reseau[x][list(self.reseau.adj[x])[0]]["nature"] == 'liaison exterieur'
        return nx.subgraph_view(self.reseau, filter_node=filter_node)
    

    
    
    