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

def get_data_for_influx(installation_id, start, end, msp_columns, data_source):
    """
    Retrieves data from a PostgreSQL database.

    :param int installation_id:  site identifier in target database
    :param date start: start date (e.g. 2018-1-1)
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

def get_ges_data_for_influx(installation_id, start, end, msp_columns):
    """
    Retrieves data from a PostgreSQL database.

    :param int installation_id:  site identifier in target database
    :param date start: start date (e.g. 2018-1-1)
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

def write_files(db_name, uuid, df, column_mapping, chunk_size, j):
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
    print (len(df_split))
    for i in range(len(df_split)):
        lp_file_name = ['C:/Llano/oTherm_CTGB_chunks/'+ db_name, install, str(j), ('chunk_%d.txt' % i )]
        lp_file_for_chunk = open("_".join(lp_file_name), 'w')
        for index, row in df_split[i].iterrows():
            measures = []
            for column in columns:
                if column != 'created':
                    measures.append("=".join([column, str(row[column])]))
                data_elements = ','.join(measures)
                timestamp = str(row.created.timestamp()).split('.')[0]
            lp_line = " ".join([line_reference, data_elements, timestamp, '\n'])
            lp_file_for_chunk.write(lp_line)
        lp_file_for_chunk.flush()
        lp_file_for_chunk.close()
    return


if __name__ == '__main__':
    import ctgb_ges_installs
    installs = ctgb_ges_installs.installs

    data_source = 'ges'
    db_name = 'otherm-data'

    #start = datetime.datetime(2016, 1, 1)
    stop = datetime(2022, 4, 1)

    chunk_size = 8000

    for install in installs:
        start = datetime.strptime(installs[install]['start'], '%Y-%m-%d')
        for i in range(len(installs[install]['hp_id'])):
            hp_uuid = installs[install]['hp_id'][i]
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

            data = get_data_for_influx(install, start, stop, msp_columns, data_source)

            write_files(db_name, hp_uuid, data, column_mapping, chunk_size, j)



