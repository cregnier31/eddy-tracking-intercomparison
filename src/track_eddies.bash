#!/bin/bash

#Activate environment

DIR_IN=/home/onyxia/work/DATA/DETECT_GLO12/
DIR_OUT=/home/onyxia/work/DATA/TRACKING_GLO12/

eddy_types=("Cyclonic" "Anticyclonic")
tracking_method="overlap"

for eddy_type in "${eddy_types[@]}"
do
    # Prepare config .yaml file for eddy tracking
    cp ../confs/${tracking_method}_template.yaml ../confs/${tracking_method}.yaml
    sed -i 's+DIR_IN+'${DIR_IN}'+g' ../confs/${tracking_method}.yaml
    sed -i 's+DIR_OUT+'${DIR_OUT}'+g' ../confs/${tracking_method}.yaml
    sed -i 's+EDDY_TYPE+'$eddy_type'+g' ../confs/${tracking_method}.yaml

    # Print out config file
    echo "Configuration for tracking:"
    cat ../confs/${tracking_method}.yaml

    # Count the number of eddy files
    echo "Number of ${eddy_type} files:"
    ls -l ${DIR_IN}/${eddy_type}*.nc | wc -l

    echo "Track eddies:"
    EddyTracking ../confs/${tracking_method}.yaml 

    echo ".oO Eddy Tracking Done Oo."
done
