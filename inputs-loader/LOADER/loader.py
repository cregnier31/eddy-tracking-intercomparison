# ==========================================================
#
#                         LOADER
#
# ==========================================================
#
# Description : Load MDS model and obs files and put them 
#               into the right format for py_eddy-tracking
#               tool with uo, vo, and ssh variables in the 
#               required units.
# Authors     : S. Cailleau
# Version     : 06/08/2024
#
# ===========================================================
#
# ---------------
# Used Libraries
# ---------------
import copernicusmarine as cm
import xarray as xr
import numpy as np
import datetime
import datetime as dt
import os
import sys
import matplotlib.pyplot as plt
sys.path.append("../MY_TOOLS/")
import my_functions as fn # use of homemade function modules
from my_classes import *  # use of homemade class modules
#
# ---------------
# USER PARAMETERS
# ---------------
if (len(sys.argv)==3):
   # Considered period (in arguments)
   date_start = str(sys.argv[1])
   date_end = str(sys.argv[2])
   print ("Date start = ",date_start)
   print ("Date end = ",date_end)
else:
   print ("!!! ERROR: 2 arguments to be chosen !!!")
   print ("Argument 1 = Date start (yyyy-mm-dd)")
   print ("Argument 2 = Date end (yyyy-mm-dd)")
   sys.exit()
#
from namelist_mod import *
from namelist_obs import *
#
# Make data directories
if not os.path.exists(dirout_mod):
   os.mkdir(dirout_mod)
if not os.path.exists(dirout_obs):
   os.mkdir(dirout_obs)
if mod_obs_equi:
   if not os.path.exists(dirout_mod_equi):
      os.mkdir(dirout_mod_equi)
   if not os.path.exists(dirout_mod_equi+"FIG/"):    
      os.mkdir(dirout_mod_equi+"FIG/")
