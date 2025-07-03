#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 09:39:20 2023

@authors: Titouan Derreveaux, Sylvain Cailleau

Updated on Wed Mar 20 2024
"""
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from scipy.signal import butter, filtfilt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator, FixedLocator)
import matplotlib.dates as mdates
import cartopy
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
#
# ---------------------------------
# FIND NEAREST POINT FROM ORCA GRID
# ---------------------------------
def nearest_orca_point(lon0, lat0, longitude, latitude):
   #
   # Parameters: 
   #
   #    lon0 = longitude of the considered point 
   #    lat0 = Latitude of the considered point
   #    longitude = 2D array longitude of the chosen orca grid
   #    latitude = 2D array latiitude of the chosen orca grid
   #
   rpi=2*np.arcsin(1.)  # pi  
   degrad = rpi/180 # Conversion of degrees to radian
   ra = 6371.229  #  Average earth radius in kms
   # Compute spherical distance:
   lon0 = lon0*degrad
   lat0 = lat0*degrad
   longitude = longitude*degrad
   latitude = latitude*degrad

   dist = np.zeros_like(latitude)
   dlon = lon0 - longitude

   term1 = (np.cos(lat0) * np.sin(dlon))**2
   term2 = (np.cos(latitude) * np.sin(lat0) - np.sin(latitude) * np.cos(lat0) * np.cos(dlon))**2
   numerator = np.sqrt(term1 + term2)
   denominator = np.sin(latitude) * np.sin(lat0) + np.cos(latitude) * np.cos(lat0) * np.cos(dlon)

   dist = np.arctan2(numerator, denominator)

   # Trouver les indices où dist est minimal (équivalent à MAXLOC(..., .eq. MINVAL))
   min_val = np.min(dist)
   ijfound = np.argwhere(dist == min_val)

   # Pour récupérer un seul couple d'indices (le premier trouvé)
   iji_found = tuple(ijfound[0])
    
   return(iji_found)
#
# --------------------
# GEOSTROPHIC CURRENT 
# --------------------
def geos_current(res, lat, ssh):
   '''
   Calculate geostrophic current components from ssh 
   
   Parameters:
      - res = data resolution (cst)
      - lat = 1D latitude array depending on y-latitude dimension 
      - ssh = 3D (time, lat, lon) ssh array in regular Mercator grid
      
   Returns:
      3D (time, lat, lon) ugos and vgos geostrophic zonal and meridian current components:
         ugos = - (g / f) * dssh/dy
         vgos =   (g / f) * dssh/dx
           with f = 2 * omega * sin(lat)
           and (omega = 7.2921 . 10−5 rad/s
   '''
   earth_rad = 6371000. # earth radius in meter
   delta = res * earth_rad * np.pi / 180. # model resolution in meter
   dx = np.ones(len(lat))   # zonal model resolution in meter (vs latitude, for regular Mercator grid)
   dy = delta   # cst meridian model resolution in meter (for regular Mercator grid)
   omega = 7.2921 * 0.00001   # earth rotation
   f = np.ones(len(lat))   # Coriolis parameter (vs latitude, for regular grid)
   g = 9.81  # earth gravity cst
   #
   ssh = ssh[0,:,:] 
   shape_ssh = np.shape(ssh)
   len_lat = shape_ssh[0]
   len_lon =  shape_ssh[1]
   dssh_dx = np.ones((len_lat, len_lon))
   dssh_dy = np.ones((len_lat, len_lon))
   ugos = np.ones((len_lat, len_lon))
   vgos = np.ones((len_lat, len_lon))
   #
   # f parameter
   for j in range(len_lat-1):
      f[j] = 2 * omega * np.sin(lat[j] * np.pi / 180.)
   # ugos component
   for i in range(len_lon-1):
      dssh_dy[:, i] = np.gradient(ssh[:, i], dy)     # meridian partial derivative: dssh/dy
      ugos[:, i] = - (g / f[:]) * dssh_dy[:, i]  # zonal geostrophic current component
   # vgos component   
   for j in range(len_lat-1):
      dx[j] = delta * np.cos(lat[j] * np.pi / 180.)
      dssh_dx[j, :] = np.gradient(ssh[j, :], dx[j])  # zonal partial derivative dssh/dx
      vgos[j, :] = (g / f[j]) * dssh_dx[j, :]    # meridian geostrophic current components
   #
   return (ugos, vgos) 
#
# ---------------------------------------------
# MDS TO EDDY_TRACKING INPUT MODEL FILE FORMAT
# ---------------------------------------------
def mds2eddy_track(
             dirout,
             fileout,
             var_ssu,
             var_ssv,
             var_ssh,
             var_time,
             var_depth,            
             var_lat,
             var_lon,
             dimt_name,
             dimz_name,             
             dimy_name,
             dimx_name,
             var_ssu_name,
             var_ssv_name,
             var_ssh_name, 
             var_time_name,             
             var_depth_name,                         
             var_lat_name,
             var_lon_name,
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
             ):
   #
   # Definition of the dictionnaries : variables and coordinates + their attributes
   #  
   data_vars = {
                var_ssu_name: ((dimt_name, dimz_name, dimy_name, dimx_name), var_ssu,
                  {'units': unit_ssu_attr, 
                   'long_name': lname_ssu_attr,
                   'standard_name': sname_ssu_attr}),
                 var_ssv_name: ((dimt_name, dimz_name, dimy_name, dimx_name), var_ssv,
                  {'units': unit_ssv_attr, 
                   'long_name': lname_ssv_attr,
                   'standard_name': sname_ssv_attr}),
                 var_ssh_name: ((dimt_name, dimy_name, dimx_name), var_ssh,
                  {'units': unit_ssh_attr, 
                   'long_name': lname_ssh_attr,
                   'standard_name': sname_ssh_attr}),
                 var_time_name: ((dimt_name), var_time,
                  {'units': unit_time_attr, 
                   'long_name': lname_time_attr,
                   'standard_name': sname_time_attr}),
                 var_depth_name: ((dimz_name), var_depth,
                  {'units': unit_depth_attr, 
                   'long_name': lname_depth_attr,
                   'standard_name': sname_depth_attr}),  
                 var_lat_name: ((dimy_name),var_lat,
                  {'units': unit_lat_attr, 
                   'long_name': lname_lat_attr,
                   'standard_name': sname_lat_attr}),
                 var_lon_name: ((dimx_name),var_lon,
                  {'units': unit_lon_attr, 
                   'long_name': lname_lon_attr,
                   'standard_name': sname_lon_attr})
                 }
   # New dataset
   ds = xr.Dataset(data_vars)
   #
   ds.to_netcdf(dirout+fileout)
#
# ----------------------
#     SHAPIRO FILTER 
# space iterative filter
# ----------------------
def shapiro_1d(rla_varin, id_np, missval, ln_depth):
    """
    Apply a 1D Shapiro filter (3 points filter) horizontally to a 2D field
    for a regional domain (embedded in a global one).

    Parameters:
    rla_varin : numpy.ndarray
        Input variable to filter (3D or 4D array).
    id_np : int
        Number of Shapiro filter iterations.
    missval : float
        Missing value.
    ln_depth : boolean for nb of dim:
               - True => 4D input array with depth dim
               - False => 3D input array without depth dim

    Returns:
    rla_varout : numpy.ndarray
        Output filtered variable.
    """
    rl_alpha = 1. / 2.  # fixed stability coefficient
    #
    if ln_depth:   # 4D input array 
       # Allocate arrays
       jpi = rla_varin.shape[3]  # x dimension length
       jpj = rla_varin.shape[2]  # y dimension length
       print('------------------------------------------')
       print('            Shapiro Filter                ')
       print('------------------------------------------')
       print('')
       print('- nb of passages           = ', id_np)
       print('- nb of X grid point :jpi  = ', jpi)
       print('- nb of Y grid point :jpj = ', jpj)
       print('- ln_depth = ', ln_depth)
       print('')
       print('------------------------------------------')
       rla_varout = np.zeros((1, 1, jpj, jpi))
       rla_varout_tmp = np.zeros((1, 1, jpj, jpi))
       rla_mask = np.zeros((1, 1, jpj, jpi))
       #
       # Initialize mask
       #rla_mask[rla_varin == missval] = 0.0
       #rla_mask[rla_varin != missval] = 1.0
       for ji in range(0, jpi):
          for jj in range(0, jpj):
             if np.isnan(rla_varin[0, 0, jj, ji]):
                rla_mask[0, 0, jj, ji] = 0.0
             else:
                rla_mask[0, 0, jj, ji] = 1.0  
       #
       rla_varout_tmp[0, 0, :, :] = rla_varin[0, 0, :, :]
       #
       # Loop on several filter iterations
       for jn in range(id_np):  # nb of filter passages
          for ji in range(1, jpi - 1):
             for jj in range(1, jpj - 1):
                # We crop on the coast
                test1 = rla_mask[0, 0, jj, ji-1]
                test2 = rla_mask[0, 0, jj, ji]
                test3 = rla_mask[0, 0, jj, ji+1]
                test4 = rla_mask[0, 0, jj-1, ji]
                test5 = rla_mask[0, 0, jj+1, ji]
                if ((test1 == 1.0) and (test2 == 1.0) and (test3 == 1.0) and (test4 == 1.0) and (test5 == 1.0)):
                   znum = (rla_varout_tmp[0, 0, jj, ji] - 
                            0.25 * rl_alpha * 
                            (rla_mask[0, 0, jj, ji - 1] + rla_mask[0, 0, jj, ji + 1] +
                             rla_mask[0, 0, jj - 1, ji] + rla_mask[0, 0, jj + 1, ji]) *
                             rla_varout_tmp[0, 0, jj, ji])
                   znum += 0.25 * rl_alpha * (
                        rla_varout_tmp[0, 0, jj, ji - 1] * rla_mask[0, 0, jj, ji - 1] +
                        rla_varout_tmp[0, 0, jj, ji + 1] * rla_mask[0, 0, jj, ji + 1] +
                        rla_varout_tmp[0, 0, jj - 1, ji] * rla_mask[0, 0, jj - 1, ji] +
                        rla_varout_tmp[0, 0, jj + 1, ji] * rla_mask[0, 0, jj + 1, ji])
                   rla_varout[0, 0, jj, ji] = znum
                else:
                   rla_varout[0, 0, jj, ji] = rla_varin[0, 0, jj, ji]       
          #
          # Boundary conditions in case of regional ocean
          # - for the 1st and last line of latitude
          rla_varout[0, 0, 0, :] = rla_varout[0, 0, 1, :]
          rla_varout[0, 0, jpj - 1, :] = rla_varout[0, 0, jpj - 2, :]
          # - for the 1st and last row of longitude
          rla_varout[0, 0, :, 0] = rla_varout[0, 0, :, 1]
          rla_varout[0, 0, :, jpi - 1] = rla_varout[0, 0, :, jpi - 2]
          #
          rla_varout_tmp[0, 0, :, :] = rla_varout[0, 0, :, :]
          #
    else:   # 3D input array
       # Allocate arrays
       jpi = rla_varin.shape[2]  # x dimension length
       jpj = rla_varin.shape[1]  # y dimension length
       print('------------------------------------------')
       print('            Shapiro Filter                ')
       print('------------------------------------------')
       print('')
       print('- nb of passages           = ', id_np)
       print('- nb of X grid point :jpi  = ', jpi)
       print('- nb of Y grid point :jpj = ', jpj)
       print('- ln_depth = ', ln_depth)
       print('')
       print('------------------------------------------')
       rla_varout = np.zeros((1, jpj, jpi))
       rla_varout_tmp = np.zeros((1, jpj, jpi))
       rla_mask = np.zeros((1, jpj, jpi))
       #rla_mask = rla_varin
       #
       # Initialize mask
       #rla_mask[rla_varin == missval] = 0.0
       #rla_mask[rla_varin != missval] = 1.0
       for ji in range(0, jpi):
         for jj in range(0, jpj):
            if np.isnan(rla_varin[0, jj, ji]):
               rla_mask[0, jj, ji] = 0.0
            else:
               rla_mask[0, jj, ji] = 1.0
       #
       rla_varout_tmp[0, :, :] = rla_varin[0, :, :]
       #
       # Loop on several filter iterations
       for jn in range(id_np):  # nb of filter passages
          for ji in range(1, jpi-1):
             for jj in range(1, jpj-1):
                # We crop on the coast
                test1 = rla_mask[0, jj, ji-1]
                test2 = rla_mask[0, jj, ji]
                test3 = rla_mask[0, jj, ji+1]
                test4 = rla_mask[0, jj-1, ji]
                test5 = rla_mask[0, jj+1, ji]
                if ((test1 == 1.0) and \
                    (test2 == 1.0) and \
                    (test3 == 1.0) and \
                    (test4 == 1.0) and \
                    (test5 == 1.0)):
                   znum = (rla_varout_tmp[0, jj, ji] - 0.25 * rl_alpha         \
                        * (rla_mask[0, jj, ji - 1] + rla_mask[0, jj, ji + 1]   \
                        +  rla_mask[0, jj - 1, ji] +  rla_mask[0, jj + 1, ji]) \
                        *  rla_varout_tmp[0, jj, ji])
                   znum += 0.25 * rl_alpha                                          \
                        * (rla_varout_tmp[0, jj, ji - 1] * rla_mask[0, jj, ji - 1]  \
                        +  rla_varout_tmp[0, jj, ji + 1] * rla_mask[0, jj, ji + 1]  \
                        +  rla_varout_tmp[0, jj - 1, ji] * rla_mask[0, jj - 1, ji]  \
                        +  rla_varout_tmp[0, jj + 1, ji] * rla_mask[0, jj + 1, ji])
                   rla_varout[0, jj, ji] = znum
                else:
                   rla_varout[0, jj, ji] = rla_varin[0, jj, ji]
          #
          # Boundary conditions in case of regional ocean
          # - for the 1st and last line of latitude
          rla_varout[0, 0, :] = rla_varout[0, 1, :]
          rla_varout[0, jpj-1, :] = rla_varout[0, jpj - 2, :]
          # - for the 1st and last row of longitude
          rla_varout[0, :, 0] = rla_varout[0, :, 1]
          rla_varout[0, :, jpi-1] = rla_varout[0, :, jpi - 2]
          # 
          rla_varout_tmp[0, :, :] = rla_varout[0, :, :]
          #
    return rla_varout
#
# ---------------------
# GET POSITION IN ARRAY
# ---------------------
#
def get_nearest_position_sorted_array_float(array, val) :
    n = len(array)
    mini = 0
    maxi = n-1
    mid=(maxi+mini)//2
    if val<=float(array[mini]): 
        return(mini)
    elif val>=float(array[maxi]):
        return(maxi)
    while mini<=maxi :
        if val==float(array[mid]):
            return(mid)
        elif val==float(array[mini]):
            return(mini)
        elif val==float(array[maxi]):
            return(maxi)
        elif (maxi==mini+1 or maxi==mini) and val!=float(array[mini]) and val!=float(array[maxi]):
            dif=min(abs(val-float(array[mini])),abs(val-float(array[maxi])))
            if dif==abs(val-float(array[mini])):
                return(mini)
            return(maxi)
        elif val<float(array[mid]):
            maxi=mid
        elif val>float(array[mid]):
            mini=mid
        mid=(maxi+mini)//2
#
def get_nearest_position_sorted_array_int(array, val) :
    n = len(array)
    mini = 0
    maxi = n-1
    mid=(maxi+mini)//2
    while mini<=maxi :
        if val<array[mini]: 
            return(mini)
        elif val>array[maxi]:
            return(maxi)
        elif val<array[mid]:
            maxi=mid-1
        elif val>array[mid]:
            mini=mid+1
        elif (maxi==mini+1 or maxi==mini) and val!=array[mini] and val!=array[maxi]:
            dif=min(abs(val-array[mini]),abs(val-array[maxi]))
            if dif==abs(val-array[mini]):
                return(mini)
            return(maxi)
        else :
            return(mid)
        mid=(maxi+mini)//2
#
# ----------------------
# MAP PLOT WITH 3 PANELS
# ----------------------
#
def three_panel_plt_color(ocean_field, jul, xmin, xmax, ymin, ymax, lon_1, lat_1, var_1, minvalue, maxvalue, colorbar, title_1, TIME, lon_2, lat_2, var_2, title_2, unit_txt, lon_3, lat_3, var_3, title_3, stepvalue, stepformat, X_TIME, Y_TIME, x_unit, y_unit):   
        # 3-panel plot setup
        num_fig = jul
        fig = plt.figure(num_fig)    
        sproj = ccrs.PlateCarree()
        #    - Map background for each both plots
        #      ----------------------------------
        land_m = cartopy.feature.NaturalEarthFeature('physical','land','10m',edgecolor=[0.8,0.8,0.8], facecolor=[0.8,0.8,0.8])
        #
        #    - Panel 1
        #      -------
        #
        ax_1 = fig.add_subplot(1, 3, 1, projection=sproj)
        ax_1.set_extent([xmin, xmax, ymin, ymax], crs=sproj)
        #
        cs_1 = plt.pcolormesh(lon_1, lat_1, var_1, vmin=minvalue,vmax=maxvalue, cmap=colorbar)
        #          Axis - Draw gridlines in degrees over Mercator map
        gl = ax_1.gridlines(crs=sproj, draw_labels=True,
                    linewidth=.6, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'color': 'k'}
        gl.ylabel_style = {'color': 'k'}
        #          Title
        plt.title(title_1)
        plt.text(X_TIME, Y_TIME, TIME, horizontalalignment='center', transform=sproj)
        #          Land & coastlines
        ax_1.add_feature(land_m)
        ax_1.coastlines(resolution='10m')
        #
        #    - Panel 2
        #      -------
        #
        ax_2 = fig.add_subplot(1, 3, 2, projection=sproj)
        ax_2.set_extent([xmin, xmax, ymin, ymax], crs=sproj)
        #
        cs_2 = plt.pcolormesh(lon_2, lat_2, var_2, vmin=minvalue,vmax=maxvalue, cmap=colorbar)
        #           Axis - Draw gridlines in degrees over Mercator map
        gl = ax_2.gridlines(crs=sproj, draw_labels=True,
                    linewidth=.6, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        gl.left_labels = False
        gl.xlabel_style = {'color': 'k'}
        gl.ylabel_style = {'color': 'k'}
        #           Title
        plt.title(title_2)
        #           Land & coastlines
        ax_2.add_feature(land_m)
        ax_2.coastlines(resolution='10m')
        #
        #    - Panel 3
        #      -------
        #
        ax_3 = fig.add_subplot(1, 3, 3, projection=sproj)
        ax_3.set_extent([xmin, xmax, ymin, ymax], crs=sproj)
        cs_3 = plt.pcolormesh(lon_3, lat_3, var_3, vmin=minvalue, vmax=maxvalue, cmap=colorbar)
        #            Axis - Draw gridlines in degrees over Mercator map
        gl = ax_3.gridlines(crs=sproj, draw_labels=True,
                    linewidth=.6, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = True
        gl.left_labels = False
        gl.xlabel_style = {'color': 'k'}
        gl.ylabel_style = {'color': 'k'}
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        #             Title
        plt.title(title_3)
        plt.text(x_unit, y_unit, unit_txt, horizontalalignment='center', transform=sproj)
        #             Land & coastlines
        ax_3.add_feature(land_m)
        ax_3.coastlines(resolution='10m')
        #
        #    - Common Colorbar (centered on the middle panel)
        #      ----------------------------------------------
        #
        numlevsv = np.linspace(minvalue,maxvalue,100)
        numlevsvar = np.arange(minvalue,maxvalue+stepvalue/2,stepvalue)
        numlevscol = [ ((stepformat)%v).rjust(2) for v in numlevsvar]
        cbar_ax = inset_axes(ax_2, width="100%",height=0.15,loc="lower center",bbox_to_anchor=(-0.8,0,2.5,1.),bbox_transform=ax_2.transAxes,borderpad=-4.2)
        cb = plt.colorbar(cs_2,cax=cbar_ax,orientation="horizontal",extend="both")
        cb.set_ticks(numlevsvar)
        cb.set_ticklabels(numlevscol)
#
# ==============================================
