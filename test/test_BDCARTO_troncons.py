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


troncons = gpd.read_file("../../BDCARTO/PACA/TRANSPORT/TRONCON_DE_ROUTE.shx")
print(troncons.columns)

nature = list(pd.unique(troncons['NATURE']))
print(nature)
"""   
['Chemin', 
 'Route à 1 chaussée',
 'Route empierrée',
 'Sentier',
 'Route à 2 chaussées',
 'Bretelle',
 'Type autoroutier',
 'Rond-point',
 'Bac ou liaison maritime',
 'Escalier']
"""

bretelles = ['Bretelle']
chaussees = ['Route à 2 chaussées', 'Type autoroutier']

troncons_nat = troncons.set_index('NATURE')

troncons_bret = troncons_nat.loc[bretelles, ['ID', 'ID_BDTOPO', 'SENS', 'geometry']]
troncons_bret_gpd = gpd.GeoDataFrame(troncons_bret, crs=2154).reset_index()
troncons_bret_gpd.to_file("../data/BDCARTO/troncons_bret.geojson", driver= "GeoJSON")

troncons_chau = troncons_nat.loc[chaussees, ['ID', 'ID_BDTOPO', 'SENS', 'geometry']]
troncons_chau_gpd = gpd.GeoDataFrame(troncons_chau, crs=2154).reset_index()
troncons_chau_gpd.to_file("../data/BDCARTO/troncons_chau.geojson", driver= "GeoJSON")


