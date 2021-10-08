#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
.. note::
        runs correctly with limited oTherm data,  still needs full testing

"""
import datetime
from db_tools import otherm_db_reader
import numpy as np
import pandas as pd
import admin_tools.db_reader as db_reader
from utilities import misc_functions as misc_functions

C_to_F = misc_functions.C_to_F

def generate_csv(data, site_name):
    """

    Parameters
    ----------
    data : pandas.DataFrame
        Heat pump operating data with datetime index

    site_name : str
        Name of the site to analyze.  At present, assumes a single heat pump at each site.

    Returns
    -------
        Produces a csv file of load factors for site.

    """
    data_monthly = pd.DataFrame()
    data_hourly_kW = pd.DataFrame()

    data_monthly['Compressor (kWh)'] = (data['heatpump_power']*data['time_elapsed']).resample('M').sum()/1000.
    data_monthly['Auxiliary (kWh)'] = (data['heatpump_aux']*data['time_elapsed']).resample('M').sum()/1000.

    #Total unit power excludes pump and fan energy here, those can be added as needed
    hp_data['totalunitpower'] = hp_data['heatpump_power'] + hp_data['heatpump_aux']
    data_monthly['Total Load (kWh)'] = (data['totalunitpower']*data['time_elapsed']).resample('M').sum()/1000.

    data_hourly_kW['totalunitpower'] = data['totalunitpower'].resample('3600S').mean()/1000.
    data_hourly_kW['heatpump_power'] = data['heatpump_power'].resample('3600S').mean()/1000.
    data_hourly_kW['heatpump_aux'] = data['heatpump_aux'].resample('3600S').mean()/1000.

    data_monthly['Total Peak (hourly)'] = data_hourly_kW['totalunitpower'].resample('M').max()
    data_monthly['Compressor Peak (hourly)'] = data_hourly_kW['heatpump_power'].resample('M').max()
    data_monthly['Auxiliary Peak (hourly)'] = data_hourly_kW['heatpump_aux'].resample('M').max()

    data_monthly['Load Factor (Total)'] = data_monthly['Total Load (kWh)'] / (data_monthly['Total Peak (hourly)'] * 730)

    intervals = np.asarray(data['heatpump_power'].resample('M').count(), dtype=float)
    intervals = intervals.reshape(len(intervals))
    days_in_month = np.asarray(data_monthly.index.daysinmonth, dtype=float)
    data_monthly['intervals'] = intervals
    data_monthly['completeness'] = intervals/(1440*days_in_month)
    with open('load_factors.csv', 'a') as f:
        header = ('\n ,' + site_name + ',' + '\n')
        f.write(header)
        data_monthly.to_csv(f, float_format='%.2f')
    return


if __name__ == '__main__':
    names = ['GES649']
    start_date = '2015-01-01'
    end_date = '2016-01-01'

    for site_name in names:
        print('Working on load factor analysis... ' + site_name)
        site = otherm_db_reader.get_site_info(site_name)
        equipment, hp_data = otherm_db_reader.get_equipment_data(site.id, start_date, end_date, site.timezone)

        if len(hp_data) > 1000:
            data_hourly = hp_data.resample('60Min').mean()
            generate_csv(hp_data, site.name)




