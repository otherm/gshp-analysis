#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""
def ewt_violin(df):
    """
     cut and paste -- untested
         
    :param df: 
    :return: 

     """

    start = datetime.datetime(2016, 1, 1)
    stop = datetime.datetime(2016, 12, 30)

    # TODO:  update this into a method within an oTherm analysis class
    columns = 'ewt_1, lwt_1, r_1_on, compressor_1, heat_flow_1, created'
    include = ['1660', '45', '1649', '1674']

    composite = pd.DataFrame()

    palette = {'Heating': 'darkorange', 'Cooling': 'dodgerblue'}
    labels = {'45': 'bcb7', '1649': 'f006', '1660': '6ee0', '1674': '97b7'}

    for installation_id in include:
        print('working on..df plots.', installation_id)
        data = db_reader.get_fr_as_dataframe(installation_id, start, stop, columns)

        # resample to 1-hour averages
        dataHourly = data.resample('3600S').mean()

        # eliminate NaNs from DataFrame and limit rows to when heat pump is 'on' >500 Watts
        dataHourly = dataHourly[np.isfinite(dataHourly['heat_flow_1'])]
        dataHourly = dataHourly.query('compressor_1 > 500.')

        # 'high' is used to filter outliers (2*95th percentile), some of which may be erroneous data
        high = 2 * dataHourly['compressor_1'].quantile(0.95)
        dataHourly = dataHourly[dataHourly['compressor_1'] < high]

        # add two more columns for heating and cooling
        dataHourly['Mode'] = dataHourly.apply(determine_mode, axis=1)
        dataHourly['EWT F'] = dataHourly['ewt_1'].apply(C_to_F)
        dataHourly['install'] = labels[installation_id]  # installs[installation_id]['label']
        composite = pd.concat([composite, dataHourly])

    print('generating plot, please stand by')
    ax = sns.violinplot(x='install', y='EWT F', data=composite,
                        hue='Mode', palette=palette, split=True)
    ax.set_xlabel('Site')
    ax.set_ylabel('EWT [$^\circ$F]')

    plt.show()

if __name__ == '__main__':
    install = 'dummy'