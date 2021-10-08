# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 17:10:56 2021

@author: rtc50
"""

import numpy as np
import pandas as pd
from utilities import df_processing

def english_to_metric(data):
    # temp (F->C)
    data['enteringwatertemp'] = (5/9)*(data['enteringwatertemp']-32)
    data['leavingwatertemp'] = (5/9)*(data['leavingwatertemp']-32)

    # flow (gpm-> m^3/s)
    data['q_device'] = (data['q_device']*0.00378541178)/60
    return data


def heat_from_ground(pfcf, data):
    # flow only counted when compressor is on
    data['q_device'] = np.where(data['compressor_1'] > 0.0, data['q_device'], 0.0)

    # see if flow was recorded while compressor was off
    data['false_flow'] = np.where(data['compressor_1'] == 0.0, data['q_device'], 0.0)

    # heat from ground (negative values-->heat withdrawn from ground)
    # entering and exiting temperatures are relative to heat pump
    data['DeltaT'] = data['leavingwatertemp']-data['enteringwatertemp']

    # heat transfer to/from ground (kilowatts)
    data['q'] = (data['DeltaT'] * pfcf * data['q_device'])/1000.0

    # convert electricity values from watts to kilowatts
    data['compressor_1'] = data['compressor_1']/1000.0
    data['looppumppower'] = data['looppumppower']/1000.0
    data['fanpower'] = data['fanpower']/1000.0

    return data


def to_kilowatts(data, derate):
    # btu/hr to kw
    data['q'] = derate*(0.29307107*data['heat_flow_1'])/1000
    data['q'].fillna(0.0, inplace=True)
    # w to kw
    data['kw_used'] = data['compressor_1']/1000
    data['enteringwatertemp'] = data['ewt_1']
    return data


def error_heat_from_ground(mrl_hr,E_deltaT,e_v,data):
    # fractional uncertainty temp difference
    data['e_deltaT'] = abs(E_deltaT/data['DeltaT'])

    # fractional uncertainty heat transfer rate
    data['e_q'] = ((e_v**2)+(data['e_deltaT']**2))**(0.5)

    # absolute uncertainty heat transfer rate
    data['E_q'] = data['e_q']*data['q']

    # elapsed time for each timestep
    data['tvalue'] = data.index
    data['timedelta'] = (data['tvalue']
                         - data['tvalue'].shift()).fillna(pd.Timedelta(seconds=0))

    # median time step to fill empty initial timestep
    mts = data['timedelta'].median()
    data.loc[data.index[0], 'timedelta'] = mts
    data['elapsed_hours'] = (data['timedelta'].dt.total_seconds())/(60*60)
    meh = data['elapsed_hours'].median()
    # set upper limit of elapsed hours
    data['elapsed_hours'] = data['elapsed_hours'].where(data['elapsed_hours']
                                                        <= mrl_hr, meh) 
    # absolute uncertainity in thermal energy (kWh)
    data['E_Q'] = data['E_q']*data['elapsed_hours']
    return data


def elec_error(e_e, data):
    # absolute error of compressor
    data['E_com'] = e_e * data['compressor_1']*data['elapsed_hours']
    # absolute error of fan
    data['E_fanp'] = e_e * data['fanpower']*data['elapsed_hours']
    # absolute error of loop pump
    data['E_lpp'] = e_e * data['looppumppower']*data['elapsed_hours']
    # absolute error for all electricity measurements
    data['E_w'] = ((data['E_com']**2)+(data['E_fanp']**2)
                                                      +(data['E_lpp']**2))**(0.5)
    return data


def elec_error_one(e_e, data):
    # no need to add in quadrature if single measurement
    # absolute electrical error
    data['E_w'] = data['kw_used']*data['elapsed_hours']*e_e
    heating_data = data.copy()
    cooling_data = data.copy()
    return heating_data, cooling_data


def spf_heating(data):
    # select heating rows (.copy() necessary to supress'SettingWithCopyWarning')
    spf_heat_data=data.loc[data['q'] < 0.0].copy()    
    # watts from compressor/fan (loop pump doesn't provide useful heat)
    spf_heat_data['elec_heat'] =(spf_heat_data['compressor_1']
                                               +spf_heat_data['fanpower'])
    # useful heat (kWh)
    spf_heat_data['heat_kWh_provided'] = (spf_heat_data['elapsed_hours']* 
                (abs(spf_heat_data['q']) +spf_heat_data['elec_heat']))
    # electricity used (kWh)
    spf_heat_data['electricity_kWh'] = (spf_heat_data['elapsed_hours']
            *(spf_heat_data['elec_heat'] + spf_heat_data['looppumppower']))
    return spf_heat_data


def spf_heating_one_elec(data):
    spf_heat_data = data

    # filter to only where heating occurs
    vals_to_filter = ['E_Q', 'E_w', 'kw_used', 'q']
    for i in range(len(vals_to_filter)):
        spf_heat_data[vals_to_filter[i]] = np.where(spf_heat_data['q'] > 0.0,
                                                    spf_heat_data[vals_to_filter[i]], 0.0)

    # electricity kWh in heating mode
    e_h_kwh = spf_heat_data['elapsed_hours'] * spf_heat_data['kw_used']

    spf_heat_data['electricity_kWh'] = e_h_kwh

    # useful heat in heating mode (kwh)
    h_h_kwh = (spf_heat_data['elapsed_hours'] *
               (spf_heat_data['q']+spf_heat_data['kw_used']))

    spf_heat_data['heat_kWh_provided'] = h_h_kwh

    # heat from ground
    spf_heat_data['hfg'] = spf_heat_data['q'] * spf_heat_data['elapsed_hours']

    return spf_heat_data


def spf_cooling(data):
    # select cooling rows(.copy() necessary to supress'SettingWithCopyWarning')
    spf_cool_data = data.loc[data['q'] < 0.0].copy()

    # watts from compressor/fan/loop_pump (subtracted from energy into ground)
    spf_cool_data['elec_heat'] = (spf_cool_data['compressor_1'] +
                                  spf_cool_data['looppumppower'] +
                                  spf_cool_data['fanpower'])

    # useful heat (kWh)
    spf_cool_data['cool_kWh_provided'] = (spf_cool_data['elapsed_hours'] *
                                          ((abs(spf_cool_data['q'])) - spf_cool_data['elec_heat']))

    # electricity used (kWh)
    spf_cool_data['electricity_kWh'] = (spf_cool_data['elapsed_hours'] *
                                        (spf_cool_data['elec_heat']))

    return spf_cool_data


def spf_cooling_one_elec(data):
    spf_cool_data = data

    # filter to only where cooling occurs
    vals_to_filter =  ['E_Q', 'E_w', 'kw_used','q']
    for i in range(len(vals_to_filter)):
        spf_cool_data[vals_to_filter[i]] = np.where(spf_cool_data['q'] < 0.0,
                                         spf_cool_data[vals_to_filter[i]], 0.0)

    # electricity kWh in cooling mode
    e_c_kwh = spf_cool_data['elapsed_hours'] * spf_cool_data['kw_used']
    spf_cool_data['electricity_kWh'] = e_c_kwh

    # useful heat in cooling mode (kwh)
    h_c_kwh = (spf_cool_data['elapsed_hours'] *
              (abs(spf_cool_data['q'])-spf_cool_data['kw_used']))
    spf_cool_data['cool_kWh_provided'] = h_c_kwh
   
    return spf_cool_data


def total_ground_heat(spf_heat_data):

    # total heat from ground (kWh)
    total_ground_heat = spf_heat_data['hfg'].sum()

    # total heat from ground absolute error
    total_gh_error = spf_heat_data['E_Q'].sum()
    
    return total_ground_heat, total_gh_error
    

def spf_heating_error_monthly(spf_heat_data):
    monthly_heating = spf_heat_data.resample('M').agg({'electricity_kWh': np.sum,
                                                       'heat_kWh_provided': np.sum,
                                                       'E_Q': np.sum, 'E_w': np.sum,
                                                       'enteringwatertemp': np.mean})
    # month and year column
    monthly_heating['year'] = monthly_heating.index.year
    monthly_heating = monthly_heating.astype({"year": str})
    monthly_heating['month_and_year'] = (monthly_heating.index.strftime('%b ') +
                                         monthly_heating['year'])

    # monthly heat provided fractional error
    monthly_heating['e_Q'] = (monthly_heating['E_Q'] /
                              monthly_heating['heat_kWh_provided'])

    # monthly electricity fractional error
    monthly_heating['e_W'] = (monthly_heating['E_w'] /
                              monthly_heating['electricity_kWh'])
    # monthly spf fractyional error
    monthly_heating['e_SPF'] = ((monthly_heating['e_Q']**2) +
                                (monthly_heating['e_W']**2))**(0.5)

    return monthly_heating 


def spf_heating_monthly(monthly_heating, percent_max):
    # filter out months with minimal cooling
    min_heat = monthly_heating['heat_kWh_provided'].max()*percent_max
    monthly_heating['heat_kWh_provided'] = np.where(monthly_heating['heat_kWh_provided'] < min_heat,
                                                    0.0, monthly_heating['heat_kWh_provided'])
    # filter values for monthly with minimal/no heating
    vals_to_filter = ['E_Q', 'E_w', 'electricity_kWh']
    for i in range(len(vals_to_filter)):
        monthly_heating[vals_to_filter[i]] = np.where(monthly_heating['heat_kWh_provided'] == 0.0,
                                                      0.0, monthly_heating[vals_to_filter[i]])
    # calculated spf
    monthly_heating['SPF'] = (monthly_heating['heat_kWh_provided']/
                              monthly_heating['electricity_kWh'])
    # Absolute Monthly error
    monthly_heating['error(+-)'] = (monthly_heating['SPF']
                                   * monthly_heating['e_SPF'])
    
    return monthly_heating 


def spf_cooling_error_monthly(spf_cool_data):
    monthly_cooling = spf_cool_data.resample('M').agg({'electricity_kWh': np.sum,
                                                       'cool_kWh_provided': np.sum,
                                                       'E_Q': np.sum, 'E_w': np.sum})

    # month and year column
    monthly_cooling['month_year'] = monthly_cooling.index.to_period('M')

    # monthly heat provided fractional error
    monthly_cooling['e_Q'] = (monthly_cooling['E_Q'] /
                              monthly_cooling['cool_kWh_provided'])

    # monthly electricity fractional error
    monthly_cooling['e_W'] = (monthly_cooling['E_w'] /
                              monthly_cooling['electricity_kWh'])

    # monthly spf fractional error
    monthly_cooling['e_SPF'] = ((monthly_cooling['e_Q']**2) +
                                (monthly_cooling['e_W']**2))**0.5
    return monthly_cooling


def spf_cooling_monthly(monthly_cooling, percent_max):
    # filter out months with minimal cooling
    min_cool = monthly_cooling['cool_kWh_provided'].max()*percent_max

    monthly_cooling['cool_kWh_provided'] = np.where(monthly_cooling['cool_kWh_provided']
                                                    < min_cool, 0.0, monthly_cooling['cool_kWh_provided'])

    # filter values for monthly with minimal/no heating
    vals_to_filter = ['E_Q', 'E_w', 'electricity_kWh']
    for i in range(len(vals_to_filter)):
        monthly_cooling[vals_to_filter[i]] = np.where(monthly_cooling['cool_kWh_provided'] 
                                                      == 0.0, 0.0, monthly_cooling[vals_to_filter[i]])

    # calculated spf
    monthly_cooling['SPF'] = (monthly_cooling['cool_kWh_provided'] /
                              monthly_cooling['electricity_kWh'])

    # Absolute Monthly error
    monthly_cooling['error(+-)'] = (monthly_cooling['SPF']
                                    * monthly_cooling['e_SPF'])
   
    return monthly_cooling 


'''
functions for spf as function of ewt
'''


def spf_cooling_by_EWT(spf_cool_data, Interval):
    ewt_spf_cool = spf_cool_data.resample(Interval).agg({'electricity_kWh': 
        np.sum, 'cool_kWh_provided': np.sum, 'E_Q': np.sum, 'E_w': np.sum, 
        'enteringwatertemp': np.mean})
    # month and year column
    ewt_spf_cool['spf'] = (ewt_spf_cool['cool_kWh_provided']
                           / ewt_spf_cool['electricity_kWh'])
    return ewt_spf_cool


def spf_heating_by_EWT(spf_heat_data, Interval):
    ewt_spf_heat = spf_heat_data.resample(Interval).agg({'electricity_kWh': 
        np.sum, 'heat_kWh_provided': np.sum, 'E_Q': np.sum, 'E_w': np.sum, 
        'enteringwatertemp': np.mean})
    # month and year column
    ewt_spf_heat['spf'] = (ewt_spf_heat['heat_kWh_provided']
                           / ewt_spf_heat['electricity_kWh'])
    return ewt_spf_heat

    

# plt.plot(data.index,data['DeltaT'])
# plt.xticks(rotation = 45)


# plt.plot(monthly_heating['enteringwatertemp'],
#           monthly_heating['SPF'],'bo')


