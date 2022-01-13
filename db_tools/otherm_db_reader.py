# -*- coding: utf-8 -*-

"""
A collection of functions that use oTherm APIs to retrieve data from an oTherm instance.  The typical application
is to first retrieve the *site* data.  Then, using the *site* dataclass object, retrieve information about the:

    - *weather_station*,
    - *thermal_load*,
    - *monitoring_system*, and
    - *heat_pump_data*.

The tools also contain scripts for:

    - Retrieving the specifications for any oTherm monitoring system by the name of the monitoring system, and

    - Retrieving heat pump peformance data from a local SQLite database (*note*, the SQLite database is not part
      of the oTherm database.

.. note::
    The names and types of data elements  used in the analyses differ from the oTherm data model specification.

The *dataclass* objects use for analysis are constructed from json objects returned from the oTherm database.
However, because the *dataclass* objects represent a single instance, the data elements are reorganized into
a simpler representation than the original json response.

Example
-------
    The input typically consists of a site_name and start and end dates.  The functions can be called from analyses
    modules.  For example ::

     site_name = 'GES649'
     start_date = '2015-01-01'
     end_date = '2021-01-01'

     #Get site information
     site = get_site_info(site_name)

     #Get equipment information and dataframe of heat pump operating data
     equipment, hp_data = get_equipment_data(site.id, start_date, end_date, site.timezone)

     #Get monitoring system information and measurement specifications
     equip_monitoring_system = get_equipment_monitoring_system(equipment.id)

     #Get weather data for station
     wx_data = get_weather_data(site.weather_station.nws_id, site.timezone, start_date, end_date)

     #Get thermal source specifications
     source_specs = get_source_specs(site)

"""

import pandas as pd
import requests
import numpy as np
import configuration
from dataclasses import dataclass
from dacite import from_dict
from typing import Optional
import time
import pprint


def get_site_info(site_name, db):
    """
    get site info docstring

    :param str site_name:  name of oTherm site
    :return:

       The **site** object consists is a nested dataclass object  ::

        @dataclass
        class Site:
            id: int
            name: str
            city: str
            state: str
            timezone: str
            thermal_load: ThermalLoad
            weather_station: WeatherStation

    To access data elements, use the dot syntax.  For example, the Weather Station ID, is accessed by

    >>> site.weather_station
    'KPSM'

    """


    @dataclass
    class Site:
        id: int
        name: str
        city: str
        state: str
        timezone: str
        description: str
        application: str
        thermal_load: str
        weather_station_nws_id: str


    if db == 'localhost':
        site_url = "https://localhost:8000/api/site/?name=%s" % (site_name)
        site_response = requests.get(site_url)
    else:
        site_url = "https://%s/api/site/?name=%s" % (configuration.db_info[db]['baseurl'], site_name)
        site_response = requests.get(site_url, auth=configuration.db_info[db]['auth'])

    site_dict = site_response.json()[0]
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(site_dict)

    try:
        site = from_dict(data_class=Site, data=site_dict)
        return site
    except Exception as e:
        print('Error with site data:  \n       ', e)


def get_thermal_load(site_name, db):
    """

        @dataclass
        class ThermalLoad:
            uuid: str
            name: str
            description: Optional[str]
            conditioned_area: float
            heating_design_load: float
            cooling_design_load: float
            heating_design_oat: float
            cooling_design_oat: float

    To access data elements, use the dot syntax.  For example, the Weather Station ID, is accessed by

    """


    """sphinx-ThermalLoad-begin"""
    @dataclass
    class ThermalLoad:
        uuid: str
        name: str
        description: Optional[str]
        conditioned_area: float
        heating_design_load: float
        cooling_design_load: float
        heating_design_oat: float
        cooling_design_oat: float
    """sphinx-ThermalLoad-end"""


    @dataclass
    class SiteLoad:
        id: int
        name: str
        city: str
        state: str
        thermal_load: ThermalLoad

    if db == 'localhost':
        thermal_load_url = "https://localhost:8000/api/thermal_load/?id=%s" % (site_name)
        thermal_load_response = requests.get(thermal_load_url)
    else:
        thermal_load_url = "https://%s/api/thermal_load/?id=%s" % (configuration.db_info[db]['baseurl'], site_name)
        thermal_load_response = requests.get(thermal_load_url, auth=configuration.db_info[db]['auth'])

    print(thermal_load_url)

    thermal_load_dict = thermal_load_response.json()[0]
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(thermal_load_dict)

    try:
        thermal_load = from_dict(data_class=SiteLoad, data=thermal_load_dict)
        return thermal_load
    except Exception as e:
        print('Error with thermal_load data:  \n       ', e)



