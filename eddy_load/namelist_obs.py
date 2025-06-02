#!/usr/bin/env python3
# ---------------
# USER PARAMETERS
# ---------------
#
# Input satellite obs data
# data_obs_dir = { obs_acro : DATASET_ID_OBS }
# SL-TAC NRT datasets
data_obs_dict_NRT = { "AVISO" : "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
                  "AVISO_EU" : "cmems_obs-sl_eur_phy-ssh_nrt_allsat-l4-duacs-0.0625deg_P1D" }
# SL-TAC MY datasets ==> delayed mode from 1993 up to 6 months before RT
data_obs_dict_MY = { "AVISO" : "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D",
                  "AVISO_EU" : "cmems_obs-sl_eur_phy-ssh_my_allsat-l4-duacs-0.0625deg_P1D" }
#
ssu_obs_name = "ugos"
ssv_obs_name = "vgos"
ssh_obs_name = "adt"
lat_obs_name = "latitude"
lon_obs_name = "longitude"
# Obs resolution
# AVISO
res_obs = 1 / 8.
# AVISO-EU
#res_obs = 1 / 16.
#
# =========================================================================