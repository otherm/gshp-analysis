import yaml
import pandas as pd
import model_dict_templates as mdt


#inputfile = '../temp_files/CGB_test.xlsx'

#excel_data = pd.read_excel(inputfile, header=0, engine='openpyxl')

#data = excel_data.T

site_models_list = []

site_models_list.append(mdt.site)
site_models_list.append(mdt.model)
site_models_list.append(mdt.loop_spec)

#for i in range(len(data.columns))
    # Build site dict



#site_models_list.append(site_models)

final = {'models': site_models_list}

'''
data = {'models': [{'Model':
                        {'id': "ND038",
                         'model_number': "ND038xxxxx",
                         'equipment_type': {'name':
                                                "Heat Pump"},
                         'manufacturer': {'name':
                                              "Waterfurnace"}
                         }
                    }
                   ]
        }

print(yaml.dump(data))
'''
with open('../temp_files/test.yaml', 'w') as file:
    yaml.safe_dump(final, file, default_style='"')

file.close()
