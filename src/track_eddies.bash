#!/usr/bin/bash

#Activate environment

YEAR="2024"
QUARTER="all"

list_track="AVISO GLO12"
list_track="AVISO"
eddy_types=("Cyclonic" "Anticyclonic")
eddy_types=("Anticyclonic")
tracking_method="overlap"

for mod_track in $list_track
do
    DIR_IN=/home/smer/sval001/WORK/EDDY/DETECTIONS/${mod_track}/${YEAR}/${QUARTER}/
    DIR_OUT=/home/smer/sval001/WORK/EDDY/TRACKING/TRACKING_${mod_track}/${YEAR}/${QUARTER}/
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
       EddyTracking ../confs/${tracking_method}.yaml -v DEBUG
       #EddyTracking ../confs/${tracking_method}.yaml
       echo ".oO Eddy Tracking Done Oo."
   done
done
