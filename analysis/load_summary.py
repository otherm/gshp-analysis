

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from db_tools import otherm_db_reader
from analysis import daily_summaries


# TODO align data columns with oTherm data columns

palette = {'Heating': 'darkorange', 'Cooling': 'dodgerblue'}

def load_summary_graph(site, thermal_load, ds):
    """

    Parameters
    ----------
    ds :  DataFrame
        Pandas ddataframe containing daily summaries
    site :  dict
        Dataclass object containing site information

    """
    outdoor_temp = np.asarray(ds['OAT_F'])
    geo = np.asarray(ds['mbtus_exchanged'])

    outdoor_temp_heating = []
    outdoor_temp_cooling = []

    geo_heating = []
    geo_cooling = []

    for i in range(len(geo)):
        if geo[i] > 0:
            geo_heating.append(geo[i]/24)
            outdoor_temp_heating.append(outdoor_temp[i])
        if geo[i] < 0:
            geo_cooling.append(-geo[i]/24)
            outdoor_temp_cooling.append(outdoor_temp[i])


    title = 'Daily Load Profile'

    plt.plot(outdoor_temp_heating, geo_heating, 'o', c=palette['Heating'], label="Geo Heat Extraction")
    plt.plot(outdoor_temp_cooling, geo_cooling, 'o', c=palette['Cooling'], label="Geo Heat Rejection")

    plt.xlabel('Average Daily Outside Air Temp [F]')
    plt.ylabel('Average Daily GeoExchange [MBTUs/HR]')

    degree_day_base_temperature = 65.
    balance_cool = 65.
    balance_heat = 65.
    geo_peak_heat = thermal_load.heating_design_load
    geo_peak_cool = thermal_load.cooling_design_load
    design_temperature_cool = thermal_load.cooling_design_oat
    design_temperature_heat = thermal_load.heating_design_oat


    dps = [design_temperature_heat,
           balance_heat,
           balance_cool,
           design_temperature_cool
           ]
    geo_peak = [geo_peak_heat, 0, 0, geo_peak_cool]

    plt.plot(dps, geo_peak, lw=2, c='gray', ls='--', label='GeoExchange Capacity')
    plt.ylim(0, max(max(geo/1000), geo_peak_heat))
    plt.xlim(min(min(outdoor_temp), design_temperature_heat),
             max(outdoor_temp), design_temperature_cool)

    fig_name = '../temp_files/load_summary_{}.png'.format(str(site.name))
    print(fig_name)
    plt.savefig(fig_name)
    return fig_name


if __name__ == "__main__":
    site_name = '111956'
    start = '2022-01-14'
    end = '2022-01-15'
    db = 'otherm_cgb'

    site = otherm_db_reader.get_site_info(site_name, db)
    equipment = otherm_db_reader.get_equipment(site.id, db)
    hp_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone, db)
    thermal_load = otherm_db_reader.get_thermal_load(site, db)

    heatpump_threshold_watts = 500

    ds = daily_summaries.create_daily_summaries(hp_data, heatpump_threshold_watts)

    load_summary_graph(site, thermal_load, ds)

