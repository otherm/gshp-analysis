"""
Reads data from PostgreSQL database, maps onto oTherm data fields,
and outputs .dat file using the influx line protocol
"""

import configuration
import datetime
import numpy as np
import psycopg2
import pandas as pd
from itertools import repeat
from datetime import datetime
import os
from db_tools import fetch_weather_data
import matplotlib.pyplot as plt

def get_ges_data_for_influx(installation_id, start, end, msp_columns, data_source):
    """
    Retrieves data from a PostgreSQL database.

    :param int installation_id:  site identifier in target database
    :param date start: start date (e.g. 2018-01-0)
    :param date end: end date (e.g. 2018-12-31)
    :param str msp_columns: list of columns for the SQL query (see below)

    :return:   *pandas.DataFrame*  containing data records.

    .. note::

       msp_columns for SQL query are a single *str* representing a comma separated list,
       such as::

            'ewt, lwt, compressor, created, flow_rate, auxiliary, outdoor_temperature'

    .. note::
       For the purposes of writing the line-protocol files, the DataFrame does **not** have a DatetimeIndex

    """
    parameters = (msp_columns, str(installation_id),
                  start.strftime('%Y-%m-%d 00:00:00%z'),
                  end.strftime('%Y-%m-%d 00:00:00%z'))

    if data_source == 'unh':
        unh_db = configuration.UNH
        db_read = psycopg2.connect(**unh_db)
        sql = """SELECT %s from results_flattenedresponse WHERE installation_id = %s
        and created BETWEEN TIMESTAMPTZ '%s' AND TIMESTAMPTZ '%s'""" % parameters
    elif data_source == 'ges':
        ges_db = configuration.GES
        db_read = psycopg2.connect(**ges_db)
        sql = """SELECT %s FROM results_wattresponse w INNER JOIN results_flattenedresponse fr ON w.response_id = fr.id
        WHERE fr.installation_id = %s AND created BETWEEN TIMESTAMPTZ '%s' AND TIMESTAMPTZ
        '%s' ORDER BY fr.created """ % parameters
    data = pd.read_sql(sql, db_read)
    data.sort_values('created', inplace=True)
    #Influx doesn't support NaNs so replace with large negative number (-999)
    data.fillna(-999, axis=1, inplace=True)
    db_read.close()
    return data

'''
def get_ges_data_for_influx(installation_id, start, end, msp_columns):
    """
    Retrieves data from a PostgreSQL database.

    :param int installation_id:  site identifier in target database
    :param date start: start date (e.g. 2018-01-01)
    :param date end: end date (e.g. 2018-12-31)
    :param str msp_columns: list of columns for the SQL query (see below)

    :return:   *pandas.DataFrame*  containing data records for the columns in ``msp_columns``.

    .. note::

       msp_columns for SQL query are a single *str* representing a comma separated list,
       such as::

            'ewt, lwt, compressor, created, flow_rate, auxiliary, outdoor_temperature'

    .. note::
       For the purposes of writing the line-protocol files, the DataFrame does **not** have a DatetimeIndex

    """
    ges = configuration.GES
    db_read = psycopg2.connect(**ges)
    parameters = (msp_columns, str(installation_id),
                  start.strftime('%Y-%m-%d 00:00:00%z'),
                  end.strftime('%Y-%m-%d 00:00:00%z'))

    #sql = """SELECT %s from results_flattenedresponse WHERE installation_id = %s
    #and created BETWEEN TIMESTAMPTZ '%s' AND TIMESTAMPTZ '%s'""" % parameters

    sql = """SELECT %s FROM results_wattresponse w INNER JOIN results_flattenedresponse fr ON w.response_id = fr.id
    WHERE fr.installation_id = %s AND created BETWEEN TIMESTAMPTZ '%s' AND TIMESTAMPTZ
    '%s' ORDER BY fr.created """ % parameters

    data = pd.read_sql(sql, db_read)
    data.sort_values('created', inplace=True)
    db_read.close()
    return data
'''

