# -*- coding: utf-8 -*-
"""
Test processus par étape
"""


def process(param:int, by_step=False):

    if by_step :
        yield 3
        
    #étape 1
    val1 = param + 1
    if by_step :
        yield {'param': param, 'val1': val1}

    #étape 2
    val2 = "étape 2"
    if by_step:
        yield {'param': param, 'val1': val1, 'val2': val2}    

    #étape 3
    res = "fini"
    yield  {'param': param, 'res': res}
