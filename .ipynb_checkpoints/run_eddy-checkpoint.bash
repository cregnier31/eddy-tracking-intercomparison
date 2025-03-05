#!/bin/bash
#
# DETECTION 
#   - for model
#        Detection parameters to be modified in ../confs/Config_Detect-model.ini
python src/Detect_Eddies.py ../confs/Config_Detect-model.ini
#   - for reference obs
#        Detection parameters to be modified in ../confs/Config_Detect-ref.ini
python src/Detect_Eddies.py ../confs/Config_Detect-ref.ini
# TRACKING
#     Tracking parameters to be modified in ../confs/ overlap_template.yaml
bash src/track_eddies.bash
# PLOTS
#     analysis parameters to be modified in ../confs/Config_Analysis-fdubost.ini
python src/Analysis_Eddy_1model.py ../confs/Config_Analysis-fdubost.ini