def write_files(db_name, tag, uuid, df, column_mapping, chunk_size, j):
    """ Takes heat pump operating data as pandas dataframe and writes to datafile
    using influx line protocol.

    :param str db_name: Name of the influx database, default is 'otherm-data'
    :param str uuid:  oTherm uuid of the thermal equipment, this is that influx db tag
    :param pandas.DataFrame df: Monitoring system data
    :param dict column_mapping: Mapping of monitoring system column names to standardized oTherm column names
    :param int chunk_size: Number of lines in each chunk file, recommended value is 8000
    :param int j: Index for heat pump number at site (e.g. 1, 2, 3, etc.)
    :return: Function produces a set of line-protocol text files

    The influx db line protocol consists of three *space delimited* elements: (1) a comma delimited pair of \
    the database name and the measurement tag, (2) a comma delimited list of fields and values (no spaces), and (3) \
    a timestamp in epoch time.  For example, with spaces shown with `|_|`:

    ``otherm-data,equipment=59468786-1ab3-4203-82d9-78f480ce0600|_|\
    source_supplytemp=6.88,source_returntemp=4.59,heatpump_power=2100.0|_|1454768864``

    There is one line for each record.

    """

    df.rename(mapper=column_mapping, inplace=True, axis=1)
    line_reference = ",".join([db_name, "=".join(['equipment', uuid])])
    columns = df.columns.tolist()
    chunks = int(len(df)/chunk_size)
    df_split = np.array_split(df, chunks)
    print(len(df_split))
    for i in range(len(df_split)):
        lp_file_name = ['C:\\Llano\\oTherm_CTGB_chunks\\'+ db_name, tag, str(j), ('chunk_%d.txt' % i)]
        lp_file_for_chunk = open("_".join(lp_file_name), 'w')
        for index, row in df_split[i].iterrows():
            measures = []
            for column in columns:
                if column != 'created':
                    measures.append("=".join([column, str(row[column])]))
                data_elements = ','.join(measures)
                if 'created' in columns:
                    timestamp = str(row.created.timestamp()).split('.')[0]
                else:
                    timestamp = str(datetime.timestamp(index)).split('.')[0]
            lp_line = " ".join([line_reference, data_elements, timestamp, '\n'])
            lp_file_for_chunk.write(lp_line)
        lp_file_for_chunk.flush()
        lp_file_for_chunk.close()
    return

def get_symphony_data(datafile):
    ds_data = pd.read_csv(datafile, parse_dates=True, index_col=0)
    ds_data.index = pd.to_datetime(ds_data.index, utc=True)
    ds_data['enteringwatertemp'] = (ds_data['enteringwatertemp'] - 32.)*(5./9.)
    ds_data['leavingwatertemp'] = (ds_data['leavingwatertemp'] - 32.)*(5./9.)
    ds_data.fillna(-999, axis=1, inplace=True)
    return ds_data

def get_enertech_data(datafile):
    et_data = pd.read_csv(datafile, parse_dates=True, index_col=0)
    # forward fill
    # temperature unit conversion
    return et_data

def get_dandelion_data(datafile):

    de_data_tz_naive = pd.read_csv(datafile, ['time_represented'], index_col=1)
    de_data = de_data_tz_naive.tz_localize(tz='US/Eastern', ambiuous='infer')
    #temperature unit conversion

    return de_data


