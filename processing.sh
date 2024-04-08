copernicusmarine subset --dataset-id cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable uo --variable vo --start-datetime 2023-01-01T00:00:00 --end-datetime 2023-03-31T00:00:00  --minimum-longitude -180 --maximum-longitude 179.9166717529297 --minimum-latitude -80 --maximum-latitude 90 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574 --output-filename GLO12_CURR.nc --force-download

copernicusmarine subset --dataset-id cmems_mod_glo_phy_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable zos --start-datetime 2023-01-01T00:00:00 --end-datetime 2023-03-31T00:00:00 --minimum-longitude -180 --maximum-longitude 179.9166717529297 --minimum-latitude -80 --maximum-latitude 90 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574 --output-filename GLO12_ZOS.nc --force-download



copernicusmarine subset --dataset-id cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.25deg_P1D --force-dataset-version 202311 --variable adt --variable ugos --variable vgos --start-datetime 2023-01-01T00:00:00 --end-datetime 2023-03-31T00:00:00 --minimum-longitude -180 --maximum-longitude 179.9166717529297 --minimum-latitude -80 --maximum-latitude 90 --output-filename AVISO.nc --force-download 


echo "Data downloaded"

ncatted -O -a units,uo,o,c,m/s "GLO12_CURR.nc"  ## change name for zonal velocity if not uo
ncatted -O -a units,vo,o,c,m/s  "GLO12_CURR.nc"  ## change name for meridian velocity if not vo


ncatted -O -a units,ugos,o,c,m/s "AVISO.nc"  ## change name for zonal velocity if not uo
ncatted -O -a units,vgos,o,c,m/s  "AVISO.nc"  ## change name for meridian velocity if not vo
echo "Units changed"

ncks -A  "GLO12_CURR.nc" "GLO12_ZOS.nc"

mv "GLO12_ZOS.nc" "GLO12.nc"
rm "GLO12_CURR.nc"


FILEIN='GLO12'
DIROUT='/home/onyxia/work/DATA/GLO12/'
PREOUT='GLO12'

FILEIN_REF='AVISO'
DIROUT_REF='/home/onyxia/work/DATA/AVISO/'
PREOUT_REF='AVISO'

## Format YYYYMMDD
DATE_START=20230101	
DATE_END=20230331
nan='NaN'

# Créer le répertoire DIROUT s'il n'existe pas
mkdir -p "$DIROUT"
# Créer le répertoire DIROUT_REF s'il n'existe pas
mkdir -p "$DIROUT_REF"

# DIROUT must be empty !
#
YYYY_START=`echo ${DATE_START} | cut -c 1-4`
MM_START=`echo ${DATE_START} | cut -c 5-6`
DD_START=`echo ${DATE_START} | cut -c 7-8`
YYYY_END=`echo ${DATE_END} | cut -c 1-4`
MM_END=`echo ${DATE_END} | cut -c 5-6`
DD_END=`echo ${DATE_END} | cut -c 7-8`
# Julian day period
JUL_START=`./PREPROCESS/d2j ${DATE_START}`
JUL_END=`./PREPROCESS/d2j ${DATE_END}` 
echo "JUL_START: ${JUL_START}, JUL_END: ${JUL_END}"

#
# Daily means
# -----------
for JUL in `seq ${JUL_START} ${JUL_END}`
do
DATE=`./PREPROCESS/j2d ${JUL}`
i_time=`echo "${JUL}-${JUL_START}" | bc`
   #if [ ${CONFIG} == 'SST_L4' ] || [ ${CONFIG} == 'SSH_L4' ]
   #then
ncks -d time,${i_time} ${DIRIN}${FILEIN}.nc ${DIROUT}${PREOUT}_${DATE}.nc
ncks -d time,${i_time} ${DIRIN_REF}${FILEIN_REF}.nc ${DIROUT_REF}${PREOUT_REF}_${DATE}.nc

done

echo "Done"