def get_equipment(site_id, db):
    """
    Uses 'request' method to read equipment table for a specific site

    :param int site_id:  The site_id in the PostgreSQL database.  Can be obtained from *site.id*
    :return: Equipment dataclass contains equipment information in the following fields::

            @dataclass
            class Equipment:
                id: int
                uuid: str
                model: str
                description: Optional[str]
                no_flowmeter_flowrate: float
                type: int
                site: int
                manufacturer: int

    """

    @dataclass
    class Equipment:
        id: int
        uuid: str
        model: str
        description: Optional[str]
        no_flowmeter_flowrate: float
        type: int
        site: int
        manufacturer: int


    if db == 'localhost':
        equip_url = "https://localhost:8000/api/equipment/?site=%s&start_date=%s&end_date=%s" % (site_id)
        equip_response = requests.get(equip_url)
    else:
        equip_url = "https://%s/api/equipment/?site=%s" % (configuration.db_info[db]['baseurl'], site_id)
        equip_response = requests.get(equip_url, auth=configuration.db_info[db]['auth'])

    print(equip_url)

    #Limitation:  only gets the first piece of equipmemnt at a site.

    equipment_dict = equip_response.json()[0]

    equipment = from_dict(data_class=Equipment, data=equipment_dict)

    return equipment


def get_equipment_data(site_id, start_date, end_date, timezone, db):
    """
    Uses 'request' method to reads heat pump operating data from otherm influx database and returns a pandas dataframe.
    The data DataFrame returned includes all records for the equipment at a site.  At present, the script is limited
    to a single piece of equipment at a site.

    :param int site_id:  The site_id in the PostgreSQL database.  Can be obtained from *site.id*
    :param str start_date: start date (e.g. 2018-1-1)
    :param str end_date: end date (e.g. 2018-12-31)
    :param str timezone: (e.g. 'US/Eastern')
    :return: Equipment dataclass contains equipment information in the following fields::

            @dataclass
            class Equipment:
                id: int
                uuid: str
                model: str
                description: Optional[str]
                no_flowmeter_flowrate: float
                type: int
                site: int
                manufacturer: int


        *pandas.DataFrame* containing heat pump operating data over the specified time range.  The DataFrame contains
        all fields stored for the piece of equipment in the influxDB database.

        .. note:: The index of the *DataFrame* is set to the ``time`` field and localized according the ``site.timezone`` attribute

    """

    if db == 'localhost':
        equip_url = "https://localhost:8000/api/equipment_data/?site=%s&start_date=%s&end_date=%s" % (site_id, start_date,
                                                                                                 end_date)
        equip_response = requests.get(equip_url)
    else:
        equip_url = "https://%s/api/equipment_data/?site=%s&start_date=%s&end_date=%s" % (configuration.db_info[db]['baseurl'],
                                                                         site_id, start_date, end_date)
        equip_response = requests.get(equip_url, auth=configuration.db_info[db]['auth'])

    #Limitation:  only gets the first piece of equipmemnt at a site.

    hp_data = pd.DataFrame.from_dict(equip_response.json()[0]['heat_pump_metrics'])
    try:

        hp_data.set_index(pd.to_datetime(hp_data['time']), inplace=True)
        hp_data['time_elapsed'] = hp_data.index.to_series().diff().dt.seconds.div(3600, fill_value=0)
        hp_data.tz_convert(timezone)
    except Exception as e:
        print('Error with heat pump data: \n     ', e)

    return hp_data


