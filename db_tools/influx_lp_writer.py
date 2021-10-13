"""
Reads data from PostgreSQL database, maps onto oTherm data fields,
and outputs .dat file using the influx line protocol
"""

import configuration
import datetime
import numpy as np
import psycopg2
import pandas as pd

def get_data_for_influx(installation_id, start, end, msp_columns):
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
    ges_digital_ocean = configuration.GE_READ
    db_read = psycopg2.connect(**ges_digital_ocean)
    parameters = (msp_columns, str(installation_id),
                  start.strftime('%Y-%m-%d 00:00:00%z'),
                  end.strftime('%Y-%m-%d 00:00:00%z'))

    sql = """SELECT %s from results_flattenedresponse WHERE installation_id = %s
    and created BETWEEN TIMESTAMPTZ '%s' AND TIMESTAMPTZ '%s'""" % parameters
    data = pd.read_sql(sql, db_read)
    data.sort_values('created', inplace=True)
    db_read.close()
    return data


def write_files(db_name, uuid, df, column_mapping, chunk_size):
    """ Takes heat pump operating data as pandas dataframe and writes to datafile 
    using influx line protocol.

    :param str db_name: Name of the influx database, default is 'otherm-data'
    :param str uuid:  oTherm uuid of the thermal equipment, this is that influx db tag
    :param pandas.DataFrame df: Monitoring system data
    :param dict column_mapping: Mapping of monitoring system column names to standardized oTherm column names
    :param int chunk_size: Number of lines in each chunk file, recommended value is 8000
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
        lp_file_name = ['./chunks/'+ db_name, install, ('chunk_%d.txt' % i )]
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
    db_name = 'otherm-data'
    install_id = '1649'
    hp_uuid = '3c0847d4-878b-46ad-b8cf-dd2273bd8224'
    start = datetime.datetime(2016, 1, 1)
    stop = datetime.datetime(2016, 12, 31)
    msp_columns = 'ewt_1, lwt_1, compressor_1, created, q_1_device, auxiliary_1, outdoor_temperature'
    chunk_size = 8000

    print('Working on .db_to_influx...   ', install_id)

    column_mapping = {"auxiliary_1": "heatpump_aux",
                     "compressor_1": "heatpump_power",
                     "lwt_1": "source_returntemp",
                     "ewt_1": "source_supplytemp",
                     "q_1_device": "sourcefluid_flowrate",
                     "outdoor_temperature": "outdoor_temperature",
                     "heat_flow_1": "heat_flow_rate"}

    data = get_data_for_influx(install_id, start, stop, msp_columns)

    write_files(db_name, hp_uuid, data, column_mapping)



