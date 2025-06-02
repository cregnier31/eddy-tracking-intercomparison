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
   if (len(sys.argv)==3):
      # Considered period (in arguments)
      data_acro = str(sys.argv[1])
      data_dir = str(sys.argv[2])
      print ("Input data = ", data_acro)
      print ("Input data directory = ", data_dir)
   else:
      print ("!!! ERROR: 2 arguments to be chosen !!!")
      print ("Argument 1 = Input data acronym (GLO, IBI, AVISO, AVISO_EU)")
      print ("Argument 2 = Idata directory")
      sys.exit()
   #
   #    - Var name depending on the kind of data (model or obs) ==> !!! to be updated following the Copernicus MDS updates !!!
   # 
   #       - for MDS adt AVISO obs data (SL-TAC)
   if ( ( data_acro == "AVISO" ) or ( data_acro == "AVISO_EU" ) ):
      var_adt = "adt"
      VAR_U = "ugos"
      VAR_V = "vgos"
   #       - for MDS ssh model data (MFCs)
   else:
      var_adt = "zos"
      VAR_U = "uo"
      VAR_V = "vo"
   #
   # ---------------------
   # Make data directories
   # ---------------------
   #
   INPUT_DIR = data_dir+"/"+data_acro+"/"
   OUTPUT_DIR = data_dir+"/"+data_acro+"/DETECT/"
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