if __name__ == '__main__':
    import ctgb_ges_installs
    import ctgb_wf_installs
    import ctgb_de_installs

    ges_installs = ctgb_ges_installs.installs
    wf_installs = ctgb_wf_installs.installs
    de_installs = ctgb_de_installs.installs

    data_source = 'de'
    db_name = 'otherm-data'

    chunk_size = 8000

    if data_source =='ges':
        start = datetime(2022, 4, 2)
        stop = datetime(2022, 8, 31)
        for install in ges_installs:
            #start = datetime.strptime(ges_installs[install]['start'], '%Y-%m-%d')
            for i in range(len(ges_installs[install]['hp_id'])):
                hp_uuid = ges_installs[install]['hp_id'][i]
                j = i+1
                msp_columns = 'ewt_%d, lwt_%d, compressor_%d, created, q_%d_device, auxiliary_%d, outdoor_temperature' % tuple(repeat(j, 5))

                column_mapping = {"auxiliary_%d" % j: "heatpump_aux",
                                  "compressor_%d" % j: "heatpump_power",
                                  "lwt_%d" % j: "source_returntemp",
                                  "ewt_%d" % j: "source_supplytemp",
                                  "q_%d_device" % j: "sourcefluid_flowrate",
                                  "outdoor_temperature": "outdoor_temperature",
                                  "heat_flow_%d" % j: "heat_flow_rate"}


                print('Working on .db_to_influx...   ', install, 'heat pump ', j)

                data = get_ges_data_for_influx(install, start, stop, msp_columns, data_source)

                write_files(db_name, install, hp_uuid, data, column_mapping, chunk_size, j)

    elif data_source == 'wf':
        column_mapping = {'enteringwatertemp': "source_supplytemp",
                          'leavingwatertemp': "source_returntemp",
                          'compressorpower': "heatpump_power",
                          'waterflowrate': "sourcefluid_flowrate",
                          'auxpower': "heatpump_aux",
                          'looppumppower': "sourcefluid_pump_power"}

        data_folder = 'C:\\Users\\mattd\\OneDrive - USNH\\Research\\oTherm\\CTGB\\HP Data\\wf_data\\'
        #data_folder = '..\\temp_files\\'
        #for file in ['E8EB1BCAB8E7-2022-06.csv']:
        for file in os.listdir(data_folder):
            print('working on  ', file)
            datafile = data_folder + os.fsdecode(file)
            sys_id, year, end = file.split('-')
            mo = end.split('.')[0]
            print(datafile, sys_id, year, mo)
            hp_uuid = wf_installs[sys_id]['hp_id']
            tag = sys_id[6:] + '-' + year + '-' + mo
            print(tag)
            if datafile.lower().endswith(".csv"):
                data = get_symphony_data(datafile)
            else:
                continue

            wx_data = fetch_weather_data.get_hourly_temps(wf_installs[sys_id]['zip_code'],
                                                          datetime.date(data.index[0]),
                                                          datetime.date(data.index[-1]))

            wx_data.index = pd.to_datetime(wx_data.index, utc=True)
            oat_minute = wx_data.resample('60S').backfill()
            symphony_data = data.join(oat_minute, how='left')
            symphony_data.fillna(-999, axis=1, inplace=True)

            write_files(db_name, tag, hp_uuid, symphony_data, column_mapping, chunk_size, j=0)

    elif data_source == 'de':
        #column_mapping = {'enteringwatertemp': "source_supplytemp",
        #                  'leavingwatertemp': "source_returntemp",
        #                  'compressorpower': "heatpump_power",
        #                  'waterflowrate': "sourcefluid_flowrate",
        #                  'auxpower': "heatpump_aux",
        #                  'looppumppower': "sourcefluid_pump_power"}

        #column_mapping = {['timestamp', '[kWh Monthly][kWh][118]', '[Water Flow][gpm][307]',
        #                   '[Aux Heat Current][A][129]', '[System Power][W][107]',
        #                   '[System Current][A][106]', '[Return Air][ºF][102]',
        #                   '[Entering Water][ºF][103]', '[kWh][kWh][116]',
        #                   '[Leaving Water][ºF][104]', '[Supply Air][ºF][101]']}

        data_folder = ctgb_de_installs.de_data_folder
        for file in os.listdir(data_folder):
            if file.lower().endswith(".csv"):
                print('working on  ', file)
                datafile = data_folder + os.fsdecode(file)
                basename = file.split('.')[0]
                dum, ngen, date = basename.split('_')

                hp_uuid = de_installs[ngen]['hp_id']
                print(ngen, date, datafile)

                #tag = sys_id[6:] + '-' + mo

                if ngen == '111619':
                    data = get_enertech_data(datafile)
                    resampled = data.resample('60S').backfill()
                    print('in if block')



