# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 12:12:38 2021

@author: rtc50
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from db_tools import otherm_db_reader

def lag_temps(initial_data):
    """Lag temperature measurements by one value.   Necessary for on-pipe measurements.
    Assumes that operating data is at minute-resolution and thermal response of temperature sensors is
    approximately one minute.

    Parameters
    ----------
    initial_data : pd.DataFrame
        Data as initially pulled from database.

    Returns
    -------
    pd.DataFrame
        Dataframe with lagged temperature measurements. Additional column
        is as follows:

        ======  ======================================================
        DeltaT  circulating fluid temperature change (as `float`)
        ======  ======================================================

    """

    # lag temp measurements by 1 datapoint for on pipe measurements
    initial_data['source_supplytemp'] = initial_data['source_supplytemp'].shift(-1)
    initial_data['source_returntemp'] = initial_data['source_returntemp'].shift(-1)
    data = initial_data[:-1].copy()
    data['DeltaT'] = data['source_returntemp'] - data['source_supplytemp']
    return data


def to_kilowatts(data, derate, power_fac):
    """Unit conversion and electricity usage/heat rate adjustments.

    Converts heat flow from btu/hr to kW and electricity from W to kW.
    Scales heat flow and electricity consumption values.

    Parameters
    ----------
    data : pd.DataFrame
        Heat pump operational data.
    derate : float
        Scales heat flow values.
    power_fac : float
        Scales electricity usage.

    Returns
    -------
    pd.DataFrame
        Dataframe with unit conversion and necessary scaling applied to
        electricity usage and heatflow. Additional columns are
        as follows:

        =======  =======================================================
        q        heat flow in kW with scaling (as `float`)
        kw_used  electricity usage in kW with scaling (as `float`)
        =======  =======================================================

    """

    # btu/hr to kw
    data['q'] = derate*(0.29307107*data['heat_flow_rate'])/1000
    data['q'].fillna(0.0, inplace=True)
    # w to kw
    data['kw_used'] = power_fac * data['heatpump_power']/1000
    return data


def error_heat_from_ground(mrl_hr, E_deltaT, e_v, data):
    """Calculates error associated with heat transfer from ground.

    Converts heat flow from btu/hr to kW and electricity from W to kW.
    Scales heat flow and electricity consumption values.

    Parameters
    ----------
    mrl_hr : float
        Max record length in hours.
    E_deltaT : float
        Absolute uncertainty in temperature change of circulating fluid.
    e_v : float
        Flow rate fractional error.
    data : pd.Dateframe
        Heatpump operational data.

    Returns
    -------
    pd.DataFrame
        Dataframe with additional columns associated with error in heat
        exchange rates. Additional columns are as follows:

        =============  ========================================================
        e_deltaT       fractional uncertainty deltaT (as `float`)
        e_q            fractional uncertainty heat transfer rate (as `float`)
        E_q            absolute uncertainty heat transfer rate (as `float`)
        tvalue         date time (as `datetime64[ns, UTC]`)
        timedelta      time since last timestep (as `timedelta64[ns]`)
        elapsed_hours  hours since last timestep (as `float`)
        E_Q            absolute uncertainity in kWh to/from ground (as `float`)
        =============  ========================================================

    """

    error_data = data.copy()

    # fractional uncertainty temp difference
    error_data['e_deltaT'] = abs(E_deltaT/error_data['DeltaT'])

    # fractional uncertainty heat transfer rate
    error_data['e_q'] = ((e_v**2)+(error_data['e_deltaT']**2))**(0.5)

    # absolute uncertainty heat transfer rate
    error_data['E_q'] = error_data['e_q']*error_data['q']

    # elapsed time for each timestep
    error_data['tvalue'] = error_data.index

    # fill first timestep with zero seconds
    z_sec = pd.Timedelta(seconds=0)
    error_data['timedelta'] = (error_data['tvalue'] -
                               error_data['tvalue'].shift()).fillna(z_sec)

    # median time step to fill empty initial timestep
    mts = error_data['timedelta'].median()
    error_data.loc[data.index[0], 'timedelta'] = mts
    error_data['elapsed_hours'] = (error_data['timedelta']
                                   .dt.total_seconds())/(60*60)
    meh = error_data['elapsed_hours'].median()

    # set upper limit of elapsed hours
    error_data['elapsed_hours'] = error_data['elapsed_hours'].where(
        error_data['elapsed_hours'] <= mrl_hr, meh)

    # absolute uncertainity in thermal energy (kWh)
    error_data['E_Q'] = error_data['E_q']*error_data['elapsed_hours']
    return error_data