#
# Time Loop
#
d_date = CnesJulianCal()
d_start = date_start[0:4]+date_start[5:7]+date_start[8:10]
d_end = date_end[0:4]+date_end[5:7]+date_end[8:10]
jul_start = d_date.tojulian(d_start)
jul_end = d_date.tojulian(d_end)
jul = jul_start
while jul <= jul_end:
   time_mod = []
   date = d_date.fromjulian(jul)
   date_mds = date[0:4]+"-"+date[4:6]+"-"+date[6:8]  # mds date format yyyy-mm-dd
   print("*******************")
   print("DATE = ",date_mds)
   print("*******************")
   #
   # ----------
   # MODEL DATA
   # ----------
   #   
   #   - Load model data through MDS API
   #
   print("-----------------------------------------------")
   print("Input model data - Surface Current ")
   print("-----------------------------------------------")
   print("DATASET_ID = "+DATASET_ID_MOD_SSV)
   print("-----------------------------------------------")
   #
   fileout_mod = fileout_mod_pre+"_"+date+".nc"
   #
   #   - Set parameters
   data_request = {
      "dataset_id_mod_ssv" : DATASET_ID_MOD_SSV,
      "longitude" : [xmin, xmax], 
      "latitude" : [ymin, ymax],
      "depth" : [zmin, zmax],
      "time" : [date_mds, date_mds],
      "variables" : [ssu_mod_name, ssv_mod_name]
   }   
   #    - Load xarray dataset for ssu, ssv
   data_mod_ssv = cm.open_dataset(
      dataset_id = data_request["dataset_id_mod_ssv"],
      minimum_longitude = data_request["longitude"][0],
      maximum_longitude = data_request["longitude"][1],
      minimum_latitude = data_request["latitude"][0],
      maximum_latitude = data_request["latitude"][1],
      minimum_depth = data_request["depth"][0],
      maximum_depth = data_request["depth"][1],
      start_datetime = data_request["time"][0],
      end_datetime = data_request["time"][1],
      variables = data_request["variables"]
   )
   ssu_mod = data_mod_ssv.variables[ssu_mod_name].values
   ssv_mod = data_mod_ssv.variables[ssv_mod_name].values
   time_mod = [jul * 24] # hours since 1950-01-01T00:00:00
   depth_mod = data_mod_ssv.variables[depth_mod_name].values
   lat_mod = data_mod_ssv.variables[lat_mod_name].values   
   lon_mod = data_mod_ssv.variables[lon_mod_name].values
   #
   print("-----------------------------------------------")
   print("Input model data - Sea Surface Height ")
   print("-----------------------------------------------")
   print("DATASET_ID = "+DATASET_ID_MOD_SSH)
   print("-----------------------------------------------")
   #   - Set parameters
   data_request = {
      "dataset_id_mod_ssh" : DATASET_ID_MOD_SSH,
      "longitude" : [xmin, xmax], 
      "latitude" : [ymin, ymax],
      "time" : [date_mds, date_mds],
      "variables" : [ssh_mod_name]
   }   
   #    - Load xarray dataset for ssh
   data_mod_ssh = cm.open_dataset(
      dataset_id = data_request["dataset_id_mod_ssh"],
      minimum_longitude = data_request["longitude"][0],
      maximum_longitude = data_request["longitude"][1],
      minimum_latitude = data_request["latitude"][0],
      maximum_latitude = data_request["latitude"][1],
      start_datetime = data_request["time"][0],
      end_datetime = data_request["time"][1],
      variables = data_request["variables"]
   )
   ssh_mod = data_mod_ssh.variables[ssh_mod_name].values
   #
   #   - Write nc file gathering ssu, ssv and ssh 
   #     with the right units following the Eddy_Tracking file format        
   fn.mds2eddy_track(dirout_mod,
                     fileout_mod,
                     ssu_mod,
                     ssv_mod,
                     ssh_mod,
                     time_mod,
                     depth_mod,
                     lat_mod,
                     lon_mod,        
                     dimt_mod_name,
                     dimz_mod_name,
                     dimy_mod_name,
                     dimx_mod_name,
                     ssu_mod_name,
                     ssv_mod_name,
                     ssh_mod_name,
                     time_mod_name,
                     depth_mod_name,
                     lat_mod_name,
                     lon_mod_name,
                     unit_ssu_attr,
                     lname_ssu_attr,
                     sname_ssu_attr,
                     unit_ssv_attr,
                     lname_ssv_attr,
                     sname_ssv_attr,
                     unit_ssh_attr,
                     lname_ssh_attr,
                     sname_ssh_attr,
                     unit_time_attr,
                     lname_time_attr,
                     sname_time_attr,
                     unit_depth_attr,
                     lname_depth_attr,
                     sname_depth_attr,
                     unit_lat_attr,
                     lname_lat_attr,
                     sname_lat_attr,
                     unit_lon_attr,
                     lname_lon_attr,
                     sname_lon_attr
                     )
   #
   # ----------------
   # OBSERVATION DATA
   # ----------------
   #   
   #   - Load obs data through MDS API
   #
   print("-----------------------------------------------")
   print("Input obs data")
   print("-----------------------------------------------")
   print("DATASET_ID = "+DATASET_ID_OBS)
   print("-----------------------------------------------")
   #
   fileout_obs = fileout_obs_pre+"_"+date+".nc"
   if os.path.isfile(dirout_obs+fileout_obs):
      os.remove(dirout_obs+fileout_obs) 
   #
   #   - Set parameters
   data_request = {
      "dataset_id_obs" : DATASET_ID_OBS,
      "longitude" : [xmin, xmax],
      "latitude" : [ymin, ymax],
      "time" : [date_mds, date_mds],
      "variables" : [ssu_obs_name, ssv_obs_name, ssh_obs_name],
      "directory" : dirout_obs,
      "file" : fileout_obs
   }   
   #    - Download MDS file of the obs dataset by using subsetting to extract ssu, ssv and ssh
   data_obs = cm.subset(
      dataset_id = data_request["dataset_id_obs"],
      minimum_longitude = data_request["longitude"][0],
      maximum_longitude = data_request["longitude"][1],
      minimum_latitude = data_request["latitude"][0],
      maximum_latitude = data_request["latitude"][1],
      start_datetime = data_request["time"][0],
      end_datetime = data_request["time"][1],
      variables = data_request["variables"],
      output_filename = data_request["file"],
      output_directory = data_request["directory"],
      force_download=True
   )
   #
   # -------------------------
   # MODEL/OBS EQUIVALENT DATA
   # -------------------------
   #  
   if mod_obs_equi:
      #
      #     - Load xarray obs dataset
      #
      data_obs = xr.open_dataset(dirout_obs+fileout_obs)
      ssu_obs = data_obs.variables[ssu_obs_name].values
      ssv_obs = data_obs.variables[ssv_obs_name].values  
      ssh_obs = data_obs.variables[ssh_obs_name].values
      lat_obs = data_obs.variables[lat_obs_name].values
      lon_obs = data_obs.variables[lon_obs_name].values   
      #
      #    - Model/obs ssh shift
      #
      ssh_shift = np.nanmean(ssh_obs) - np.nanmean(ssh_mod)
      print("ssh shift mod/obs = ", ssh_shift)
      #
      #    - Geostrophic model current from ssh
      #
      #         py-eddy-tracker tool uses ssh, ugos and vgos from obs data such as AVISO for its detection creteria. So to be fully consistent with obs, we must also consider ugos and vgos from model data, and then here the geostrophic model current is calculated from the model ssh to get the model/obs equivalent. 
      #
      ugos, vgos = fn.geos_current(res_mod, lat_mod, ssh_mod)
      # reset ssu_mod and ssv_mod to replace by ugos and vgos values
      ugos_mod = np.ones((1, 1, len(lat_mod), len(lon_mod)))  # 4D array
      vgos_mod = np.ones((1, 1, len(lat_mod), len(lon_mod)))  # 4D array
      ugos_mod[0,0,:,:] = ugos[:,:]
      vgos_mod[0,0,:,:] = vgos[:,:]
      #
      if res_mod < res_obs:
         #
         #   - Shapiro filter
         #
         #        higher resolution model data must be smoothed before interpolating
         #        on coarser obs grid data to prevent sampling errors. To smooth, we will choose
         #        a nb of Shapiro filter loops to reach approximately the effective resolution of the obs data
         missval = np.nan
         ugos_mod_filt = fn.shapiro_1d(ugos_mod, nb_shapi, missval, True)
         vgos_mod_filt = fn.shapiro_1d(vgos_mod, nb_shapi, missval, True)
         ssh_mod_filt = fn.shapiro_1d(ssh_mod, nb_shapi, missval, False)
         #
         #   - Interpolation on a common model/obs grid
         #       
         #         Data interpolation on the coarser grid following a nearest point method
         #         If ref model regular grid resolution > obs regular grid resolution 
         #         => model dataset fitted to the obs grid for the equivalent model/obs
         #
         list_i_interp = []
         list_j_interp = []
         ugos_mod_interp = np.ones((1, 1, len(lat_obs), len(lon_obs)))
         vgos_mod_interp = np.ones((1, 1, len(lat_obs), len(lon_obs))) 
         ssh_mod_interp = np.ones((1, len(lat_obs), len(lon_obs)))
         lat_mod_interp = lat_obs
         lon_mod_interp = lon_obs 
         #      
         for target_lat in lat_obs:
            list_j_interp.append(fn.get_nearest_position_sorted_array_float(lat_mod, target_lat))
         for target_lon in lon_obs:
            list_i_interp.append(fn.get_nearest_position_sorted_array_float(lon_mod, target_lon))
         for j in range(len(lat_obs)):
            j_interp = list_j_interp[j]
            for i in range(len(lon_obs)):
               i_interp = list_i_interp[i]
               ugos_mod_interp[0, 0, j, i] = ugos_mod_filt[0, 0, j_interp, i_interp]
               vgos_mod_interp[0, 0, j, i] = vgos_mod_filt[0, 0, j_interp, i_interp]
               ssh_mod_interp[0, j, i] = ssh_mod_filt[0, j_interp, i_interp]
      else:
         ugos_mod_interp = ugos_mod
         vgos_mod_interp = vgos_mod
         ssh_mod_interp = ssh_mod
         lat_mod_interp = lat_mod
         lon_mod_interp = lon_mod
      #
      #   - Write nc file gathering ssu, ssv and ssh model/obs equivalent
      #     with the right units following the Eddy_Tracking file format 
      #
      fileout_mod_equi = fileout_mod_pre+"_EQUI_"+date+".nc"      
      fn.mds2eddy_track(dirout_mod_equi,
                     fileout_mod_equi,
                     ugos_mod_interp,
                     vgos_mod_interp,
                     ssh_mod_interp,
                     time_mod,
                     depth_mod,
                     lat_mod_interp,
                     lon_mod_interp,        
                     dimt_mod_name,
                     dimz_mod_name,
                     dimy_mod_name,
                     dimx_mod_name,
                     ugos_mod_name,
                     vgos_mod_name,
                     ssh_mod_name,
                     time_mod_name,
                     depth_mod_name,
                     lat_mod_name,
                     lon_mod_name,
                     unit_ssu_attr,
                     lname_ugos_attr,
                     sname_ugos_attr,
                     unit_ssv_attr,
                     lname_vgos_attr,
                     sname_vgos_attr,
                     unit_ssh_attr,
                     lname_ssh_attr,
                     sname_ssh_attr,
                     unit_time_attr,
                     lname_time_attr,
                     sname_time_attr,
                     unit_depth_attr,
                     lname_depth_attr,
                     sname_depth_attr,
                     unit_lat_attr,
                     lname_lat_attr,
                     sname_lat_attr,
                     unit_lon_attr,
                     lname_lon_attr,
                     sname_lon_attr
                     )
      #
      #   - Plot to monitor the processing (filter + interpolation)
      #
      if jul == jul_start: # plot to monitor the processing (geos current + filter + interpolation)
         # 2D dimension data for plot function
         ugos_mod_interp_2D = ugos_mod_interp[0, 0, :, :]
         ssu_mod_2D = ssu_mod[0, 0, :, :]
         ssu_obs_2D = ssu_obs[0, :, :]
         # plot for ssu    
         fn.three_panel_plt_color(ssu_mod_name, jul, xmin, xmax, ymin, ymax, lon_mod, lat_mod, ssu_mod_2D, minvalue_ssu, maxvalue_ssu, colorbar, title_1, date_mds, lon_mod_interp, lat_mod_interp, ugos_mod_interp_2D, title_2, unit_txt_ssu, lon_obs, lat_obs, ssu_obs_2D, title_3, stepvalue_ssu, stepformat, X_TIME, Y_TIME, x_unit, y_unit)
         plt.savefig(dirout_mod_equi+"FIG/ssu_equi.png",dpi=100,bbox_inches="tight",pad_inches=0.2)
         plt.close()
         # 2D dimension data for plot function
         vgos_mod_interp_2D = vgos_mod_interp[0, 0, :, :]
         ssv_mod_2D = ssv_mod[0, 0, :, :]
         ssv_obs_2D = ssv_obs[0, :, :]         
         # plot for ssv
         fn.three_panel_plt_color(ssv_mod_name, jul, xmin, xmax, ymin, ymax, lon_mod, lat_mod, ssv_mod_2D, minvalue_ssv, maxvalue_ssv, colorbar, title_1, date_mds, lon_mod_interp, lat_mod_interp, vgos_mod_interp_2D, title_2, unit_txt_ssv, lon_obs, lat_obs, ssv_obs_2D, title_3, stepvalue_ssv, stepformat, X_TIME, Y_TIME, x_unit, y_unit)
         plt.savefig(dirout_mod_equi+"FIG/ssv_equi.png",dpi=100,bbox_inches="tight",pad_inches=0.2)
         plt.close()
         # 2D dimension data for plot function
         ssh_mod_interp_2D = ssh_mod_interp[0, :, :]
         ssh_mod_2D = ssh_mod[0, :, :]
         ssh_obs_2D = ssh_obs[0, :, :]
         ssh_obs_2D = ssh_obs_2D - ssh_shift
         # plot for ssh
         fn.three_panel_plt_color(ssh_mod_name, jul, xmin, xmax, ymin, ymax, lon_mod, lat_mod, ssh_mod_2D, minvalue_ssh, maxvalue_ssh, colorbar, title_1, date_mds, lon_mod_interp, lat_mod_interp, ssh_mod_interp_2D, title_2, unit_txt_ssh, lon_obs, lat_obs, ssh_obs_2D, title_3, stepvalue_ssh, stepformat, X_TIME, Y_TIME, x_unit, y_unit)
         plt.savefig(dirout_mod_equi+"FIG/ssh_equi.png",dpi=100,bbox_inches="tight",pad_inches=0.2)
         plt.close()
   #
   jul += 1
#
# =========================================================================
