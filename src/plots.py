import os
import fnmatch

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from labellines import labelLine, labelLines
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import netCDF4 as nc
data_crs = ccrs.PlateCarree()


def plt_cartopy(ax, labels=True):
    # ax.set_aspect('auto') # The figure will follow the ratio of the figsize
    ax.coastlines()  # Plot the coastlines
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
        self.periods = (
            len(fnmatch.filter(os.listdir(general_info["PATH_DETECT_FILES"]), "*.*"))
            // 2
        )

        self.PATH_DETECT_FILES = str(general_info["PATH_DETECT_FILES"])
        self.PATH_TRAJ_FILES = str(general_info["PATH_TRAJ_FILES"])
        self.PATH_REF_TRACK = str(general_info["PATH_REF_TRACK"])

        # Geographical extend
        self.lon_min = int(general_info["LON_MIN"])
        self.lon_max = int(general_info["LON_MAX"])
        self.lat_min = int(general_info["LAT_MIN"])
        self.lat_max = int(general_info["LAT_MAX"])

        self.dir_plot = str(info["PLOT_INFO"]["PATH_PLOT"])
        self.GRID_SIZE =int(plot_info["GRID_SIZE"])
        self.show = show

    def plot_one_day_adt(self, h, var_adt, a, c):
        fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
        

        AC_x, AC_y = a.effective_contour_longitude, a.effective_contour_latitude
        CC_x, CC_y = c.effective_contour_longitude, c.effective_contour_latitude

        ax.plot(
            AC_x.T, AC_y.T, color="k", linestyle="-", linewidth=1, transform=data_crs
        )
        ax.plot(
            CC_x.T, CC_y.T, color="k", linestyle=":", linewidth=1.5, transform=data_crs
        )

        ax.set_title(self.model)
        im = h.display(ax, var_adt, vmin=-0.15, vmax=0.15)
        plt_cartopy(ax, labels=False)
        plt.suptitle("Detection Cyclonic (Dotted) & Anticyclonic (Solid)")
        cbar = fig.colorbar(im, orientation='horizontal', ticks=[-0.1, 0, 0.1, 0.2], pad=0.08, shrink=0.8, extend='both')
        cbar.ax.set_xlabel("ADT (m) Filtered (500 km)")
        
        
        # Pour rendre l'étiquette de la colorbar centrée
        cbar.ax.xaxis.set_label_coords(0.5, 1.5)
        
        # Pour ajuster la taille de la police de l'étiquette
        cbar.ax.xaxis.label.set_fontsize(12)

        
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False
        # Save or show
        plt.savefig(self.dir_plot + self.model + "_Detection.jpeg", bbox_inches="tight", dpi=500)

        if self.show:
            plt.show()
        else:
            pass


    def plot_heatmap(self):


        dossier_data = self.PATH_DETECT_FILES
        
        # Geographical extent
        longitude_min = self.lon_min
        longitude_max = self.lon_max
        latitude_min = self.lat_min
        latitude_max = self.lat_max
        
        # Define grid size (ex 2 degrees * 2 degrees) 
        grid_size = 2.0
        
        # Compute the number of cells 
        lat_cells = int((latitude_max - latitude_min) / grid_size)
        lon_cells = int((longitude_max - longitude_min) / grid_size)
        
        # Create an empty grid
        cell_counters = np.zeros((lat_cells, lon_cells), dtype=int)
        
        
        for fichier in os.listdir(dossier_data):
            with nc.Dataset(os.path.join(dossier_data, fichier), 'r') as ds:
                # Find the coordinates of the eddies 
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                
                # For each coordinate 
                for i in range(len(latitudes)):
                    x, y = latitudes[i], longitudes[i]  # Coordonnées du tourbillon
                    # Check if the eddy is in the domain of study 
                    if (longitude_min <= y <= longitude_max) and (latitude_min <= x <= latitude_max):
                        
                        # Compute the index 
                        lat_index = min(max(int((x - latitude_min) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - longitude_min) / grid_size), 0), lon_cells - 1)
                 
        
                        # Add to the counter of the appropriate cell
                        cell_counters[lat_index, lon_index] += 1
        
        # Create a map
        fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Add coasts
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        
        # Create a mask 
        mask = cell_counters == 0
        
        
        cell_counters = np.ma.masked_array(cell_counters, mask=mask)
        
        # Create the heatmap
        heatmap = ax.imshow(cell_counters/periods, vmin=0,vmax=5,cmap='jet', origin='lower', extent=[longitude_min, longitude_max, latitude_min, latitude_max])
        cbar = plt.colorbar(heatmap,orientation='horizontal', label='Daily number of eddies')
        
        # Add a title and labels 
        plt.title('Heatmap of eddies ' + str(self.model))
        
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False


        #Save and show
        plt.savefig(
                self.dir_plot + self.model + "_HEATMAP" + ".jpeg",
                bbox_inches="tight",
                dpi=500,)
    
        if self.show:
            plt.show()



    def plot_heatmap_radius(self):    
                    
        dossier_data = self.PATH_DETECT_FILES
        
        ## Geographical extent
        longitude_min = self.lon_min
        longitude_max = self.lon_max
        latitude_min = self.lat_min
        latitude_max = self.lat_max
        
        # Define grid size (ex 2 degrees * 2 degrees) 
        grid_size = 2.0
        
        # Compute the number of cells 
        lat_cells = int((latitude_max - latitude_min) / grid_size)
        lon_cells = int((longitude_max - longitude_min) / grid_size)
        
        # Create empty grids
        radius_sums = np.zeros((lat_cells, lon_cells), dtype=float)
        cell_counts = np.zeros((lat_cells, lon_cells), dtype=int)  # Compteur de tourbillons dans chaque cellule
        
        
        for fichier in os.listdir(dossier_data):
            with nc.Dataset(os.path.join(dossier_data, fichier), 'r') as ds:
                # Get eddies coordinates and radius
                latitudes = ds.variables['latitude'][:]
                longitudes = ds.variables['longitude'][:]
                radii = ds.variables['effective_radius'][:] /1000
                
                # For each eddy 
                for i in range(len(latitudes)):
                    x, y, radius = latitudes[i], longitudes[i], radii[i]
                    
                    #  Check if the eddy is in the domain of study 
                    if (longitude_min <= y <= longitude_max) and (latitude_min <= x <= latitude_max):
                        # Compute the index
                        lat_index = min(max(int((x - latitude_min) / grid_size), 0), lat_cells - 1)
                        lon_index = min(max(int((y - longitude_min) / grid_size), 0), lon_cells - 1)
                        
                        # Add the radius to the sum 
                        radius_sums[lat_index, lon_index] += radius

                        #Compute the number of eddies
                        cell_counts[lat_index, lon_index] += 1
        
        # Compute the average radius for each cell (avoiding division by zero)
        average_radii = np.divide(radius_sums, cell_counts, where=cell_counts != 0)
        
        #Create a map
        fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Add coasts
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        
        # Create a masque for values = 0 
        mask = cell_counts == 0
        
        
        average_radii = np.ma.masked_array(average_radii, mask=mask)

        #Create heatmap
        heatmap = ax.imshow(average_radii, cmap='jet',vmax=80 ,origin='lower',
                            extent=[longitude_min, longitude_max, latitude_min, latitude_max])
        
        cbar = plt.colorbar(heatmap ,location='bottom',shrink=0.7,label='Mean radius of eddies (km)')
        
        # Add title and labels
        plt.title('Radius of eddies ' + str(self.model))
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False

        #Save and show
        plt.savefig(
            self.dir_plot + self.model + "_HEATMAP_RADIUS" + ".jpeg",
            bbox_inches="tight",
            dpi=500,)

        if self.show:
            plt.show()

    
    def plot_all_tracks_period(self, at, ct):
        fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
        at.plot(
            ax,
            # ref=-10,
            label="Anticyclonic {nb_tracks} tracks",
            color="r",
            lw=0.9,
            transform=data_crs,
        )
        ct.plot(
            ax,
            # ref=-10,
            label="Cyclonic {nb_tracks} tracks",
            color="b",
            lw=0.9,
            transform=data_crs,
        )

        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1) # ghostwhite
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False ; gl.top_labels = False
        ax.legend()
    
        ax.set_title("Tracks " + str(self.model) + " " + str(self.year))
        plt_cartopy(ax, labels=False)
        plt.savefig(
            self.dir_plot + self.model + "_TRACKS_" + str(self.year) + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )

        if self.show:
            plt.show()

    def plot_number_detection_time_mean(self, NB_EDDIES):
        t_data = pd.date_range(self.date_start, periods=self.periods, freq="D")
        NB_mean = np.full(len(t_data), np.mean(NB_EDDIES))

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(t_data, NB_EDDIES, color="black")
        ax.xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.ylabel("Nb eddy detected")
        ax.plot(t_data, NB_mean, label="Mean", linestyle="--")
        ax.legend()

        plt.savefig(
            f"{self.dir_plot}NB_EDDIES_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_2d_histo(self, at):
        fig, ax = plt.subplots()
        counts, xedges, yedges, im = ax.hist2d(
            at["effective_radius"] / 1000,
            at["amplitude"] * 100,
            bins=200,
            cmap=plt.cm.jet,
            cmin=1,
        )
        ax.set_xlabel("Radius (km)")
        ax.set_ylabel("Amplitude (cm)")

        fig.colorbar(im, ax=ax)
        plt.title(self.model)
        plt.savefig(
            f"{self.dir_plot}HIST2D_AMP_RAD_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_histo_hits_false(self, radius_AR_hits, radius_AR_misses, radius_AR_falarm):
        bins = np.arange(0, 250, 5)


        hits_histogram = np.histogram(radius_AR_hits, bins=bins)
        misses_histogram = np.histogram(radius_AR_misses, bins=bins)
        falarm_histogram = np.histogram(radius_AR_falarm, bins=bins)

    
        max_value = max(
        	max(hits_histogram[0]),
        	max(misses_histogram[0]),
    		max(falarm_histogram[0])
	    	)
        
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(
            radius_AR_hits,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="hits",
            color="green",
        )
        ax.hist(
            radius_AR_misses,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="misses",
            color="red",
        )
        ax.hist(
            radius_AR_falarm,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="false alarm",
            color="orange",
        )

        ax.set_ylim(0, max_value + 1000 )
        ax.set_xlim(0, 100)
        ax.set_xlabel("Radius (km)")
        ax.legend()
        ax.set_title(f"{self.model} Reference {self.reference}")
        plt.savefig(
            f"{self.dir_plot}HIST_MATCHING_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()

    def plot_pod_far_amplitude(self, POD_AR, FAR_AR):
        bins = np.arange(0, 400, 1)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        axes[0].step(bins[:-1], POD_AR, color="black", linewidth=2)
        axes[0].set(
            ylim=(0, 1.05),
            ylabel="Probability of Detection",
            xlim=(0, 15),
            xlabel="Amplitude (cm)",
            xticks=np.arange(0, 15, 5),
        )
        axes[0].grid()

        axes[1].step(bins[:-1], FAR_AR, color="black", linewidth=2)
        axes[1].set(
            ylim=(0, np.nanmax(FAR_AR) + 0.2),
            ylabel="False Alarm Ratio",
            xlim=(0, 15),
            xlabel="Amplitude (cm)",
            xticks=np.arange(0, 15, 5),
        )
        axes[1].grid()

        fig.suptitle(f"{self.model} Reference {self.reference}")
        plt.tight_layout()
        plt.savefig(
            f"{self.dir_plot}POD_FAR_AMP_{self.model}_{self.year}.jpeg",
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
            f"{self.dir_plot}POD_FAR_TEMP_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()

    def perf_diag(self, SR, AR_POD):
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
        ax.scatter(np.mean(SR), np.mean(AR_POD), color="blue", s=200)
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

        plt.savefig(
            f"{self.dir_plot}PERFORMANCE_DIAG_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
            dpi=500,
        )

        if self.show:
            plt.show()
