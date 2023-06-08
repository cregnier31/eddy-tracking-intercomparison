#!/usr/bin/env python3

import sys
#sys.path.append("/home/btchonang/py-eddy-tracker/")
# sys.path.append("/home/btchonang/py-eddy-tracker/src/py_eddy_tracker/appli")
from py_eddy_tracker.appli.grid import eddy_id
from py_eddy_tracker.dataset.grid import RegularGridDataset
from datetime import datetime
import glob
from netCDF4 import Dataset
import re
import pandas as pd
import os

###################################### function to read time from a netcdf file name
def reg_date(string_to_find_date_in):
    """function that uses regular expressions to find start and end date from file.
    
    :string_to_find_date_in: string from NEMO netCDF file.
    :returns: string with start and end date
    """
    #really handonline regex finder: https://regex101.com/#python
    # pour OSSE

    exp = re.search(r'[0-9]{8}', string_to_find_date_in) 

    exp=exp.group()

    #print('exp=',exp.group())
    return exp

######################################################################################


### CONFIG FILE ### 

from configparser import ConfigParser
import argparse

#Read in config file name
parser = argparse.ArgumentParser(description='Script that reads in a config file')
				 #default drifting time 90 days 
				 #model output NEMO Mercator PSY4V3R1_1dAV 
				 #advection in 2D at the surface'''))
#add command line option
parser.add_argument("CONFIG_FILE", help="specify name of configuration file", type=str)
args = parser.parse_args()
CONFIG_FILE=args.CONFIG_FILE
print('read in:', CONFIG_FILE)

#Read in user input arguments
config_object = ConfigParser()
config_object.read(CONFIG_FILE)


### IN CONFIG FILE : 2 sections : GENERAL INFO and PLOT INFO

general_info  = config_object["GENERAL_INFO"]
MODEL	      = str(general_info["MODEL"])
INPUT_FILES   = str(general_info["INPUT_FILES"])
OUTPUT_DIR    = str(general_info["OUTPUT_DIR"])

var_adt       = str(general_info["var_adt"])
VAR_U	      = str(general_info["VAR_U"])
VAR_V         = str(general_info["VAR_V"])

SHAPE_ERROR   = int(general_info["SHAPE_ERROR"])
PIXEL_MIN     = int(general_info["PIXEL_MIN"])
PIXEL_MAX     = int(general_info["PIXEL_MAX"])
AMP_MIN       = float(general_info["AMP_MIN"])
WAVELENGTH    = int(general_info["WAVELENGTH"])
ORDER_FILTER  = int(general_info["ORDER_FILTER"])


if not os.path.exists(OUTPUT_DIR):
    print('\ncreate directory : ', OUTPUT_DIR)
    # Create directory where to store results:
    os.makedirs(OUTPUT_DIR )

INPUT_FILES = sorted(glob.glob(INPUT_FILES +'*.nc'))

for i, file in enumerate(INPUT_FILES[:]):
    date_file = reg_date(file)[0:8]
    date = pd.to_datetime(reg_date(file)[0:8],format='%Y%m%d')#### define date for eddy detection
    date_file = reg_date(file)[0:8]

    print(date_file)
    lon_name, lat_name = 'longitude', 'latitude' #### longitude and latitude name in each netcdf file
    grid_name = file
    h = RegularGridDataset(grid_name, lon_name, lat_name) #### centered pixel position of grid
  
   # h.add_uv("zos")   # if no u vend v in files, the function compute geostrophic velocities
   
    h.bessel_high_filter(var_adt,WAVELENGTH,order=ORDER_FILTER) 

    a, c = h.eddy_identification(
    var_adt , VAR_U, VAR_V, # Variables used for identification
    date,
    AMP_MIN, # step between two isolines of detection (m)
    pixel_limit=(PIXEL_MIN, PIXEL_MAX), # Min and max pixel count for valid contour
    shape_error=SHAPE_ERROR, # Error max (%) between ratio of circle fit and contour
    )
   
    ################# save eddy detcted in netcdf files
    with Dataset(date.strftime(OUTPUT_DIR+'Anticyclonic_'+MODEL+'_'+date_file+'.nc'), 'w') as h:
        a.to_netcdf(h)
    with Dataset(date.strftime(OUTPUT_DIR+'Cyclonic_'+MODEL+'_'+date_file+'.nc'), 'w') as h:
        c.to_netcdf(h)

  
print('Eddy detection done')        















