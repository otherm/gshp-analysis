"""
Finds the dictionary for the measurement specification based on the name of the measurement.
"""


def find_measurement_spec(monitoring_system_specs, measurement_type):
    """
    Scans the list of specs and returns dictionary of specifications for the named measurement type

    Parameters
    ----------
        monitoring_system_specs: list
            The list of all measurement specs for a monitoring system
        measurement_type: str
            The name of the measurement type to be located

    Returns
    -------
        dict
            measurement specifications
    """

    for specs in monitoring_system_specs:
        for measurement in specs.items():
             if measurement[1]['type']['name'] == measurement_type:
                return measurement[1]


if __name__ == '__main__':

    name = 'auxiliary_power'

    monitoring_system_specs=[{'measurement_spec': {'name': 'HPP VA W 8% EP',
                                               'description': 'Heat pump power, volt-amps, electrical panel',
                                               'type': {'name': 'heatpump_power',
                                                        'msp_columns': None,
                                                        'description': ''},
                                               'accuracy': '8.00000',
                                               'accuracy_pct': True,
                                               'meas_bias_abs': 0.0,
                                               'meas_bias_pct': 0.0,
                                               'location': {'name': 'Electrical Panel',
                                                            'description': ''},
                                               'unit': {'name': 'W',
                                                        'description': 'watts'}}},
                             {'measurement_spec': {'name': 'HPP VA W 8% EP',
                                               'description': 'Heat pump power, volt-amps, electrical panel',
                                               'type': {'name': 'auxiliary_power',
                                                        'msp_columns': None,
                                                        'description': ''},
                                               'accuracy': '8.00000',
                                               'accuracy_pct': True,
                                               'meas_bias_abs': 0.0,
                                               'meas_bias_pct': 0.0,
                                               'location': {'name': 'Electrical Panel',
                                                            'description': ''},
                                               'unit': {'name': 'W',
                                                        'description': 'watts'}}}]

    measurement_spec = find_measurement_spec(monitoring_system_specs, name)
