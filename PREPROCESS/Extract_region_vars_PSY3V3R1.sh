#!/bin/bash


#SBATCH -J NCO_job
##SBATCH --time=00:60:00
#SBATCH -p mono
#SBATCH -o nco_out.%j.out
#SBATCH -e nco_out.%j.err
#SBATCH -N 1
#SBATCH --ntasks-per-node=2
#SBATCH --exclusive
#Nom du job
#SBATCH -J  EXTRACT_BIOVAR_JOB
YEAR=2021
#MODEL=GLO12V4
MODEL=PSY4V3R1
zlevel=0   #11

FLIST=list_${MODEL}_y${YEAR}_01.txt
echo $FLIST
OUT_DIR=/data/rd_exchange/svangennip/MODEL_OUTPUT/${MODEL}/PGS/${YEAR}/
#OUT_DIR=/data/rd_exchange/svangennip/MODEL_OUTPUT/PSY4V3R1/UV/surface/${YEAR}/
#f1=/data/rd_exchange2/svangennip/interp/PSY4V3_deg/mercatorpsy4v3_deg_GLO_y2008m03d10_UV.nc

if [ ! -d $OUT_DIR ]; then mkdir -p $OUT_DIR; fi # create output dir
n=0
#LIST="gridU gridV gridT"

lat1=29.875
lat2=59.625
lon1=-90.125
lon2=-30.375


LIST_GRIDS="gl12_mean"

gridtype=($LIST_GRIDS)
zlevel=1
vars="zos,uo,vo,so,thetao" 
count=${#gridtype[@]} 
echo "count=" $count

for f in $( cat $FLIST )
#for f in $( head -2 $FLIST )
#for f in $( tail -76l $FLIST )
 do
  printf "\nf=$f\n"
  for i in `seq 1 $count`; do
    #echo '   i='$i
    grid_i=`echo ${gridtype[$i-1]}` 
    #echo '   grid='$grid_i 'var='$var_i 'zvar='$zvar_i gridtype0=${gridtype[0]}
    ff=`echo $f | sed -e 's/'${gridtype[0]}'/'${grid_i}'/'`
    #echo '   f_in='$ff

    #Generate output name
    fname="$(basename -- $ff)"  # retrieve filename
    #fname2=`echo $fname | sed -e 's/'${gridtype}'/'${gridtype}_surf'/'`
    fname2=`echo $fname | sed -e 's/'${grid_i}'/'${grid_i}'/'`
    f_temp=`echo $fname | sed -e 's/'${grid_i}'/'${grid_i}_temp'/'`
    #echo $fname2

    if [ ! -f $OUT_DIR/$fname2 ];then

       #1 extract surface only layer and wanted var
       # ncks -d dim,min[,max[,stride]] infile outfile
       echo ncks -F -A -d longitude,${lon1},${lon2} -d latitude,${lat1},$lat2 -d depth,${zlevel},${zlevel},1 -v $vars $ff ${OUT_DIR}/${fname2}
       ncks -F -A -d longitude,${lon1},${lon2} -d latitude,${lat1},$lat2 -d depth,${zlevel},${zlevel},1 -v $vars $ff ${OUT_DIR}/${fname2}
       #ncks -F -A -d depth,${zlevel},${zlevel},1 -v $vars $ff ${OUT_DIR}/${fname2}
       echo ncatted -O -a units,uo,o,c,m/s ${OUT_DIR}/${fname2} ${OUT_DIR}/${fname2}
       ncatted -O -a units,uo,o,c,m/s ${OUT_DIR}/${fname2} ${OUT_DIR}/${fname2}
       echo ncatted -O -a units,vo,o,c,m/s ${OUT_DIR}/${fname2} ${OUT_DIR}/${fname2}
       ncatted -O -a units,vo,o,c,m/s ${OUT_DIR}/${fname2} ${OUT_DIR}/${fname2}
 
       
    else
      echo $OUT_DIR/$fname2  " exists ..."
    fi
  
  done
done

