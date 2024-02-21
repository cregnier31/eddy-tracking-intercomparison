#!/usr/bin/env python3
import os
import sys
import glob
import re
from datetime import datetime
from configparser import ConfigParser
import argparse
import multiprocessing as mp
from functools import partial

from py_eddy_tracker.appli.grid import eddy_id
from py_eddy_tracker.dataset.grid import RegularGridDataset
from netCDF4 import Dataset
import pandas as pd

import warnings 
warnings.filterwarnings("ignore")

def reg_date(string_to_find_date_in):
    """function that uses regular expressions to find start and end date from file.

    :string_to_find_date_in: string from NEMO netCDF file.
    :returns: string with start and end date
    """
    # really handonline regex finder: https://regex101.com/#python
    # pour OSSE

    return re.search(r"[0-9]{8}", string_to_find_date_in).group()


def compute_eddy(file, general_info):
    
    MODEL = str(general_info["MODEL"])
    OUTPUT_DIR = str(general_info["OUTPUT_DIR"])
    print(MODEL)
    var_adt = str(general_info["var_adt"])
    VAR_U = str(general_info["VAR_U"])
    VAR_V = str(general_info["VAR_V"])

    SHAPE_ERROR = int(general_info["SHAPE_ERROR"])
    PIXEL_MIN = int(general_info["PIXEL_MIN"])
    PIXEL_MAX = int(general_info["PIXEL_MAX"])
    AMP_MIN = float(general_info["AMP_MIN"])
    WAVELENGTH = int(general_info["WAVELENGTH"])
    ORDER_FILTER = int(general_info["ORDER_FILTER"])
    
    #date_file = reg_date(file)[0:8]
    date_file="20230201"
    print(date_file)
    
    date = pd.to_datetime(
        date_file, format="%Y%m%d"
    )  #### define date for eddy detection
    print(date)
    lon_name, lat_name = (
        "longitude",
        "latitude",
    )  #### longitude and latitude name in each netcdf file
    grid_name = file
    h = RegularGridDataset(
        grid_name, lon_name, lat_name
    )  #### centered pixel position of grid
  
    # h.add_uv("zos")   # if no u vend v in files, the function compute geostrophic velocities
    print('toto')
    h.bessel_high_filter(var_adt, WAVELENGTH, order=ORDER_FILTER)
    print("h filtered")
    print(var_adt)
    a, c = h.eddy_identification(
        var_adt,
        VAR_U,
        VAR_V,  # Variables used for identification
        date,
        AMP_MIN,  # step between two isolines of detection (m)
        pixel_limit=(PIXEL_MIN, PIXEL_MAX),  # Min and max pixel count for valid contour
        shape_error=SHAPE_ERROR,  # Error max (%) between ratio of circle fit and contour
    )
    print("a and c ok")
    ################# save eddy detcted in netcdf files
    with Dataset(
        date.strftime(OUTPUT_DIR + "Anticyclonic_" + MODEL + "_" + date_file + ".nc"),
        "w",
    ) as h:
        a.to_netcdf(h)
    with Dataset(
        date.strftime(OUTPUT_DIR + "Cyclonic_" + MODEL + "_" + date_file + ".nc"), "w"
    ) as h:
        c.to_netcdf(h)


def detect_eddies():
    
    # Read in config file name
    parser = argparse.ArgumentParser(description="Script that reads in a config file")
    # default drifting time 90 days
    # model output NEMO Mercator PSY4V3R1_1dAV
    # advection in 2D at the surface'''))
    # add command line option
    parser.add_argument(
        "CONFIG_FILE", help="specify name of configuration file", type=str
    )
    args = parser.parse_args()
    CONFIG_FILE = args.CONFIG_FILE
    print("read in:", CONFIG_FILE)

    # Read in user input arguments
    config_object = ConfigParser()
    config_object.read(CONFIG_FILE)

    general_info = config_object["GENERAL_INFO"]
    INPUT_FILES = str(general_info["INPUT_FILES"])
    OUTPUT_DIR = str(general_info["OUTPUT_DIR"])
    print(OUTPUT_DIR)
    if not os.path.exists(OUTPUT_DIR):
        print("\ncreate directory : ", OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)

    INPUT_FILES = sorted(glob.glob(INPUT_FILES + "*.nc"))
    print(INPUT_FILES)
    pool = mp.Pool()
    pool.imap(partial(compute_eddy, general_info=general_info), INPUT_FILES)
    pool.close()
    pool.join()
    print(OUTPUT_DIR)
    print("Eddy detection done")


if __name__ == "__main__":
    detect_eddies()
