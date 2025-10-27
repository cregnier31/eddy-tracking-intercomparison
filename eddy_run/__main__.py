#!/usr/bin/env python3
###############################################################################
#
#                      EDDY MONITORING MAIN SCRIPT
#
###############################################################################
#
# Description : run the different components for the eddy diagnostics
#               used i the quarterly FC bulletin QUOVADIS:
#                  - Loads the uo, vo & ssh of the MDS model (GLO or IBI) 
#                    & obs (AVISO or AVISO_EU) & write in the right input 
#                    format for "py-eddy-tracker"
#                  - Applies detection to these data (for model & obs data)
#                  - Applies tracking to these data (for model & obs data)
#                  - makes diagnostics & plots
#
# Authors     : S. Cailleau
#
# Version     : 05/2025
#
##############################################################################
#
# ---------------
#    IMPORT
# ---------------
#
import subprocess
import sys
#
def main():
   #
   # -----------------------------------
   #    Main parameters in arguments
   # -----------------------------------   
   #
   if (len(sys.argv)==11):
      # Considered period (in arguments)
      date_start = str(sys.argv[1])
      date_end = str(sys.argv[2])
      xmin = str(sys.argv[3])
      xmax = str(sys.argv[4])
      ymin = str(sys.argv[5])
      ymax = str(sys.argv[6])
      mode = str(sys.argv[7])
      model_acro = str(sys.argv[8])
      obs_acro = str(sys.argv[9])
      data_dir = str(sys.argv[10])
      print ("Date start = ",date_start)
      print ("Longitude min = ",xmin)
      print ("Longitude max = ",xmax)
      print ("Latitude min = ",ymin)
      print ("Latitude max = ",ymax)
      print ("Analysis & Forecasting system = ",model_acro)
      print ("Altimetric satellite data = ",obs_acro)
      print ("Downloaded file directory = ",data_dir)
   else:
      print ("!!! ERROR: 10 arguments to be chosen !!!")
      print ("Argument 1 = Date start (yyyy-mm-dd)")
      print ("Argument 2 = Date end (yyyy-mm-dd)") 
      print ("Argument 3 = Longitude min (-180/180° longitude convention)")
      print ("Argument 4 = Longitude max (-180/180° longitude convention)")
      print ("Argument 5 = Latitude min (-90/90° latitude convention)")
      print ("Argument 6 = Latitude max (-90/90° latitude convention)")
      print ("Argument 7 = NRT or MY datasets") 
      print ("Argument 8 = Analysis & Forecasting system (GLO, IBI, ...)")
      print ("Argument 9 = Altimetric satellite data (AVISO, AVISO_EU)")
      print ("Argument 10 = Downloaded file directory")
      sys.exit()
   #
   # ------------------------------------
   #   Run of the different components
   # ------------------------------------
   #    - Input data loading
   proc1 = subprocess.run([r'eddy_load', date_start, date_end, xmin, xmax, ymin, ymax, mode, model_acro, obs_acro, data_dir])
   #    - Model eddy detection
   proc2 = subprocess.run([r'eddy_detect', mode, model_acro, data_dir])
   #    - Obs eddy detection
   proc3 = subprocess.run([r'eddy_detect', mode, obs_acro, data_dir])
   #    - Model eddy tracking
   proc4 = subprocess.run([r'eddy_track', model_acro, data_dir])
   #    - Obs eddy detection
   proc5 = subprocess.run([r'eddy_track', obs_acro, data_dir])
   #    - eddy diagnostics model vs obs
   proc6 = subprocess.run([r'eddy_diags', date_start, xmin, xmax, ymin, ymax, model_acro, obs_acro, data_dir])
   #
# Run the main code
if __name__ == "__main__":
    print('eddy_run')
    main()
#
# =========================================================================
