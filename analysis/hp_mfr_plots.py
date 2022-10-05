# -*- coding: utf-8 -*-
"""
@author: Matt Davis

"""
import os
from datetime import date
import pprint
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import pandas as pd
from db_tools import otherm_db_reader

from utilities import misc_functions

mpl.use('Qt5Agg')

C_to_F = misc_functions.C_to_F


def get_mfr_data(heat_pump):
    db_name = os.path.join('../temp_files/MfrPD.db')
    mfr_db_con = sqlite3.connect(db_name)
    sql = """SELECT * from '%s' """ % heat_pump
    pd_table = pd.read_sql(sql, mfr_db_con)
    mfr_db_con.close()
    return pd_table


def mfr_data(HP_ids):
    mfr_pl = get_mfr_data(HP_ids[0])

    mfr_pl['EWT [F]'] = pd.Series(mfr_pl['EWT [F]']).fillna(method='ffill')
    mfr_pl['Flow [GPM]'] = pd.Series(mfr_pl['Flow [GPM]']).fillna(method='ffill')

    mfr_fl = get_mfr_data(HP_ids[1])

    mfr_fl['EWT [F]'] = pd.Series(mfr_fl['EWT [F]']).fillna(method='ffill')
    mfr_fl['Flow [GPM]'] = pd.Series(mfr_fl['Flow [GPM]']).fillna(method='ffill')

    return mfr_pl, mfr_fl


def get_xy(X, Y):
    x = np.asarray(X[~np.isnan(Y)])
    y = np.asarray(Y[~np.isnan(Y)])
    x = C_to_F(x)
    y = y / 1000.
    return x, y


MFR = None


