#!/usr/bin/env python3
################################################################################
#                            EDDY DETECTION                                    #
################################################################################
#
#   Description : creates cyclonic and anti-cyclonic detection files / day
#
#   Authors     : S. Cailleau, F. Dubost, C. Reignier
#
#   Version     : 05/2025
#
#################################################################################
#
# ----------
#   IMPORT
# ----------
#
import os
import sys
import argparse
import glob
import re
from datetime import datetime
#from configparser import ConfigParser
#import argparse
import multiprocessing as mp
#from functools import partial
import logging
from py_eddy_tracker.appli.grid import eddy_id
from py_eddy_tracker.dataset.grid import RegularGridDataset
from py_eddy_tracker import start_logger
from netCDF4 import Dataset
import pandas as pd
#import numba
sys.path.append("./")
import eddy_detect.my_functions as fn # use of homemade function modules

import warnings 
warnings.filterwarnings("ignore")
#
# ---------------
# USER PARAMETERS
# ---------------
#
from eddy_detect.namelist_detect import *
#
def main():
   # -------------------- 
   # MAIN USER PARAMETERS
   # --------------------
   #
   #    - Main parameters in arguments
   #
   # Create the parser
   parser = argparse.ArgumentParser()
   # Add arguments
   parser.add_argument('--mode', type=str, required=True, help='mode: Near Real Time (NRT) or Reanalysis (MY)') 
   parser.add_argument('--acro', type=str, required=True, help='Analysis & Forecasting system acronyme (eg.: GLO, IBI, MED, BAL, BLK, NWS, ORCA36) or altimetry data acronyme (eg.: AVISO, AVISO_EU)')
   parser.add_argument('--area', type=str, help='Area name you defined according to your coord lon0, lon1, lat0, lat1') 
   parser.add_argument('--folder', type=str, required=True, help='Downloaded file directory')
   # Parse the argument
   args = parser.parse_args()
   #
   mode = args.mode
   data_acro = args.acro
   area = args.area
   data_dir = args.folder
   print ("mode = ",mode)
   print ("Analysis & Forecasting system or altimetry data = ",data_acro)
   print ("Area name = ",area)
   print ("Inut data directory = ",data_dir)
   #
   #    - Var name depending on the kind of data (model or obs) ==> !!! to be updated following the Copernicus MDS updates for AVISO data !!!
   # 
   #       - for MDS adt AVISO obs data (SL-TAC)
   if ( ( data_acro == "AVISO" ) or ( data_acro == "AVISO_EU" ) ):
      if mode == 'NRT': 
         VAR_U = data_obs_dict_NRT[data_acro][0]
         VAR_V = data_obs_dict_NRT[data_acro][1]
         var_adt = data_obs_dict_NRT[data_acro][2]
      elif mode == 'MY':
         VAR_U = data_obs_dict_MY[data_acro][0]
         VAR_V = data_obs_dict_MY[data_acro][1]
         var_adt = data_obs_dict_MY[data_acro][2]
   #       - for model data
   else:
      if mode == 'NRT': 
         VAR_U = data_mod_dict_NRT[data_acro][0]
         VAR_V = data_mod_dict_NRT[data_acro][1]
         var_adt = data_mod_dict_NRT[data_acro][2]
      elif mode == 'MY':
         VAR_U = data_mod_dict_MY[data_acro][0]
         VAR_V = data_mod_dict_MY[data_acro][1]
         var_adt = data_mod_dict_MY[data_acro][2]
   #
   # ---------------------
   # Make data directories
   # ---------------------
   #
   INPUT_DIR = data_dir+"/"+data_acro+"/"+area+"/"
   OUTPUT_DIR = INPUT_DIR+"DETECT/"
   if not os.path.exists(INPUT_DIR):
      os.mkdir(INPUT_DIR)
   if not os.path.exists(OUTPUT_DIR):
      os.mkdir(OUTPUT_DIR)
   #
   # --------------
   # Eddy detection
   # --------------
   #
   fn.detect_eddies(data_acro, INPUT_DIR, OUTPUT_DIR, var_adt, VAR_U, VAR_V, SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER)
   #
   # --------------
#
# Run the main code
if __name__ == "__main__":
    print('compute_eddy')
    main()
#
# =========================================================================