# -*- coding: utf-8 -*-
"""
Test qualicharge_rtet
"""
import unittest

from shapely import Point
import networkx as nx 
from qualicharge_rtet import to_macro_node, to_undirected_edges
import geopandas as gpd
import pandas as pd
import geo_nx as gnx 
import networkx as nx 

from qualicharge_rtet import troncons_non_mailles, troncons_peu_mailles, gr_maillage

paris = Point(2.3514, 48.8575)
lyon = Point(4.8357, 45.7640)
marseille = Point(5.3691, 43.3026)
bordeaux = Point(-0.56667, 44.833328)

SLICE = 10000

class TestMacroNode(unittest.TestCase):
    """tests node convertions"""

    def test_macro_node(self):
        """tests macro-node"""
        gr = nx.Graph()
        gr.add_edges_from([(1, 2), (3, 1), (3,4), (2,3)])
        dgr = gr.to_directed()
        nodes = list(dgr.nodes)
        for node in nodes:
            to_macro_node(dgr, node)
        self.assertEqual(to_undirected_edges(dgr.edges), list(gr.edges))
        for node in nodes:
            to_macro_node(dgr, node, uturn=True)
        self.assertEqual(to_undirected_edges(dgr.edges), list(gr.edges))

class TestGraphDigraph(unittest.TestCase):
    """tests convertion Graph DiGraph"""

    def test_rtet(self):
        '''test rte-t complet'''
        rtet_path = '../rtet/'
        vl_global_2027 = (False, 300, 150, 60)
        version = 'V1'
        scenario = vl_global_2027        
        central, pcum, pmax, dist = scenario
        add_name = '_core' if central else ''
        add_pcum = '_' + str(pcum)    
        add_pmax = '_' + str(pmax)
        
        gr_tot = gnx.from_geopandas_edgelist(gpd.read_file(rtet_path + version + add_name + add_pcum + add_pmax + '_afir_edge.geojson'), 
                                     node_gdf=gpd.read_file(rtet_path + version + add_name + add_pcum + add_pmax + '_afir_node.geojson'),
                                     node_attr=True, edge_attr=True)
        dgr_tot = gr_tot.to_directed()
        bollene = [node for node in gr_tot.nodes if gr_tot.nodes[node].get('id_station') == 'FR*IZF*EFAST*95*1*3']
        bollene = bollene[0] if bollene else None
        st_martin_de_crau = [node for node in gr_tot.nodes if gr_tot.nodes[node].get('id_station') == 'FR*PVD*EVG*SMC13*D01*1']
        st_martin_de_crau = st_martin_de_crau[0] if st_martin_de_crau else None
        dist_gr = nx.shortest_path_length(gr_tot, source=bollene, target=st_martin_de_crau, weight='weight')
        dist_dgr = nx.shortest_path_length(dgr_tot, source=bollene, target=st_martin_de_crau, weight='weight')
        self.assertEqual(dist_gr, dist_dgr)
        
        stat_edges = [edge for edge in gr_tot.edges if gr_tot.edges[edge]['nature'][:7] == 'liaison']
        gs = nx.edge_subgraph(gr_tot, stat_edges)
        rtet_edges = [edge for edge in gr_tot.edges if gr_tot.edges[edge]['nature'][:7] != 'liaison']
        gr = nx.edge_subgraph(gr_tot, rtet_edges)
        dstat_edges = [edge for edge in dgr_tot.edges if dgr_tot.edges[edge]['nature'][:7] == 'liaison']
        dgs = nx.edge_subgraph(dgr_tot, dstat_edges)
        drtet_edges = [edge for edge in dgr_tot.edges if dgr_tot.edges[edge]['nature'][:7] != 'liaison']
        dgr = nx.edge_subgraph(dgr_tot, drtet_edges)   
        seuil = dist * 1000
        dispo = 'dispo'
        gr_stat_indispo, gr_non_maille = troncons_non_mailles(gr_tot, gs, gr, dispo, seuil)
        gr_peu_maille = troncons_peu_mailles(gr_non_maille, gr_tot, dispo)
        dgr_stat_indispo, dgr_non_maille = troncons_non_mailles(dgr_tot, dgs, dgr, dispo, seuil)
        dgr_peu_maille = troncons_peu_mailles(dgr_non_maille, dgr_tot, dispo)
        gr_longueur_rtet = sum([gr_tot.edges[edge]['weight'] for edge in rtet_edges])
        gr_longueur_non_afir = sum([gr_non_maille.edges[edge]['weight'] for edge in gr_non_maille.edges])
        gr_longueur_peu_afir = sum([gr_peu_maille.edges[edge]['weight'] for edge in gr_peu_maille.edges])        
        dgr_longueur_rtet = sum([dgr_tot.edges[edge]['weight'] for edge in drtet_edges])
        dgr_longueur_non_afir = sum([dgr_non_maille.edges[edge]['weight'] for edge in dgr_non_maille.edges])
        dgr_longueur_peu_afir = sum([dgr_peu_maille.edges[edge]['weight'] for edge in dgr_peu_maille.edges])
        self.assertEqual(gr_longueur_rtet, dgr_longueur_rtet / 2)
        self.assertEqual(gr_longueur_non_afir, dgr_longueur_non_afir / 2)
        #self.assertEqual(gr_longueur_peu_afir, dgr_longueur_peu_afir / 2) ## probleme !!
        



if __name__ == "__main__":
    unittest.main(verbosity=2)
