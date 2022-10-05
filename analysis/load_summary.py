

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from db_tools import otherm_db_reader
from analysis import daily_summaries


# TODO include cooling once time shift is applied for on-pipe temps

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
    mbtus_heat = np.asarray(ds['mbtus_heat'])
    mbtus_cool = np.asarray(ds['mbtus_cool'])
    mbtus_aux = 3.412*np.asarray(ds['auxiliary_kwh'])

    outdoor_temp_heating = []
    outdoor_temp_cooling = []

    heat_load = []
    cool_load = []

    for i in range(len(geo)):
        if geo[i] > 0:
            heat_load.append(geo[i]/24 + mbtus_heat[i]/24 + mbtus_heat[i]/24 + mbtus_aux[i]/24)
            outdoor_temp_heating.append(outdoor_temp[i])
        if geo[i] < 0:
            cool_load.append(-geo[i]/24 - mbtus_cool/24)
            outdoor_temp_cooling.append(outdoor_temp[i])

    plt.plot(outdoor_temp_heating, heat_load, 'o', c=palette['Heating'], label="Heating Load")
#    plt.plot(outdoor_temp_cooling, cool_load, 'o', c=palette['Cooling'], label="Cooling Load")

    plt.xlabel('Average Daily Outside Air Temp [F]')
    plt.ylabel('Average Daily Thermal Load [MBTUs/HR]')

    degree_day_base_temperature = 65.
    balance_cool = 65.
    balance_heat = 65.
    peak_heat_load = thermal_load.heating_design_load
    peak_cool_load = thermal_load.cooling_design_load
    design_temperature_cool = thermal_load.cooling_design_oat
    design_temperature_heat = thermal_load.heating_design_oat


    dps = [design_temperature_heat,
           balance_heat,
           balance_cool,
           design_temperature_cool
           ]

    dps = [design_temperature_heat,
           balance_heat
           ]

    peak_load = [peak_heat_load, 0, 0, peak_cool_load]
    peak_load = [peak_heat_load, 0]

    plt.plot(dps, peak_load, lw=2, c='gray', ls='--', label='Design Load [MBtuH]')

    plt.ylim(0, max(1.25*max(np.asarray(heat_load)), peak_heat_load*1.1))
    plt.xlim(min(min(outdoor_temp), design_temperature_heat),
             max(outdoor_temp), design_temperature_cool)
    plt.xlim(0, 70)
    plt.title('Daily Heating Load Profile for: ' + site.name)
    fig_name = '../temp_files/load_summary_{}.png'.format(str(site.name))
    print(fig_name)
    plt.savefig(fig_name)
    return fig_name


if __name__ == "__main__":
    site_name = '111520'
    start = '2021-07-01'
    end = '2022-06-30'
    db = 'otherm_cgb'

    site = otherm_db_reader.get_site_info(site_name, db)
    equipment = otherm_db_reader.get_equipment(site.id, db)
    hp_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone, db)
    thermal_load = otherm_db_reader.get_thermal_load(site, db)

    heatpump_threshold_watts = 500

    ds = daily_summaries.create_daily_summaries(hp_data, heatpump_threshold_watts)

    load_summary_graph(site, thermal_load, ds)