class MfrDualStage:
    slopes_dict = {}

    def __init__(self, mfr_pl, mfr_fl):
        self.set_he_ewt(mfr_pl, mfr_fl)
        self.set_kw_h_c(mfr_pl, mfr_fl)

        self.qmin = mfr_pl['Flow [GPM]'].min()
        self.qmax = mfr_fl['Flow [GPM]'].max()

    def set_he_ewt(self, mfr_pl, mfr_fl):
        HE_EWT_PL = mfr_pl.groupby('EWT [F]').mean()['HE [Mbtuh]']
        HE_EWT_PL.dropna(axis=0, inplace=True)
        HR_EWT_PL = mfr_pl.groupby('EWT [F]').mean()['HR [Mbtuh]']
        HR_EWT_PL.dropna(axis=0, inplace=True)

        HE_EWT_FL = mfr_fl.groupby('EWT [F]').mean()['HE [Mbtuh]']
        HE_EWT_FL.dropna(axis=0, inplace=True)
        HR_EWT_FL = mfr_fl.groupby('EWT [F]').mean()['HR [Mbtuh]']
        HR_EWT_FL.dropna(axis=0, inplace=True)

        HE_PL_m = (HE_EWT_PL.values[-1] - HE_EWT_PL.values[0]) / (
            HE_EWT_PL.keys()[-1] - HE_EWT_PL.keys()[0])
        HR_PL_m = (HR_EWT_PL.values[-1] - HR_EWT_PL.values[0]) / (
            HR_EWT_PL.keys()[-1] - HR_EWT_PL.keys()[0])
        HE_FL_m = (HE_EWT_FL.values[-1] - HE_EWT_FL.values[0]) / (
            HE_EWT_FL.keys()[-1] - HE_EWT_FL.keys()[0])
        HR_FL_m = (HR_EWT_FL.values[-1] - HR_EWT_FL.values[0]) / (
            HR_EWT_FL.keys()[-1] - HR_EWT_FL.keys()[0])

        # The multiplier of 0.7 is use to adjust HR for latent heat component (not
        # rejected to the ground).  Could be more refined using Sensible Cooling
        # performance data but would need to add kW from compressor, making it quite
        # a bit more complicated

        HE_PL_b = float(HE_EWT_PL.values[-1]) - HE_PL_m * HE_EWT_PL.keys()[-1]
        HR_PL_b = 0.7*(float(HR_EWT_PL.values[-1]) - HR_PL_m * HR_EWT_PL.keys()[-1])
        HE_FL_b = float(HE_EWT_FL.values[-1]) - HE_FL_m * HE_EWT_FL.keys()[-1]
        HR_FL_b = 0.7*(float(HR_EWT_FL.values[-1]) - HR_FL_m * HR_EWT_FL.keys()[-1])

        self.slopes_dict.update({'HE_EWT_PL': HE_EWT_PL,
                                 'HE_EWT_FL': HE_EWT_FL,
                                 'HE_PL_m': HE_PL_m,
                                 'HE_PL_b': HE_PL_b,
                                 'HE_FL_b': HE_FL_b,
                                 'HE_FL_m': HE_FL_m,
                                 'HR_EWT_PL': HR_EWT_PL,
                                 'HR_EWT_FL': HR_EWT_FL,
                                 'HR_PL_m': HR_PL_m,
                                 'HR_FL_b': HR_FL_b,
                                 'HR_FL_m': HR_FL_m,
                                 'HR_PL_b': HR_PL_b})

    def set_kw_h_c(self, mfr_pl, mfr_fl):
        kW_h_PL = mfr_pl.groupby('EWT [F]').mean()['HE kW']
        kW_h_PL.dropna(axis=0, inplace=True)
        kW_c_PL = mfr_pl.groupby('EWT [F]').mean()['HR kW']
        kW_c_PL.dropna(axis=0, inplace=True)

        kW_h_FL = mfr_fl.groupby('EWT [F]').mean()['HE kW']
        kW_h_FL.dropna(axis=0, inplace=True)
        kW_c_FL = mfr_fl.groupby('EWT [F]').mean()['HR kW']
        kW_c_FL.dropna(axis=0, inplace=True)

        kW_h_PL_m = (kW_h_PL.values[-1] - kW_h_PL.values[0]) / (
            kW_h_PL.keys()[-1] - kW_h_PL.keys()[0])
        kW_c_PL_m = (kW_c_PL.values[-1] - kW_c_PL.values[0]) / (
            kW_c_PL.keys()[-1] - kW_c_PL.keys()[0])
        kW_h_FL_m = (kW_h_FL.values[-1] - kW_h_FL.values[0]) / (
            kW_h_FL.keys()[-1] - kW_h_FL.keys()[0])
        kW_c_FL_m = (kW_c_FL.values[-1] - kW_c_FL.values[0]) / (
            kW_c_FL.keys()[-1] - kW_c_FL.keys()[0])

        kW_h_PL_b = float(kW_h_PL.values[-1]) - kW_h_PL_m * kW_h_PL.keys()[-1]
        kW_c_PL_b = float(kW_c_PL.values[-1]) - kW_c_PL_m * kW_c_PL.keys()[-1]
        kW_h_FL_b = float(kW_h_FL.values[-1]) - kW_h_FL_m * kW_h_FL.keys()[-1]
        kW_c_FL_b = float(kW_c_FL.values[-1]) - kW_c_FL_m * kW_c_FL.keys()[-1]

        self.slopes_dict.update({'kW_h_PL': kW_h_PL,
                                 'kW_c_PL': kW_c_PL,
                                 'kW_h_FL': kW_h_FL,
                                 'kW_c_FL': kW_c_FL,
                                 'kW_h_PL_m': kW_h_PL_m,
                                 'kW_h_FL_m': kW_h_FL_m,
                                 'kW_c_FL_m': kW_c_FL_m,
                                 'kW_c_PL_m': kW_c_PL_m,
                                 'kW_h_PL_b': kW_h_PL_b,
                                 'kW_c_PL_b': kW_c_PL_b,
                                 'kW_h_FL_b': kW_h_FL_b,
                                 'kW_c_FL_b': kW_c_FL_b})

    def kw_geo_graphs(self):
        slopes = [[[self.slopes_dict['kW_h_PL_m'], self.slopes_dict['kW_h_FL_m']],
                  [self.slopes_dict['HE_PL_m'], self.slopes_dict['HE_FL_m']]],
                  [[self.slopes_dict['kW_c_PL_m'], self.slopes_dict['kW_c_FL_m']],
                  [self.slopes_dict['HR_PL_m'], self.slopes_dict['HR_FL_m']]]]
        intercepts = [[[self.slopes_dict['kW_h_PL_b'], self.slopes_dict['kW_h_FL_b']],
                      [self.slopes_dict['HE_PL_b'], self.slopes_dict['HE_FL_b']]],
                      [[self.slopes_dict['kW_c_PL_b'], self.slopes_dict['kW_c_FL_b']],
                      [self.slopes_dict['HR_PL_b'], self.slopes_dict['HR_FL_b']]]]
        linecolor = [[['lightsalmon', 'r'],
                      ['lightsalmon', 'r']],
                     [['dodgerblue', 'b'],
                      ['dodgerblue', 'b']]]
        ymin = [[[self.slopes_dict['kW_h_PL'].min(), self.slopes_dict['kW_c_PL'].min()]],
                [[self.slopes_dict['HE_EWT_PL'].min(), self.slopes_dict['HR_EWT_PL'].min()]]]
        ymax = [[self.slopes_dict['kW_h_FL'].max(), self.slopes_dict['HR_EWT_FL'].max()],
                [self.slopes_dict['kW_c_FL'].max(), self.slopes_dict['HR_EWT_FL'].max()]]
        ymin = [[0, 0],
                [0, 0]]
        ymax = [[10, 80],
                [5, 80]]

        EWT_min = [25, 40, 35, 35]  # [25,45]
        EWT_max = [65, 80, 95, 95]  # [65,90]

        graph_header = [['Heating kW v. EWT', 'Heat Extraction v. EWT'],
                        ['Cooling kW v. EWT', 'Heat Rejection v. EWT']]

        nrows = 2
        ncols = 2

        fig, axarr = plt.subplots(nrows=nrows, ncols=ncols, figsize=(8, 6))
        for j in range(nrows):
            for i in range(ncols):
                EWTlist = np.linspace(EWT_min[i], EWT_max[i],
                                      num=25, endpoint=True)
                X = np.asarray(EWTlist)
                for k in range(2):
                    Y = X * slopes[i][j][k] + intercepts[i][j][k]
                    axarr[i, j].plot(X, Y, color=linecolor[i][j][k])
                axarr[i, j].set_title(graph_header[i][j])
                axarr[i, j].set_ylim(ymin[i][j], ymax[i][j])

        axarr[0, 0].set_ylabel("Measured kW")
        axarr[1, 0].set_ylabel("Measured kW")
        axarr[0, 1].set_ylabel("Measured HE [MBtuH]")
        axarr[1, 1].set_ylabel("Measured HR [MBtuH]")
        axarr[1, 0].set_xlabel("Measured Entering WaterTemperature [$^\circ$F]")
        axarr[1, 1].set_xlabel("Measured Entering Water Temperature [$^\circ$F]")

        return fig, axarr


