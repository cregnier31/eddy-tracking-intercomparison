#!/usr/bin/env python3
###########################################################
#
#                     EDDY TRACKING
#
###########################################################
#
# Description : Creates cyclonic and anticyclonic 
#               tracking files by using overlap tracking  
#               method
#
# Authors     : S. Cailleau, F. Dubost, C. Reignier
#
# Version     : 05/2025
#
############################################################
#
# ---------------
#     IMPORT
# ---------------
#
import os
import sys
import argparse
import shutil
from pathlib import Path
#
def main():
   #
   # ---------------
   # USER PARAMETERS
   # --------------- 
   #
   #    - Main parameters in arguments
   #  
   # Create the parser
   parser = argparse.ArgumentParser()
   # Add arguments
   parser.add_argument('--acro', type=str, required=True, help='Analysis & Forecasting system acronyme (eg.: GLO, IBI, MED, BAL, BLK, NWS, ORCA36) or altimetry data acronyme (eg.: AVISO, AVISO_EU)')
   parser.add_argument('--area', type=str, help='Area name you defined according to your coord lon0, lon1, lat0, lat1')
   parser.add_argument('--folder', type=str, required=True, help='Input file directory')
   # Parse the argument
   args = parser.parse_args()
   #
   data_acro = args.acro
   area = args.area
   data_dir = args.folder
   print ("Input data = ",data_acro)
   print ("Area name = ",area)
   print ("Input data directory = ",data_dir)
   #
   # ---------------
   # 
   eddy_types = ["Cyclonic", "Anticyclonic"]
   tracking_method = "overlap" 
   # Chemins relatifs
   conf_template = os.path.join(os.path.dirname(__file__), str(tracking_method+"_template.yaml"))
   #conf_template = f"eddy_track/{tracking_method}_template.yaml"
   conf_file = os.path.join(os.path.dirname(__file__), str(tracking_method+".yaml"))
   #conf_file = f"eddy_track/{tracking_method}.yaml"

   DIR_IN = data_dir+"/"+data_acro+"/"+area+"/DETECT/"
   DIR_OUT = data_dir+"/"+data_acro+"/"+area+"/TRACK/"

   for eddy_type in eddy_types:
      # Préparer le fichier de config YAML
      shutil.copy(conf_template, conf_file)

      with open(conf_file, "r") as f:
         content = f.read()

      content = content.replace("DIR_IN", DIR_IN)
      content = content.replace("DIR_OUT", DIR_OUT)
      content = content.replace("EDDY_TYPE", eddy_type)

      with open(conf_file, "w") as f:
         f.write(content)

      # Afficher le contenu du fichier de config
      print("Configuration for tracking:")
      with open(conf_file, "r") as f:
         print(f.read())
 
      # Compter le nombre de fichiers .nc pour le type d'eddy
      eddy_files = list(Path(DIR_IN).glob(f"{eddy_type}*.nc"))
      print(f"Number of {eddy_type} files: {len(eddy_files)}")

      # Lancer le tracking
      print("Track eddies:")
      os.system(f"EddyTracking {conf_file}")
      print(".oO Eddy Tracking Done Oo.")
       #
# Run the main code
if __name__ == "__main__":
    main()       
#
# ===========================================
