# ---------------
# USER PARAMETERS
# ---------------
#
# Input satellite obs data
# AVISO 1/4° GLOBAL
# DATASET_ID_OBS = "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.25deg_P1D" # up to 2024-11
#DATASET_ID_OBS = "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D"
# AVISO 1/8° EUROPE
#DATASET_ID_OBS = "cmems_obs-sl_eur_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D"
#DATASET_ID_OBS = "cmems_obs-sl_eur_phy-ssh_nrt_allsat-l4-duacs-0.0625deg_P1D"
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
# Output files
#dirout_obs = "/home/jovyan/work/DATA/AVISO/"
#dirout_obs = "/home/jovyan/work/DATA/AVISO_EU/"
#fileout_obs_pre = "AVISO"
#fileout_obs_pre = "AVISO_EU"
#
# =========================================================================
