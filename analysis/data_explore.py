# -*- coding: utf-8 -*-
"""

This module creates time series plots for individual heat pumps.

"""

import pandas as pd
import numpy as np
from db_tools import otherm_db_reader

import matplotlib.pyplot as plt


if __name__ == "__main__":
    site_name = '111011'
    start = '2023-08-20'
    end = '2023-08-22'
    db = 'otherm_cgb'

    site_names = ['110459', '110720', '110722', '110855', '110912', '110918', '111011', '111071', '111382', '111383',
                  '111468', '111469', '111516', '111520', '111548', '111596', '111619', '111685', '111693', '111731',
                  '111734', '111759', '111760', '111858', '111956', '111995']

    site_names = ['111516', '111520', '111548', '111596', '111619', '111685', '111693', '111731',
                  '111734', '111759', '111760', '111858', '111956', '111995']
    site_names = ['110722']

    for site_name in site_names:
        site = otherm_db_reader.get_site_info(site_name, db)
        equipment = otherm_db_reader.get_equipment(site.id, db)
        hp_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone, db)

        try:
            print(site_name, hp_data.index[-1])
        except Exception as e:
            print('Error reading operating data pump data: \n     ', e)


    hp_data['kw_hp'] = hp_data['heatpump_power'][~np.isnan(hp_data['heatpump_power'])] / 1000.
    hp_data['kw_aux'] = hp_data['heatpump_aux'][~np.isnan(hp_data['heatpump_aux'])] / 1000.

    hp_data['outdoor_temperature_F'] = hp_data['outdoor_temperature']*9/5 + 32

    hp_data['dtime'] = hp_data['time_elapsed'][~np.isnan(hp_data['time_elapsed'])]

    hp_data['kwh_hp'] = hp_data['kw_hp']*hp_data['dtime']
    hp_data['kwh_aux'] = hp_data['kw_aux']*hp_data['dtime']
    hp_data['kwh_total'] = hp_data['kwh_aux'] + hp_data['kwh_hp']

    # filter dataframe to exclude NaNs and heat pump is on, calculate heating only
    hp_data = hp_data[np.isfinite(hp_data['heat_flow_rate'])]
    #hp_data = hp_data.query('heatpump_power > 500')
    hp_data['MBtuH'] = (3.412*(hp_data['kw_hp'] + hp_data['kw_aux']) +
                       (hp_data['heat_flow_rate'])/1000)

    hp_data_hourly = hp_data.resample('1800S').mean()

    hp_data_daily = hp_data.resample('1D').mean()


    hp_data.plot(kind='line', y=['kw_hp','kw_aux','outdoor_temperature_F'],
                    secondary_y='outdoor_temperature_F',
                    xlabel='Time', ylabel='Power [kW]',
                    title='Site NGEN ID  {}'.format(str(site.name)))

    #plt.ylim([0, 60])

    #hp_data_hourly.plot(kind='line', y=['MBtuH','outdoor_temperature_F'],
    #                secondary_y='outdoor_temperature_F',
    #                xlabel='Time', ylabel='MBtuH [Total heating]',
    #                title='Site NGEN ID  {}'.format(str(site.name)))

    #plt.ylim([0, 60])

    #plt.scatter(hp_data_daily['outdoor_temperature_F'], hp_data_daily['MBtuH'])
    '''
    fig_name = '../temp_files/explorer_plot_{}.png'.format(str(site.name))
    print(fig_name)
    plt.show()
    plt.savefig(fig_name)

    x = ['heatpump_power', 'source_supplytemp',
         'source_returntemp']
    y = ['heatpump_power', 'source_supplytemp',
         'source_returntemp']

    x_label = ['System Current', 'EWT',
               'LWT']
    y_label = ['System Current', 'EWT',
               'LWT']

    ngen = site_name
    data = hp_data

    fig, axs = plt.subplots(3, 3)
    for i in range(3):
        for j in range(3):
            axs[i, j].scatter(data[x[i]], data[y[j]], s=2)
            axs[i, j].set(xlabel=x_label[i])
            axs[i, j].set(ylabel=y_label[j])

    # Hide x labels and tick labels for top plots and y ticks for right plots.
    # for ax in axs.flat:
    #    ax.label_outer()

    plt.suptitle("NGEN %s  %s to %s " % (ngen, data.index[0].strftime("%m-%d-%Y"), data.index[-1].strftime("%m-%d-%Y")))
    '''
    plt.show()
