#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 23 11:40:50 2017

@author: gxdata

miscellaneous functions that may be needed from several unh_modules
"""

'''
It would seem that this is not necessary but numpy is throwing error
when trying to calculate mean of empty slice

use single line, like:
    dT_true_heat.mean() if len(dT_true_heat) > 0 else 0.

instead of this function

def calc_mean(x):
    if len(x) >0:
        return x.mean()
    else:
        return 0.
'''


def C_to_F(C):
    F = 9. / 5. * (C) + 32.
    return F


def F_to_C(F):
    C = 5./9. * (F - 32.)
    return C


if __name__ == '__main__':
    install = 'dummy'
