#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This module creates a scatterplot of energy use intensity as a function of average daily
outdoor air temperature.

"""

import matplotlib.pyplot as plt
from db_tools import otherm_db_reader
from utilities import misc_functions as misc_functions
from datetime import date
import time

C_to_F = misc_functions.C_to_F


def kwh_per_mmbtu(site_names, start_date, end_date, db):
    """

    Parameters
    ----------
    site_names : list
        List of site names, as strings

    start_date : str
        Beginning date of request, such as *'2015-01-01'*

    end_date : str
        End date of request

    symbol_colors : dict
        Dictionary of colors for graph symbols with site name as keys

    db : str
        The name of the database to pull operating data from

    """

    for name in site_names:
        site = otherm_db_reader.get_site_info(name, db)
        thermal_load = otherm_db_reader.get_thermal_load(site_name=site.id, db=db)
        #equipment, hp_data = otherm_db_reader.get_equipment_data(site.id, start_date, end_date, site.timezone, db)
        equipment = otherm_db_reader.get_equipment(site.id, db)
        print('working on ...', site.name)
        try:
            db_data = otherm_db_reader.get_equipment_data(site.id, start_date, end_date, site.timezone, db)
            if len(db_data) > 100:
                if 'heatpump_aux' in db_data.columns:
                    db_data['totalunitpower'] = db_data['heatpump_power'] + db_data['heatpump_aux']
                else:
                    db_data['totalunitpower'] = db_data['heatpump_power']
                hp_data = db_data[db_data['outdoor_temperature'] > -100]
                heating = hp_data[hp_data['heat_flow_rate']>1000]

                kWh_heating = (heating['totalunitpower'] * heating['time_elapsed']).sum()/1e3
                mmbtu = (heating['heat_flow_rate']*heating['time_elapsed']).sum()/1e6
                print(site.name, kWh_heating, mmbtu, )
        except Exception as e:
            print('Error reading operating data pump data: \n     ', e)

        time.sleep(30)

    '''
    plt.ylabel('kWh/SF per day')
    plt.title('Heat Pump kWh/Square Feet vs. Outdoor Air Temperature')
    plt.xlabel('Average Daily Outdoor Air Temperature [$^\circ F$]')
    plt.legend()
    fig_name = '../temp_files/kwh_per_sf_{}.png'.format(str(date.today().strftime("%m-%d-%y")))
    print(fig_name)
    plt.savefig(fig_name)
    return fig_name
    '''
    return

if __name__ == '__main__':
    site_names = ['110722', '110720', '110459', '111011'] #, '03824', '03561', '06018']
    site_names = ['110459', '110722', '110855', '111011', '111382', '111596', '111469',
                  '111468', '111520', '111383', '111548', '111071', '111956', '111693']
    site_names = ['110918', '110912', '110459', '110722', '110855', '111011', '111071', '111520',
                  '111548', '111383', '111382', '111468', '111469', '111956', '111693', '111995',
                  '110720', '111731']
    start_date = '2016-01-01'
    end_date = '2022-04-10'
    #symbol_colors = {'110720': 'b'} #, '03824': 'r', '03561': 'g', '06018': 'c'}
    db = 'otherm_cgb'
    #db = 'localhost'

    kwh_per_mmbtu(site_names, start_date, end_date, db)