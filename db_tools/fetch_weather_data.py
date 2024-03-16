
from degreedays.api import DegreeDaysApi, AccountKey, SecurityKey
from degreedays.api.data import DataSpec, Calculation, Temperature, \
    DatedBreakdown, Period, Location, DataSpecs, LocationDataRequest
from degreedays.time import DayRange, DayRanges, DayOfWeek, StartOfMonth, StartOfYear
from degreedays.api.data import AverageBreakdown, TemperatureUnit, TimeSeriesCalculation
from datetime import date
import configuration
import pandas as pd
from datetime import datetime

acct_key = configuration.dd_net['account-key']
security_key = configuration.dd_net['security-key']

def get_hourly_temps(zip_code, start, end):

    api = DegreeDaysApi.fromKeys(AccountKey(acct_key),SecurityKey(security_key))

    hourlySpec = DataSpec.timeSeries(
        TimeSeriesCalculation.hourlyTemperature(TemperatureUnit.CELSIUS),
        DatedBreakdown.daily(Period.dayRange(DayRange(start, end))))

    request = LocationDataRequest(Location.postalCode(zip_code, 'US'),
                                  DataSpecs(hourlySpec))

    response = api.dataApi.getLocationData(request)

    hourly_data = response.dataSets[hourlySpec]

    hourly_temps = {}
    for i in range(len(hourly_data.values)):
        hourly_temps.update({hourly_data.values[i].datetime: hourly_data.values[i].value})

    oat_df = pd.DataFrame.from_dict(hourly_temps, orient='index', columns=['outdoor_temperature'])

    #oat_df.index = pd.to_datetime(oat_df.index, utc=True)

    return oat_df

if __name__ == '__main__':

    zip_code = '06010'
    start = date(2023, 8, 19)
    end = date(2023, 8, 20)
    oat = get_hourly_temps(zip_code, start, end)