def elec_error_single_elec_measurement(e_e, error_data):
    """Calculates absolute electrical error.

    For datasets that include a single electricity consumption value.
    Calculates absolute electrical error for each timestep in kWh.

    Parameters
    ----------
    e_e : float
        Fractional uncertainty of electricity usage.
    error_data : pd.Dateframe
        Heatpump operational data.

    Returns
    -------
    pd.DataFrame
        Dataframe with additional column for electricity usage uncertainty.
        Additional column is as follows:

        ===  =======================================================
        E_W  absolute electrical uncertainity in kWh (as `float`)
        ===  =======================================================

    """
    # no need to add in quadrature if single measurement
    # absolute electrical error
    error_data['E_w'] = (error_data['kw_used'] *
                         error_data['elapsed_hours'] * e_e)

    return error_data


def heat_calcs_single_elec_measurement(error_data, pump_power):
    """Calculates heat flow and electricity usage during heating periods.

    For datasets that include a single electricity consumption value.
    Considers electricity consumption of single stage circulating pump that will not
    contribute useful heat to building.

    Parameters
    ----------
    error_data : pd.Dateframe
        Heatpump operational data.
    pump_power : float
        Electricity consumption of single stage circulating pump.

    Returns
    -------
    pd.DataFrame
        Dataframe with additional columns associated with heatflow and
        electricity consumption. Additional columns are as follows:

        ===============  ====================================================
        electricity_kWh  electricity kWh used in heating mode (as `float`)
        hfg              heat from ground in kWh (as `float`)
        pump_power       pump electricity usage in Kw (as `float`)
        heat_provided    heat provided to building in kWh (as `float`)
        ===============  ====================================================

    """


    heating_data = error_data.copy()
    # filter to only where heating occurs
    vals_to_filter = ['E_Q', 'E_w', 'kw_used', 'q']
    for i in range(len(vals_to_filter)):
        f_v = vals_to_filter[i]
        heating_data[f_v] = np.where(heating_data['q'] > 0.0,
                                     heating_data[f_v], 0.0)
    # electricity kWh in heating mode
    e_h_kwh = heating_data['elapsed_hours'] * heating_data['kw_used']
    heating_data['electricity_kWh'] = e_h_kwh
    # heat from ground
    heating_data['hfg'] = heating_data['q']*heating_data['elapsed_hours']
    # pump power (kw)
    heating_data['pump_power'] = np.where(heating_data['kw_used'] > 0,
                                          pump_power, 0.0)
    # heat provided (kWh)
    heating_data['heat_provided'] = (heating_data['elapsed_hours'] *
                                     (heating_data['q'] +
                                      heating_data['kw_used']
                                      - heating_data['pump_power']))
    return heating_data


def total_heat_sum_error(spf_heat_data):
    """Total values for heating and overall heating spf.

    Uses heating operational data. Calculate total heat extracted from
    ground and absolute error. Also calculates spf and fractional error.

    Parameters
    ----------
    spf_heat_data : pd.Dateframe
        Heatpump operational data during heating.

    Returns
    -------
    total_ground_heat : float
        Total heat from ground in kWh.
    total_gh_error : float
        Absolute error of total heat from ground in kWh.
    total_heat_spf : float
        Heating spf.
    ah_e_spf : float
        Heating fractional uncertainity of SPF.

    """
    # total heat from ground (kWh)
    total_ground_heat = spf_heat_data['hfg'].sum()
    # total heat from ground absolute error
    total_gh_error = spf_heat_data['E_Q'].sum()
    # heating spf for data period
    total_heat_spf = ((spf_heat_data['heat_provided'].sum())
                      / (spf_heat_data['electricity_kWh'].sum()))
    # fractional heating error
    fhe = total_gh_error/(spf_heat_data['heat_provided'].sum())
    # fractional electric error
    fee = spf_heat_data['E_w'].sum()/spf_heat_data['electricity_kWh'].sum()
    # heating fractional uncertainity of the SPF for data period
    ah_e_spf = ((fhe**2)+(fee**2))**0.5

    return total_ground_heat, total_gh_error, total_heat_spf, ah_e_spf


