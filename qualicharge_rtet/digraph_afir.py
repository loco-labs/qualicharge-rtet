# -*- coding: utf-8 -*-
"""
Ce module contient les fonctions de convertion entre un graphe directionnel et non directionnel
"""
from itertools import product
import networkx as nx

SLICE = 10000

def macro_node(nb_neighbors: int, node, uturn: bool=False) -> tuple:
    '''
    Transforme un noeud non connecté en macro-noeud.

    Parameters
    ----------
    nb_neighbors : int
        Number of neighbors of the node.
    node : int
        id of the node to transform.
    uturn : boolean, optional
        If True the macro-node is equivalent to the node. The default is False.

    Returns
    -------
    e_nodes : list
        Entry internals nodes.
    s_nodes : list
        exit internals nodes.
    i_edges : list
        internals edges.
    '''
    e_nodes = list(range(node * SLICE + 2, node * SLICE + 2 * (1 + nb_neighbors), 2))
    s_nodes = list(range(node * SLICE + 1, node * SLICE + 1 + 2 * nb_neighbors, 2))
    i_edges = list(product(e_nodes, s_nodes))
    if not uturn:
        i_edges = [edge for edge in i_edges if edge[0] != edge[1] + 1]
    return (e_nodes, s_nodes, i_edges)

def to_macro_node(dgr, node: int, uturn: bool=False) -> tuple:
    '''
    Transforme un noeud connecté en macro-noeud.


    Parameters
    ----------
    dgr : GeoDiGraph
        grph how includes the node.
    node : int
        id of the node to transform.
    uturn : boolean, optional
        If True the macro-node is equivalent to the node. The default is False.

    Returns
    -------
    e_nodes : list
        Entry internals nodes.
    s_nodes : list
        exit internals nodes.
    i_edges : list
        internals edges.
    '''
    e_nodes, s_nodes, i_edges = macro_node(len(list(dgr.neighbors(node))), node, uturn)
    pred_nodes = list(dgr.predecessors(node))
    succ_nodes = list(dgr.successors(node))
    for e_node, pnd in zip(e_nodes, pred_nodes):
        attr = dgr.edges[pnd, node]
        dgr.remove_edge(pnd, node)
        dgr.add_edges_from([(pnd, e_node, attr)])
        #dgr.add_edge(pnd, e_node)
        #print(list(dgr.predecessors(e_node)))
    for s_node, snd in zip(s_nodes, succ_nodes):
        attr = dgr.edges[node, snd]
        dgr.remove_edge(node, snd)
        dgr.add_edges_from([(s_node, snd, attr)])
        #dgr.add_edge(s_node, snd)    
        #print(list(dgr.successors(node)))
    dgr.add_edges_from(i_edges)
    dgr.remove_node(node)
    dg_node = dgr.subgraph(e_nodes + s_nodes)
    nx.set_node_attributes(dg_node, 'connecteur', 'nature')
    nx.set_node_attributes(dg_node, None, 'geometry')
    nx.set_edge_attributes(dg_node, 'connexion', 'nature')
    nx.set_edge_attributes(dg_node, None, 'geometry')
    nx.set_edge_attributes(dg_node, 0, 'weight')
    nx.set_edge_attributes(dg_node, None, 'NATIONALRO')
    return (e_nodes, s_nodes, i_edges)

def to_undirected_edges(edges: list) -> list:
    '''
    Transforme des tronçons orientés en tronçons non orientés.


    Parameters
    ----------
    edges : list
        directed edges.

    Returns
    -------
    list
        undirected edges.

    '''
    ext_edges = [(edge[0] // SLICE, edge[1] // SLICE) for edge in edges if edge[0] // SLICE != edge[1] // SLICE]
    return sorted(list(set([(min(edge), max(edge)) for edge in ext_edges])))
    