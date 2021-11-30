



model = {'Model': {'id': "ND038",
                   'model_number': "ND038xxxxx",
                   'equipment_type': {'name': "Heat Pump"},
                    'manufacturer': {'name':  "Waterfurnace"}
                    }
         }

site = {'Site': {'name': "03824",
               'description': "4-ton residential",
               'city': "Durham",
               'state': {'name': "New Hampshire"},
               'zip_code': "03824",
               'timezone': {'tzone_name': "US/Eastern"},
               'application': "renonvation",
               'thermal_load': {'name': "03824 thermal load"},
               'weather_station_nws_id':{'nws_id': "KPSM"}
                }
        }

loop_spec = {'VerticalLoopSpec': {'name': "06018 ground loop spec",
                                  'description': " ",
                                  'type': {'name': "Vertical Loop"},
                                  'ghex_pipe_spec': {'name': "unknown"},
                                  'antifreeze': {'name': "unknown"},
                                  'freeze_protection': None,
                                  'grout_conductivity': None,
                                  'grout_type': None,
                                  'formation_conductivity': None,
                                  'formation_type': None}
             }


combined = [model, site, loop_spec]

combined = {'models': combined}


