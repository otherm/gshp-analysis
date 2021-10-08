

import pandas as pd
import admin_tools.db_reader as db_reader
import numpy as np
import matplotlib.pyplot as plt
import logging
from db_tools import otherm_db_reader

# TODO align data columns with oTherm data columns

palette = {'Heating': 'darkorange', 'Cooling': 'dodgerblue'}

def daily_summary(data, site, **kwargs):
    """
    Calculates daily summaries

    :param pandas.DataFram data: minute-resolution operating data
    :param class site: site dataclass
    :param dict kwargs:
    :return: DataFrame with Daily Summaries::

            class Equipment:
                id: int
                uuid: str
                model: str
                description: Optional[str]
                type: int
                site: int
                manufacturer: int


    """
    # Some additional columns to minute resolution data to facilitate
    # computation of daily values
    e_measures = ['heatpump_power_kwh']

    #TODO:  otherm:  move weather data to line-protocol file and upload to otherm db
    #then join weather data with heat pump data into 'outdoor_temperature' columne

    data['OAT_F'] = data['outdoor_temperature']*(9/5) + 32.

    data['cooling_degrees'] = np.where(data['OAT_F'] > 65.,
                                       (data['OAT_F'] -
                                        65)*data['time_elapsed']/24, 0.)
    data['heating_degrees'] = np.where(data['OAT_F'] < 65.,
                                       (65 - data['OAT_F'])
                                       * data['time_elapsed']/24, 0.)

    #TODO update to use compressor threshold as keyword

    data['heatpump_on'] = np.where(data['heatpump_power'] > heatpump_theshold, True)

    data['ewt_on'] = (data['r_1_on'] * data['ewt_1']).apply(lambda x: np.nan
                                                          if x == 0 else x)

    data['heatpump_power_kwh'] = np.where(data['time_elapsed'] < 0.083,
                                      data['heatpump_power'] * data['time_elapsed'] / 1000., 0)

    if 'heatpump_aux' in data.columns:
        data['heatpump_aux_kwh'] = np.where(data['time_elapsed'] < 0.083,
                                     data['heatpump_aux'] * data['time_elapsed']/1000.,0)
        e_measures.append('heatpump_aux_kwh')

    if 'sourcefluid_pump_power' in data.columns:
        data['sourcefluid_pump_power'] = np.where(data['time_elapsed'] < 0.083,
                                     data['sourcefluid_pump_power'] * data['time_elapsed']/1000.,0)
        e_measures.append('sourcefluid_pump_power_kwh')

    data['btu_heating'] = np.where(data['heat_flow_1'] > 0,
                                   3412.14 * data['compressor_kwh'], 0)
    data['btu_cooling'] = np.where(data['heat_flow_1'] < 0,
                                   3412.14 * data['compressor_kwh'], 0)

    data['pump_1_runtime'] = np.where(data['time_elapsed'] < 0.083,
                                       data['r_1_on']*data['time_elapsed'], 0)
    data['btus_exchanged'] = np.where(data['time_elapsed'] < 0.083,
                                     data['heat_flow_1'] * data['time_elapsed'], 0)
    # Initialize data frame for computing and storing daily values
    # use np.nan as placeholder, as needed to make consistent with
    ds = pd.DataFrame()

    ds['runtime'] = data['pump_1_runtime'].resample('D').sum()

    ds['kwh_pump_1'] = data['compressor_kwh'].resample('D').sum()

    ds['kwh_aux'] = data['auxiliary_kwh'].resample('D').sum()

    #ds['kwh_loop_pump'] = data['loop_pump_kwh'].resample('D').sum()
    ds['kwh_total'] = ds['kwh_pump_1'] + ds['kwh_aux'] #+ ds['kwh_loop_pump']

    ds['cooling_degree_days'] = data['cooling_degrees'].resample('D').sum()
    ds['heating_degree_days'] = data['heating_degrees'].resample('D').sum()
    ds['Mbtus_exchanged'] = data['btus_exchanged'].resample('D').sum()/24000

    #ds['any_pump_runtime'] = ds['pump_1_runtime']

    ds['btus_heat'] = data['btu_heating'].resample('D').sum()
    ds['btus_cool'] = data['btu_cooling'].resample('D').sum()

    ds['ewt_min'] = data['ewt_on'].resample('D').min()*(9/5)+32.
    ds['ewt_max'] = data['ewt_on'].resample('D').max()*(9/5)+32.

    ds['OAT_F'] = data['OAT_F'].resample('D').mean()

    ds['date'] = ds.index.strftime("%Y-%m-%d")
    ds['installation_id'] = int(site.replace('s', '9'))

    # To the extent we need to pad DataFrame with NaNs, here they are:
    NaNs = ['pump_2_runtime', 'pump_3_runtime', 'kwh_pump_2', 'kwh_pump_3',
            'operating_cost', 'hot_water_generated', 'kwh_hot_water',
            'btus_exchanged_2', 'btus_exchanged_3']
    #for item in NaNs:
    #    ds[item] = np.nan

    return ds


