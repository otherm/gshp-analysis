import pandas as pd
import matplotlib.pyplot as plt
from db_tools import otherm_db_reader

data = pd.read_csv('../temp_files/weather_data/KXLL_data.csv')

data['temperature_c'].plot()
plt.show()
