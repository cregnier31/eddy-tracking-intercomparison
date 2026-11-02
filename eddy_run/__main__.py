#!/usr/bin/env python3
###############################################################################
#
#                      EDDY MONITORING MAIN SCRIPT
#
###############################################################################
#
# Description : run the different components for the eddy diagnostics
#               used in the quarterly FC bulletin QUOVADIS:
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
import argparse
#
def main():
   #
   # -----------------------------------
   #    Main parameters in arguments
   # -----------------------------------   
   #
   # Create the parser
   parser = argparse.ArgumentParser()
   # Add arguments
   parser.add_argument('--date0', type=str, required=True, help='Start Date (yyyy-mm-dd)')
   parser.add_argument('--date1', type=str, required=True, help='End Date (yyyy-mm-dd)') 
   parser.add_argument('--lon0', type=float, required=True, help='Longitude min (-180°/180° convention)')
   parser.add_argument('--lon1', type=float, required=True, help='Longitude max (-180°/180° convention)')
   parser.add_argument('--lat0', type=float, required=True, help='Latitude min')
   parser.add_argument('--lat1', type=float, required=True, help='Latitude max')
   parser.add_argument('--mode', type=str, required=True, help='mode: Near Real Time (NRT) or Reanalysis (MY)') 
   parser.add_argument('--model', type=str, required=True, help='Analysis & Forecasting system acronyme (eg.: GLO, IBI, MED, BAL, BLK, NWS, ORCA36)')
   parser.add_argument('--obs', type=str, required=True, help='Altimetric satellite data acronyme (eg.: AVISO, AVISO_EU)')
   parser.add_argument('--area', type=str, required=True, help='Area name you defined according to your coord lon0, lon1, lat0, lat1')
   parser.add_argument('--cells', type=float, required=True, help='Size of cells for number of eddies by day and mean radius, GRID_SIZE° * GRID_SIZE°, ex: 1°*1°')
   parser.add_argument('--folder', type=str, required=True, help='Downloaded file directory')
   # Parse the argument
   args = parser.parse_args()
   #
   date_start = args.date0
   date_end = args.date1
   xmin = args.lon0
   xmax = args.lon1
   ymin = args.lat0
   ymax = args.lat1
   mode = args.mode
   model_acro = args.model
   obs_acro = args.obs
   area = args.area
   GRID_SIZE = args.cells
   data_dir = args.folder
   print ("Start Date = ",date_start)
   print ("End Date = ",date_end) 
   print ("Longitude min = ",xmin)
   print ("Longitude max = ",xmax)
   print ("Latitude min = ",ymin)
   print ("Latitude max = ",ymax)
   print ("mode = ",mode)
   print ("Analysis & Forecasting system = ",model_acro)
   print ("Altimetric satellite data = ",obs_acro)
   print ("Area name = ",area) 
   print ("Cells size = ",GRID_SIZE)
   print ("Downloaded file directory = ",data_dir)
   #
   # ------------------------------------
   #   Run of the different components
   # ------------------------------------
   #    - Input data loading
   proc1 = subprocess.run([r'eddy_load', "--date0",date_start, "--date1",date_end, "--lon0",str(xmin), "--lon1",str(xmax), "--lat0",str(ymin), "--lat1",str(ymax), "--mode",mode, "--model",model_acro, "--obs",obs_acro, "--area",area, "--folder",data_dir]) 
   #    - Model eddy detection
   proc2 = subprocess.run([r'eddy_detect', '--mode', mode, '--acro', model_acro, "--area",area, '--folder', data_dir])
   #    - Obs eddy detection
   proc3 = subprocess.run([r'eddy_detect', '--mode', mode, '--acro', obs_acro, "--area",area, '--folder', data_dir])
   #    - Model eddy tracking
   proc4 = subprocess.run([r'eddy_track', '--acro', model_acro, "--area",area, '--folder', data_dir])
   #    - Obs eddy tracking
   proc5 = subprocess.run([r'eddy_track', '--acro', obs_acro, "--area",area, '--folder', data_dir])
   #    - eddy diagnostics model vs obs
   proc6 = subprocess.run([r'eddy_diags', '--date0', date_start, '--lon0', str(xmin), '--lon1', str(xmax), '--lat0', str(ymin), '--lat1', str(ymax), '--model', model_acro, '--obs', obs_acro, "--area",area, "--cells", str(GRID_SIZE), '--folder', data_dir])
   #
# Run the main code
if __name__ == "__main__":
    print('eddy_run')
    main()
#
# =========================================================================