def get_equipment_monitoring_system(equip_id):
    """
    Retrieves the equipment monitoring system and specifications

    :param str uuid: *uuid* of thermal equipment
    :return:

        Dataclass object with equipment monitoring system specifications ::

            @dataclass
            class MonitoringSysInfo:
                id: int
                name: Optional[str]
                description: Optional[str]
                specs: list

            @dataclass
            class EquipmentMonitor:
                id: int
                start_date: str
                end_date: Optional[str]
                equip_id: int
                monitoring_system_spec: int
                info: MonitoringSysInfo

    To access data elements, use the dot syntax.  For example, the *list* containing the monitoring system specifications
    can be accessed by

    >>> monitoring_system.info.specs
    `[{'measurement_spec': {'name': 'HPP VA W 8% EP', 'description': 'Heat pump power, volt-amps, electrical panel', ...`

    The monitoring system specifications is a list of measurements performed by the monitoring system, each measurement
    has its own set of specifications.  See oTherm documentation for more details.

    The list can be search for individual measurements specifications with ``utilities.get_measurement_specs``

    """
    @dataclass
    class MonitoringSysInfo:
        id: int
        name: Optional[str]
        description: Optional[str]
        specs: list

    @dataclass
    class EquipmentMonitor:
        id: int
        start_date: str
        end_date: Optional[str]
        equip_id: int
        monitoring_system_spec: Optional[int]
        info: MonitoringSysInfo

    if db == 'localhost':
        equipment_monitoring_system_url = "http://localhost:8000/api/equipment_monitoring/?equip_id=%s" % (equip_id)
        equip_mon_response = requests.get(equipment_monitoring_system_url)
    else:
        equipment_monitoring_system_url = "http://%s/api/equipment_monitoring/?equip_id=%s" %(configuration.db_info[db]['baseurl'], equip_id)
        equip_mon_response = requests.get(equipment_monitoring_system_url, auth=configuration.db_info[db]['auth'])

    equipment_monitoring_system_url = "http://%s/api/equipment_monitoring/?equip_id=%s" %(configuration.db_info[db]['baseurl'], equip_id)
    equip_mon_response = requests.get(equipment_monitoring_system_url, auth=configuration.db_info[db]['auth'])

    equipment_monitoring_system_dict = equip_mon_response.json()[0]

    equipment_monitoring_system_dict['info'] = equipment_monitoring_system_dict.pop('monitoring_sys_info')
    equipment_monitoring_system_dict['info']['specs'] = equipment_monitoring_system_dict['info'].pop('monitoring_system_specs')

    try:
        monitoring_system = from_dict(data_class=EquipmentMonitor, data=equipment_monitoring_system_dict)
    except Exception as e:
        print('Error with monitoring system data:  \n       ', e)

    return monitoring_system


def get_weather_data(nws_id,timezone, start_date, end_date):
    """

    Parameters
    ----------
    nws_id : str
        National Weather Station 4 character station identifier

    timezone : str
        Timezone of site, such as *'US/Eastern'*

    start_date : str
        Beginning date of request, such as *'2015-01-01'*

    end_date : str
        End date of request

    Returns
    -------
        pandas.DataFrame

        The returned DataFrame contains weather station data over the specified time range and contains all \
        fields stored for the weather station.


        .. note::    The index of the *DataFrame* is set to the ``time`` field and localized according the ``site.timezone`` attribute

    """
    weather_url = "https://%s/api/weather_station/?nws_id=%s&start_date=%s&end_date=%s" % (configuration.db_info['baseurl'],
                                                                                           nws_id, start_date, end_date)

    wx_response = requests.get(weather_url, auth=configuration.db_info[db]['auth'])

    try:
        wx_data = pd.DataFrame.from_dict(wx_response.json()[0]['weather_data'])
        wx_data.set_index(pd.to_datetime(wx_data['time']), inplace=True)
        wx_data['time_elapsed'] = wx_data.index.to_series().diff().dt.seconds.div(3600, fill_value=0)
        wx_data.tz_convert(timezone)
    except Exception as e:
        print('Error with weather data:  \n       ', e)
        pass
        return None
    return wx_data

