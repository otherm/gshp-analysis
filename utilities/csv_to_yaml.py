import yaml
import pandas as pd
import model_dict_templates as mdt


inputfile = '../temp_files/NWS_stations_2.csv'

station_data = pd.read_csv(inputfile, header=0)

station_dict_list = station_data.set_index('model').to_dict('records')

weather_station_list = []
for data in station_dict_list:
    if data['nws_id'] not in ['KPSM', 'KPSF', 'KHIE', 'KBED']:
        weather_station_list.append({'WeatherStation': data})
        print(data)

with open('../temp_files/nws_stations.yaml', 'w') as file:
    yaml.safe_dump(weather_station_list, file, default_style='"')

file.close()
