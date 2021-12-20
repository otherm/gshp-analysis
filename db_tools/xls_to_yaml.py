import yaml
import pandas

csvfile = '../temp_files/GB_SiteInfo.csv'
data = pandas.read_csv(csvfile)

yaml_out = open('../temp_files/site_info.yaml', 'a')

for i in range(len(data)):
    yaml_out.write('    - Site: \n')

yaml_out.close()



