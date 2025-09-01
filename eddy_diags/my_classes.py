import os
import sys
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
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
dir_cartopy = "/home/smer/sval001/WORK/DATA/cartopy_data/"
cartopy.config['pre_existing_data_dir'] = os.path.join(dir_cartopy, 'cartopy_data')
os.environ['CARTOPY_USER_BACKGROUNDS'] = os.path.join(dir_cartopy, 'cartopy_data')

data_crs = ccrs.PlateCarree()
from scipy.interpolate import interp1d

sys.path.append("./")
import eddy_diags.my_functions as fn

class Plots:
    def __init__(self, DATE_START, MODEL, REFERENCE, YEAR, PATH_DETECT_FILES, PATH_DETECT_FILES_REF, PATH_TRAJ_FILES, PATH_REF_TRACK, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, PATH_PLOT, GRID_SIZE, show=False):
        dir_cartopy = "/home/smer/regnierc/code/LIB_PYT/lib_pyt_dev/lib_pyt/lib_pyt/statics/cartopy_data/"
        cartopy.config['pre_existing_data_dir'] = os.path.join(dir_cartopy, 'cartopy_data')
        self.model = str(MODEL)
        self.reference = str(REFERENCE)
        self.year = int(YEAR)
        self.date_start = str(DATE_START)
        self.periods = (
            len(fnmatch.filter(os.listdir(PATH_DETECT_FILES), "*.*"))
            // 2
        )

        self.PATH_DETECT_FILES = str(PATH_DETECT_FILES)
        self.PATH_DETECT_FILES_REF=str(PATH_DETECT_FILES_REF)
        self.PATH_TRAJ_FILES = str(PATH_TRAJ_FILES)
        self.PATH_REF_TRACK = str(PATH_REF_TRACK)

        # Geographical extend
        self.lon_min = int(LON_MIN)
        self.lon_max = int(LON_MAX)
        self.lat_min = int(LAT_MIN)
        self.lat_max = int(LAT_MAX)

        self.dir_plot = str(PATH_PLOT)
        self.GRID_SIZE =int(GRID_SIZE)
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
        plt.cartopy(ax, labels=False)
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


    def plot_heatmap(self, dossier_data, model_name, vmin, vmax):
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
        
        fig, ax = plt.subplots(figsize=(10,10),subplot_kw={'projection': ccrs.PlateCarree()})
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
        
        mask = cell_counters == 0
        cell_counters = np.ma.masked_array(cell_counters, mask=mask)
        
        heatmap = ax.imshow(cell_counters/self.periods, vmin=vmin, vmax=vmax, cmap='jet', origin='lower', extent=[longitude_min, longitude_max, latitude_min, latitude_max])
        cbar = plt.colorbar(heatmap, orientation='horizontal', label='Daily number of eddies')
        
        plt.title('Heatmap of eddies ' + model_name)
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1)
        
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False
        gl.top_labels = False

        plt.savefig(
                self.dir_plot + model_name + "_HEATMAP" + ".jpeg",
                bbox_inches="tight",
                dpi=500,)
    
        if self.show:
            plt.show()

    def plot_heatmap_model(self):
        self.plot_heatmap(self.PATH_DETECT_FILES, str(self.model), 0, 4)

    def plot_heatmap_ref(self):
        self.plot_heatmap(self.PATH_DETECT_FILES_REF, str(self.reference), 0, 4)


    def plot_heatmap_radius(self, dossier_data, model_name, vmax):
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
    
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
    
        mask = cell_counts == 0
        average_radii = np.ma.masked_array(average_radii, mask=mask)
    
        heatmap = ax.imshow(average_radii, cmap='jet', vmax=vmax, origin='lower', extent=[longitude_min, longitude_max, latitude_min, latitude_max])
    
        cbar = plt.colorbar(heatmap, location='bottom', shrink=0.5, label='Mean radius of eddies (km)')
    
        plt.title('Radius of eddies ' + model_name)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
    
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1)
    
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False
        gl.top_labels = False
    
        plt.savefig(
            self.dir_plot + model_name + "_HEATMAP_RADIUS" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
    
        if self.show:
            plt.show()


    def plot_heatmap_radius_model(self):
        self.plot_heatmap_radius(self.PATH_DETECT_FILES, str(self.model), 100)
    
    def plot_heatmap_radius_ref(self):
        self.plot_heatmap_radius(self.PATH_DETECT_FILES_REF, str(self.reference), 100)
    
    def plot_heatmap_amplitude(self, dossier_data, model_name, vmax):
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
    
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor='black')
    
        mask = cell_counts == 0
        average_amp = np.ma.masked_array(average_amp, mask=mask)
    
        heatmap = ax.imshow(average_amp, cmap='jet', vmax=vmax, origin='lower', extent=[longitude_min, longitude_max, latitude_min, latitude_max])
    
        cbar = plt.colorbar(heatmap, location='bottom', shrink=0.5, label='Mean amplitude of eddies (cm)')
    
        plt.title('Amplitude of eddies ' + model_name)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
    
        ax.add_feature(cartopy.feature.LAND, edgecolor='k', facecolor='linen', zorder=1)
    
        gl = ax.gridlines(draw_labels=True, linestyle=':', xlocs=np.arange(self.lon_min, self.lon_max, 30), ylocs=np.arange(self.lat_min, self.lat_max, 20))
        gl.xlabel_style = {'color': 'k', 'size': 'medium'}
        gl.ylabel_style = {'color': 'k', 'size': 'medium'}
        gl.right_labels = False
        gl.top_labels = False
    
        plt.savefig(
            self.dir_plot + model_name + "_HEATMAP_AMPLITUDE" + ".jpeg",
            bbox_inches="tight",
            dpi=500,
        )
    
        if self.show:
            plt.show()


    def plot_heatmap_amplitude_model(self):
        self.plot_heatmap_amplitude(self.PATH_DETECT_FILES, str(self.model), 7)
        
    def plot_heatmap_amplitude_ref(self):
        self.plot_heatmap_amplitude(self.PATH_DETECT_FILES_REF, str(self.reference), 7)

    def plot_all_tracks_period(self, at, ct):
        dir_cartopy = "/home/smer/sval001/WORK/DATA/cartopy_data/"
        cartopy.config['pre_existing_data_dir'] = os.path.join(dir_cartopy, 'cartopy_data')
        os.environ['CARTOPY_USER_BACKGROUNDS'] = os.path.join(dir_cartopy, 'cartopy_data')
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
        fn.plt_cartopy(ax, labels=False)
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

    def plot_2d_histo(self, eddies):
        fig, ax = plt.subplots()
        counts, xedges, yedges, im = ax.hist2d(
            eddies["effective_radius"] / 1000,
            eddies["amplitude"] * 100,
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

    def plot_count_log_amp(self,at,ct,a_ref,c_ref):
        
        kwargs_a = dict(label="Anticyclonic", color="r")
        kwargs_c = dict(label="Cyclonic", color="b")
        kwargs_eddies = dict(label="Eddies " + str(self.model), color="k")
        kwargs_eddies_ref = dict(label="Eddies "+ str(self.reference), color="g")
        
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
        
        
        ax.semilogy(bins[:-1], hist_eddies, **kwargs_eddies)
        ax.semilogy(bins_ref[:-1], hist_eddies_ref, **kwargs_eddies_ref)
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


    def plot_count_speed_radius(self,at,ct,a_ref,c_ref):
        fig, ax = plt.subplots(figsize=(6, 4))
        kwargs_a = dict(label="Anticyclonic", color="r")
        kwargs_c = dict(label="Cyclonic", color="b")
        kwargs_eddies = dict(label="Eddies "+ str(self.model), color="k")
        kwargs_eddies_ref = dict(label="Eddies " + str(self.reference), color="g")
        name = "speed_radius"
        title = "Speed Radius (km)"
        
        data_a = at[name] * 0.001
        data_c = ct[name] * 0.001
        bins = np.arange(0, 2000, 1)
        
        hist_a, bins = np.histogram(data_a, bins=bins)
        hist_c, _ = np.histogram(data_c, bins=bins)
        
        hist_eddies = hist_a + hist_c
        
        #### REF
        data_a_ref = a_ref[name] * 0.001
        data_c_ref = c_ref[name] * 0.001
        bins_ref = np.arange(0, 2000, 1)
        
        hist_a_ref, bins_ref = np.histogram(data_a_ref, bins=bins_ref)
        hist_c_ref, _ = np.histogram(data_c_ref, bins=bins_ref)
  
        hist_eddies_ref = hist_a_ref + hist_c_ref
        
        
        ax.semilogy(bins[:-1], hist_eddies, **kwargs_eddies)
        ax.semilogy(bins[:-1], hist_eddies_ref, **kwargs_eddies_ref)
        ax.grid()
        ax.set_title(title)
        ax.set_xlabel("Speed Radius Value (km)")
        ax.set_ylabel("Count (log scale)")
        ax.set_xlim(0, 100)  
        ax.legend()
        
        plt.savefig(
            f"{self.dir_plot}COUNT_RADIUS_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()
            
    def plot_count_lifetime(self,at,ct,a_ref,c_ref):
        
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
        
        kwargs_a = dict(label="Anticyclonic", color="r", bins=x)
        kwargs_c = dict(label="Cyclonic", color="b", bins=x)
        
       
        hist_a, x = np.histogram(data_a, bins=x)
        hist_c, _ = np.histogram(data_c, bins=x)
        hist_eddies = hist_a + hist_c
        
        hist_a_ref, x = np.histogram(data_a_ref, bins=x)
        hist_c_ref, _ = np.histogram(data_c_ref, bins=x)
        hist_eddies_ref = hist_a_ref + hist_c_ref
        
        # Log scale 
        ax.semilogy(x[:-1], hist_eddies, color="k",label='Eddies ' + str(self.model))
        ax.semilogy(x[:-1], hist_eddies_ref, color="g",label='Eddies ' + str(self.reference))
                    
        # Add legend and label
        ax.set_xlabel(title)
        ax.set_ylabel("Count (log scale)")
        ax.legend()
        ax.set_xlim(0, 150)
        ax.grid()

        #Show and save
        plt.savefig(
            f"{self.dir_plot}COUNT_LIFETIME_{self.model}_{self.year}.jpeg",
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
        
        ax.hist(radius_AR_hits,bins=bins,fill=False,linewidth=3,histtype="step",label="hits",color="green",)
        ax.hist(radius_AR_misses,bins=bins,fill=False,linewidth=3,histtype="step",label="misses",color="red",)
        ax.hist( radius_AR_falarm, bins=bins, fill=False, linewidth=3, histtype="step", label="false alarm", color="orange",)

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

    def plot_histo_lisse(self,radius_AR_hits, radius_AR_misses, radius_AR_falarm):
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

        print ("maxvlue = ",max_value)
        
        # Lissage des donn??es
        f_hits = interp1d(hits_x, hits_y, kind='cubic')
        f_misses = interp1d(misses_x, misses_y, kind='cubic')
        f_falarm = interp1d(falarm_x, falarm_y, kind='cubic')
        
        # Cr??er des points liss??s pour chaque histogramme
        # x_new = np.linspace(0, 245, 1000)  # Plus de points pour un lissage plus pr??cis
        x_new = np.linspace(0, max(max(hits_x), max(misses_x), max(falarm_x)), 1000)

        y_hits_smooth = f_hits(x_new)
        y_misses_smooth = f_misses(x_new)
        y_falarm_smooth = f_falarm(x_new)
        
        # Tracer l'histogramme liss??
        fig, ax = plt.subplots(figsize=(8, 6))
        
        ax.plot(x_new, y_hits_smooth, label='hits', color='green')
        ax.plot(x_new, y_misses_smooth, label='misses', color='red')
        ax.plot(x_new, y_falarm_smooth, label='false alarm', color='orange')
        
        # # Points pour chaque valeur d'escalier
        # ax.plot(hits_x, hits_y, 'o', color='green')
        # ax.plot(misses_x, misses_y, 'o', color='red')
        # ax.plot(falarm_x, falarm_y, 'o', color='orange')
        
        #ax.set_ylim(0, max_value + 10)
        ax.set_ylim(0, 70)
        ax.set_xlim(0, 80)
        ax.set_xlabel("Radius (km)")
        ax.set_ylabel("Occurences")
        ax.set_title(f"{self.model} Reference {self.reference}")
        ax.legend()
        ax.grid(True)


        plt.savefig(
            f"{self.dir_plot}HIST_MATCHING_lisse_{self.model}_{self.year}.jpeg",
            bbox_inches="tight")
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
