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
from scipy.interpolate import interp1d

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
        self.year = int(general_info["YEAR"])
        self.date_start = str(general_info["DATE_START"])
        self.periods = int(general_info["PERIODS"])
        
        self.PATH_DETECT_FILES = str(general_info["PATH_DETECT_FILES"])
        self.PATH_DETECT_FILES_REF = str(general_info["PATH_DETECTION_REF_FILES"])
        self.PATH_TRAJ_FILES = str(general_info["PATH_TRAJ_FILES"])
        self.PATH_REF_TRACK = str(general_info["PATH_REF_TRACK"])
        self.grid_size=int(general_info["GRID_SIZE"])

        # Geographical extend
        self.lon_min = int(general_info["LON_MIN"])
        self.lon_max = int(general_info["LON_MAX"])
        self.lat_min = int(general_info["LAT_MIN"])
        self.lat_max = int(general_info["LAT_MAX"])

        self.dir_plot = str(info["PLOT_INFO"]["PATH_PLOT"])

        self.show = show

    def plot_heatmap_glo(self, dossier_data, model_name, vmin, vmax, ax):
        longitude_min = self.lon_min
        longitude_max = self.lon_max
        latitude_min = self.lat_min
        latitude_max = self.lat_max
        
        grid_size = 2.0
        lat_cells = int((latitude_max - latitude_min) / grid_size)
        lon_cells = int((longitude_max - longitude_min) / grid_size)
        
        cell_counters = np.zeros((lat_cells, lon_cells), dtype=int)
        
        for fichier in os.listdir(dossier_data):
            with nc.Dataset(os.path.join(dossier_data, fichier), 'r') as ds:
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                
                for i in range(len(latitudes)):
                    x, y = latitudes[i], longitudes[i]
                    if (longitude_min <= y <= longitude_max) and (latitude_min <= x <= latitude_max):
                        lat_index = min(max(int((x - latitude_min) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - longitude_min) / grid_size), 0), lon_cells - 1)
                        cell_counters[lat_index, lon_index] += 1
        
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        
        mask = cell_counters == 0
        cell_counters = np.ma.masked_array(cell_counters, mask=mask)
        
        heatmap = ax.imshow(cell_counters/self.periods, vmin=vmin, vmax=vmax, cmap='jet', origin='lower', 
                            extent=[longitude_min, longitude_max, latitude_min, latitude_max])
        
        ax.set_title('Heatmap of eddies ' + model_name)
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1)
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30),
                          ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False
        gl.top_labels = False
        
        return heatmap


    def plot_heatmap_model_and_ref(self):
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Plot the model heatmap
        heatmap1 = self.plot_heatmap_glo(self.PATH_DETECT_FILES, str(self.model), 0, 4, ax1)
        
        # Plot the reference heatmap
        heatmap2 = self.plot_heatmap_glo(self.PATH_DETECT_FILES_REF, str(self.reference), 0, 4, ax2)
        
        # Create a single colorbar for both heatmaps
        cbar = fig.colorbar(heatmap1, ax=[ax1, ax2], orientation='vertical', fraction=0.02, pad=0.1)
        cbar.set_label('Daily number of eddies')
        

        
        # Save and show the figure
        plt.savefig(
            self.dir_plot + "MODEL_AND_REFERENCE_HEATMAP" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
        
        if self.show:
            plt.show()



    def plot_heatmap(self,zone_params,ax,vmax):

        GRID_SIZE=self.grid_size
        
        # Calculate the number of cells in latitude and longitude for the specified zone_params
        lat_cells = int((zone_params['urcrnrlat'] - zone_params['llcrnrlat']) / GRID_SIZE)
        lon_cells = int((zone_params['urcrnrlon'] - zone_params['llcrnrlon']) / GRID_SIZE)
        
        
        # Create an empty grid to store cell counters
        cell_counters = np.zeros((lat_cells, lon_cells), dtype=int)
        
        # Iterate through all files in the folder
        for file in os.listdir(self.PATH_DETECT_FILES):
            with nc.Dataset(os.path.join(self.PATH_DETECT_FILES, file), 'r') as ds:
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
        
         # Create a mask for values = 0
        mask = cell_counters == 0
        cell_counters = np.ma.masked_array(cell_counters, mask=mask)
    
        # Create heatmap
        heatmap = ax.imshow(cell_counters/self.periods, vmin=0, vmax=vmax, cmap='jet', origin='lower',
                            extent=[zone_params['llcrnrlon'], zone_params['urcrnrlon'], zone_params['llcrnrlat'], zone_params['urcrnrlat']]) 
    
        cbar = plt.colorbar(heatmap, ax=ax, orientation='horizontal', label='Nb eddies by day')  # Ajout de ax=ax
        ax.set_title('Mean nb of eddies by day')
    
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        ax.add_feature(cfeature.LAND, edgecolor='k', facecolor='linen', zorder=1)  # ghostwhite
    
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(-180, 180, 10), ylocs=np.arange(-180, 180, 10))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False


    def plot_multiple_heatmaps(self, zone_params_list,vmax):
        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(20, 20), subplot_kw={'projection': ccrs.PlateCarree()})
    
        for ax, zone_params in zip(axes.flat, zone_params_list):
            self.plot_heatmap(zone_params, ax,vmax)
    
        plt.tight_layout()
    
        # Save and show
        plt.savefig(
            self.dir_plot + self.model + "_MULTIPLE_HEATMAPS" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
    
        if self.show:
            plt.show()

    def plot_heatmap_radius_glo(self, dossier_data, model_name, vmin,vmax,ax):
        longitude_min = self.lon_min
        longitude_max = self.lon_max
        latitude_min = self.lat_min
        latitude_max = self.lat_max
    
        grid_size = 2.0
        lat_cells = int((latitude_max - latitude_min) / grid_size)
        lon_cells = int((longitude_max - longitude_min) / grid_size)
    
        radius_sums = np.zeros((lat_cells, lon_cells), dtype=float)
        cell_counts = np.zeros((lat_cells, lon_cells), dtype=int)
    
        for fichier in os.listdir(dossier_data):
            with nc.Dataset(os.path.join(dossier_data, fichier), 'r') as ds:
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                radii = ds.variables['effective_radius'][:] / 1000
    
                for i in range(len(latitudes)):
                    x, y, radius = latitudes[i], longitudes[i], radii[i]
    
                    if (longitude_min <= y <= longitude_max) and (latitude_min <= x <= latitude_max):
                        lat_index = min(max(int((x - latitude_min) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - longitude_min) / grid_size), 0), lon_cells - 1)
    
                        radius_sums[lat_index, lon_index] += radius
                        cell_counts[lat_index, lon_index] += 1
    
        average_radii = np.divide(radius_sums, cell_counts, where=cell_counts != 0)
    
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
    
        mask = cell_counts == 0
        average_radii = np.ma.masked_array(average_radii, mask=mask)
    
        heatmap = ax.imshow(average_radii, cmap='jet', vmax=vmax, origin='lower', extent=[longitude_min, longitude_max, latitude_min, latitude_max])
    
        cbar = plt.colorbar(heatmap, location='bottom', shrink=0.5, label='Mean radius of eddies (km)')
    
        ax.set_title('Radius of eddies ' + model_name)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
    
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1)
    
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False
        gl.top_labels = False

        return heatmap

    def plot_heatmap_radius_model_and_ref(self,vmax):
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Plot the model heatmap
        heatmap1 = self.plot_heatmap_radius_glo(self.PATH_DETECT_FILES, str(self.model), 0, vmax, ax1)
        
        # Plot the reference heatmap
        heatmap2 = self.plot_heatmap_radius_glo(self.PATH_DETECT_FILES_REF, str(self.reference), 0, vmax, ax2)
        
        # Create a single colorbar for both heatmaps
        cbar = fig.colorbar(heatmap1, ax=[ax1, ax2], orientation='vertical', fraction=0.02, pad=0.1)
        cbar.set_label('Mean radius of eddies')
        
        
        # Save and show the figure
        plt.savefig(
            self.dir_plot + "MODEL_AND_REFERENCE_HEATMAP_RADIUS" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
        
        if self.show:
            plt.show()

    def plot_heatmap_radius(self,zone_params,ax,vmax):    

        grid_size=self.grid_size
        
        # Calculate the number of cells in latitude and longitude for the specified zone_params
        lat_cells = int((zone_params['urcrnrlat'] - zone_params['llcrnrlat']) / grid_size)
        lon_cells = int((zone_params['urcrnrlon'] - zone_params['llcrnrlon']) / grid_size)
        
        # Create empty grids
        radius_sums = np.zeros((lat_cells, lon_cells), dtype=float)
        cell_counts = np.zeros((lat_cells, lon_cells), dtype=int)  
        
        
        for fichier in os.listdir(self.PATH_DETECT_FILES):
            with nc.Dataset(os.path.join(self.PATH_DETECT_FILES, fichier), 'r') as ds:
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
        
        #Create a map
        # fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
        
        
        
        # Create a masque for values = 0 
        mask = cell_counts == 0
        
        
        average_radii = np.ma.masked_array(average_radii, mask=mask)

        #Create heatmap
        heatmap = ax.imshow(average_radii, cmap='jet',vmax=vmax ,origin='lower',
                            extent=[zone_params['llcrnrlon'], zone_params['urcrnrlon'], zone_params['llcrnrlat'],zone_params['urcrnrlat']])
        
        cbar = plt.colorbar(heatmap ,location='bottom',shrink=0.5,label='Mean radius of eddies (km)')
        
        # Add title and labels
        plt.title('Radius of eddies ' + str(self.model))
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')

        # Add coasts and land
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(-180, 180, 10), ylocs=np.arange(-180, 180, 10))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False


    def plot_multiple_heatmaps_radius(self, zone_params_list,vmax):
        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(20, 20), subplot_kw={'projection': ccrs.PlateCarree()})
    
        for ax, zone_params in zip(axes.flat, zone_params_list):
            self.plot_heatmap_radius(zone_params, ax,vmax)
    
        plt.tight_layout()
    
        # Save and show
        plt.savefig(
            self.dir_plot + self.model + "_MULTIPLE_HEATMAPS_RADIUS" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
    
        if self.show:
            plt.show()


    def plot_heatmap_amplitude_glo(self, dossier_data, model_name, vmin,vmax,ax):
        longitude_min = self.lon_min
        longitude_max = self.lon_max
        latitude_min = self.lat_min
        latitude_max = self.lat_max
    
        grid_size = 2.0
        lat_cells = int((latitude_max - latitude_min) / grid_size)
        lon_cells = int((longitude_max - longitude_min) / grid_size)
    
        amp_sums = np.zeros((lat_cells, lon_cells), dtype=float)
        cell_counts = np.zeros((lat_cells, lon_cells), dtype=int)
    
        for fichier in os.listdir(dossier_data):
            with nc.Dataset(os.path.join(dossier_data, fichier), 'r') as ds:
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                amp = ds.variables['amplitude'][:] * 100
    
                for i in range(len(latitudes)):
                    x, y, amplitude = latitudes[i], longitudes[i], amp[i]
    
                    if (longitude_min <= y <= longitude_max) and (latitude_min <= x <= latitude_max):
                        lat_index = min(max(int((x - latitude_min) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - longitude_min) / grid_size), 0), lon_cells - 1)
    
                        amp_sums[lat_index, lon_index] += amplitude
                        cell_counts[lat_index, lon_index] += 1
    
        average_amp = np.divide(amp_sums, cell_counts, where=cell_counts != 0)
    
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
    
        mask = cell_counts == 0
        average_amp = np.ma.masked_array(average_amp, mask=mask)
    
        heatmap = ax.imshow(average_amp, cmap='jet', vmax=vmax, origin='lower', extent=[longitude_min, longitude_max, latitude_min, latitude_max])
    
        cbar = plt.colorbar(heatmap, location='bottom', shrink=0.5, label='Mean amplitude of eddies (cm)')
    
        ax.set_title('Amplitude of eddies ' + model_name)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
    
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1)
    
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False
        gl.top_labels = False

        return heatmap

    def plot_heatmap_amplitude_model_and_ref(self,vmax):
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Plot the model heatmap
        heatmap1 = self.plot_heatmap_amplitude_glo(self.PATH_DETECT_FILES, str(self.model), 0, vmax, ax1)
        
        # Plot the reference heatmap
        heatmap2 = self.plot_heatmap_amplitude_glo(self.PATH_DETECT_FILES_REF, str(self.reference), 0, vmax, ax2)
        
        # Create a single colorbar for both heatmaps
        cbar = fig.colorbar(heatmap1, ax=[ax1, ax2], orientation='vertical', fraction=0.02, pad=0.1)
        cbar.set_label('Mean amplitude of eddies')
        

        
        # Save and show the figure
        plt.savefig(
            self.dir_plot + "MODEL_AND_REFERENCE_HEATMAP_AMPLITUDE" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
        
        if self.show:
            plt.show()

    def plot_heatmap_amplitude(self,zone_params,ax,vmax):    

        grid_size=self.grid_size
        
        # Calculate the number of cells in latitude and longitude for the specified zone_params
        lat_cells = int((zone_params['urcrnrlat'] - zone_params['llcrnrlat']) / grid_size)
        lon_cells = int((zone_params['urcrnrlon'] - zone_params['llcrnrlon']) / grid_size)
        
        # Create empty grids
        amp_sums = np.zeros((lat_cells, lon_cells), dtype=float)
        cell_counts = np.zeros((lat_cells, lon_cells), dtype=int)  
        
        
        for fichier in os.listdir(self.PATH_DETECT_FILES):
            with nc.Dataset(os.path.join(self.PATH_DETECT_FILES, fichier), 'r') as ds:
                # Get eddies coordinates and amplitude
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                amp = ds.variables['amplitude'][:] * 100
                
                # For each eddy 
                for i in range(len(latitudes)):
                    x, y, amplitude = latitudes[i], longitudes[i], amp[i]
                    
                    #  Check if the eddy is in the domain of study 
                    if (zone_params['llcrnrlon'] <= y <= zone_params['urcrnrlon']) and (zone_params['llcrnrlat'] <= x <= zone_params['urcrnrlat']):
                        # Calculate corresponding cell indices while keeping values within bounds
                        lat_index = min(max(int((x - zone_params['llcrnrlat']) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - zone_params['llcrnrlon']) / grid_size), 0), lon_cells - 1)
                        
                        # Add the radius to the sum 
                        amp_sums[lat_index, lon_index] += amplitude

                        #Compute the number of eddies
                        cell_counts[lat_index, lon_index] += 1
        
        # Compute the average radius for each cell (avoiding division by zero)
        average_amp = np.divide(amp_sums, cell_counts, where=cell_counts != 0)
        
        #Create a map
        # fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
        
        
        
        # Create a masque for values = 0 
        mask = cell_counts == 0
        
        
        average_amp = np.ma.masked_array(average_amp, mask=mask)

        #Create heatmap
        heatmap = ax.imshow(average_amp, cmap='jet',vmax=vmax ,origin='lower',
                            extent=[zone_params['llcrnrlon'], zone_params['urcrnrlon'], zone_params['llcrnrlat'],zone_params['urcrnrlat']])
        
        cbar = plt.colorbar(heatmap ,location='bottom',shrink=0.5,label='Mean amplitude of eddies (cm)')
        
        # Add title and labels
        plt.title('Amplitude of eddies ' + str(self.model))
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')

        # Add coasts and land
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(-180, 180, 10), ylocs=np.arange(-180, 180, 10))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False


    def plot_multiple_heatmaps_amplitude(self, zone_params_list,vmax):
        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(20, 20), subplot_kw={'projection': ccrs.PlateCarree()})
    
        for ax, zone_params in zip(axes.flat, zone_params_list):
            self.plot_heatmap_amplitude(zone_params, ax,vmax)
    
        plt.tight_layout()
    
        # Save and show
        plt.savefig(
            self.dir_plot + self.model + "_MULTIPLE_HEATMAPS_AMPLITUDE" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
    
        if self.show:
            plt.show()
    
    def plot_number_detection_time(self, NB_EDDIES):
        t_data = pd.date_range(self.date_start, periods=self.periods, freq="D")
        # NB_mean = np.full(len(t_data), np.mean(NB_EDDIES))
        # NB_mean_zone = [np.mean(NB_EDDIES)]*len(t_data)
        fig, ax = plt.subplots(figsize=(12, 6))
        # ax = fig.add_axes([.03,.03,.94,.94])
        ax.plot(t_data, NB_EDDIES, color="black")
        ax.xaxis.set_major_locator(mdates.MonthLocator([1,2,3]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.ylabel("Nb eddy detected")
        # ax.plot(t_data, NB_mean, label='Mean by day =  '+ str(int(np.round(np.mean(NB_mean_zone)))), linestyle="--")
        # ax.legend()

        plt.savefig(
            f"{self.dir_plot}NB_EDDIES_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()

    def plot_number_detection_multizone(self, NB_EDDIES_GS,NB_EDDIES_IBI,NB_EDDIES_AG,NB_EDDIES_KOE):
        t_data = pd.date_range(self.date_start, periods=self.periods, freq="D")
        # NB_mean = np.full(len(t_data), np.mean(NB_EDDIES))
        # NB_mean_zone = [np.mean(NB_EDDIES)]*len(t_data)
        fig, ax = plt.subplots(figsize=(12, 6))
        # ax = fig.add_axes([.03,.03,.94,.94])
        ax.plot(t_data, NB_EDDIES_GS, color="red",label='GS')
        ax.plot(t_data, NB_EDDIES_IBI, color="green",label='IBI')
        ax.plot(t_data, NB_EDDIES_AG, color="pink",label='AG')
        ax.plot(t_data, NB_EDDIES_KOE, color="purple",label='KOE')
        
        ax.xaxis.set_major_locator(mdates.MonthLocator([1,2,3]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.ylabel("Nb eddy detected")
        # ax.plot(t_data, NB_mean, label='Mean by day =  '+ str(int(np.round(np.mean(NB_mean_zone)))), linestyle="--")
        ax.legend()

        plt.savefig(
            f"{self.dir_plot}NB_EDDIES_MULTIPLE_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    
    def plot_count_log_amp(self,eddies,eddies_ref):

        kwargs_eddies = dict(label="Eddies " + str(self.model), color="blue")
        kwargs_eddies_ref = dict(label="Eddies "+ str(self.reference), color="grey")
        
        fig, ax = plt.subplots(figsize=(6, 4))

        title = "Amplitude"
        
        data = eddies["amplitude"] * 100
        bins = np.arange(0.0005, 1000, 0.2)
        
        hist, bins = np.histogram(data, bins=bins)

        
        data_ref = eddies_ref["amplitude"] * 100

        bins_ref = np.arange(0.0005, 1000, 0.2)
        
        hist_ref, bins_ref = np.histogram(data_ref, bins=bins_ref)

        ax.semilogy(bins[:-1], hist, **kwargs_eddies)
        ax.semilogy(bins_ref[:-1], hist_ref, **kwargs_eddies_ref)
        ax.grid()
        ax.set_title(title)
        ax.set_xlabel("Amplitude Value (cm)")
        ax.set_ylabel("Count (log scale)")
        ax.set_xlim(0, 20)  # Limite de l'axe des abscisses
        ax.legend()
        plt.savefig(
            f"{self.dir_plot}COUNT_AMP_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()


    def plot_count_log_amp_multiple(self,eddies_GS, eddies_IBI, eddies_AG, eddies_KOE):
        
        kwargs_eddies_GS = dict(label="GS", color="red")
        kwargs_eddies_IBI = dict(label="IBI", color="green")
        kwargs_eddies_AG = dict(label="AG", color="pink")
        kwargs_eddies_KOE = dict(label="KOE", color="purple")


        fig, ax = plt.subplots(figsize=(6, 4))

        # name = "amplitude"
        title = "Amplitude"
        bins = np.arange(0.0005, 1000, 0.2)

        
        data_GS=eddies_GS["amplitude"]*100
        hist_GS, bins_GS = np.histogram(data_GS, bins=bins)

        data_IBI=eddies_IBI["amplitude"]*100
        hist_IBI, bins_IBI = np.histogram(data_IBI, bins=bins)

        data_AG=eddies_AG["amplitude"]*100
        hist_AG, bins_AG = np.histogram(data_AG, bins=bins)

        data_KOE=eddies_KOE["amplitude"]*100
        hist_KOE, bins_KOE = np.histogram(data_KOE, bins=bins)


    
        ax.semilogy(bins_GS[:-1], hist_GS, **kwargs_eddies_GS)
        ax.semilogy(bins_IBI[:-1], hist_IBI, **kwargs_eddies_IBI)
        ax.semilogy(bins_AG[:-1], hist_AG, **kwargs_eddies_AG)
        ax.semilogy(bins_KOE[:-1], hist_KOE, **kwargs_eddies_KOE)
 

        ax.grid()
        ax.set_title(title)
        ax.set_xlabel("Amplitude Value (cm)")
        ax.set_ylabel("Count (log scale)")
        ax.set_xlim(0, 20)  # Limite de l'axe des abscisses
        ax.legend()
        
        # Save the plot
        plt.savefig(f"{self.dir_plot}COUNT_AMP_{self.model}_MULTIPLE.jpeg", bbox_inches="tight")

        # Show the plot
        if self.show:
            plt.show()


    def plot_count_log_rad(self,eddies,eddies_ref):

        kwargs_eddies = dict(label="Eddies " + str(self.model), color="blue")
        kwargs_eddies_ref = dict(label="Eddies "+ str(self.reference), color="grey")
        
        fig, ax = plt.subplots(figsize=(6, 4))

        title = "Radius"
        
        data = eddies["effective_radius"] / 1000
        bins = np.arange(0, 2000, 1)
        
        hist, bins = np.histogram(data, bins=bins)
        
        data_ref = eddies_ref["effective_radius"] /1000

        bins_ref = np.arange(0, 2000, 1)
        
        hist_ref, bins_ref = np.histogram(data_ref, bins=bins_ref)

        ax.semilogy(bins[:-1], hist, **kwargs_eddies)
        ax.semilogy(bins_ref[:-1], hist_ref, **kwargs_eddies_ref)
        ax.grid()
        ax.set_title(title)
        ax.set_xlabel("Radius Value (km)")
        ax.set_ylabel("Count (log scale)")
        ax.set_xlim(0, 130)  # Limite de l'axe des abscisses
        ax.legend()
        plt.savefig(
            f"{self.dir_plot}COUNT_RAD_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()


    def plot_count_log_rad_multiple(self,eddies_GS, eddies_IBI, eddies_AG, eddies_KOE):
        
        kwargs_eddies_GS = dict(label="GS", color="red")
        kwargs_eddies_IBI = dict(label="IBI", color="green")
        kwargs_eddies_AG = dict(label="AG", color="pink")
        kwargs_eddies_KOE = dict(label="KOE", color="purple")

        fig, ax = plt.subplots(figsize=(6, 4))

        title = "Radius"
        bins =  np.arange(0, 2000, 1)

        data_GS=eddies_GS["effective_radius"]/1000
        hist_GS, bins_GS = np.histogram(data_GS, bins=bins)

        data_IBI=eddies_IBI["effective_radius"]/1000
        hist_IBI, bins_IBI = np.histogram(data_IBI, bins=bins)

        data_AG=eddies_AG["effective_radius"]/1000
        hist_AG, bins_AG = np.histogram(data_AG, bins=bins)

        data_KOE=eddies_KOE["effective_radius"]/1000
        hist_KOE, bins_KOE = np.histogram(data_KOE, bins=bins)

        ax.semilogy(bins_GS[:-1], hist_GS, **kwargs_eddies_GS)
        ax.semilogy(bins_IBI[:-1], hist_IBI, **kwargs_eddies_IBI)
        ax.semilogy(bins_AG[:-1], hist_AG, **kwargs_eddies_AG)
        ax.semilogy(bins_KOE[:-1], hist_KOE, **kwargs_eddies_KOE)
 

        ax.grid()
        ax.set_title(title)
        ax.set_xlabel("Radius Value (km)")
        ax.set_ylabel("Count (log scale)")
        ax.set_xlim(0, 130)  # Limite de l'axe des abscisses
        ax.legend()
        
        # Save the plot
        plt.savefig(f"{self.dir_plot}COUNT_RAD_{self.model}_MULTIPLE.jpeg", bbox_inches="tight")

        # Show the plot
        if self.show:
            plt.show()


        
    def plot_count_lifetime(self,eddies,eddies_ref):
        
        fig, ax = plt.subplots(figsize=(6, 4))

        # Select the variable nb_obs-by_track which is the lifetime of eddies
        name = "nb_obs_by_track"
        title = "Eddy lifetime (days)"
        x = np.arange(0, 2000, 1)
        
        data = eddies.nb_obs_by_track
        data= data[data!= 0]

        data_ref = eddies_ref.nb_obs_by_track
        data_ref= data_ref[data_ref!= 0]


        hist, x = np.histogram(data, bins=x)
        hist_ref, x_ref = np.histogram(data_ref, bins=x)
        
        ######PLOT######
        
        # Log scale 
        ax.semilogy(x[:-1], hist, color="blue",label='Eddies ' + str(self.model))
        ax.semilogy(x[:-1], hist_ref, color="grey",label='Eddies ' + str(self.reference))
         
        # Add legend and label
        ax.set_xlabel(title)
        ax.set_ylabel("Count (log scale)")
        ax.legend()
        ax.set_xlim(10, self.periods)
        ax.grid()
        x_ticks = np.arange(10, self.periods, 10)  # Generate ticks from 10 to 30 with step 1
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([str(int(tick)) for tick in x_ticks])

        # Save the plot
        plt.savefig(f"{self.dir_plot}LIFETIME_{self.model}_{self.reference}.jpeg", bbox_inches="tight")

        # Show the plot
        if self.show:
            plt.show()

    def plot_count_lifetime_multiple(self,eddies_GS, eddies_IBI, eddies_AG, eddies_KOE):
        
        fig, ax = plt.subplots(figsize=(6, 4))

        # Select the variable nb_obs-by_track which is the lifetime of eddies
        name = "nb_obs_by_track"
        title = "Eddy lifetime"
        x = np.arange(0, 2000, 1)
        
        data_GS = eddies_GS.nb_obs_by_track
        data_GS= data_GS[data_GS!= 0]

        data_IBI = eddies_IBI.nb_obs_by_track
        data_IBI= data_IBI[data_IBI!= 0]

        data_AG = eddies_AG.nb_obs_by_track
        data_AG= data_AG[data_AG!= 0]

        data_KOE = eddies_KOE.nb_obs_by_track
        data_KOE= data_KOE[data_KOE!= 0]

  
        hist_GS, x_GS = np.histogram(data_GS, bins=x)
        hist_IBI, x_IBI = np.histogram(data_IBI, bins=x)
        hist_AG, x_AG = np.histogram(data_AG, bins=x)
        hist_KOE, x_KOE = np.histogram(data_KOE, bins=x)
       
        
        ######PLOT######
        
        # Log scale 
        ax.semilogy(x[:-1], hist_GS, color="red",label='GS')
        ax.semilogy(x[:-1], hist_IBI, color="green",label='IBI')
        ax.semilogy(x[:-1], hist_AG, color="pink",label='AG')
        ax.semilogy(x[:-1], hist_KOE, color="purple",label='KOE')
         
        # Add legend and label
        ax.set_xlabel("Eddy lifetime (days)")
        ax.set_ylabel("Count (log scale)")
        ax.legend()
        ax.set_xlim(10, self.periods)
        ax.grid()
        x_ticks = np.arange(10, self.periods, 10)  # Generate ticks from 10 to 30 with step 1
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([str(int(tick)) for tick in x_ticks])
        
        # Save the plot
        plt.savefig(f"{self.dir_plot}LIFETIME_MULTIPLE.jpeg", bbox_inches="tight")

        # Show the plot
        if self.show:
            plt.show()
            

    def plot_histo_matching(self,radius_AR_hits, radius_AR_misses, radius_AR_falarm):
        bins = np.arange(0, 250, 5)
        
        hits_histogram = np.histogram(radius_AR_hits, bins=bins)
        misses_histogram = np.histogram(radius_AR_misses, bins=bins)
        falarm_histogram = np.histogram(radius_AR_falarm, bins=bins)
        
        # Calculer les coordonn??es des points d'escalier pour chaque histogramme
        hits_x = hits_histogram[1][:-1]
        hits_y = hits_histogram[0]
        
        misses_x = misses_histogram[1][:-1]
        misses_y = misses_histogram[0]
        
        falarm_x = falarm_histogram[1][:-1]
        falarm_y = falarm_histogram[0]
        max_value = max(
            max(hits_histogram[0]),
            max(misses_histogram[0]),
            max(falarm_histogram[0])
            )
        # Lissage des donn??es
        f_hits = interp1d(hits_x, hits_y, kind='cubic')
        f_misses = interp1d(misses_x, misses_y, kind='cubic')
        f_falarm = interp1d(falarm_x, falarm_y, kind='cubic')
        
        x_new = np.linspace(0, max(max(hits_x), max(misses_x), max(falarm_x)), 1000)

        y_hits_smooth = f_hits(x_new)
        y_misses_smooth = f_misses(x_new)
        y_falarm_smooth = f_falarm(x_new)
        
    
        fig, ax = plt.subplots(figsize=(8, 6))
        
        ax.plot(x_new, y_hits_smooth, label='hits', color='green')
        ax.plot(x_new, y_misses_smooth, label='misses', color='red')
        ax.plot(x_new, y_falarm_smooth, label='false alarm', color='orange')
        

        ax.set_ylim(0, max_value + 1000)
        ax.set_xlim(0, 130)
        ax.set_xlabel("Radius (km)")
        ax.set_ylabel("Occurences")
        ax.set_title(f"{self.model} Reference {self.reference}")
        ax.legend()
        ax.grid(True)

        plt.savefig(
            f"{self.dir_plot}HIST_MATCHING_{self.model}_{self.year}.jpeg",
            bbox_inches="tight")
        if self.show:
            plt.show()




    def plot_pod_far_time(self, AR_POD, AR_FAR):
        t_data_obs = pd.date_range(self.date_start, periods=self.periods - 1, freq="D")
    
        fig, ax = plt.subplots(figsize=(17, 3))
    
        # Plot Probability Of Detection
        ax.plot(t_data_obs, AR_POD, color="green", label="Probability Of Detection")
    
        # Plot False Alarm Ratio
        ax.plot(t_data_obs, AR_FAR, color="red", label="False Alarm Ratio")
    
        # Setting limits for y-axis
        ax.set_ylim(0, 1)
    
        # Setting major locators and formatters for x-axis
        ax.xaxis.set_major_locator(mdates.MonthLocator([1,2,3]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    
        # Add title and labels
        ax.set_title("Probability Of Detection and False Alarm Ratio Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
    
        # Add a legend
        ax.legend()
    
        # Add grid
        ax.grid()

        # Save the figure
        plt.savefig(
            f"{self.dir_plot}POD_FAR_TEMP_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )

        # Show the plot if specified
        if self.show:
            plt.show()


    def perf_diag(self, SR_GS, AR_POD_GS, SR_IBI, AR_POD_IBI, SR_AG, AR_POD_AG, SR_KOE, AR_POD_KOE ,SR_GLO,AR_POD_GLO):
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

        ax.set_title("Performance Diagram " + self.model + " " + str(self.year), y=1.08)
        ax.scatter(np.mean(SR_GLO), np.mean(AR_POD_GLO), color="blue", s=200)
        ax.text(np.mean(SR_GLO), np.mean(AR_POD_GLO) + 0.02, "Global", color="blue", size=15)

        ax.scatter(np.mean(SR_GS), np.mean(AR_POD_GS), color="red", s=150, label="GS")
        ax.scatter(np.mean(SR_IBI), np.mean(AR_POD_IBI), color="green", s=150, label="IBI")
        ax.scatter(np.mean(SR_AG), np.mean(AR_POD_AG), color="pink", s=150, label="AG")
        ax.scatter(np.mean(SR_KOE), np.mean(AR_POD_KOE), color="purple", s=150, label="KOE")
    
        # Add legend
        ax.legend(loc="best")
        # ax.scatter(np.mean(SR_GS), np.mean(AR_POD_GS), color="red", s=150)
        # ax.scatter(np.mean(SR_IBI), np.mean(AR_POD_IBI), color="green", s=150)
        # ax.scatter(np.mean(SR_AG), np.mean(AR_POD_AG), color="pink", s=150)
        # ax.scatter(np.mean(SR_KOE), np.mean(AR_POD_KOE), color="purple", s=150)

        
        # ax.text(np.mean(SR_GS), np.mean(AR_POD_GS) - 0.05, "GS", color="red", size=13)
        # ax.text(np.mean(SR_IBI), np.mean(AR_POD_IBI) - 0.05, "IBI", color="green", size=13)
        # ax.text(np.mean(SR_AG), np.mean(AR_POD_AG) - 0.05, "AG", color="pink", size=13)
        # ax.text(np.mean(SR_KOE), np.mean(AR_POD_KOE) - 0.05, "DKOE", color="purple", size=13)

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
        
            
        plt.savefig(f"{self.dir_plot}PERFORMANCE_DIAG_{self.model}_{self.year}.jpeg", bbox_inches="tight", dpi=600)

        if self.show:
            plt.show()


