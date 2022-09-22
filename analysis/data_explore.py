# -*- coding: utf-8 -*-
"""

This module creates time series plots for individual heat pumps.

"""

import pandas as pd
import numpy as np
from db_tools import otherm_db_reader

import matplotlib.pyplot as plt


if __name__ == "__main__":
    site_name = '111956'
    start = '2021-10-01'
    end = '2022-04-01'
    db = 'otherm_cgb'

    site = otherm_db_reader.get_site_info(site_name, db)

    equipment = otherm_db_reader.get_equipment(site.id, db)
    hp_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone, db)

    hp_data['kw_hp'] = hp_data['heatpump_power'][~np.isnan(hp_data['heatpump_power'])] / 1000.
    hp_data['kw_aux'] = hp_data['heatpump_aux'][~np.isnan(hp_data['heatpump_aux'])] / 1000.

    hp_data['outdoor_temperature_F'] = hp_data['outdoor_temperature']*9/5 + 32

    hp_data['dtime'] = hp_data['time_elapsed'][~np.isnan(hp_data['time_elapsed'])]

    hp_data['kwh_hp'] = hp_data['kw_hp']*hp_data['dtime']
    hp_data['kwh_aux'] = hp_data['kw_aux']*hp_data['dtime']
    hp_data['kwh_total'] = hp_data['kwh_aux'] + hp_data['kwh_hp']

    # filter dataframe to exclude NaNs and heat pump is on, calculate heating only
    hp_data = hp_data[np.isfinite(hp_data['heat_flow_rate'])]
    hp_data = hp_data.query('heatpump_power > 500')
    hp_data['MBtuH'] = (3.412*(hp_data['kw_hp'] + hp_data['kw_aux']) +
                       (hp_data['heat_flow_rate'])/1000)

    hp_data_hourly = hp_data.resample('1800S').mean()

    hp_data_daily = hp_data.resample('1D').mean()


    #hp_data.plot(kind='line', y=['kw_hp','kw_aux','outdoor_temperature_F'],
    #                secondary_y='outdoor_temperature_F',
    #                xlabel='Time', ylabel='Power [kW]',
    #                title='Site NGEN ID  {}'.format(str(site.name)))

    #plt.ylim([0, 60])

    #hp_data_hourly.plot(kind='line', y=['MBtuH','outdoor_temperature_F'],
    #                secondary_y='outdoor_temperature_F',
    #                xlabel='Time', ylabel='MBtuH [Total heating]',
    #                title='Site NGEN ID  {}'.format(str(site.name)))

    #plt.ylim([0, 60])

    plt.scatter(hp_data_daily['outdoor_temperature_F'], hp_data_daily['MBtuH'])

    fig_name = '../temp_files/explorer_plot_{}.png'.format(str(site.name))
    print(fig_name)
    plt.show()
    plt.savefig(fig_name)


