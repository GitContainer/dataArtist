# coding=utf-8
import numpy as np

# TODO: do i really need that module??


def RMS(x, axis=None, dtype=None):
    '''calculate the Root-Mean-Square of a given number or np.array'''
    return np.sqrt(np.mean(x * x, axis=axis, dtype=dtype))
