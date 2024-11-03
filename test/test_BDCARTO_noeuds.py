# -*- coding: utf-8 -*-
"""
tests BDCARTO
"""

from shapely import LineString, Point
import geopandas as gpd
import geo_nx as gnx 
import networkx as nx 
import pandas as pd
import geo_nx.utils as utils
from networkx.utils import graphs_equal


noeuds = gpd.read_file("../../BDCARTO/PACA/TRANSPORT/EQUIPEMENT_DE_TRANSPORT.shx")
print(noeuds)

nature = list(pd.unique(noeuds['NATURE']))
nat_det =list(pd.unique(noeuds['NAT_DETAIL']))
"""   
['Carrefour',
 'Aire de repos ou de service',
 'Péage',
 'Arrêt voyageurs',
 'Port',
 'Aérogare',
 'Gare voyageurs uniquement',
 'Gare voyageurs et fret',
 'Gare fret uniquement',
 'Gare maritime']
['Echangeur partiel',
 'Echangeur',
 'Aire de service',
 'Echangeur complet',
 None,
 'Arrêt touristique saisonnier',
 'Port de plaisance',
 'Aire de repos',
 'Gare TGV']
"""

echangeurs = ['Echangeur partiel', 'Echangeur', 'Echangeur complet']
# aires = ['Aire de service', 'Aire de repos']
aires = ['Aire de service']

noeuds_nat = noeuds.set_index('NAT_DETAIL')

noeuds_aires = noeuds_nat.loc[aires, ['ID', 'geometry']]  # -> 75
noeuds_aires_gpd = gpd.GeoDataFrame(noeuds_aires, crs=2154).reset_index()
noeuds_aires_gpd.to_file("../data/BDCARTO/noeuds_aires.geojson", driver= "GeoJSON")

noeuds_ech = noeuds_nat.loc[echangeurs, ['ID', 'geometry']]  # -> 75
noeuds_ech_gpd = gpd.GeoDataFrame(noeuds_ech, crs=2154).reset_index()
noeuds_ech_gpd.to_file("../data/BDCARTO/noeuds_ech.geojson", driver= "GeoJSON")

'''
noeuds_rp = noeuds_nat.loc[rond_point, ['INSEE_COMM', 'geometry']]  # -> 20506
noeuds_rp_gpd = gpd.GeoDataFrame(noeuds_rp, crs=2154)
noeuds_rp_gpd.to_file("noeuds_rp.geojson", driver= "GeoJSON")

noeuds_div = noeuds_nat.loc[divers, ['INSEE_COMM', 'geometry']]  # -> 13714
noeuds_div_gpd = gpd.GeoDataFrame(noeuds_div, crs=2154)
noeuds_div_gpd.to_file("noeuds_div.geojson", driver= "GeoJSON")

noeuds_car = noeuds_nat.loc[carrefour, ['INSEE_COMM', 'geometry']]  # -> 867959
noeuds_car_gpd = gpd.GeoDataFrame(noeuds_car, crs=2154)
noeuds_car_gpd.to_file("noeuds_car.geojson", driver= "GeoJSON")
'''