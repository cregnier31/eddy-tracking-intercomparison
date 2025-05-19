#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path
#
def main():
   # ---------------
   # USER PARAMETERS
   # --------------- 
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
      print ("Argument 1 = Input data acronym (GLO, IBI, AVISO, AVISO-EU)")
      print ("Argument 2 = Idata directory")
      sys.exit()
   #
   # ---------------
   # 
   eddy_types = ["Cyclonic", "Anticyclonic"]
   tracking_method = "overlap" 
   # Chemins relatifs
   conf_template = f"eddy_track/{tracking_method}_template.yaml"
   conf_file = f"eddy_track/{tracking_method}.yaml"

   DIR_IN = data_dir+"/"+data_acro+"/DETECT/"
   DIR_OUT = data_dir+"/"+data_acro+"/TRACK/"

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
