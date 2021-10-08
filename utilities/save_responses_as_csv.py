import pandas as pd

import sys
import psycopg2
import datetime
from configuration import GE_READ


def get_wr_as_dataframe(installation_id, start, end, columns):
    ge_read = psycopg2.connect(**GE_READ)
    parameters = (columns, str(installation_id),
                  start.strftime('%Y-%m-%d 00:00:00%z'),
                  end.strftime('%Y-%m-%d 00:00:00%z'))

    sql = """SELECT %s FROM results_wattresponse w
INNER JOIN results_flattenedresponse fr ON w.response_id = fr.id
WHERE fr.installation_id = %s AND fr.created BETWEEN TIMESTAMPTZ '%s'
AND TIMESTAMPTZ '%s'""" % parameters
    wr_data = pd.read_sql(sql, ge_read, index_col='created')
    local_data_prefix = '../local_data'
    datafile = local_data_prefix + '/install_' + installation_id + '_CY2016_wr.csv'
    wr_data = wr_data.to_csv(datafile)
    ge_read.close()
    return wr_data


def save_responses_csv():

    start = datetime.datetime(2016, 2, 2)
    stop = datetime.datetime(2016, 12, 31)

    if len(sys.argv) > 1:
        start = eval("datetime.datetime(sys.argv[1])")
        stop = eval("datetime.datetime(sys.argv[2])")
        print("Using Argument parameters: " + str(start) + " to " + str(stop))
    else:
        print("Using Programmed parameters: " + str(start) + " to " + str(stop))

    # infer_stage = True
    installation_id = '1674'  # 'S37' #'1660'

    installation_id_list = [45, 1649, 1692, 1683, 1660, 75, 1667, 1634, 1648, 1691, 70, 1677, 1685, 1695, 1632, 1676, 1659]

    for id in installation_id_list:
        print("New Frame Generation Started...")
        get_wr_as_dataframe(str(id), start, stop, '*')


if __name__ == '__main__':
    install = 'dummy'