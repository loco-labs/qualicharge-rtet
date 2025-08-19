# -*- coding: utf-8 -*-
"""
**qualicharge_rtet Package**

This package contains classes and functions for AFIR networks.

For more information, see the
[github repository](https://github.com/loco-labs/geo_nx).
"""

from qualicharge_rtet.afir import Afir

from qualicharge_rtet.digraph_afir import to_macro_node, to_undirected_edges

from qualicharge_rtet.fonction_afir import (
    insertion_noeuds,
    proximite,
    insertion_projection,
    association_stations,
)
from qualicharge_rtet.fonction_afir import (
    get_rtet_attr_station,
    get_parc_id_station,
    propagation_attributs_core,
    propagation_attributs_edges,
)

from qualicharge_rtet.fonction_afir_maillage import (
    troncons_non_mailles,
    troncons_peu_mailles,
)
from qualicharge_rtet.fonction_afir_maillage import (
    aretes_adjacentes,
    green_list,
    gr_maillage,
)

from qualicharge_rtet.interfaces_afir_rtet import (
    creation_reseau_rtet,
    creation_pandas_aires,
)
from qualicharge_rtet.interfaces_afir_qualicharge import (
    creation_pandas_stations,
    export_stations_parcs,
    filter_stations_parcs,
    lecture_statiques,
)
