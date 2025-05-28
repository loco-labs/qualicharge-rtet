import pandas as pd
import geo_nx as gnx 

from qualicharge_rtet import association_stations
from qualicharge_rtet import creation_pandas_stations, export_stations_parcs
from qualicharge_rtet import propagation_attributs_core

def filter_stations_parcs(rtet_edges, rtet_nodes, stations_production, stations_staging, pmax=0, pcum=0, simple=False):

    # réseau rtet
    gr = gnx.from_geopandas_edgelist(rtet_edges, node_gdf= rtet_nodes, node_attr=True, edge_attr=True)
    
    # mise au format afir des stations
    first_id = max(gr.nodes) + 1
    stations_afir_production = creation_pandas_stations(stations_production, nature="station_irve", first_id=first_id, source="qualicharge")
    first_id = max(gr.nodes) + 1 + len(stations_afir_production)
    stations_afir_staging = creation_pandas_stations(stations_staging, nature="station_irve", first_id=first_id, source="qualicharge")
    stations = pd.concat([stations_afir_staging, stations_afir_production], ignore_index=True)
    stations_afir = stations[(stations["p_max"] > pmax) & (stations["p_cum"] > pcum)].reset_index()

    # réseau global
    gr_afir = association_stations(gr, stations_afir, log=True) 
    propagation_attributs_core(gr_afir, "aire de recharge")
    
    # génération des stations liées au réseau RTET
    return export_stations_parcs(gr_afir, simple=simple)
