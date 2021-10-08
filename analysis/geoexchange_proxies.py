import admin_tools.db_reader as db_reader
import datetime
import pandas as pd


def C_to_F(C):
    F = (9. / 5) *C  + 32.
    return F


def rec_calc_prep(df):
    df.loc[:, 'ewt'] = C_to_F(df.loc[:, 'ewt_1'])
    df.loc[:, 'lwt'] = C_to_F(df.loc[:, 'lwt_1'])
    df.loc[:, 'delT'] = df.loc[:, 'ewt'] - df.loc[:, 'lwt']

    data_heating = df.loc[data.delT > 1]
    data_running = data_heating[data_heating.compressor_1 > 500]
    data_final = data_running[data_running.time_elapsed < 0.08333]
    data_final.loc[:, 'heat_MWh'] = (500 * data_final.loc[:, 'delT']
                                     * data_final.loc[:, 'q_1_device']
                                     * data_final.loc[:, 'time_elapsed']
                                     * 2.93E-07)
    return data_final


def ma_thermal_recs(data, ma_hp_params):

    data_ma = pd.DataFrame()
    a = ma_hp_params['COP-ewt'][0]
    b = ma_hp_params['COP-ewt'][1]
    c = ma_hp_params['COP-ewt'][2]

    # Calculate table look up of COP based on EWT'
    data.loc[:, 'COPewt'] = a * data.loc[:, 'ewt'] * data.loc[:, 'ewt'] + b * data.loc[:, 'ewt'] + c

    data.loc[:, 'kW'] = data.loc[:, 'compressor_1'] /1000. * ma_hp_params['kw_bias'] - ma_hp_params['circ-pump-kw']
    data_ma.loc[:, 'RH'] = (data.loc[:, 'COPewt'] - 1) * data.loc[:, 'kW'] * data.loc[:, 'time_elapsed']
    #conversion to MWh
    return data_ma/1000.


def nh_thermal_recs(data, heatpump_AHRI):
    data_nh = pd.DataFrame()
    data_nh.loc[:, 'nh_rec'] = (data.loc[:, 'time_elapsed']
                                * heatpump_AHRI['hc_part_load'] * (heatpump_AHRI['cop']-1.)/heatpump_AHRI['cop'])
    #conversion to MWh
    return data_nh*2.93E-07


if __name__ == '__main__':
    installs = {'1649': 'none'}
    start = datetime.datetime(2016, 1, 1)
    stop = datetime.datetime(2016, 12, 31)


    # Hardwired for specific heat pump
    nh_heatpump_AHRI = {'install_id': '1649', 'model': 'HXT036', 'cop': 4.9, 'hc_part_load': 22600, 'hc_full_load': 28600}
    #nh_heatpump_AHRI = {'install_id': '45', 'model': 'HXT048', 'cop': 4.3, 'hc_part_load': 29700, 'hc_full_load':33700}
    # nh_heatpump_AHRI = {'install_id': '1674', 'model': 'NDH038', 'cop': 4.8, 'hc_part_load': 22900, 'hc_full_load': 28500}
    #nh_heatpump_AHRI = {'install_id': '1660', 'model': 'NDV072', 'cop': 3.9, 'hc_part_load': 47400, 'hc_full_load': 55400}
    ma_hp_parameters = {'install_id': '1649', 'COP-ewt': [-0.0013, 0.1361, 0.619], 'circ-pump-kw': 0.2, 'kw_bias': 1.15}
    #ma_hp_parameters = {'install_id': '45', 'COP-ewt': [-0.0003, 0.0758, 1.498] , 'circ-pump-kw': 0.4, 'kw_bias': 1.00}
    # ma_hp_parameters = {'install_id': '1674', 'COP-ewt': [0.00, 0.05, 2.2], 'circ-pump-kw': 0.2, 'kw_bias': 1.00}
    #ma_hp_parameters = {'install_id': '1660', 'COP-ewt': [0.0003, 0.0154, 2.586], 'circ-pump-kw': 0.0, 'kw_bias': 1.15}

    db_columns = 'ewt_1, lwt_1, compressor_1, created, q_1_device, auxiliary_1, time_elapsed'
    for install, hp_uuid in installs.items():
        print('Working on ..geoexchange proxies..   ', install)

        data = db_reader.get_fr_as_dataframe(install, start, stop, db_columns)
        data.sort_values('created', inplace=True)
        df = rec_calc_prep(data)

        nh_recs = nh_thermal_recs(df, nh_heatpump_AHRI)

        ma_recs = ma_thermal_recs(df, ma_hp_parameters)

        results = {'NH RECs': nh_recs.sum(),
                   'MA AECs': ma_recs.sum(),
                   'Measured': df.heat_MWh.sum()}

if __name__ == '__main__':
    installation_id = 'GES649'
    start_date = '2015-01-01'
    end_date = '2016-01-01'

    start = datetime.datetime(2016, 1, 1)
    stop = datetime.datetime(2016, 12, 30)