def plots_and_stats(site, equipment, data):
    """
    System and analysis parameters
    """

    '''
    Retrieve chunk of operating data
    '''
    if len(data) > 1000:
        data = data[np.isfinite(data['heat_flow_rate'])]
    else:
        print('Insufficient data for Site %s,  %s' % (site.name, equipment.model))
        return

    HP_table_name = {'HXT036': ['Hydron_HXT_036_PL', 'Hydron_HXT_036_FL']}
    
    HP_ids = HP_table_name[equipment.model]

    mfr_pl, mfr_fl = mfr_data(HP_ids)

    '''
    Use mfr data to initialize heat pump object (on global scope)
    '''
    global MFR
    MFR = MfrDualStage(mfr_pl, mfr_fl)

    c_pumps_watts = 0.
    
    data['heatpump_power_adj'] = data['heatpump_power'] - c_pumps_watts

    '''
    Determine on/off, heating/cooling
    '''
    htg = data.query('heat_flow_rate >  500')
    clg = data.query('heat_flow_rate <= -500')

    modes = [htg, clg]
    keys = ['htg', 'clg']
    plots = True
    summary_stats = True
    flow_stats = {}
    i = 0
    if summary_stats:
        '''
        Generate metrics comparing observed to expected
        '''
        # ----------------------
        # Power usage statistics
        # ----------------------
        # kW_keys = ['N', 'kW_obs_avg', 'kW_mfg_avg', 'kW_ratio']
        kW_stats = {}
        slopes = [MFR.slopes_dict['kW_h_PL_m'],
                  MFR.slopes_dict['kW_h_FL_m'],
                  MFR.slopes_dict['kW_c_PL_m'],
                  MFR.slopes_dict['kW_c_FL_m']]
        intercepts = [MFR.slopes_dict['kW_h_PL_b'],
                      MFR.slopes_dict['kW_h_FL_b'],
                      MFR.slopes_dict['kW_c_PL_b'],
                      MFR.slopes_dict['kW_c_FL_b']]

        i = 0
        for mode in modes:
            ewt_F = np.asarray(C_to_F(mode['source_supplytemp']))
            kW_obs = np.asarray(mode['heatpump_power']) / 1000.
            kW_mfg = ((9. / 5.) * np.asarray(mode['source_supplytemp']) +
                      32) * slopes[i] + intercepts[i]
            if kW_obs.any():
                kW_detrended = (abs(kW_obs) - (ewt_F * slopes[i] +
                                               intercepts[i]))
                noise = np.var(100 * kW_detrended) / np.var(ewt_F)
            else:
                print ('no results to compute statistics')
            kW_stats.update({keys[i]: {'N': len(kW_obs),
                                       'kW_obs_avg': round(kW_obs.mean(), 2),
                                       'kW_mfg_avg': round(kW_mfg.mean(), 2),
                                       'kW_ratio': round((kW_obs.mean() /
                                                          kW_mfg.mean()), 2),
                                       'kW_noise': round(noise, 2)
                                       }})

            i += 1
        print('Power Statistics')
        pprint.pprint(kW_stats)

        # ----------------------
        # GeoExchange statistics
        # ----------------------
        geo_stats = {}
        slopes = [MFR.slopes_dict['HE_PL_m'],
                  MFR.slopes_dict['HE_FL_m'],
                  MFR.slopes_dict['HR_PL_m'],
                  MFR.slopes_dict['HR_FL_m']]
        intercepts = [MFR.slopes_dict['HE_PL_b'],
                      MFR.slopes_dict['HE_FL_b'],
                      MFR.slopes_dict['HR_PL_b'],
                      MFR.slopes_dict['HR_FL_b']]

        i = 0
        for mode in modes:
            ewt_F = np.asarray(C_to_F(mode['source_supplytemp']))
            geo_obs = abs(np.asarray(mode['heat_flow_rate']) / 1000.)
            geo_mfg = ewt_F * slopes[i] + intercepts[i]
            if geo_obs.any():
                geo_detrended = (abs(geo_obs) - (ewt_F * slopes[i] +
                                                 intercepts[i]))
                noise = np.var(geo_detrended) / np.var(ewt_F)
            else:
                print ('no results to compute Noise statistic')
            geo_stats.update({keys[i]: {'N': len(geo_obs),
                                        'geo_obs_avg': round(geo_obs.mean(), 2),
                                        'geo_mfg_avg': round(geo_mfg.mean(), 2),
                                        'geo_ratio': round((geo_obs.mean() /
                                                            geo_mfg.mean()), 2),
                                        'geo_noise': round(noise, 2)
                                        }})

            i += 1
        print('GeoExchange Statistics')
        pprint.pprint(geo_stats)


    if plots:
        '''
        Create figure for kW vs EWT and HE/HR vs. EWT.  Four subplots in all
        '''
        fig2, axarr2 = MFR.kw_geo_graphs()

        title_text1 = ('kW and GeoExchange for Site %s,  %s' % (site.name, equipment.model))

        plt.suptitle(title_text1)

        x, y = get_xy(htg['source_supplytemp'], htg['heatpump_power_adj'])

        axarr2[0,0].scatter(x, y, color='tomato', s=0.1)

        x, y = get_xy(clg['source_supplytemp'], clg['heatpump_power_adj'])
        axarr2[1,0].scatter(x, y, color='c', s=0.1)

        x, y = get_xy(htg['source_supplytemp'], htg['heat_flow_rate'])
        axarr2[0, 1].scatter(x, y, color='tomato', s=0.1)

        x, y = get_xy(clg['source_supplytemp'], -clg['heat_flow_rate'])
        axarr2[1, 1].scatter(x, y, color='c', s=0.1)

        ymin = [[0, 0],
                [0, 0]]
        ymax = [[5, 50],
                [5, 60]]
        for i in range(2):
            for j in range(2):
                axarr2[i, j].set_ylim(ymin[i][j], ymax[i][j])

        fig = plt.gcf()
        fig_name = '../temp_files/hp_mfr_plots_{}_{}.png'.format(site.name, str(date.today().strftime("%m-%d-%y")))
        print(fig_name)
        plt.savefig(fig_name)
        return fig_name
        plt.close()


if __name__ == '__main__':
    site_name = '111520'
    start = '2021-07-01'
    end = '2022-06-30'
    timezone = 'US/Eastern'
    db = 'otherm_cgb'
    #db = 'localhost'

    site = otherm_db_reader.get_site_info(site_name, db)
    equipment = otherm_db_reader.get_equipment(site.id, db)
    hp_data = otherm_db_reader.get_equipment_data(site.id, start, end, site.timezone, db)
    print(hp_data.columns)
    plots_and_stats(site, equipment, hp_data)