def get_source_specs(site):
    """
    Retrieves the source specifications.

    :param str site:  site name
    :return:

        Dataclass object with source specifications ::

            @dataclass
            class SourceSpec:
                site: str
                site_id: int
                source_name: str
                source_type: str
                description: str
                freeze_protection: Optional[float]
                grout_type: Optional[str]
                formation_conductivity: Optional[float]
                formation_type: Optional[str]
                grout_conductivity: Optional[float]
                antifreeze: Optional[str]
                pipe_dimension_ratio: Optional[str]
                n_pipes_in_circuit: Optional[int]
                n_circuits: Optional[int]
                total_pipe_length: Optional[float]


    To access data elements, use the dot syntax.

    .. note::    While the oTherm data model supports multiple types of sources, this db_reader tool only supports
                 the vertical loop spec at present.


    """
    # currently limited to vertical loop source specs
    @dataclass
    class SourceSpec:
        site: str
        site_id: int
        source_name: str
        source_type: str
        description: str
        freeze_protection: Optional[float]
        grout_type: Optional[str]
        formation_conductivity: Optional[float]
        formation_type: Optional[str]
        grout_conductivity: Optional[float]
        antifreeze: Optional[str]
        pipe_dimension_ratio: Optional[str]
        n_pipes_in_circuit: Optional[int]
        n_circuits: Optional[int]
        total_pipe_length: Optional[float]


    source_spec_url = "http://%s/api/thermal_source/?site=%s" % (configuration.db_info['baseurl'] , site.id)
    source_spec_response = requests.get(source_spec_url, auth=configuration.db_info[db]['auth'])

    otherm_spec_dict = source_spec_response.json()[0]

    source_spec_dict = {}
    source_spec_dict.update({'site': site.name, 'site_id': site.id})
    source_spec_dict.update({'source_name': otherm_spec_dict['name']})
    source_spec_dict.update(otherm_spec_dict['source_info']['source_type'])
    source_spec_dict.update(otherm_spec_dict['source_info']['source_spec_info'])
    antifreeze = source_spec_dict.pop('antifreeze_info')
    source_spec_dict.update({'antifreeze': antifreeze['name']})
    ghex_specs = source_spec_dict.pop('ghex_specs')
    source_spec_dict.update({'pipe_dimension_ratio': ghex_specs['dimension_ratio'],
                             'n_pipes_in_circuit': ghex_specs['n_pipes_in_circuit'],
                             'n_circuits': ghex_specs['n_circuits'],
                             'total_pipe_length': ghex_specs['total_pipe_length']
                             })
    source_spec_dict.pop('id')
    source_spec_dict['source_type'] = source_spec_dict.pop('name')

    source_spec = from_dict(data_class=SourceSpec, data=source_spec_dict)

    return source_spec, otherm_spec_dict

def get_mfr_data(parameters):

    ge = psycopg2.connect("dbname='mgf_performance_data' user='gxi' host='45.55.41.135' password='geoSTTR!'")
    #TODO:  sql query will need to be more specific as all pd is in one table so need to SELECT * FROM ... WHERE ....
    sql = """SELECT * FROM \"%s\"""" % parameters
    ds_data = pd.read_sql(sql, ge)
    ge.close()
    return ds_data

def get_monitoring_system(name):
    """

    Similar to :func:`get_equipment_monitoring_system` but returns monitoring_system attributes for a given monitoring
    system by name rather than equipment being monitored.  This function requires the exact name of the monitoring
    system, as specified in the oTherm database

    Parameters
    ----------
    name : str
           The name of the monitoring system

    Returns
    -------
    dict
            All specifications of a monitoring system in the oTherm database.  Refer to oTherm documentation for detais.


    For more explanation of the parameters and return values, see :func:`get_equipment_monitoring_system`

    """

    mon_sys_url = "https://%s/api/monitoring_system/?name=%s" % (configuration.db_info['baseurl'], name)
    mon_sys_response = requests.get(mon_sys_url, auth=configuration.db_info[db]['auth'])

    mon_sys_json = mon_sys_response.json()[0]
    mon_sys_response.close()

    return mon_sys_json


if __name__ == '__main__':
    site_name = '03824'
    #site_name = 'GES649'
    start_date = '2016-01-01'
    end_date = '2016-01-05'
    timezone = 'US/Eastern'
    db = 'otherm'
    db = 'othermdev'
    #db = 'localhost'

    site = get_site_info(site_name, db)
    print(site.name)
    print(site.id)

    equipment = get_equipment(site.id, db)
    hp_data = get_equipment_data(site.id, start_date, end_date, site.timezone, db)
    thermal_load = get_thermal_load(site.id, db)
    equip_monitoring_system = get_equipment_monitoring_system(equipment.id)

    #wx_data = get_weather_data(site.weather_station.nws_id, site.timezone, start_date, end_date)
    #monitoring_system_dict = get_monitoring_system(equip_monitoring_system.info.name)
    #source_spec, otherm_source = get_source_specs(site)


#    station_data = pd.read_csv('../temp_files/NWS_stations_2.csv', header=0)
#    for nws_id in station_data['nws_id']:
#        print(nws_id)

#        wx_data = get_weather_data(nws_id, timezone, start_date, end_date)
#        if wx_data is not None:
#            print(len(wx_data))
#            outputfile = nws_id +'_data.csv'
#            wx_data.to_csv('../temp_files/weather_data/' + outputfile)




