# -*- coding: utf-8 -*-
"""

@author: Matt Davis

9.2.2018
Aggregate statistics for kW on an hourly, time-of-day basis
Currently calculates mean and 90th quantile for each hour and
creates matplotlib plot

Set up for a single year but should be extendable to multiple years
using methods similar to ewt_aggregate_stats.py
"""

import pandas as pd
import numpy as np
from db_tools import otherm_db_reader

import matplotlib.pyplot as plt

def hourly_daily_stats(site, hp_data):
    """

    Parameters
    ----------
    site
    hp_data

    Returns
    -------

    """
    hp_data['kw_hp'] = hp_data['heatpump_power'][~np.isnan(hp_data['heatpump_power'])] / 1000.
    hp_data['kw_aux'] = hp_data['heatpump_aux'][~np.isnan(hp_data['heatpump_aux'])] / 1000.

    hp_data['dtime'] = hp_data['time_elapsed'][~np.isnan(hp_data['time_elapsed'])]

    hp_data['kwh_hp'] = hp_data['kw_hp']*hp_data['dtime']
    hp_data['kwh_aux'] = hp_data['kw_aux']*hp_data['dtime']
    hp_data['kwh_total'] = hp_data['kwh_aux'] + hp_data['kwh_hp']

    wrh = hp_data.resample('3600S').sum()

    winter = wrh[(wrh.index.month >= 12)].append(wrh[(wrh.index.month < 3)])
    spring = wrh[(wrh.index.month >= 3) & (wrh.index.month < 6)]
    summer = wrh[(wrh.index.month >= 6) & (wrh.index.month < 9)]
    fall =   wrh[(wrh.index.month >= 9) & (wrh.index.month < 12)]
    print(len(winter), len(spring), len(summer), len(fall))

    print(len(winter), len(spring), len(summer), len(fall))

    stats = pd.DataFrame()
    quantiles = pd.DataFrame()
    stats['Winter'] = winter['kwh_total'].groupby(winter.index.hour).mean()
    stats['Spring'] = spring['kwh_total'].groupby(spring.index.hour).mean()
    stats['Summer'] = summer['kwh_total'].groupby(summer.index.hour).mean()
    stats['Fall'] = fall['kwh_total'].groupby(fall.index.hour).mean()
    quantiles['Winter q90'] = winter['kwh_total'].groupby(winter.index.hour).quantile(q=0.90)

    _, ax = plt.subplots()
    quantiles.plot(ax=ax)
    stats.plot(kind='bar', width=0.90, color=['b', 'g', 'r', 'orange'], ax=ax)
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Hourly Demand [kW]')
    plt.title(site.name)
    plt.legend(loc='upper right')
    fig_name = '../temp_files/kwh_hourly_stats_{}.png'.format(str(site.name))
    print(fig_name)
    plt.savefig(fig_name)
    return fig_name


if __name__ == "__main__":
    site_name = 'GES649'
    start = '2015-01-01'
    end = '2016-12-31'

    site = otherm_db_reader.get_site_info(site_name)

    equipment, hp_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone)

    stats = hourly_daily_stats(site, hp_data)
