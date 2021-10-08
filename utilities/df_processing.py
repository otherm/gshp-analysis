#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataframe processing functions

"""
def determine_mode(row):
    """
    Args:
        row:  a row in a pandas DataFrame

    Returns:
        Two new columns in the DataFrame, one that identifies when heat pump is heating
        the other when heat pump is cooling
    """
    if row['heat_flow_1'] > 0:
        return 'Heating'
    else:
        return 'Cooling'

def lag_temps(data):
    # lag temp measurements by 1 datapoint for on pipe measurements
    data['ewt_1'] = data['ewt_1'].shift(-1)
    data['lwt_1'] = data['lwt_1'].shift(-1)

    data = data[:-1]   # what is this doing?

    data['DeltaT'] = data.lwt_1 - data.ewt_1

    return data

if __name__ == '__main__':
    install = 'dummy'