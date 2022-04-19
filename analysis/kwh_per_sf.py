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

C_to_F = misc_functions.C_to_F


def kwh_vs_oat(site_names, start_date, end_date, db):
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
                area = thermal_load.conditioned_area

                kWh_perSF = (hp_data['totalunitpower'] * hp_data['time_elapsed']).resample('D').sum() / (1000 * area)
                OAT_F = (hp_data['outdoor_temperature'] * (9 / 5) + 32).resample('D').mean()
                plt.scatter(OAT_F, kWh_perSF, marker='o', s=2, alpha=0.75, label=site.name) #c=symbol_colors[name]
        except Exception as e:
            print('Error reading operating data pump data: \n     ', e)

        thermal_load = otherm_db_reader.get_thermal_load(site_name=site.id, db=db)



    plt.ylabel('kWh/SF per day')
    plt.title('Heat Pump kWh/Square Feet vs. Outdoor Air Temperature')
    plt.xlabel('Average Daily Outdoor Air Temperature [$^\circ F$]')
    plt.legend()
    fig_name = '../temp_files/kwh_per_sf_{}.png'.format(str(date.today().strftime("%m-%d-%y")))
    print(fig_name)
    plt.savefig(fig_name)
    return fig_name


if __name__ == '__main__':
    site_names = ['110722', '110720', '110459', '111011'] #, '03824', '03561', '06018']
    site_names = ['110912', '110459', '110720', '110722', '110855', '110912', '111011', '111382',
                  '111469', '111468', '111520', '111383', '111548', '111071', '111956']
    start_date = '2016-01-01'
    end_date = '2022-04-10'
    #symbol_colors = {'110720': 'b'} #, '03824': 'r', '03561': 'g', '06018': 'c'}
    db = 'otherm_cgb'
    #db = 'localhost'

    kwh_vs_oat(site_names, start_date, end_date, db)