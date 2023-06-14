#!bin/bash

#Activate environment

DIR_IN=/data/rd_exchange/fdubost/EddyDetection/FDUBOST/nrt/GLO12V4/Detect_eddies_2019_SE55/
DIR_OUT=/home/fdubost/DEV/Eddy_DetectAndTrack/scr/tracking_test/

eddy_types=("Cyclonic" "Anticyclonic")
tracking_method="overlap"

for eddy_type in "${eddy_types[@]}"
do
    # Prepare config .yaml file for eddy tracking
    cp ${tracking_method}_template.yaml ${tracking_method}.yaml
    sed -i 's+DIR_IN+'${DIR_IN}'+g' ${tracking_method}.yaml
    sed -i 's+DIR_OUT+'${DIR_OUT}'+g' ${tracking_method}.yaml
    sed -i 's+EDDY_TYPE+'$eddy_type'+g' ${tracking_method}.yaml
    
    # Print out config file
    echo "Configuration for tracking:"
    cat ${tracking_method}.yaml

    # Count the number of eddy files
    echo "Number of ${eddy_type} files:"
    ls -l ${DIR_IN}/${eddy_type}*.nc | wc -l

    echo "Track eddies:"
    EddyTracking ${tracking_method}.yaml -v DEBUG

    echo ".oO Eddy Tracking Done Oo."
done


     
