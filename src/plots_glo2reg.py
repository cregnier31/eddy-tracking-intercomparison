import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from labellines import labelLine, labelLines
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy
import cartopy.feature as cfeature
data_crs = ccrs.PlateCarree()
from matplotlib.patches import Rectangle
import os
import fnmatch
import netCDF4 as nc
import xarray as xr
#import ssl
#ssl._create_default_https_context = ssl._create_unverified_context

def plt_cartopy_ibi(ax, labels=True):
    # ax.set_aspect('auto') # The figure will follow the ratio of the figsize
    ax.coastlines()  # Plot the coastlines
    # ax.set_xticks([-15, -5, 5], crs=data_crs)  # Set ticks for longitude
    # ax.set_yticks([30, 40, 50], crs=data_crs)  # Set ticks for latitude
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)


class Plots:
    def __init__(self, info, show=False):
        general_info = info["GENERAL_INFO"]
        self.model = str(general_info["MODEL"])
        self.reference = str(general_info["REFERENCE"])
        self.year = str(general_info["YEAR"])
        self.date_start = str(general_info["DATE_START"])
        self.DOMAIN = str(general_info["DOMAIN"])
        self.PATH_DETECT_FILES = str(general_info["PATH_DETECT_FILES"])
        self.PATH_TRAJ_FILES = str(general_info["PATH_TRAJ_FILES"])
        self.PATH_REF_TRACK = str(general_info["PATH_REF_TRACK"])
        self.PATH_DETECT_REF_FILES=str(general_info["PATH_DETECTION_REF_FILES"])
        self.PATH_STATS = str(info["GENERAL_INFO"]["PATH_STATS"])
        self.grid_size=int(general_info["GRID_SIZE"])
        self.quarter = str(general_info["QUARTER"])
        self.PATH_DETECT_FILES = f"{self.PATH_DETECT_FILES}{self.year}/{self.quarter}/"
        self.PATH_TRAJ_FILES = f"{self.PATH_TRAJ_FILES}{self.year}/{self.quarter}/"
        self.PATH_REF_TRACK = f"{self.PATH_REF_TRACK}{self.year}/{self.quarter}/"
        self.PATH_DETECT_REF_FILES= f"{self.PATH_DETECT_REF_FILES}{self.year}/{self.quarter}/"
        self.periods = (
            len(fnmatch.filter(os.listdir(self.PATH_DETECT_FILES), "*.*"))
            // 2
        )
        # Geographical extend
        self.lon_min = int(general_info["LON_MIN"])
        self.lon_max = int(general_info["LON_MAX"])
        self.lat_min = int(general_info["LAT_MIN"])
        self.lat_max = int(general_info["LAT_MAX"])
        self.average_radius_units = "km"
        self.average_radius_long_name = "Mean radius of eddies"
        self.cell_counters_units = "counts"
        self.average_amp_units = "cm"
        self.average_amp_long_name = "Mean amplitude of eddies"
        self.cell_counters_long_name = "Number of eddies"
        self.dir_plot = str(info["PLOT_INFO"]["PATH_PLOT"])
        self.colors = {}
        self.colors['GS'] = "red"
        self.colors['IBI'] = "green"
        self.colors['AG'] = "pink"
        self.colors['KOE'] = "purple"
        self.colors['GLOBAL'] = "black"
        self.show = show


       
    def plot_one_day_adt(self, h, var_adt, a, c):
        fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
        #ax.set_extent([self.lon_min, self.lon_max, self.lat_min, self.lat_max])
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(-100, 40, 30), ylocs=np.arange(0, 70, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False
        AC_x, AC_y = a.effective_contour_longitude, a.effective_contour_latitude
        CC_x, CC_y = c.effective_contour_longitude, c.effective_contour_latitude

        ax.plot(AC_x.T, AC_y.T, color="k", linestyle="-", linewidth=1, transform=data_crs)
        ax.plot(CC_x.T, CC_y.T, color="k", linestyle=":", linewidth=1.5, transform=data_crs)

        ax.set_title(self.model)
        im = h.display(ax, var_adt, vmin=-0.2, vmax=0.2)
        plt_cartopy_ibi(ax, labels=False)
        plt.suptitle("Detection Cyclonic (Dotted) & Anticyclonic (Solid)")
        cbar = fig.colorbar(im, ticks=[-0.1, 0, 0.1])
        cbar.ax.set_ylabel("ADT (m) Filtered (500 km)")  # Colorbar label
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        # Save or show
        plt.savefig(self.dir_plot + self.model + "_Detection.jpeg", bbox_inches="tight", dpi=3000)
        
        if self.show:
            plt.show()
        else:
            pass


    def plot_all_tracks_period(self, at_zone, ct_zone,rect_params):
        fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
        ax.set_extent([self.lon_min, self.lon_max, self.lat_min, self.lat_max])

        at_zone.plot(ax, ref =-10, label="Anticyclonic {nb_tracks} tracks", color="r", lw=0.9,transform=data_crs)
        ct_zone.plot(ax, ref=-10, label="Cyclonic {nb_tracks} tracks",color="b", lw=0.9,transform=data_crs)

        rect = Rectangle((rect_params['llcrnrlon'], rect_params['llcrnrlat']),
                         rect_params['urcrnrlon'] - rect_params['llcrnrlon'],
                         rect_params['urcrnrlat'] - rect_params['llcrnrlat'],
                         edgecolor='black', facecolor='none', linewidth=2, transform=data_crs)
        
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1)
    
        ax.add_patch(rect)
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False
        ax.legend()
        ax.set_title(f"Tracks {self.model} {self.year}_{self.quarter}")
        plt_cartopy_ibi(ax, labels=False)
        plt.savefig(
            f"{self.dir_plot}{self.model}_TRACKS_{self.year}_{self.quarter}.jpeg",
            bbox_inches="tight",
            dpi=600,
        )

        if self.show:
            plt.show()

    def plot_heatmap(self,zone_params, val_REF=""):

        GRID_SIZE=self.grid_size
        
        # Calculate the number of cells in latitude and longitude for the specified zone_params
        lat_cells = int((zone_params['urcrnrlat'] - zone_params['llcrnrlat']) / GRID_SIZE)
        lon_cells = int((zone_params['urcrnrlon'] - zone_params['llcrnrlon']) / GRID_SIZE)
        # Generate latitude and longitude arrays based on the grid size
        lat_values = np.linspace(
                    zone_params['llcrnrlat'] + GRID_SIZE / 2,
                        zone_params['urcrnrlat'] - GRID_SIZE / 2,
                            lat_cells
                            )
        lon_values = np.linspace(
                    zone_params['llcrnrlon'] + GRID_SIZE / 2,
                        zone_params['urcrnrlon'] - GRID_SIZE / 2,
                            lon_cells
                            )

        # Create an empty grid to store cell counters
        cell_counters = np.zeros((lat_cells, lon_cells), dtype=int)
        if val_REF == "AVISO":
            input_files = self.PATH_DETECT_REF_FILES
        else:
            input_files = self.PATH_DETECT_FILES
        
        # Iterate through all files in the folder
        for file in os.listdir(input_files):
            with nc.Dataset(os.path.join(input_files, file), 'r') as ds:
                # Get eddies' coordinates (latitude, longitude) from the NetCDF file
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
        
                # Iterate through each eddy coordinate
                for i in range(len(latitudes)):
                    x, y = latitudes[i], longitudes[i]  # Eddy coordinates
                    # Check if coordinates are within the specified zone_params
                    if (zone_params['llcrnrlon'] <= y <= zone_params['urcrnrlon']) and (zone_params['llcrnrlat'] <= x <= zone_params['urcrnrlat']):
                        # Calculate corresponding cell indices while keeping values within bounds
                        lat_index = min(max(int((x - zone_params['llcrnrlat']) / GRID_SIZE), 0), lat_cells - 1)
                        lon_index = min(max(int((y - zone_params['llcrnrlon']) / GRID_SIZE), 0), lon_cells - 1)
        
                        # Increment the counter of the appropriate cell
                        cell_counters[lat_index, lon_index] += 1
        
        # Create a map using the PlateCarree projection
        fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
                                                             
        # Add coastline
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        
        # Create a mask for values = 0
        mask = cell_counters == 0
        
        cell_counters = np.ma.masked_array(cell_counters, mask=mask)
        
        # Save netcdf file
        # Create an xarray DataArray and Dataset
        data_array = xr.DataArray(
                                  cell_counters/self.periods,
                                  dims=("latitude", "longitude"),
                                  coords={"latitude": lat_values, "longitude": lon_values},
                                  name="cell_counters",
                                  attrs={
                                         "units": self.cell_counters_units,
                                         "long_name": self.cell_counters_long_name
                                        }
                                )
        # Create a Dataset and save to NetCDF
        dataset = xr.Dataset({"cell_counters": data_array})
        dataset.to_netcdf(f"{self.PATH_STATS}{val_REF}_{self.year}_{self.quarter}_Heatmap-eddies.nc")

        # Create heatmap
        heatmap = ax.imshow(cell_counters/self.periods, vmin=0, vmax=(cell_counters/self.periods).max(), cmap='jet', origin='lower',
                            extent=[zone_params['llcrnrlon'], zone_params['urcrnrlon'], zone_params['llcrnrlat'], zone_params['urcrnrlat']]) 
        
        cbar = plt.colorbar(heatmap, orientation='horizontal', label='Nb eddies by day')
        plt.title('Mean nb of eddies by day')
        
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(-180, 180, 10), ylocs=np.arange(-180, 180, 10))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False


        #Save and show
        plt.savefig(f'{self.dir_plot}{val_REF}_HEATMAP_{self.year}_{self.quarter}.jpeg',
                bbox_inches="tight",
                dpi=500,)
    
        if self.show:
            plt.show()

    def plot_heatmap_amplitude(self,zone_params, val_REF=""):    

        grid_size=self.grid_size
        GRID_SIZE = grid_size 
        
        # Calculate the number of cells in latitude and longitude for the specified zone_params
        lat_cells = int((zone_params['urcrnrlat'] - zone_params['llcrnrlat']) / grid_size)
        lon_cells = int((zone_params['urcrnrlon'] - zone_params['llcrnrlon']) / grid_size)
        
        # Generate latitude and longitude arrays based on the grid size
        lat_values = np.linspace(
                    zone_params['llcrnrlat'] + GRID_SIZE / 2,
                        zone_params['urcrnrlat'] - GRID_SIZE / 2,
                            lat_cells
                            )
        lon_values = np.linspace(
                    zone_params['llcrnrlon'] + GRID_SIZE / 2,
                        zone_params['urcrnrlon'] - GRID_SIZE / 2,
                            lon_cells
                            )

        # Create empty grids
        amp_sums = np.zeros((lat_cells, lon_cells), dtype=float)
        cell_counts = np.zeros((lat_cells, lon_cells), dtype=int)  
        
        if val_REF == "AVISO":
            input_files = self.PATH_DETECT_REF_FILES
        else:
            input_files = self.PATH_DETECT_FILES
        for fichier in os.listdir(input_files):
            with nc.Dataset(os.path.join(input_files, fichier), 'r') as ds:
                # Get eddies coordinates and amplitude
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                amplitude = ds.variables['amplitude'][:]*100
                
                # For each eddy 
                for i in range(len(latitudes)):
                    x, y, amp = latitudes[i], longitudes[i], amplitude[i]
                    
                    #  Check if the eddy is in the domain of study 
                    if (zone_params['llcrnrlon'] <= y <= zone_params['urcrnrlon']) and (zone_params['llcrnrlat'] <= x <= zone_params['urcrnrlat']):
                        # Calculate corresponding cell indices while keeping values within bounds
                        lat_index = min(max(int((x - zone_params['llcrnrlat']) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - zone_params['llcrnrlon']) / grid_size), 0), lon_cells - 1)
                        
                        # Add the amplitude to the sum 
                        amp_sums[lat_index, lon_index] += amp

                        #Compute the number of eddies
                        cell_counts[lat_index, lon_index] += 1
        
        # Compute the average amplitude for each cell (avoiding division by zero)
        average_amp = np.divide(amp_sums, cell_counts, where=cell_counts != 0)
        
        # Save netcdf file
        # Create an xarray DataArray and Dataset
        data_array = xr.DataArray(
                                  average_amp,
                                  dims=("latitude", "longitude"),
                                  coords={"latitude": lat_values, "longitude": lon_values},
                                  name="average_amp",
                                  attrs={
                                         "units": self.average_amp_units,
                                         "long_name": self.average_amp_long_name
                                        }
                                )
        # Create a Dataset and save to NetCDF
        dataset = xr.Dataset({"average_amp": data_array})
        # Add the average_amplitude as an attribute to the Dataset

        dataset.to_netcdf(f"{self.PATH_STATS}{val_REF}_{self.year}_{self.quarter}_Heatmap-amplitude-eddies.nc")

        # Create heatmap
        
        #Create a map
        fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Add coasts
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        
        # Create a masque for values = 0 
        mask = cell_counts == 0
        
        
        average_amp = np.ma.masked_array(average_amp, mask=mask)

        #Create heatmap
        heatmap = ax.imshow(average_amp, cmap='jet',vmax=80 ,origin='lower',
                            extent=[zone_params['llcrnrlon'], zone_params['urcrnrlon'], zone_params['llcrnrlat'], zone_params['urcrnrlat']])
        
        cbar = plt.colorbar(heatmap ,location='bottom',shrink=0.5,label='Mean Amplitude of eddies (cm)')
        
        # Add title and labels
        plt.title('Amplitude of eddies ' + str(self.model))
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(-180, 180, 10), ylocs=np.arange(-180, 180, 10))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False

        #Save and show
        plt.savefig(f"{self.dir_plot}{val_REF}_HEATMAP_Amplitude_{self.year}_{self.quarter}.jpeg",
            bbox_inches="tight",
            dpi=500)

        if self.show:
            plt.show()


    def plot_heatmap_radius(self,zone_params, val_REF=""):    

        grid_size=self.grid_size
        GRID_SIZE = grid_size 
        # Calculate the number of cells in latitude and longitude for the specified zone_params
        lat_cells = int((zone_params['urcrnrlat'] - zone_params['llcrnrlat']) / grid_size)
        lon_cells = int((zone_params['urcrnrlon'] - zone_params['llcrnrlon']) / grid_size)
        # Generate latitude and longitude arrays based on the grid size
        lat_values = np.linspace(
                    zone_params['llcrnrlat'] + GRID_SIZE / 2,
                        zone_params['urcrnrlat'] - GRID_SIZE / 2,
                            lat_cells
                            )
        lon_values = np.linspace(
                    zone_params['llcrnrlon'] + GRID_SIZE / 2,
                        zone_params['urcrnrlon'] - GRID_SIZE / 2,
                            lon_cells
                            )
        # Create empty grids
        radius_sums = np.zeros((lat_cells, lon_cells), dtype=float)
        cell_counts = np.zeros((lat_cells, lon_cells), dtype=int)  
        if val_REF == "AVISO":
            input_files = self.PATH_DETECT_REF_FILES
        else:
            input_files = self.PATH_DETECT_FILES
        
        for fichier in os.listdir(input_files):
            with nc.Dataset(os.path.join(input_files, fichier), 'r') as ds:
                # Get eddies coordinates and radius
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                radii = ds.variables['effective_radius'][:] /1000
                
                # For each eddy 
                for i in range(len(latitudes)):
                    x, y, radius = latitudes[i], longitudes[i], radii[i]
                    
                    #  Check if the eddy is in the domain of study 
                    if (zone_params['llcrnrlon'] <= y <= zone_params['urcrnrlon']) and (zone_params['llcrnrlat'] <= x <= zone_params['urcrnrlat']):
                        # Calculate corresponding cell indices while keeping values within bounds
                        lat_index = min(max(int((x - zone_params['llcrnrlat']) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - zone_params['llcrnrlon']) / grid_size), 0), lon_cells - 1)
                        
                        # Add the radius to the sum 
                        radius_sums[lat_index, lon_index] += radius

                        #Compute the number of eddies
                        cell_counts[lat_index, lon_index] += 1
        
        # Compute the average radius for each cell (avoiding division by zero)
        average_radii = np.divide(radius_sums, cell_counts, where=cell_counts != 0)
        
        # Save netcdf file
        # Create an xarray DataArray and Dataset
        data_array = xr.DataArray(
                                  average_radii,
                                  dims=("latitude", "longitude"),
                                  coords={"latitude": lat_values, "longitude": lon_values},
                                  name="average_radius",
                                  attrs={
                                         "units": self.average_radius_units,
                                         "long_name": self.average_radius_long_name
                                        }
                                )
        # Create a Dataset and save to NetCDF
        dataset = xr.Dataset({"average_radius": data_array})
        # Add the average_radius as an attribute to the Dataset

        dataset.to_netcdf(f"{self.PATH_STATS}{val_REF}_{self.year}_{self.quarter}_Heatmap-radius-eddies.nc")

        # Create heatmap
        
        #Create a map
        fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Add coasts
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        
        # Create a masque for values = 0 
        mask = cell_counts == 0
        
        
        average_radii = np.ma.masked_array(average_radii, mask=mask)

        #Create heatmap
        heatmap = ax.imshow(average_radii, cmap='jet',vmax=80 ,origin='lower',
                            extent=[zone_params['llcrnrlon'], zone_params['urcrnrlon'], zone_params['llcrnrlat'], zone_params['urcrnrlat']])
        
        cbar = plt.colorbar(heatmap ,location='bottom',shrink=0.5,label='Mean radius of eddies (km)')
        
        # Add title and labels
        plt.title('Radius of eddies ' + str(self.model))
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(-180, 180, 10), ylocs=np.arange(-180, 180, 10))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False

        #Save and show
        plt.savefig(
            self.dir_plot + val_REF + "_HEATMAP_RADIUS" + ".jpeg",
            bbox_inches="tight",
            dpi=500,)

        if self.show:
            plt.show()
   
    def plot_number_detection_time_mean_area(self, results):
        t_data = pd.date_range(self.date_start, periods=self.periods, freq="D")
        fig, ax = plt.subplots(figsize=(12, 6))
        # ax = fig.add_axes([.03,.03,.94,.94])
        for region in results.keys():
            print(f"Plot {region}")
            color = self.colors[region]
            NB_EDDIES = results[region]['NB_EDDIES']
            NB_EDDIES_REF = results[region]['NB_EDDIES_REF']
            ax.plot(t_data, NB_EDDIES, color=color, label=region)
            ax.plot(t_data, NB_EDDIES_REF, color=color, linestyle="--")
            #NB_mean = np.nanmean(NB_EDDIES)
            #ax.plot(t_data, NB_mean, label='Mean by day =  '+ str(int(np.round(np.mean(NB_mean)))), linestyle="--")
        plt.ylabel("Nb eddy detected", fontsize=16)
        plt.title("Evolution of eddies detected for GLO12 and AVISO (dashed)",  fontsize=20)
        ax.xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        # Adjust font size of tick labels
        ax.tick_params(axis="x", labelsize=16)  # X-axis tick labels
        ax.tick_params(axis="y", labelsize=16)  # Y-axis tick labels
        # Set y-axis to log scale
        #ax.set_yscale("log")
        ax.legend()

        plt.savefig(
            f"{self.dir_plot}NB_EDDIES_all_regions_withREF_{self.model}_{self.year}_{self.quarter}.jpeg",
            bbox_inches="tight",
        )


    def plot_number_detection_time_mean(self, NB_EDDIES):
        t_data = pd.date_range(self.date_start, periods=self.periods, freq="D")
        NB_mean = np.full(len(t_data), np.mean(NB_EDDIES))
        NB_mean_zone = [np.mean(NB_EDDIES)]*len(t_data)
        fig, ax = plt.subplots(figsize=(12, 6))
        # ax = fig.add_axes([.03,.03,.94,.94])
        ax.plot(t_data, NB_EDDIES, color="black")
        ax.xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.ylabel("Nb eddy detected")
        ax.plot(t_data, NB_mean, label='Mean by day =  '+ str(int(np.round(np.mean(NB_mean_zone)))), linestyle="--")
        ax.legend()

        plt.savefig(
            f"{self.dir_plot}NB_EDDIES_{self.model}_{self.year}_{self.quarter}.jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()


    def plot_count_log_amp(self, at, ct, a_ref, c_ref, at_zone, ct_zone, a_zone_ref, c_zone_ref):
        
        kwargs_eddies = dict(label=str(self.model), color="k")
        kwargs_eddies_ref = dict(label=str(self.reference), color="g")
        kwargs_zone_eddies = dict(label=str(self.model) + " " + self.DOMAIN, color="grey")
        kwargs_zone_eddies_ref = dict(label=str(self.reference) + " " + self.DOMAIN, color="limegreen")

        fig, ax = plt.subplots(figsize=(6, 4))

        name = "amplitude"
        title = "Amplitude (cm)"

        data_a = at[name] * 100
        data_c = ct[name] * 100
        bins = np.arange(0.0005, 1000, 0.2)

        hist_a, bins = np.histogram(data_a, bins=bins)
        hist_c, _ = np.histogram(data_c, bins=bins)

        hist_eddies = hist_a + hist_c

        data_a_ref = a_ref[name] * 100
        data_c_ref = c_ref[name] * 100
        bins_ref = np.arange(0.0005, 1000, 0.2)

        hist_a_ref, bins_ref = np.histogram(data_a_ref, bins=bins_ref)
        hist_c_ref, _ = np.histogram(data_c_ref, bins=bins_ref)

        hist_eddies_ref = hist_a_ref + hist_c_ref

        ####################################################################

        # Data for the domain
        data_zone_a = at_zone[name] * 100
        data_zone_c = ct_zone[name] * 100
        bins_zone = np.arange(0.0005, 100, 0.5)

        hist_zone_a, bins_zone = np.histogram(data_zone_a, bins=bins_zone)
        hist_zone_c, _ = np.histogram(data_zone_c, bins=bins_zone)

        hist_eddies_zone = hist_zone_a + hist_zone_c

        # Data ref for the domain
        data_zone_a_ref = a_zone_ref[name] * 100
        data_zone_c_ref = c_zone_ref[name] * 100
        bins_zone_ref = np.arange(0.0005, 100, 0.5)

        hist_zone_a_ref, bins_zone_ref = np.histogram(data_zone_a_ref, bins=bins_zone_ref)
        hist_zone_c_ref, _ = np.histogram(data_zone_c_ref, bins=bins_zone_ref)

        hist_eddies_zone_ref = hist_zone_a_ref + hist_zone_c_ref

        ################################################################

        ax.semilogy(bins[:-1], hist_eddies, **kwargs_eddies)
        ax.semilogy(bins_ref[:-1], hist_eddies_ref, **kwargs_eddies_ref)
        ax.semilogy(bins_zone[:-1], hist_eddies_zone, **kwargs_zone_eddies)
        ax.semilogy(bins_zone[:-1], hist_eddies_zone_ref, **kwargs_zone_eddies_ref)

        ax.grid()
        ax.set_title(title)
        ax.set_xlabel("Amplitude Value (cm)")
        ax.set_ylabel("Count (log scale)")
        ax.set_xlim(0, 20)  # Limite de l'axe des abscisses
        ax.legend()
        
        # Save the plot
        plt.savefig(f"{self.dir_plot}Amplitude_{self.model}_{self.reference}_{self.DOMAIN}.jpeg", bbox_inches="tight")

        # Show the plot
        if self.show:
            plt.show()

    def plot_count_speed_radius(self,at, ct, a_ref, c_ref, at_zone, ct_zone, a_zone_ref, c_zone_ref):

        kwargs_eddies = dict(label=str(self.model), color="k")
        kwargs_eddies_ref = dict(label=str(self.reference), color="g")
        kwargs_zone_eddies = dict(label=str(self.model) + " " + self.DOMAIN, color="grey")
        kwargs_zone_eddies_ref = dict(label=str(self.reference) + " " + self.DOMAIN, color="limegreen")
        
        fig, ax = plt.subplots(figsize=(6, 4))
        
        name = "speed_radius"
        title = "Speed Radius (km)"

        #### GLOBAL DATA ####
        ### MODEL ###
        data_a = at[name] * 0.001
        data_c = ct[name] * 0.001
        bins = np.arange(0, 2000, 1)
        
        hist_a, bins = np.histogram(data_a, bins=bins)
        hist_c, _ = np.histogram(data_c, bins=bins)
        
        hist_eddies = hist_a + hist_c
        
        ### REF ###
        data_a_ref = a_ref[name] * 0.001
        data_c_ref = c_ref[name] * 0.001
        bins_ref = np.arange(0, 2000, 1)
        
        hist_a_ref, bins_ref = np.histogram(data_a_ref, bins=bins_ref)
        hist_c_ref, _ = np.histogram(data_c_ref, bins=bins_ref)
        
        hist_eddies_ref = hist_a_ref + hist_c_ref
        
        
        
        #### DATA FOR DOMAIN ####

        ### MODEL ###
        
        data_zone_a = at_zone[name] * 0.001
        data_zone_c = ct_zone[name] *0.001
        bins_zone = np.arange(0, 2000, 1)
        
        hist_zone_a, bins_zone = np.histogram(data_zone_a, bins=bins_zone)
        hist_zone_c, _ = np.histogram(data_zone_c, bins=bins_zone)
        
        hist_eddies_zone = hist_zone_a + hist_zone_c
        
        
        ### REF ###
        
        data_zone_a_ref = a_zone_ref[name] * 0.001
        data_zone_c_ref = c_zone_ref[name] * 0.001
        bins_zone_ref = np.arange(0, 2000, 1)
        
        hist_zone_a_ref, bins_zone_ref = np.histogram(data_zone_a_ref, bins=bins_zone_ref)
        hist_zone_c_ref, _ = np.histogram(data_zone_c_ref, bins=bins_zone_ref)
        
        hist_eddies_zone_ref = hist_zone_a_ref + hist_zone_c_ref

        ##### PLOT ####
        
        ax.semilogy(bins[:-1], hist_eddies, **kwargs_eddies)
        ax.semilogy(bins[:-1], hist_eddies_ref, **kwargs_eddies_ref)
        ax.semilogy(bins[:-1], hist_eddies_zone, **kwargs_zone_eddies)
        ax.semilogy(bins[:-1], hist_eddies_zone_ref, **kwargs_zone_eddies_ref)
        
        ax.grid()
        ax.set_title(title)
        ax.set_xlabel("Speed Radius Value (km)")
        ax.set_ylabel("Count (log scale)")
        ax.set_xlim(0, 150)  
        ax.legend()

        
        # Save the plot
        plt.savefig(f"{self.dir_plot}Speed_Radius_{self.model}_{self.reference}_{self.DOMAIN}.jpeg", bbox_inches="tight")

        # Show the plot
        if self.show:
            plt.show()
            

    def plot_count_lifetime(self,at, ct, a_ref, c_ref, at_zone, ct_zone, a_zone_ref, c_zone_ref):
        
        fig, ax = plt.subplots(figsize=(6, 4))

        # Select the variable nb_obs-by_track which is the lifetime of eddies
        name = "nb_obs_by_track"
        title = "Eddy lifetime (days)"
        x = np.arange(0, 2000, 1)
        
        data_a = at.nb_obs_by_track
        data_c = ct.nb_obs_by_track
        
        # Delete nul values
        data_a = data_a[data_a != 0]
        data_c = data_c[data_c != 0]
        
        data_a_ref = a_ref.nb_obs_by_track
        data_c_ref = c_ref.nb_obs_by_track
        
        data_a_ref = data_a_ref[data_a_ref != 0]
        data_c_ref = data_c_ref[data_c_ref != 0]
        
        
        hist_a, x = np.histogram(data_a, bins=x)
        hist_c, _ = np.histogram(data_c, bins=x)
        hist_eddies = hist_a + hist_c
        
        hist_a_ref, x = np.histogram(data_a_ref, bins=x)
        hist_c_ref, _ = np.histogram(data_c_ref, bins=x)
        hist_eddies_ref = hist_a_ref + hist_c_ref
        
        ######### DATA ZONE ######
        data_a_zone=at_zone.nb_obs_by_track
        data_c_zone=ct_zone.nb_obs_by_track
        
        data_a_zone = data_a_zone[data_a_zone != 0]
        data_c_zone = data_c_zone[data_c_zone != 0]
        
        hist_a_zone, x = np.histogram(data_a_zone, bins=x)
        hist_c_zone, _ = np.histogram(data_c_zone, bins=x)
        hist_eddies_zone = hist_a_zone + hist_c_zone
        
        ###data zone ref ###
        data_a_zone_ref=a_zone_ref.nb_obs_by_track
        data_c_zone_ref=c_zone_ref.nb_obs_by_track
        
        data_a_zone_ref = data_a_zone_ref[data_a_zone_ref != 0]
        data_c_zone_ref = data_c_zone_ref[data_c_zone_ref != 0]
        
        hist_a_zone_ref, x = np.histogram(data_a_zone_ref, bins=x)
        hist_c_zone_ref, _ = np.histogram(data_c_zone_ref, bins=x)
        hist_eddies_zone_ref = hist_a_zone_ref + hist_c_zone_ref
        
        
        
        ######PLOT######
        
        # Log scale 
        ax.semilogy(x[:-1], hist_eddies, color="k",label='Eddies ' + str(self.model))
        ax.semilogy(x[:-1], hist_eddies_ref, color="g",label='Eddies ' + str(self.reference))
        ax.semilogy(x[:-1], hist_eddies_zone,label=str(self.model) +" " +self.DOMAIN, color="grey")
        ax.semilogy(x[:-1], hist_eddies_zone_ref,label=str(self.reference) +" " +self.DOMAIN, color="limegreen")            
        # Add legend and label
        ax.set_xlabel(title)
        ax.set_ylabel("Count (log scale)")
        ax.legend()
        ax.set_xlim(10, 30)
        ax.grid()

        # Save the plot
        plt.savefig(f"{self.dir_plot}Lifetime_{self.model}_{self.reference}_{self.DOMAIN}.jpeg", bbox_inches="tight")

        # Show the plot
        if self.show:
            plt.show()
            
    def plot_2d_histo(self, eddies_zone):
        fig, ax = plt.subplots()
        counts, xedges, yedges, im = ax.hist2d(
            eddies_zone["effective_radius"] / 1000,
            eddies_zone["amplitude"] * 100,
            bins=200,
            cmap=plt.cm.jet,
            cmin=1,
        )
        ax.set_xlabel("Radius (km)")
        ax.set_ylabel("Amplitude (cm)")

        fig.colorbar(im, ax=ax)
        plt.title(self.model)
        plt.savefig(
            f"{self.dir_plot}HIST2D_AMP_RAD_{self.model}_{self.year}_{self.quarter}.jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_histo_hits_false(self, radius_AR_hits_glo, radius_AR_misses_glo, radius_AR_falarm_glo, radius_AR_hits, radius_AR_misses, radius_AR_falarm):
        
        bins = np.arange(0, 400, 3)
        hits_histogram_glo = np.histogram(radius_AR_hits_glo, bins=bins)
        misses_histogram_glo = np.histogram(radius_AR_misses_glo, bins=bins)
        falarm_histogram_glo = np.histogram(radius_AR_falarm_glo, bins=bins)
        
        hits_histogram = np.histogram(radius_AR_hits, bins=bins)
        misses_histogram = np.histogram(radius_AR_misses, bins=bins)
        falarm_histogram = np.histogram(radius_AR_falarm, bins=bins)
        
        max_value1 = max(
            max(hits_histogram[0]),
            max(misses_histogram[0]),
            max(falarm_histogram[0]))
        
        max_value2=max(
            max(hits_histogram_glo[0]),
            max(misses_histogram_glo[0]),
            max(falarm_histogram_glo[0])
        )
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Plot for Global data
        ax1.hist(
            [radius_AR_hits_glo, radius_AR_misses_glo, radius_AR_falarm_glo],
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label=["hits", "misses", "false alarm"],
            color=["green", "red", "orange"],
        )
        ax1.set_ylim(0, max_value2+100)
        ax1.set_xlim(0, 130)
        ax1.set_xlabel("Radius (km)")
        ax1.legend()
        ax1.set_title(f"{self.model} Reference {self.reference} (Global)")
        
        # Plot for regional data
        ax2.hist(
            [radius_AR_hits, radius_AR_misses, radius_AR_falarm],
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label=["hits", "misses", "false alarm"],
            color=["green", "red", "orange"],
        )
        ax2.set_ylim(0, max_value1+20)
        ax2.set_xlim(0, 130)
        ax2.set_xlabel("Radius (km)")
        ax2.legend()
        ax2.set_title(f"{self.model} Reference {self.reference} (Domain)")
        
        plt.tight_layout()  # Ensures proper spacing
        plt.savefig(f"{self.dir_plot}HIST_MATCHING_{self.model}_{self.year}_{self.quarter}_dual.jpeg", bbox_inches="tight")
        
        if self.show:
            plt.show()




    def plot_pod_far_amplitude(self, POD_AR, FAR_AR):
        bins = np.arange(0, 400, 1)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        axes[0].step(bins[:-1], POD_AR, color="black", linewidth=2)
        axes[0].set(
            ylim=(np.nanmin(POD_AR) - 0.2, 1.05),
            ylabel="Probability of Detection",
            xlim=(0, 20),
            xlabel="Amplitude (cm)",
            xticks=np.arange(0, 25, 5),
        )
        axes[0].grid()

        axes[1].step(bins[:-1], FAR_AR, color="black", linewidth=2)
        axes[1].set(
            ylim=(0, np.nanmax(FAR_AR) + 0.2),
            ylabel="False Alarm Ratio",
            xlim=(0, 20),
            xlabel="Amplitude (cm)",
            xticks=np.arange(0, 25, 5),
        )
        axes[1].grid()

        fig.suptitle(f"{self.model} Reference {self.reference}")
        plt.tight_layout()
        plt.savefig(
            f"{self.dir_plot}POD_FAR_AMP_{self.model}_{self.year}_{self.quarter}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()


    def plot_pod_far_time(self, AR_POD, AR_FAR):
        t_data = pd.date_range(self.date_start, periods=self.periods - 1, freq="D")
        t_data_obs = pd.date_range(self.date_start, periods=self.periods - 1, freq="D")

        fig, axes = plt.subplots(1, 2, figsize=(17, 3))

        axes[0].plot(t_data_obs, AR_POD, color="black")
        axes[0].set_ylim(0, 1)
        axes[0].xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        axes[0].set_title("Probability Of Detection")

        axes[1].plot(t_data_obs, AR_FAR, color="black")
        axes[1].set_ylim(0, 1)
        axes[1].xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        axes[1].set_title("False Alarm Ratio")

        plt.savefig(
            f"{self.dir_plot}POD_FAR_TEMP_{self.model}_{self.year}_{self.quarter}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()


    def perf_diag(self, SR, AR_POD,SR_GLO,AR_POD_GLO):
        fig, ax = plt.subplots(figsize=(10, 10))

        CSI = np.arange(0.1, 1, 0.1)
        xvals = [0.57, 0.62, 0.77, 0.79, 0.85, 0.9, 0.95, 0.935, 0.96]
        labels = ["0.3", "0.5", "0.8", "1", "1.3", "1.5", "2", "3", "5", "10"]

        
        for c in CSI:
            i = np.arange(0, 1.1, 0.01)
            y = (c * i) / (c * i - c + i)
            indices = np.where(y <= 0.0)
            y = np.delete(y, indices)
            i = np.delete(i, indices)
            ax.plot(i, y, color="k", linewidth=1.8, label=str(np.round(c, 2)))

        labelLines(ax.get_lines(), xvals=xvals, fontsize=15)


        x = [ 1.01, 1.01, 1.01, 1.01, 0.76,0.65,0.5,0.327,0.2,0.09]
        y_offsets = [0.295, 0.495, 0.795, 1, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01]
        pente = np.arange(0, 1.1, 0.1)
        for i, label in enumerate(labels):
            ax.plot(pente, pente * float(label), linestyle="--", color="k", linewidth=1)
            ax.text(x[i], y_offsets[i], label, size=10)

        ax.set_title(f"Performance Diagram {self.model} {self.year}_{self.quarter}", y=1.08)
        ax.scatter(np.mean(SR), np.mean(AR_POD), color="blue", s=200)
        ax.scatter(np.mean(SR_GLO), np.mean(AR_POD_GLO), color="red", s=200)

        ax.text(np.mean(SR), np.mean(AR_POD) - 0.05, "Domain", color="blue", size=15)
        ax.text(np.mean(SR_GLO), np.mean(AR_POD_GLO) + 0.02, "Global", color="red", size=15)

        ax.scatter(0.995, 0.995, color="orange", s=200, marker="D")
        ax.text(0.8, 0.96, "Perfect match", size=15)
        ax.set_xlabel("Success Ratio (1-FAR)", fontsize=20)
        ax.set_ylabel("Probability of detection (POD)", fontsize=20)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks(np.arange(0, 1.1, step=0.1))
        ax.set_yticks(np.arange(0, 1.1, step=0.1))
        ax.tick_params(axis="both", which="both", labelsize=20)
        ax.minorticks_on()
        
            
        plt.savefig(f"{self.dir_plot}PERFORMANCE_DIAG_{self.model}_{self.year}_{self.quarter}.jpeg", bbox_inches="tight", dpi=600)

        if self.show:
            plt.show()