if __name__ == "__main__":
    site_name = 'GES649'
    start = '2015-01-01'
    end = '2016-01-01'

    site = otherm_db_reader.get_site_info(site_name)
    equipment, hp_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone)

    kwargs = {'heatpump_threshold': 500}
    ds = daily_summary(hp_data, site, **kwargs)

    outdoor_temp = np.asarray(ds['OAT_F'])
    geo = np.asarray(ds['Mbtus_exchanged'])

    outdoor_temp_heating = []
    outdoor_temp_cooling = []

    geo_heating = []
    geo_cooling = []

    for i in range(len(geo)):
        if geo[i] > 0:
            geo_heating.append(geo[i])
            outdoor_temp_heating.append(outdoor_temp[i])
        if geo[i] < 0:
            geo_cooling.append(-geo[i])
            outdoor_temp_cooling.append(outdoor_temp[i])

    """Insert Display Name for "Site" """
    title = 'Daily Load Profile'

    plt.plot(outdoor_temp_heating, geo_heating, 'o', c=palette['Heating'], label="Geo Heat Extraction")
    plt.plot(outdoor_temp_cooling, geo_cooling, 'o', c=palette['Cooling'], label="Geo Heat Rejection")

    plt.xlabel('Average Daily Outside Air Temp [F]')
    plt.ylabel('Average Daily GeoExchange [MBTUs/HR]')

    design_params = db_reader.get_design_parameters(installation_id)

    degree_day_base_temperature = 65.
    balance_cool = None
    balance_heat = None
    geo_peak_heat = None
    geo_peak_cool = None
    design_temperature_cool = None
    design_temperature_heat = None

    try:
        balance_cool = float(design_params['balance_cool'])
        balance_heat = float(design_params['balance_heat'])
        geo_peak_heat = float(design_params['geo_peak_heat'])
        geo_peak_cool = float(design_params['geo_peak_cool'])
        design_temperature_cool = float(design_params['design_temperature_cool'])
        design_temperature_heat = float(design_params['design_temperature_heat'])
        logging.info('Successfully found data for %s' % installation_id)
    except TypeError:
        logging.error('Failed to get information for installation %s, passing' % install)


    if design_params is not None:
        # TODO Write this to check if the DesignParamters is present as the condition for running
        dps = [design_temperature_heat,
               balance_heat,
               balance_cool,
               design_temperature_cool
               ]
        geo_peak = [geo_peak_heat, 0, 0, geo_peak_cool]

        plt.plot(dps, geo_peak, lw=2, c='gray', ls='--', label='GeoExchange Capacity')
        plt.ylim(0, max(max(geo), geo_peak_heat))
        plt.xlim(min(min(outdoor_temp), design_temperature_heat),
                 max(outdoor_temp), design_temperature_cool)

    plt.show()