def monthly_ground_heat(spf_heat_data, percent_max):
    """Calculates monthly heat flow and spf values for plotting.

    Resamples data to monthly values.
    Determines which months have signifigant heating loads to be plotted.
    Calculates monthly spf values and absolute uncertainty for plotting.

    Parameters
    ----------
    spf_heat_data : pd.Dateframe
        Heatpump operational data during heating.
    percent_max : float
        Multipled by highest heating month to determine minimum kWh to plot.

    Returns
    -------
    pd.DataFrame
        Dataframe with additional columns associated with monthly heatflow
        and spf. Additional columns are as follows:

        ===================  ==================================================
        year                 year of each timestep (as `str`)
        month_and_year       year and month of each timestep (as `str`)
        monthly_heating_spf  heating spf value for month (as `float`)
        fhe                  heating fractional uncertainity (as `float`)
        fee                  electric fractional uncertainity (as `float`)
        e_spf                fractional uncertainity heating SPF (as `float`)
        E_spf                absolute uncertainity heating SPF (as `float`)
        ===================  ==================================================

    """
    # resample to monthly values
    monthly_heating = spf_heat_data.resample('M').agg({'electricity_kWh':
                                                       np.sum,
                                                       'heat_provided': np.sum,
                                                       'E_Q': np.sum,
                                                       'E_w': np.sum,
                                                       'source_supplytemp':
                                                           np.mean})
    # month and year column
    monthly_heating['year'] = monthly_heating.index.year
    monthly_heating = monthly_heating.astype({"year": str})
    monthly_heating['month_and_year'] = (monthly_heating.index.strftime('%b ')
                                         + monthly_heating['year'])
    # minimum heating value
    min_heat = monthly_heating['heat_provided'].max()*percent_max
    # filter out value below min_heat
    monthly_heating['heat_provided'] = np.where(
                        monthly_heating['heat_provided'] < min_heat, 0.0,
                        monthly_heating['heat_provided'])
    # filter values for monthly with minimal/no heating
    vals_to_filter = ['E_Q', 'E_w', 'electricity_kWh']
    for i in range(len(vals_to_filter)):
        vf = vals_to_filter[i]
        monthly_heating[vf] = np.where(monthly_heating['heat_provided']
                                       == 0.0, 0.0, monthly_heating[vf])

    # monthly spf
    monthly_heating['monthly_heating_spf'] = (monthly_heating['heat_provided']
                                              /
                                              monthly_heating
                                              ['electricity_kWh'])
    # monthly fractional heating error
    monthly_heating['fhe'] = (monthly_heating['E_Q'] /
                              monthly_heating['heat_provided'])
    # monthly fractional electric error
    monthly_heating['fee'] = (monthly_heating['E_w'] /
                              monthly_heating['electricity_kWh'])
    # monthly heating fractional uncertainity of SPF
    monthly_heating['e_spf'] = ((monthly_heating['fhe']**2) +
                                (monthly_heating['fee']**2))**0.5
    # monthly heating absolute error
    monthly_heating['E_spf'] = (monthly_heating['e_spf'] *
                                monthly_heating['monthly_heating_spf'])
    return monthly_heating

if __name__ == '__main__':
    site_name = '01886'
    start = '2016-01-01'
    end = '2016-12-31'
    db = 'otherm'
    # sites analyzed in report
    # installation_id = '1674'
    # installation_id = '1649'
    # installation_id = '45'

    site = otherm_db_reader.get_site_info(site_name, db)
    equipment, initial_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone, db)


    '''
    hardwire data for testing
    '''
    # value multiplied by maximum heating/cooling value for month to determine min
    # kWh of heating/cooling to be plotted
    percent_max = 0.05
    # maximum record length (min)
    mrl_min = 5
    mrl_hr = mrl_min / 60
    # electricity fractional error
    e_e = 0.2
    # delta T absolute error
    single_deltaT = 0.1
    E_deltaT = (2 * (single_deltaT ** 2)) ** 0.5
    # flow rate fractional error
    e_v = 0.2
    # Adjusts heat rate
    derate = 1.0
    # (pump electricity usage in kW)
    pump_power = 0.0
    # Adjusts electricity consumption
    power_fac = 1.2

    '''
    call functions from error_calcs_funcs
    '''
    # lag on pipe measurements
    data = lag_temps(initial_data)

    # convert to kW and scale electricity or heat if necessary
    data = to_kilowatts(data, derate, power_fac)

    # calculate error related to heat from ground
    error_data = error_heat_from_ground(mrl_hr, E_deltaT, e_v, data)

    # calculate electrical error when single electricity value
    error_data = elec_error_single_elec_measurement(e_e, error_data)

    # calculate useful heat, heat from ground etc.
    heating_data = heat_calcs_single_elec_measurement(error_data, pump_power)

    # sums heat values and calculates cumulative errors
    total_ground_heat, total_gh_error, annual_heat_spf, ah_e_spf = (
        total_heat_sum_error(heating_data))

    # monthly heating values for plotting
    monthly_heating = monthly_ground_heat(heating_data, percent_max)

    '''
    SPF heating only plot
    function is set up to plot heating/cooling bars in same month
    '''


    def subcategorybar(X, vals, label, errors, width=0.8):
        n = len(vals)
        _X = np.arange(len(X))
        for i in range(n):
            plt.bar(_X - width / 2. + i / float(n) * width, vals[i],
                    width=width / float(n),
                    align="edge", label=label[i], color=color[i], yerr=errors[i])
        plt.xticks(_X, X)


    # values for function
    X = monthly_heating['month_and_year']
    vals = [monthly_heating['monthly_heating_spf']]
    label = ['Monthly Heating SPF']
    color = ['darkorange']
    errors = [monthly_heating['E_spf']]
    subcategorybar(X, vals, label, errors, width=0.8)
    plt.xticks(rotation=60)
    plt.legend(loc='upper right')
    plt.ylabel('Monthly SPF')
    plt.title('Monthly Heating Seasonal Performance Factors (SPF)')
    plt.tight_layout()
    fig_name = '../temp_files/spf_plots_{}_{}.png'.format(site.name, str(date.today().strftime("%m-%d-%y")))
    print(fig_name)
    plt.savefig(fig_name)
    plt.close()