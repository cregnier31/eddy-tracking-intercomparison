#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@authors: Flavie Dubost, Sylvain Cailleau

Updated on Wed May 14 2025
"""
import os
import sys
import glob
import re
from datetime import datetime
#from configparser import ConfigParser
#import argparse
import multiprocessing as mp
from functools import partial
import logging
from py_eddy_tracker.appli.grid import eddy_id
from py_eddy_tracker.dataset.grid import RegularGridDataset
from py_eddy_tracker import start_logger
from netCDF4 import Dataset
import pandas as pd
#import numba

import warnings 
warnings.filterwarnings("ignore")
#
# ------------------------------------------------
# Start & end date definition from input file list 
# ------------------------------------------------
#
def reg_date(string_to_find_date_in):
    """function that uses regular expressions to find start and end date from file.

    :string_to_find_date_in: string from NEMO netCDF file.
    :returns: string with start and end date
    """
    # really handonline regex finder: https://regex101.com/#python
    # pour OSSE

    return re.search(r"[0-9]{8}", string_to_find_date_in).group()
#
# ---------------------------------
#  Eddy detection / each input file
# ---------------------------------
#
#def compute_eddy(file, general_info, log):
def compute_eddy(file, DATA, INPUT_DIR, OUTPUT_DIR, var_adt, VAR_U, VAR_V, SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER):
    
    date_file = reg_date(file)[0:8]
    #date_file="20230201"
    
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
    h.bessel_high_filter(var_adt, WAVELENGTH, order=ORDER_FILTER)
    print("h filtered")
    a, c = h.eddy_identification(
    	var_adt,
        VAR_U,
        VAR_V,  # Variables used for identification
        date,
        AMP_MIN,  # step between two isolines of detection (m)
        pixel_limit=(PIXEL_MIN, PIXEL_MAX),  # Min and max pixel count for valid contour
        shape_error=SHAPE_ERROR,
        ) # Error max (%) between ratio of circle fit and contour)
     
    print("Eddy identification ok")
    ################# save eddy detcted in netcdf files
    with Dataset(
        date.strftime(OUTPUT_DIR + "Anticyclonic_" + DATA + "_" + date_file + ".nc"),
        "w",
    ) as h:
        a.to_netcdf(h)
    with Dataset(
        date.strftime(OUTPUT_DIR + "Cyclonic_" + DATA + "_" + date_file + ".nc"), "w"
    ) as h:
        c.to_netcdf(h)
    print("write ok")
#
# ------------------------------------------------------------------------------
# Eddy detection in multiprocessing (parallel calculation following input files)
# ------------------------------------------------------------------------------
#
#def detect_eddies(logger):
def detect_eddies(DATA, INPUT_DIR, OUTPUT_DIR, var_adt, VAR_U, VAR_V, SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER):    

    if not os.path.exists(OUTPUT_DIR):
        print("\ncreate directory : ", OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)

    INPUT_FILES = sorted(glob.glob(INPUT_DIR + "*.nc"))
    print (INPUT_FILES)
    #
    # Sequential calculation / data file
    #for FILE in INPUT_FILES: 
    #   print ("input files = ", FILE)
    #   compute_eddy(FILE, DATA, INPUT_DIR, OUTPUT_DIR, var_adt, VAR_U, VAR_V, SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER)
    #
    # Multiproc calculation for all data files
    pool = mp.Pool()
    pool.imap(partial(compute_eddy, DATA=DATA, INPUT_DIR=INPUT_DIR, OUTPUT_DIR=OUTPUT_DIR, var_adt=var_adt, VAR_U=VAR_U, VAR_V=VAR_V, SHAPE_ERROR=SHAPE_ERROR, PIXEL_MIN=PIXEL_MIN, PIXEL_MAX=PIXEL_MAX, AMP_MIN=AMP_MIN, WAVELENGTH=WAVELENGTH, ORDER_FILTER=ORDER_FILTER), INPUT_FILES)
    pool.close()
    pool.join()
    print(f"{OUTPUT_DIR=}")
    print("oO Eddy Detection Done Oo")
#
# =============================================================================