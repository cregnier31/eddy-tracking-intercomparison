# ---------------
# USER PARAMETERS
# ---------------
#
# Geo. domain
#    - IBI
#xmin=-19.
#xmax=5.
#ymin=26.
#ymax=56.
#   - GLO
xmin=-180.
xmax=180.
ymin=-70.
ymax=70.
zmin=0.5
zmax=0.5
# Input MDS GLO12 data set
DATASET_ID_MOD_SSV = "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"
DATASET_ID_MOD_SSH = "cmems_mod_glo_phy_anfc_0.083deg_P1D-m"
# Input MDS IBI data set
#DATASET_ID_MOD_SSV = "cmems_mod_ibi_phy_anfc_0.027deg-3D_P1D-m"
#DATASET_ID_MOD_SSH = "cmems_mod_ibi_phy_anfc_0.027deg-3D_P1D-m"
ssu_mod_name = "uo"
ssv_mod_name = "vo"
ssh_mod_name = "zos"
time_mod_name = "time"
depth_mod_name = "depth"
lat_mod_name = "latitude"
lon_mod_name = "longitude"
dimt_mod_name = "time"
dimz_mod_name = "depth"           
dimy_mod_name = "latitude"
dimx_mod_name = "longitude"
# model resolution
#   - GLO
res_mod = 1 / 12.
#   - IBI
#res_mod = 1 / 36.
# Output files
#   - filename
dirout_mod = "/home/jovyan/work/DATA/GLO/"
fileout_mod_pre = "GLO"
#dirout_mod = "/home/jovyan/work/DATA/IBI/"
#fileout_mod_pre = "IBI"
#   - attributes
unit_ssu_attr = "m/s"
lname_ssu_attr = "Eastward velocity"
sname_ssu_attr = "eastward_sea_water_velocity"
#
unit_ssv_attr = "m/s"
lname_ssv_attr = "Northward velocity"
sname_ssv_attr = "northward_sea_water_velocity"
#
unit_ssh_attr = "m"
lname_ssh_attr = "Sea surface height"
sname_ssh_attr = "sea_surface_height_above_geoid"
#
unit_time_attr = "hours since 1950-01-01 00:00:00"
lname_time_attr = "Time (hours since 1950-01-01)"
sname_time_attr = "time"
#
unit_depth_attr = "m"
lname_depth_attr = "Depth"
sname_depth_attr = "depth"
#
unit_lat_attr = "degrees_north"
lname_lat_attr = "Latitude"
sname_lat_attr = "latitude"
#
unit_lon_attr = "degrees_east"
lname_lon_attr = "Longitude"
sname_lon_attr = "longitude"
#
# Plot parameters
#    - Title of the plot
title_1 = "GLO"
#title_1 = "IBI"
title_2 = "OBS EQUIVALENT"
title_3 = "OBS"
#    - space between lon & lat ticks
#       - for IBI
lon_ticks = 3
lat_ticks = 5
#    - Colormap
#       - colorbar
colorbar ='nipy_spectral'
#       - Min and max values for colormap
minvalue_ssu = -0.5
maxvalue_ssu = 0.5
minvalue_ssv = -0.5
maxvalue_ssv = 0.5
minvalue_ssh = -0.5
maxvalue_ssh = 0.0
#        - stepvalue
stepvalue_ssu = 0.2
stepvalue_ssv = 0.2
stepvalue_ssh = 0.1
#        - format
#stepformat = '%i'
stepformat = '%3.1f'
#    - Legend and unit of the considered variable
unit_txt_ssu = "SSU [m/s]"
unit_txt_ssv = "SSV [m/s]"
unit_txt_ssh = "SSH [m]"
#    - Coord of the legend and unit in the plot frame (in lon/lat  coord)
X_TIME = xmin
Y_TIME = 20.
x_unit = xmin
y_unit = 20.
#
#    - Model/obs equivalent 
#          => model geostrophic current + Shapiro filter + interpolation on obs grid
mod_obs_equi = False # equivalent calculation if True
ugos_mod_name = "ugos"   # zonal model geostrophic current component
lname_ugos_attr = "Absolute geostrophic velocity: zonal component"
sname_ugos_attr = "surface_geostrophic_eastward_sea_water_velocity"
vgos_mod_name = "vgos"   # meridian model geostrophic current component
lname_vgos_attr = "Absolute geostrophic velocity: meridian component"
sname_vgos_attr = "surface_geostrophic_northward_sea_water_velocity"
#missval = np.nan # missing value of the model data
# for GLO12 vs AVISO 1/4°
#nb_shapi = 20 # nb of Shapiro loops
# for GLO12 vs AVISO 1/8°
# for GLO12 vs AVISO 1/16°
nb_shapi = 1 # nb of Shapiro loops
# for IBI vs AVISO 1/16°
#nb_shapi = 10 # nb of Shapiro loops
# for IBI vs AVISO 1/8°
#nb_shapi = 30 # nb of Shapiro loops
# output dir and file for model/obs equivalent
#dirout_mod_equi = "/home/jovyan/work/DATA/GLO_EQUI/GLO_vs_AVISO/"
dirout_mod_equi = "/home/jovyan/work/DATA/GLO_EQUI/GLO_vs_AVISO_EU/"
#dirout_mod_equi = "/home/jovyan/work/DATA/IBI_EQUI/"
#
# =========================================================================
