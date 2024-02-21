# copernicusmarine subset --dataset-id cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable uo --variable vo --start-datetime 2023-01-01T00:00:00 --end-datetime 2023-12-29T00:00:00 --minimum-longitude -70 --maximum-longitude 10 --minimum-latitude 10 --maximum-latitude 60 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574 --output-filename GLO12_CURR_2023_NA.nc --force-download

# copernicusmarine subset --dataset-id cmems_mod_glo_phy_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable zos --start-datetime 2023-01-01T00:00:00 --end-datetime 2023-12-31T00:00:00 --minimum-longitude -70 --maximum-longitude 10 --minimum-latitude 10 --maximum-latitude 60 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574 --output-filename GLO12_ZOS_2023_NA.nc --force-download


copernicusmarine subset --dataset-id cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable uo --variable vo --start-datetime 2024-02-01T00:00:00 --end-datetime 2024-02-01T00:00:00 --minimum-longitude -180 --maximum-longitude 179.91668701171875 --minimum-latitude -80 --maximum-latitude 90 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574  --output-filename GLO12_CURR_2023_NA.nc --force-download

copernicusmarine subset --dataset-id cmems_mod_glo_phy_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable zos --start-datetime 2024-02-01T00:00:00 --end-datetime 2024-02-01T00:00:00 --minimum-longitude -180 --maximum-longitude 179.91668701171875 --minimum-latitude -80 --maximum-latitude 90 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574 --output-filename GLO12_ZOS_2023_NA.nc --force-download


echo "Data downloaded"

ncatted -O -a units,uo,o,c,m/s "GLO12_CURR_2023_NA.nc"  ## change name for zonal velocity if not uo
ncatted -O -a units,vo,o,c,m/s  "GLO12_CURR_2023_NA.nc"  ## change name for meridian velocity if not vo
echo "Units changed"

ncks -A  "GLO12_CURR_2023_NA.nc" "GLO12_ZOS_2023_NA.nc"

mv "GLO12_ZOS_2023_NA.nc" "GLO12_2023_NA.nc"
rm "GLO12_CURR_2023_NA.nc"

echo "The data is in one file:)"


# FILEIN='GLO12_2023_NA'
# DIROUT='/work/DATA/GLO12_2023_NA/'
# PREOUT='GLO12_NA'
# DATE_START=20230101	
# DATE_END=20231231
# nan='NaN'

# # DIROUT must be empty !
# #
# YYYY_START=`echo ${DATE_START} | cut -c 1-4`
# MM_START=`echo ${DATE_START} | cut -c 5-6`
# DD_START=`echo ${DATE_START} | cut -c 7-8`
# YYYY_END=`echo ${DATE_END} | cut -c 1-4`
# MM_END=`echo ${DATE_END} | cut -c 5-6`
# DD_END=`echo ${DATE_END} | cut -c 7-8`
# # Julian day period
# JUL_START=`./PREPROCESS/d2j ${DATE_START}`
# JUL_END=`./PREPROCESS/d2j ${DATE_END}` 
# echo "JUL_START: ${JUL_START}, JUL_END: ${JUL_END}"

# #
# # Daily means
# # -----------
# for JUL in `seq ${JUL_START} ${JUL_END}`
# do
# DATE=`./j2d ${JUL}`
# i_time=`echo "${JUL}-${JUL_START}" | bc`
#    #if [ ${CONFIG} == 'SST_L4' ] || [ ${CONFIG} == 'SSH_L4' ]
#    #then
# ncks -d time,${i_time} ${DIRIN}${FILEIN}.nc ${DIROUT}${PREOUT}_${DATE}.nc


# done