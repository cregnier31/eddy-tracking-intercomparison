#!/usr/bin/env python3
###########################################################
#
#                         LOADER
#
###########################################################
#
# Description : Load MDS model and obs files and put them 
#               into the right format for py_eddy-tracking
#               tool with uo, vo, and ssh variables in the 
#               required units.
# Authors     : S. Cailleau
# Version     : 06/08/2024
#
############################################################
#
# ---------------
#    IMPORT
# ---------------
import copernicusmarine as cm
import xarray as xr
import numpy as np
import datetime
import datetime as dt
import os
import sys
import shutil
import matplotlib.pyplot as plt
from pyregrid.make_mask import make_mask
from pyregrid.interp import interp
sys.path.append("./")
import eddy_load.my_functions as fn # use of homemade function modules
from eddy_load.my_classes import *  # use of homemade class modules
#
# ---------------
# USER PARAMETERS
# ---------------
#
from eddy_load.namelist_mod import *
from eddy_load.namelist_obs import *
#
def main():
   #
   #   - Main parameters in arguments
   #     
   if (len(sys.argv)==11):
      # Considered period (in arguments)
      date_start = str(sys.argv[1])
      date_end = str(sys.argv[2])
      xmin = float(sys.argv[3])
      xmax = float(sys.argv[4])
      ymin = float(sys.argv[5])
      ymax = float(sys.argv[6])
      mode = str(sys.argv[7])
      model_acro = str(sys.argv[8])
      obs_acro = str(sys.argv[9])
      data_dir = str(sys.argv[10])
      print ("Date start = ",date_start)
      print ("Date end = ",date_end)
      print ("Longitude min = ",xmin)
      print ("Longitude max = ",xmax)
      print ("Latitude min = ",ymin)
      print ("Latitude max = ",ymax)
      print ("Mode = ",mode)
      print ("Analysis & Forecasting or reanalysis system = ",model_acro)
      print ("Altimetric satellite data = ",obs_acro)
      print ("Downloaded file directory = ",data_dir)
   else:
      print ("!!! ERROR: 10 arguments to be chosen !!!")
      print ("Argument 1 = Date start (yyyy-mm-dd)")
      print ("Argument 2 = Date end (yyyy-mm-dd)")
      print ("Argument 3 = Longitude min (-180/180° longitude convention)")
      print ("Argument 4 = Longitude max (-180/180° longitude convention)")
      print ("Argument 5 = Latitude min (-90/90° latitude convention)")
      print ("Argument 6 = Latitude max (-90/90° latitude convention)")
      print ("Argument 7 = NRT or MY datasets")
      print ("Argument 8 = Analysis & Forecasting system (GLO, IBI, ... (for MDS))")
      print ("Argument 9 = Altimetric satellite data (AVISO, AVISO_EU)")
      print ("Argument 10 = Downloaded file directory")
      sys.exit()
   #
   #   - Dataset from the model chosen data 
   if mode == 'NRT':
      DATASET_ID_MOD_SSV = data_mod_dict_NRT[model_acro][0]
      DATASET_ID_MOD_SSH = data_mod_dict_NRT[model_acro][1]
      ssu_mod_name = data_mod_dict_NRT[model_acro][2]
      ssv_mod_name = data_mod_dict_NRT[model_acro][3]
      ssh_mod_name = data_mod_dict_NRT[model_acro][4]
      zmin = data_mod_dict_NRT[model_acro][5]
      zmax =data_mod_dict_NRT[model_acro][6] 
      time_mod_name = data_mod_dict_NRT[model_acro][7]
      depth_mod_name = data_mod_dict_NRT[model_acro][8]
      lat_mod_name = data_mod_dict_NRT[model_acro][9]
      lon_mod_name = data_mod_dict_NRT[model_acro][10]
      dimt_mod_name = data_mod_dict_NRT[model_acro][11]
      dimz_mod_name = data_mod_dict_NRT[model_acro][12]       
      dimy_mod_name = data_mod_dict_NRT[model_acro][13]
      dimx_mod_name = data_mod_dict_NRT[model_acro][14]
      res_mod = data_mod_dict_NRT[model_acro][15]
   elif mode == 'MY':
      DATASET_ID_MOD_SSV = data_mod_dict_MY[model_acro][0]
      DATASET_ID_MOD_SSH = data_mod_dict_MY[model_acro][1]
      ssu_mod_name = data_mod_dict_MY[model_acro][2]
      ssv_mod_name = data_mod_dict_MY[model_acro][3]
      ssh_mod_name = data_mod_dict_MY[model_acro][4]
      zmin = data_mod_dict_MY[model_acro][5]
      zmax =data_mod_dict_MY[model_acro][6]
      time_mod_name = data_mod_dict_MY[model_acro][7]
      depth_mod_name = data_mod_dict_MY[model_acro][8]
      lat_mod_name = data_mod_dict_MY[model_acro][9]
      lon_mod_name = data_mod_dict_MY[model_acro][10]
      dimt_mod_name = data_mod_dict_MY[model_acro][11]
      dimz_mod_name = data_mod_dict_MY[model_acro][12]       
      dimy_mod_name = data_mod_dict_MY[model_acro][13]
      dimx_mod_name = data_mod_dict_MY[model_acro][14]
      res_mod = data_mod_dict_MY[model_acro][15] 
   #
   #   - Copernicus dataset IDs from the obs chosen data (AVISO, AVISO_EU)
   if mode == 'NRT':
      DATASET_ID_OBS = data_obs_dict_NRT[obs_acro]
   elif mode == 'MY':
      DATASET_ID_OBS = data_obs_dict_MY[obs_acro]
   #
   # ----------------------------------
   #
   # Make data directories
   dirout_mod = data_dir+"/"+model_acro+"/"
   dirout_obs = data_dir+"/"+obs_acro+"/"
   dirout_mod_equi = data_dir+"/"+model_acro+"_EQUI/" 
   if not os.path.exists(dirout_mod):
      os.mkdir(dirout_mod)
   if not os.path.exists(dirout_obs):
      os.mkdir(dirout_obs)
   if mod_obs_equi:
      if not os.path.exists(dirout_mod_equi):
         os.mkdir(dirout_mod_equi)
      if not os.path.exists(dirout_mod_equi+"FIG/"):    
         os.mkdir(dirout_mod_equi+"FIG/")
   # Absolute Workdir
   workdir = os.getcwd()+"/"
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
      fileout_mod = model_acro+"_"+date+".nc"
      #
      if model_acro == "ORCA36":
          # 
          #   - Load native orca grid model data through edito S3 bucket
          #     --------------------------------------------------------
          # 
          #      NB.: ORCA36 available simulation period : 20160101 => 20181231
          #
          # Input files
          #
          filein_ssu = DATASET_ID_MOD_SSV+"_"+date+"-"+date+"_"+ssu_mod_name+".zarr"
          filein_ssv = DATASET_ID_MOD_SSV+"_"+date+"-"+date+"_"+ssv_mod_name+".zarr"
          filein_ssh = DATASET_ID_MOD_SSH+"_"+date+"-"+date+"_"+ssh_mod_name+".zarr"

          if jul == jul_start:
             #
             # Spatial extraction (one times)
             #
             dataset = (xr.open_dataset(filein_ssh, engine="zarr")).isel(time_counter=slice(0,1)) # time extraction (dim time index = 0) just while defining spatial extraction indexes
             longitude = dataset[lon_mod_name].values
             latitude = dataset[lat_mod_name].values
             indexes = fn.nearest_orca_point(xmin, ymin, longitude, latitude)
             imin = indexes[0]
             jmin = indexes[1]
             indexes = fn.nearest_orca_point(xmax, ymax, longitude, latitude)
             imax = indexes[0]
             jmax = indexes[1]

             print("lon min = ",longitude[imin,jmin])
             print("lat min = ",latitude[imin,jmin])
             print("lon max = ", longitude[imax,jmax])
             print("lat max = ", latitude[imax, jmax])
          #
          # Model sea surface height
          # ------------------------
          #
          # pyregrid namelist for interpolating ORCA gridT to regular grid
          shutil.copyfile(workdir+"eddy_load/namelist_pyregrid_T.yaml", workdir+"namelist_pyregrid.yaml")
          #
          dataset = (xr.open_dataset(filein_ssh, engine="zarr")).isel(x=slice(imin, imax), y=slice(jmin, jmax))

          lon_mod = np.ones((imax-imin, jmax-jmin))
          lat_mod = np.ones((imax-imin, jmax-jmin))
          lon_mod[:, :] = longitude[imin:imax, jmin:jmax]
          lon_mod = lon_mod.transpose()  # longitude(y,x) instead of (x,y): same dim order than ssh, ssu, ssv variables
          lat_mod[:, :] = latitude[imin:imax, jmin:jmax]
          lat_mod = lat_mod.transpose()  # latitude(y,x) instead of (x,y): same dim order than ssh, ssu, ssv variables
          ssh_mod = dataset[ssh_mod_name].values
          ssh_mod = np.mean(ssh_mod, axis = (0)) # daily mean from hourly data
          
          data_vars = {
            ssh_mod_name: ((dimy_mod_name, dimx_mod_name), ssh_mod),
            lat_mod_name: ((dimy_mod_name, dimx_mod_name), lat_mod),
            lon_mod_name: ((dimy_mod_name, dimx_mod_name), lon_mod)
            }
          # New dataset
          ds = xr.Dataset(data_vars)
          #
          ds.to_netcdf(dirout_mod+"ssh_tmp.nc")
          #
          # parameters for interpolation
          f = dirout_mod+"ssh_tmp.nc"
          name_grid_in = model_acro+"_NG"
          name_grid_out = model_acro+"_RG"
          method = "bilin"
          lg_drown = False
          conservative_method = "None"
          maskin = "meshmask_"+name_grid_in+".nc"
          maskout = dirout_mod+"meshmask_"+name_grid_out+".nc"
          #
          if not os.path.exists(dirout_mod+maskin):
             # Make mesh maskin/out if not available (To do be done only once!):
             # Creation of meshmask_{name_grid_in}.nc
             fillvalue = np.nan
             make_mask(name_grid_in, f, ssh_mod_name, fillvalue)
              
             shutil.move(maskin, dirout_mod)

             stepy = res_mod
             stepx = res_mod
             lat = np.arange(ymin, ymax, stepy)
             lon = np.arange(xmin, xmax, stepx)
    
             #mask = np.ones((1, 1, len(lat), len(lon)))
             mask = np.ones((1, 1, len(lat), len(lon)))

             mesh = xr.Dataset()
             mesh['lon'] = ('x', lon)
             mesh['lat'] = ('y', lat)
             mesh['depth'] = ('z', [0])
             #mesh['mask'] = (('t', 'z', 'y', 'x'), mask)
             mesh['mask'] = (('t', 'z', 'y', 'x'), mask)
             mesh.to_netcdf(maskout)
          #
          # Interpolation
          #
          maskin = dirout_mod+maskin
          op = interp(
              f,
              ssh_mod_name,
              "t",
              "",
              name_grid_in,
              maskin,
              name_grid_out,
              maskout,
              method,
              conservative_method,
              lg_drown,
              False,
              np.array([0])
          )
          #    - Make weights if not available (To do be done only once!)
          if not os.path.isfile(op.wfile):
             op.make_vertices()
          #    - Interpolation
          data = op.read_file()
          ssh_interp = op.horizontal_interp(data)
          
          ssh_mod = np.ones((1, len(lat), len(lon)))  # 3D array (t, y, x) on regular lon/lat grid
          ssh_mod[0,:,:] = ssh_interp[:,:]
          #
          # Zonal surface model current
          # ---------------------------
          #
          # namelist
          shutil.copyfile(workdir+"eddy_load/namelist_pyregrid_U.yaml", workdir+"namelist_pyregrid.yaml")
          dataset = (xr.open_dataset(filein_ssu, engine="zarr")).isel(x=slice(imin, imax), y=slice(jmin, jmax))
          #lon_mod = dataset['nav_lon'].values # orca grid u
          #lat_mod = dataset['nav_lat'].values
          ssu_mod = dataset[ssu_mod_name].values
          ssu_mod = np.mean(ssu_mod, axis = (0)) # daily mean from hourly data

          data_vars = {
                      ssu_mod_name: ((dimy_mod_name, dimx_mod_name), ssu_mod),
                      lat_mod_name: ((dimy_mod_name, dimx_mod_name), lat_mod),
                      lon_mod_name: ((dimy_mod_name, dimx_mod_name), lon_mod)
                      }
          # New dataset
          ds = xr.Dataset(data_vars)
          #
          ds.to_netcdf(dirout_mod+"ssu_tmp.nc")
          #
          # parameters for interpolation
          f = dirout_mod+"ssu_tmp.nc"
          #
          # Interpolation
          #
          op = interp(
              f,
              ssu_mod_name,
              "u",
              "x",
              name_grid_in,
              maskin,
              name_grid_out,
              maskout,
              method,
              conservative_method,
              lg_drown,
              False,
              np.array([0])
          )
          #    - Make weights if not available (To do be done only once!)
          if not os.path.isfile(op.wfile):
             op.make_vertices()
          if not os.path.isfile(op.projection_wfile):
             op.make_projection_weights()
          #    - Interpolation
          data = op.read_file()
          ssu_interp = op.horizontal_interp(data)
          ssu_interp_x, ssu_interp_y = op.projection(ssu_interp)
          #
          # Meridian surface model current  
          # ------------------------------
          #
          # namelist
          shutil.copyfile(workdir+"eddy_load/namelist_pyregrid_V.yaml", workdir+"namelist_pyregrid.yaml")
          dataset = (xr.open_dataset(filein_ssv, engine="zarr")).isel(x=slice(imin, imax), y=slice(jmin, jmax))
          #lon_mod = dataset['nav_lon'].values # orca grid v
          #lat_mod = dataset['nav_lat'].values
          ssv_mod = dataset[ssv_mod_name].values
          ssv_mod = np.mean(ssv_mod, axis = (0)) # daily mean from hourly data

          data_vars = {
                      ssv_mod_name: ((dimy_mod_name, dimx_mod_name), ssv_mod),
                      lat_mod_name: ((dimy_mod_name, dimx_mod_name), lat_mod),
                      lon_mod_name: ((dimy_mod_name, dimx_mod_name), lon_mod)
                      }
          # New dataset
          ds = xr.Dataset(data_vars)
          #
          ds.to_netcdf(dirout_mod+"ssv_tmp.nc")
          #
          # parameters for interpolation
          f = dirout_mod+"ssv_tmp.nc"
          #
          # Interpolation
          #
          op = interp(
              f,
              ssv_mod_name,
              "v",
              "y",
              name_grid_in,
              maskin,
              name_grid_out,
              maskout,
              method,
              conservative_method,
              lg_drown,
              False,
              np.array([0])
          )
          #    - Make weights (for vector) if not available (To do be done only once!)
          if not os.path.isfile(op.wfile):
             op.make_vertices()
          if not os.path.isfile(op.projection_wfile):
             op.make_projection_weights()
          #    - Interpolation
          data = op.read_file()
          ssv_interp = op.horizontal_interp(data)
          # vector projection 
          ssv_interp_x, ssv_interp_y = op.projection(ssv_interp)
          #
          # final vector rotation from native grid to regular one
          ssu_interp = ssu_interp_x + ssv_interp_x
          ssv_interp = ssu_interp_y + ssv_interp_y
          ssu_mod = np.ones((1, 1, len(lat), len(lon)))  # 4D array (t, z, y, x) on regular lon/lat grid
          ssv_mod = np.ones((1, 1, len(lat), len(lon)))  # 4D array
          ssu_mod[0,0,:,:] = ssu_interp[:,:]
          ssv_mod[0,0,:,:] = ssv_interp[:,:]

          lon_mod = lon
          lat_mod = lat
          lon_mod_name = "longitude"
          lat_mod_name = "latitude"
          depth_mod = [zmin]
          time_mod =  [jul * 24] # hours since 1950-01-01T00:00:00

          # cleanning : remove tmp files from dirout_mod
          os.remove(dirout_mod+"ssh_tmp.nc")
          os.remove(dirout_mod+"ssu_tmp.nc")
          os.remove(dirout_mod+"ssv_tmp.nc")
          #   
      else:
         # 
         #   - Load standard model data through MDS API
         #     ----------------------------------------
         #
         print("-----------------------------------------------")
         print("Input model data - Surface Current ")
         print("-----------------------------------------------")
         print("DATASET_ID = "+DATASET_ID_MOD_SSV)
         print("-----------------------------------------------")
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
            variables = data_request["variables"])
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
         #
         ssu_mod = data_mod_ssv.variables[ssu_mod_name].values
         ssv_mod = data_mod_ssv.variables[ssv_mod_name].values
         ssh_mod = data_mod_ssh.variables[ssh_mod_name].values
         depth_mod = data_mod_ssv.variables[depth_mod_name].values
         time_mod = [jul * 24] # hours since 1950-01-01T00:00:00
         lat_mod = data_mod_ssv.variables[lat_mod_name].values
         lon_mod = data_mod_ssv.variables[lon_mod_name].values
         #
         # --------------------------------
         #
      #
      #   - Write nc file gathering ssu, ssv and ssh 
      #     with the right units following the Eddy_Tracking file format     
      #ssu_mod_name = uo
      #ssv_mod_name = vo
      #ssh_mod_name = zos
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
      fileout_obs = obs_acro+"_"+date+".nc"
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
         fileout_mod_equi = model_acro+"_EQUI_"+date+".nc"      
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
   # Cleanning : remove weight, mask and projection files from dirout_mod
   if model_acro == "ORCA36":
       os.remove(dirout_mod+"meshmask_"+model_acro+"_NG.nc")
       os.remove(dirout_mod+"meshmask_"+model_acro+"_RG.nc")
       os.remove(dirout_mod+"weights_bilin_"+model_acro+"_NG-"+model_acro+"_RG_gridu.nc")
       os.remove(dirout_mod+"weights_bilin_"+model_acro+"_NG-"+model_acro+"_RG_gridv.nc")
       os.remove(dirout_mod+"weights_bilin_"+model_acro+"_NG-"+model_acro+"_RG_gridt.nc")
       os.remove(dirout_mod+"nc_projection_weights_"+model_acro+"_NG_to_"+model_acro+"_RG_gridu.nc")
       os.remove(dirout_mod+"nc_projection_weights_"+model_acro+"_NG_to_"+model_acro+"_RG_gridv.nc")
       os.remove(dirout_mod+"projection_weights_"+model_acro+"_NG_to_"+model_acro+"_RG_gridu.nc")
       os.remove(dirout_mod+"projection_weights_"+model_acro+"_NG_to_"+model_acro+"_RG_gridv.nc")
#
# Run the main code
if __name__ == "__main__":
    main()
#
# =========================================================================
