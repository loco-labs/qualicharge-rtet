# -*- coding: utf-8 -*-
"""
tests
"""

from shapely import LineString, Point
import geopandas as gpd
import geo_nx as gnx 
import networkx as nx 
import pandas as pd
import geo_nx.utils as utils
from networkx.utils import graphs_equal


noeuds = gpd.read_file("./route500/NOEUD_ROUTIER.shx")

nature = list(pd.unique(noeuds['NATURE']))

"""   ['Carrefour simple', 'Barrière', "Changement d'attribut",
       'Petit rond-point', 'Coupure arbitraire', 'Echangeur complet',
       'Noeud de communication restreinte', 'Echangeur partiel',
       'Carrefour avec toboggan ou passage inférieur',
       'Carrefour aménagé à niveau', 'Grand rond-point',
       'Barrière de douane', 'Embarcadère',
       "Noeud représentatif d'une commune"]"""

nature_ok = ['Carrefour simple', "Changement d'attribut",
       'Petit rond-point', 'Coupure arbitraire', 'Echangeur complet',
       'Noeud de communication restreinte', 'Echangeur partiel',
       'Carrefour avec toboggan ou passage inférieur',
       'Carrefour aménagé à niveau', 'Grand rond-point']

echangeur = ['Echangeur complet', 'Echangeur partiel', 'Noeud de communication restreinte']
rond_point = ['Petit rond-point', 'Grand rond-point']
divers = ["Changement d'attribut", 'Coupure arbitraire']
carrefour = ['Carrefour simple']

noeuds_nat = noeuds.set_index('NATURE')
# noeuds_nat.loc[nature_ok]  # -> 907394

noeuds_ech = noeuds_nat.loc[echangeur, ['INSEE_COMM', 'geometry']]  # -> 4328
noeuds_ech_gpd = gpd.GeoDataFrame(noeuds_ech, crs=2154)
noeuds_ech_gpd.to_file("noeuds_ech.geojson", driver= "GeoJSON")

noeuds_rp = noeuds_nat.loc[rond_point, ['INSEE_COMM', 'geometry']]  # -> 20506
noeuds_rp_gpd = gpd.GeoDataFrame(noeuds_rp, crs=2154)
noeuds_rp_gpd.to_file("noeuds_rp.geojson", driver= "GeoJSON")

noeuds_div = noeuds_nat.loc[divers, ['INSEE_COMM', 'geometry']]  # -> 13714
noeuds_div_gpd = gpd.GeoDataFrame(noeuds_div, crs=2154)
noeuds_div_gpd.to_file("noeuds_div.geojson", driver= "GeoJSON")

noeuds_car = noeuds_nat.loc[carrefour, ['INSEE_COMM', 'geometry']]  # -> 867959
noeuds_car_gpd = gpd.GeoDataFrame(noeuds_car, crs=2154)
noeuds_car_gpd.to_file("noeuds_car.geojson", driver= "GeoJSON")