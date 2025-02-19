# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 15:42:55 2025

@author: a lab in the Air
"""
from itertools import product

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
    e_nodes, s_nodes, i_edges = macro_node(dgr, node, uturn)
    pred_nodes = list(dgr.predecessors(node))
    succ_nodes = list(dgr.successors(node))
    for e_node, pnd in zip(e_nodes, pred_nodes):
        dgr.remove_edge(pnd, node)
        dgr.add_edge(pnd, e_node)
    for s_node, snd in zip(s_nodes, succ_nodes):
        dgr.remove_edge(node, snd)
        dgr.add_edge(s_node, snd)    
    dgr.add_edges_from(i_edges)
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
    