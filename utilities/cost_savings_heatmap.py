"""
Analysis of cost savings for heating based on cost of electricity and cost of heating oil for a given COP
"""

import pandas as pd
import numpy as np
from db_tools import otherm_db_reader

import matplotlib.pyplot as plt

def fmt(x):
    s = f"{x:.1f}"
    if s.endswith("0"):
        s = f"{x:.0f}"
    return rf"\$ {s} \%" if plt.rcParams["text.usetex"] else f"$ {s}"


per_mmbtu_basis = True

c_elec, c_oil = np.meshgrid(np.linspace(0.12, 0.40, 100), np.linspace(2.50, 6.5, 100))

cop = 2.5

per_mmbtu_oil = (1/0.85)*(c_oil/136000)*1E6
per_mmbtu_hp = (1/cop)*(1/3412)*c_elec*1E6

z_per_mmbtu = per_mmbtu_oil - per_mmbtu_hp

z = z_per_mmbtu

if per_mmbtu_basis:
    z = z_per_mmbtu
    fig, ax = plt.subplots()

    l = ax.contour(c_elec, c_oil, z, levels=np.linspace(-50, 50, 21), cmap='YlGn')
    #c = ax.pcolormesh(c_elec, c_oil, z, cmap='RdYlGn', vmin=-3200, vmax=3200,shading='auto')
    c = ax.pcolormesh(c_elec, c_oil, z, cmap='PiYG', vmin=-50, vmax=50)

    label_locations_1 =[(0.16, 6.0), (0.2, 5.25), (0.23, 4.75), (0.26, 4.5), (0.29, 4.0),
                      (0.33, 3.4), (0.35, 3.0)]

    label_locations_1 =[(0.16, 5.5), (0.19, 5.25), (0.26, 4.5), (0.33, 3.4), (0.37, 2.9)]

    label_locations_2 =[(0.15,6.0), (.18, 5.8), (0.20, 5.5), (0.22, 5.25), (0.225, 5.0), (0.25, 4.75), (0.27, 4.5),
                        (0.29, 4.00), (0.31, 3.65), (0.325, 3.33), (0.35, 3.10), (0.375, 2.85)]   #(0.27, 4.25),

    ax.clabel(l, l.levels, inline=True, fontsize=10, fmt=fmt, colors='black', manual=label_locations_2)

    ax.set_title('Cost Savings per MMBTU; COP = 2.5', fontsize = 12)
    plt.xlabel('Cost of electricity [$/kWh]', fontsize=10)
    plt.ylabel('Cost of heating oil [$/gallon] @85% efficiency', fontsize=10)
    # set the limits of the plot to the limits of the data
    ax.axis([c_elec.min(), c_elec.max(), c_oil.min(), c_oil.max()])
    fig.colorbar(c, ax=ax)
    plt.scatter(0.26, 5.8, marker='+', s=160, c='blue')
    plt.scatter(0.18, 3.8, marker='o', s=320, alpha=0, edgecolors='blue')
    plt.show()

else:
    z = 60*z_per_mmbtu

    fig, ax = plt.subplots()

    l = ax.contour(c_elec, c_oil, z, levels=np.linspace(-3200, 3200, 17), cmap='YlGn')
    c = ax.pcolormesh(c_elec, c_oil, z, cmap='RdYlGn', vmin=-3200, vmax=3200,shading='auto')

    label_locations_1 = [(0.16, 6.0), (0.2, 5.25), (0.23, 4.75), (0.26, 4.5), (0.29, 4.0),
                         (0.33, 3.4), (0.35, 3.0)]

    label_locations_1 = [(0.16, 5.5), (0.19, 5.25), (0.26, 4.5), (0.33, 3.4), (0.37, 2.9)]

    label_locations_2 = [(.13, 5.75), (0.16, 5.5), (0.18, 5.25), (0.20, 5.0), (0.22, 4.75), (0.25, 4.5),
                         (0.29, 4.00), (0.31, 3.65), (0.325, 3.33), (0.35, 3.00), (0.375, 2.85)]  # (0.27, 4.25),

    ax.clabel(l, l.levels, inline=True, fontsize=10, fmt=fmt, colors='black', manual=label_locations_2)

    ax.set_title('Annual Cost Savings  (SPF = 4.0; 60MMBTU/yr)', fontsize=12)
    plt.xlabel('Cost of electricity [$/kWh]', fontsize=10)
    plt.ylabel('Cost of heating oil [$/gallon] @85% efficiency', fontsize=10)
    # set the limits of the plot to the limits of the data
    ax.axis([c_elec.min(), c_elec.max(), c_oil.min(), c_oil.max()])
    fig.colorbar(c, ax=ax)
    plt.scatter(0.26, 5.8, marker='+', s=160, c='blue')
    plt.show()