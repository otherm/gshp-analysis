#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  3 18:17:51 2018

@author: M Davis

calculatoin and plotting of kwh per SF as function of OAT

"""

import matplotlib.pyplot as plt
from db_tools import otherm_db_reader
from utilities import misc_functions as misc_functions

C_to_F = misc_functions.C_to_F

def create_kwh_per_sf_plots(site, data, symbol_color):
    """
    Add up two integer numbers.

    This function simply wraps the ``+`` operator, and does not
    do anything interesting, except for illustrating what
    the docstring of a very simple function looks like.

    Parameters
    ----------
    num1 : int
        First number to add.
    num2 : int
        Second number to add.

    Returns
    -------
    int
        The sum of ``num1`` and ``num2``.

    See Also
    --------
    subtract : Subtract one integer from another.

    Examples
    --------
    >>> add(2, 2)
    4
    >>> add(25, 0)
    25
    >>> add(10, -10)
    0
    """

    if 'heatpump_aux' in data.columns:
        data['totalunitpower'] = data['heatpump_power'] + data['heatpump_aux']
    else:
        data['totalunitpower'] = data['heatpump_power']

    area = site.thermal_load.conditioned_area

    kWh_perSF = (data['totalunitpower'] * data['time_elapsed']).resample('D').sum() / (1000 * area)
    OAT_F = (data['outdoor_temperature'] * (9 / 5) + 32).resample('D').mean()
    plt.scatter(OAT_F, kWh_perSF, marker='o', s=2, alpha=0.75, mc= symbol_color, label=site.name)


    plt.ylabel('kWh/SF per day')
    plt.title('Heat Pump kWh/Square Feet vs. Outdoor Air Temperature')
    plt.xlabel('Average Daily Outdoor Air Temperature [$^\circ F$]')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    site_names = ['GES649']
    start_date = '2016-01-01'
    end_date = '2016-12-31'
    symbol_color = ['b', 'r', 'g', 'o']
    for name in site_names:
        site = otherm_db_reader.get_site_info(name)

        equipment, hp_data = otherm_db_reader.get_equipment_data(site.id, start_date, end_date, site.timezone)

        if len(hp_data) > 100:
            create_kwh_per_sf_plots(site, hp_data, symbol_color)
