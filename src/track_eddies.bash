#!bin/bash

#Activate environment

#Run eddy tracking command from py_eddy_tracker
eddy_type=Cyclonic  #Cyclonic or anticyclonic (Careful works only if file named $eddy_type.nc)
#eddy_type=Anticyclonic  #Cyclonic or anticyclonic (Careful works only if file named $eddy_type.nc)
tracking_method=overlap   #or conf.yaml  #overlap or cost method

DIR_IN=/home/jbrouillet/eddy-tracking-intercomparison/result-ref/
DIR_OUT=/home/jbrouillet/eddy-tracking-intercomparison/dt-ref/
#Prepare config .yaml file for eddy tracking
cp ${tracking_method}_template.yaml ${tracking_method}.yaml  #create a copy
sed -i 's+DIR_IN+'${DIR_IN}'+g' ${tracking_method}.yaml  #replace with correct DIR_IN path,
                                                         #note "+" replaces '/' delimiter character
sed -i 's+DIR_OUT+'${DIR_OUT}'+g' ${tracking_method}.yaml #Same for dir_out
sed -i 's+EDDY_TYPE+'$eddy_type'+g' ${tracking_method}.yaml #Same for dir_out
#print out config file
echo "Configuration for tracking:"
cat ${tracking_method}.yaml

echo "nb of " ${eddy_type} "files:"
ls -l ${DIR_IN}/${eddy_type}*.nc | wc -l

echo "\ntrack eddies:"
EddyTracking ${tracking_method}.yaml #-v DEBUG
#set verbose add  -v DEBUG

echo ".oO Eddy Tracking Done Oo."
