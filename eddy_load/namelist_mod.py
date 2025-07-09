#!/usr/bin/env python3
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
#xmin=-180.
#xmax=180.
#ymin=-70.
#ymax=70.
#    - MED
#xmin=17.29
#xmax=36.30
#ymin=30.18
#ymax=45.98
#   - NWS
#xmin=-16
#xmax=10
#ymin=46
#ymax=61
#   - BAL
#xmin=9
#xmax=30
#ymin=53
#ymax=66
#   - BLK
#xmin=27.25
#xmax=41.1
#ymin=40.5
#ymax=47
#
# Input MDS data set
# data_mod_dict = { model_acro : [ DATASET_ID_MOD_SSV,  
#                                  DATASET_ID_MOD_SSH, 
#                                  ssu_mod_name, 
#                                  ssv_mod_name, 
#                                  ssh_mod_name, 
#                                  zmin, 
#                                  zmax,
#                                  time_mod_name,
#                                  depth_mod_name,
#                                  lat_mod_name,
#                                  lon_mod_name,
#                                  dimt_mod_name,
#                                  dimz_mod_name,
#                                  dimy_mod_name,
#                                  dimx_mod_name,
#                                  res_mod
#                                ] }
#data_mod_dict = dict()
# NRT datasets (from MDS but also other model data
# NB.: ARC not available in regular mercator grid, only on stereographic grid ==> ARC removed from the MFC choice
data_mod_dict_NRT = { "GLO" : [ "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m", 
                                "cmems_mod_glo_phy_anfc_0.083deg_P1D-m", 
                                "uo", 
                                "vo", 
                                "zos", 
                                0.51, 
                                0.51,
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                1 / 12.
                              ],
                      "IBI" : [ "cmems_mod_ibi_phy_anfc_0.027deg-3D_P1D-m", 
                                "cmems_mod_ibi_phy_anfc_0.027deg-3D_P1D-m", 
                                "uo", 
                                "vo", 
                                "zos", 
                                0.51, 
                                0.51,
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                1 / 36.
                              ],
                      "MED" : [ "cmems_mod_med_phy-cur_anfc_4.2km_P1D-m",
                                "cmems_mod_med_phy-ssh_anfc_4.2km_P1D-m",
                                "uo", 
                                "vo", 
                                "zos", 
                                1.02, 
                                1.02, 
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                1 / 36.
                              ],
                      "NWS" : [ "cmems_mod_nws_phy_anfc_0.027deg-3D_P1D-m", 
                                "cmems_mod_nws_phy_anfc_0.027deg-3D_P1D-m", 
                                "uo", 
                                "vo", 
                                "zos", 
                                0.51, 
                                0.51,
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                1 / 36.
                              ],
                      "BAL" : [ "cmems_mod_bal_phy_anfc_P1D-m", 
                                "cmems_mod_bal_phy-ssh_anfc_detided_P1D-m", 
                                "uo", 
                                "vo", 
                                "zos_detided", 
                                0.51, 
                                0.51,
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                1 / 36.
                              ],
                      "BLK" : [ "cmems_mod_blk_phy-cur_anfc_2.5km_P1D-m", 
                                "cmems_mod_blk_phy-ssh_anfc_2.5km_P1D-m", 
                                "uo", 
                                "vo", 
                                "zos", 
                                0.51, 
                                0.51, 
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                "time",
                                "depth",
                                "latitude",
                                "longitude",
                                1 / 36.
                              ] }
#
# MFC MY datasets !!! not interim ==> delayed mode from 1993 !!!
# NB. ssh for BAL isn't available, only sla ==> BAL is remove from this choice for MY datasets
data_mod_dict_MY = { "GLO" : [ "cmems_mod_glo_phy_my_0.083deg_P1D-m", 
                               "cmems_mod_glo_phy_my_0.083deg_P1D-m", 
                               "uo", 
                               "vo", 
                               "zos", 
                               0.51, 
                               0.51,
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               1 / 12.
                             ],
                     "IBI" : [ "cmems_mod_ibi_phy_my_0.083deg-3D_P1D-m", 
                               "cmems_mod_ibi_phy_my_0.083deg-3D_P1D-m", 
                               "uo", 
                               "vo", 
                               "zos", 
                               0.51, 
                               0.51, 
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               1 / 36.
                             ],
                     "MED" : [ "med-cmcc-cur-rean-d", 
                               "med-cmcc-ssh-rean-d", 
                               "uo", 
                               "vo", 
                               "zos", 
                               1.02, 
                               1.02,
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               1 / 36.
                             ],
                     "NWS" : [ "cmems_mod_nws_phy-uv_my_7km-3D_P1D-m", 
                               "cmems_mod_nws_phy-ssh_my_7km-2D_P1D-m", 
                               "uo", 
                               "vo", 
                               "zos", 
                               0., 
                               0., 
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               1 / 36.
                             ],
                     "BLK" : [ "cmems_mod_blk_phy-cur_my_2.5km_P1D-m", 
                               "cmems_mod_blk_phy-ssh_my_2.5km_P1D-m", 
                               "uo", 
                               "vo", 
                               "zos", 
                               0.51, 
                               0.51,
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               "time",
                               "depth",
                               "latitude",
                               "longitude",
                               1 / 36.
                             ],
                  "ORCA36" : [ "https://s3.waw3-1.cloudferro.com/ORCA36/ORCA36-T426a_1hAV", 
                               "https://s3.waw3-1.cloudferro.com/ORCA36/ORCA36-T426a_1hAV", 
                               "uos", 
                               "vos", 
                               "sossheig", 
                               0.51, 
                               0.51,
                               "time_counter",
                               "depth",
                               "nav_lat",
                               "nav_lon",
                               "time",
                               "depth",
                               "y",
                               "x",
                               1 / 36.
                             ] }
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
X_TIME = -19
Y_TIME = 20.
x_unit = -19
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
#dirout_mod_equi = "/home/jovyan/work/DATA/GLO_EQUI/GLO_vs_AVISO_EU/"
#dirout_mod_equi = "/home/jovyan/work/DATA/IBI_EQUI/"
#
# =========================================================================
