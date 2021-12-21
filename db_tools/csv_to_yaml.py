import pandas

def output_yaml(equipment_model, site_model, thermal_load_model):
    if equipment_model:
        j = 1
        equip_yaml = open('../temp_files/CTGB_equipment2.yaml', 'a')
        equip_yaml.write('models: \n')

        # Each heat pump needs to have row in csv with all columns populated
        for i in range(len(data)):
            equip_yaml.write('    - Equipment: \n')
            equip_yaml.write('         name: {:06d} Heat Pump \n'.format(int(data.Site[i])))
            equip_yaml.write('         model: \n')
            equip_yaml.write('             id: {} \n'.format(data.HP_Model[i]))
            equip_yaml.write('         type:  \n')
            equip_yaml.write('             name: "Heat Pump {} of {}" \n'.format(int(data.HP_n[i]), int(data.N_HPs[i])))
            equip_yaml.write('         site:  \n')
            equip_yaml.write('             name: "{:06d}" \n'.format(int(data.Site[i])))
            equip_yaml.write('         manufacturer: \n')
            equip_yaml.write('             name: {} \n'.format(data.HP_Mfg[i]))
            equip_yaml.write('         maintenance: \n')
            equip_yaml.write('             name: none \n')

        equip_yaml.close()

    if site_model:

        site_yaml = open('../temp_files/CTGB_site_info2.yaml', 'a')
        site_yaml.write('models: \n')
        for i in range(len(data)):
            site_yaml.write('    - Site: \n')
            site_yaml.write('         name: {:06d} \n'.format(int(data.Site[i])))
            site_yaml.write('         description: Mon Sys {}  Mon Sys ID {} Mon Sys MAC {}  \n'.format(data.Mon_Sys[i],
                                                                                                     data.Mon_Sys_ID[i],
                                                                                                     data.Mon_Sys_MAC[i]))
            site_yaml.write('         city: {} \n'.format(data.Town[i]))
            site_yaml.write('         state: \n')
            site_yaml.write('             name: Connecticut \n')
            site_yaml.write('         zip_code: "{:05d}" \n'.format(int(data.Zip[i])))
            site_yaml.write('         timezone: \n')
            site_yaml.write('             tzone_name: US/Eastern \n')
            site_yaml.write('         application: house built in {} \n'.format(data.Year_built[i]))
            site_yaml.write('         thermal_load: \n')
            site_yaml.write('             name: {} thermal load \n'.format(int(data.Site[i])))
            site_yaml.write('         weather_station_nws_id: \n')
            site_yaml.write('             nws_id: {} \n'.format(data.NWS_ID[i]))
        site_yaml.close()

    if thermal_load_model:
        thermal_load_yaml = open('../temp_files/CTGB_thermal_loads2.yaml', 'a')
        thermal_load_yaml.write('models: \n')
        for i in range(len(data)):
            thermal_load_yaml.write('    - ThermalLoad: \n')
            thermal_load_yaml.write('         name: {} thermal load \n'.format(int(data.Site[i])))
            thermal_load_yaml.write('         conditioned_area: {} \n'.format(data.Sq_ft[i]))
            thermal_load_yaml.write('         heating_design_load: {} \n'.format(data.HeatingLoad[i]))
            thermal_load_yaml.write('         cooling_design_load: {} \n'.format(data.CoolingLoad[i]))
            thermal_load_yaml.write('         heating_design_oat: {} \n'.format(data.OAT_heat[i]))
            thermal_load_yaml.write('         cooling_design_oat: {} \n'.format(data.OAT_cool[i]))

        thermal_load_yaml.close()

if __name__ == '__main__':

    csv_file = '../temp_files/GreenBank_SummaryInfo_1221.csv'
    data = pandas.read_csv(csv_file)

    equipment_model = True
    site_model = True
    thermal_load_model = True
    output_yaml(equipment_model, site_model, thermal_load_model)