import numpy as np
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
#
def reverse_index(index, nb):
    m = np.ones(nb, dtype="bool")
    m[index] = False
    return np.where(m)[0]
#
def plt_cartopy(ax, labels=True):
    # ax.set_aspect('auto') # The figure will follow the ratio of the figsize
    ax.coastlines()  # Plot the coastlines
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
#
# ======================================================================================