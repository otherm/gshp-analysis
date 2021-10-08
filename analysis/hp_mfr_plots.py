# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 12:44:35 2017

@author: Matt Davis

Notes of changes for otherm:

1. Read heat pump data from otherm db.  One value per temp

"""
import os
import datetime
import logging
import sys
import pprint
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
#import analysis.document_generation as doc_gen
from admin_tools.db_reader import get_symphony_data, MFR_data, get_fr_as_dataframe
from admin_tools import installation_settings as installation_settings
from utilities import misc_functions

mpl.use('Qt5Agg')
C_to_F = misc_functions.C_to_F


def mfr_pd_plots():
    MFR = None
    mfr_logger = logging.getLogger("mfr_plots_logger")
    mfr_logger.setLevel(logging.INFO)


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
            print(fig)
            print(axarr)
            for j in range(nrows):
                for i in range(ncols):
                    EWTlist = np.linspace(EWT_min[i], EWT_max[i],
                                          num=25, endpoint=True)
                    X = np.asarray(EWTlist)
                    for k in range(2):
                        Y = X * slopes[i][j][k] + intercepts[i][j][k]
                        print(i,j,k)
                        print(slopes[i][j][k], intercepts[i][j][k])
                        axarr[i,j].plot(X, Y, color=linecolor[i][j][k])
                    axarr[i, j].set_title(graph_header[i][j])
                    axarr[i, j].set_ylim(ymin[i][j], ymax[i][j])

            axarr[0,0].set_ylabel("Measured kW")
            axarr[1,0].set_ylabel("Measured kW")
            axarr[0,1].set_ylabel("Measured HE [MBtuH]")
            axarr[1,1].set_ylabel("Measured HR [MBtuH]")
            axarr[1,0].set_xlabel("Measured Entering WaterTemperature [$^\circ$F]")
            axarr[1,1].set_xlabel("Measured Entering Water Temperature [$^\circ$F]")

            return fig, axarr

    def get_xy(X, Y):
        x = np.asarray(X[~np.isnan(Y)])
        y = np.asarray(Y[~np.isnan(Y)])
        x = C_to_F(x)
        y = y / 1000.
        return x, y


    def plots_and_stats(installation_id, year, return_dictionary=False):
        """
        System and analysis parameters
        """
        return_dict = {}
        start = datetime.datetime(year, 1, 1)
        stop = datetime.datetime(year, 12, 31)

        if len(sys.argv) > 1:
            start = eval("datetime.datetime(" + sys.argv[1] + ")")
            stop = eval("datetime.datetime(" + sys.argv[2] + ")")
            infer_stage = sys.argv[3]
            installation_id = sys.argv[4]

        mfr_logger.info("Using params: %s to %s on %s" % (str(start), str(stop),
                                                          installation_id))

        try:
            info = installation_settings.ghp_info(installation_id)
        except IndexError:
            mfr_logger.warning('Installation id does not exist; Stopping')
            return

        '''
        Retrieve chunk of operating data
        '''
        if info.monitoring_sys == 'Symphony':
            columns = ['EWT', 'LWT', 'VC', 'WC', 'QL', 'created']
            data = get_symphony_data(installation_id, start,
                                     stop, columns)
        else:
            column_items = ['ewt_1', 'lwt_1', 'r_1_on', 'compressor_1',
                            'heat_flow_1', 'created', 'auxiliary_1']
            columns = ", ".join(column_items)
            data = get_fr_as_dataframe(installation_id, start,
                                       stop, columns)
        if len(data) > 1000:
            data = data[np.isfinite(data['heat_flow_1'])]
        else:
            mfr_logger.warning('Insufficient data for Installation %s'
                               % installation_id)
            return

        HP_ids = [str(info.HP_model) + '_PL', str(info.HP_model) + '_FL']

        # currently reads performance data from Digital Ocean db.
        # TODO:  update to local sqlite db;  exclude sqlite db from commit
        mfr_pl, mfr_fl = MFR_data(HP_ids)

        '''
        Use mfr data to initialize heat pump object (on global scope)
        '''
        global MFR
        MFR = MfrDualStage(mfr_pl, mfr_fl)

        data['heatpump_1'] = data['compressor_1'] - info.c_pumps_watts

        '''
        Determine on/off, heating/cooling
        '''

        htg = data.query('heat_flow_1 >  500')
        clg = data.query('heat_flow_1 <= -500')

        modes = [htg, clg]
        keys = ['htg', 'clg']
        plots = True
        summary_stats = True
        flow_stats = {}
        i = 0
        if summary_stats:
            '''
            Generate metrics comparing observed to expected
    
                    Still need to add uncertainty (random variable) to observations
                    kW_u, HE_u, and/or HR_u and compare observed kW_e, HE_e, HR_e
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
                ewt_F = np.asarray(C_to_F(mode['ewt_1']))
                kW_obs = np.asarray(mode['compressor_1']) / 1000.
                kW_mfg = ((9. / 5.) * np.asarray(mode['ewt_1']) +
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
            print ('Power Statistics')
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
                ewt_F = np.asarray(C_to_F(mode['ewt_1']))
                geo_obs = abs(np.asarray(mode['heat_flow_1']) / 1000.)
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
            print ('GeoExchange Statistics')
            pprint.pprint(geo_stats)


        if plots:
            '''
            Create figure for kW vs EWT and HE/HR vs. EWT.  Four subplots in all
            '''
            fig2, axarr2 = MFR.kw_geo_graphs()

            title_text1 = ('kW and GeoExchange for Installation ' +
                           str(installation_id))

            plt.suptitle(title_text1)

            x, y = get_xy(htg['ewt_1'], htg['heatpump_1'])

            axarr2[0,0].scatter(x, y, color='tomato', s=0.1)

            x, y = get_xy(clg['ewt_1'], clg['heatpump_1'])
            axarr2[1,0].scatter(x, y, color='c', s=0.1)

            x, y = get_xy(htg['ewt_1'], htg['heat_flow_1'])
            axarr2[0,1].scatter(x, y, color='tomato', s=0.1)

            x, y = get_xy(clg['ewt_1'], -clg['heat_flow_1'])
            axarr2[1,1].scatter(x, y, color='c', s=0.1)

            ymin = [[0, 0],
                    [0, 0]]
            ymax = [[5, 50],
                    [5, 60]]
            for i in range(2):
                for j in range(2):
                    axarr2[i, j].set_ylim(ymin[i][j], ymax[i][j])

            fig = plt.gcf()
            imagefile = os.path.join(os.path.dirname(doc_gen.__file__),
                                     '{}_{}_mfrPD_kW-gx_scatter.png'.format(installation_id, year))
            print ('saving.... ', imagefile)
            plt.savefig(imagefile, dpi=300)
            plt.close()

        if return_dictionary:
            return return_dict


if __name__ == '__main__':
    installs = ['45', '1649', '1659', '1674', '1692', '1695', 's44',
                's7', 's40', 's22', 's35', 's38', 's44', 's23']
    installs = ['1649']
    # TODO:  update to being a command line tool with input arguments of installation_id and year
    for installation_id in installs:
        print ('Working on ..hp_mfr_plots...   ', installation_id)
        main(installation_id, 2016)