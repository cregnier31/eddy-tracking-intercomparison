#!/usr/bin/env python3
# ---------------
# USER PARAMETERS
# ---------------
#
# Input satellite obs data
# data_obs_dir = { obs_acro : [ DATASET_ID_OBS, 
#                               ssu_obs_name, 
#                               ssv_obs_name, 
#                               ssh_obs_name, 
#                               time_obs_name,
#                               lat_obs_name,
#                               lon_obs_name,
#                               dimt_obs_name,
#                               dimy_obs_name,
#                               dimx_obs_name,
#                               res_obs,
#                               scale_fac_obs] }
# SL-TAC NRT datasets
data_obs_dict_NRT = { "AVISO" : [ "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
                                 "ugos", 
                                 "vgos", 
                                 "adt", 
                                 "time",
                                 "latitude",
                                 "longitude",
                                 "time",
                                 "latitude",
                                 "longitude",
                                 1 / 8.,
                                 0.0001 ],
                  "AVISO_EU" : [ "cmems_obs-sl_eur_phy-ssh_nrt_allsat-l4-duacs-0.0625deg_P1D", 
                                 "ugos", 
                                 "vgos", 
                                 "adt", 
                                 "time",
                                 "latitude",
                                 "longitude",
                                 "time",
                                 "latitude",
                                 "longitude",
                                 1 / 16.,
                                 0.0001 ] }
# SL-TAC MY datasets ==> delayed mode from 1993 up to 6 months before RT
# scale factor in MY case : adt is in short int type & a scale factor must be applied
data_obs_dict_MY = { "AVISO" : [ "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D",
                                 "ugos", 
                                 "vgos", 
                                 "adt", 
                                 "time",
                                 "latitude",
                                 "longitude",
                                 "time",
                                 "latitude",
                                 "longitude",
                                 1 / 8.,
                                 0.0001 ],
                  "AVISO_EU" : [ "cmems_obs-sl_eur_phy-ssh_my_allsat-l4-duacs-0.0625deg_P1D",
                                 "ugos", 
                                 "vgos", 
                                 "adt", 
                                 "time",
                                 "latitude",
                                 "longitude",
                                 "time",
                                 "latitude",
                                 "longitude",
                                 1 / 16.,
                                 0.0001 ] }
#
# =========================================================================