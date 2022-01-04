#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creates histograms of the heat pump entering water temperature averaged on hourly intervals using the Seaborn library.
When multiple site names are provided, histograms are plotted along the x axis and labeled with the site name.

When multiple sites are plotted, the *seaborn.violinplot* parameters are set to prodcue histograms that are equal width
with the area of each mode scaled to the relative number of hours in heating or cooling.
"""

import seaborn as sns
from datetime import date
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utilities import misc_functions as misc_functions
from db_tools import otherm_db_reader

C_to_F = misc_functions.C_to_F


def determine_mode(row):
    """
    Args:
        row :  a row in a pandas DataFrame

    Returns:
        new column in the DataFrame, that identifies when heat pump is heating or cooling
    """
    if row['heat_flow_rate'] > 0:
        return 'Heating'
    else:
        return 'Cooling'



def ewt_violins(site_names, start_date, end_date, timezone, db):
    """
    Parameters
    ----------
        site_names : list
            A list of site names to include in analyis.  Each site will have it's own violin plot

        start_date : str
            Start date of analysis in format 'YYYY-MM-DD'

        end_date : str
            End date of analysis in format 'YYYY-MM-DD'

        timezone : str
            Timezone of installation

        db : str
            oTherm database to use for analysis

    Returns
    -------
        image file
            The image is written to a file in the ../temp_files directory
    """


    composite = pd.DataFrame()
    palette = {'Heating': 'darkorange', 'Cooling': 'dodgerblue'}

    for site_name in site_names:
        site = otherm_db_reader.get_site_info(site_name, db)
        print('working on ...', site.name)
        equipment, data = otherm_db_reader.get_equipment_data(site.id, start_date, end_date, timezone, db)

        # resample to 1-hour averages
        dataHourly = data.resample('3600S').mean()

        # eliminate NaNs from DataFrame and limit rows to when heat pump is 'on' >500 Watts
        dataHourly = dataHourly[np.isfinite(dataHourly['heat_flow_rate'])]
        dataHourly = dataHourly.query('heatpump_power > 500')

        # 'high' is used to filter outliers (2*95th percentile), some of which may be erroneous data
        high = 2*dataHourly['heatpump_power'].quantile(0.95)
        dataHourly = dataHourly[dataHourly['heatpump_power'] < high]

        # add two more columns for heating and cooling
        dataHourly['Mode'] = dataHourly.apply(determine_mode, axis=1)
        dataHourly['EWT F'] = dataHourly['source_supplytemp'].apply(C_to_F)

        dataHourly['install'] = site.name
        composite = pd.concat([composite, dataHourly])

    composite.to_csv('../temp_files/ds_debug.csv')
    print('generating plot, please stand by')
    ax = sns.violinplot(x='install', y='EWT F', data=composite, scale='count', scale_hue=True,
                        hue='Mode', palette=palette, split=True)
    ax.set_xlabel('Site')
    ax.set_ylabel('EWT [$^\circ$F]')
    fig_name = '../temp_files/ewt_violin_plots_{}_{}.png'.format(db, str(date.today().strftime("%m-%d-%y")))
    print(fig_name)
    plt.savefig(fig_name)
    plt.close()

if __name__ == '__main__':
    site_names = ['01886', '03561', '03824', '06018']
    start_date = '2016-01-01'
    end_date = '2016-12-31'
    timezone = 'US/Eastern'
    db = 'otherm'
    #db = 'localhost'

    ewt_violins(site_names, start_date, end_date, timezone, db)
