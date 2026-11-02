#!/usr/bin/env python3
# coding: utf-8
########################################################################################################################
#                                              EDDY INTERCOMPARISON                                                    #
########################################################################################################################
#
#   Description : 	             INTERCOMPARISON MODELS (OR REGIONS FOR A SAME MODEL) OF MATCHING WITH A REFERENCE OBS
#                                (2 models or regions at least)
#
#   Authors     :                S. Cailleau
#   Version     :                11/2025
#
########################################################################################################################

# ---------
#  IMPORT
# ---------
#
# environment with py-eddy-tracker
# Mason et al.
import glob
import sys
import os
import shutil
from configparser import ConfigParser
import argparse
from datetime import datetime

from netCDF4 import Dataset
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

from py_eddy_tracker import data
from py_eddy_tracker.observations.observation import EddiesObservations
from py_eddy_tracker.observations.tracking import TrackEddiesObservations
from py_eddy_tracker.appli.grid import eddy_id
from py_eddy_tracker.dataset.grid import RegularGridDataset
from py_eddy_tracker.generic import distance_grid
from py_eddy_tracker.gui import GUI_AXES

sys.path.append("./")
import eddy_compa.my_functions as fn
#
# ---------------
# USER PARAMETERS
# ---------------
#
from eddy_diags.namelist_diags import *
#
def main():
    #
    #   - Main parameters in arguments
    #     
    # Create the parser
    parser = argparse.ArgumentParser()
    # Add arguments
    parser.add_argument('--models', nargs="+", help='String List of Analysis & Forecasting system acronymes (eg.: GLO, IBI, MED, BAL, BLK, NWS, ORCA36) => up to 5-model list, but only one area is required')
    parser.add_argument('--obs', type=str, required=True, help='Altimetric satellite data acronyme (eg.: AVISO, AVISO_EU)')
    parser.add_argument('--areas', nargs="+", help='String List of area names you defined in your data folder => up to 5-area list, but only one model is required')
    parser.add_argument('--folder', type=str, required=True, help='Downloaded file directory')
    # Parse the argument
    args = parser.parse_args()
    #
    model_acro_list = args.models
    obs_acro = args.obs
    area_list = args.areas
    data_dir = args.folder
    print ("Analysis & Forecasting system list = ",model_acro_list)
    print ("Altimetric satellite data = ",obs_acro)
    print ("Area names list = ",area_list)
    print ("Downloaded file directory = ",data_dir)
    #
    # ----------------------------------
    #
    REFERENCE = str(obs_acro)

    PIX_COLOR = [ 'red', 'blue', 'green', 'grey', 'k' ]
    col=0
    for MODEL in model_acro_list:
       print("Model = ",MODEL)
       for AREA in area_list:
          # Data directories
          PATH_DETECT_FILES = data_dir+"/"+MODEL+"/"+AREA+"/DETECT/"
          PATH_DETECT_FILES_REF = data_dir+"/"+REFERENCE+"/"+AREA+"/DETECT/"
          PATH_TRAJ_FILES = data_dir+"/"+MODEL+"/"+AREA+"/TRACK/"
          PATH_REF_TRACK = data_dir+"/"+REFERENCE+"/"+AREA+"/TRACK/"
          #path for output stats
          PATH_STATS = data_dir+"/"+MODEL+"/"+AREA+"/STATS/"
          PATH_PLOT = data_dir+"/"+MODEL+"/"+AREA+"/PLOTS/"
          if not os.path.exists(PATH_STATS):
              os.mkdir(PATH_STATS)
          if not os.path.exists(PATH_PLOT):
              os.mkdir(PATH_PLOT)
          #
          # Cleanning 
          # (sometimes ".ipynb_checkpoints" file is automatically generated in detect and track directories & then the diags run is out ...)
          if os.path.exists(PATH_DETECT_FILES+".ipynb_checkpoints"):
             shutil.rmtree(PATH_DETECT_FILES+".ipynb_checkpoints")
          if os.path.exists(PATH_DETECT_FILES_REF+".ipynb_checkpoints"):    
             shutil.rmtree(PATH_DETECT_FILES_REF+".ipynb_checkpoints")
          if os.path.exists(PATH_TRAJ_FILES+".ipynb_checkpoints"):    
             shutil.rmtree(PATH_TRAJ_FILES+".ipynb_checkpoints")
          if os.path.exists(PATH_REF_TRACK+".ipynb_checkpoints"):    
             shutil.rmtree(PATH_REF_TRACK+".ipynb_checkpoints")
          #
          ########################################################################################################################
          #
          ### NUMBER OF DETECTION ###
          NB_AC = []
          NB_CC = []
          NB_EDDIES = []

          input_file_ac = sorted(glob.glob(PATH_DETECT_FILES + "Anticyclonic" + "*.nc"))
          for i, file in enumerate(input_file_ac[:]):
              a = EddiesObservations.load_file(file)
              NB_AC.append(len(a))

          input_file_cc = sorted(glob.glob(PATH_DETECT_FILES + "Cyclonic" + "*.nc"))
          for i, file in enumerate(input_file_cc[:]):
              c = EddiesObservations.load_file(file)
              NB_CC.append(len(c))

          for i in range(len(NB_AC)):
              NB_EDDIES.append(NB_AC[i] + NB_CC[i])

          ### LOAD TRACKS ###
          ## at = anticyclonic tracked
          ## ct = cyclonic tracked
          at = TrackEddiesObservations.load_file(PATH_TRAJ_FILES + "Anticyclonic.nc")
          ct = TrackEddiesObservations.load_file(PATH_TRAJ_FILES + "Cyclonic.nc")
          at.position_filter(median_half_window=1, loess_half_window=5)
          ct.position_filter(median_half_window=1, loess_half_window=5)
          eddies = at.merge(ct)

          ### LOAD TRACKS TOO SHORT ###
          ## ats = anticyclonic tracks too short : tracks lifetime < TRACK_DURATION_MIN in tracking file
          ## cts = cyclonic tracks too short

          ats = TrackEddiesObservations.load_file(
           PATH_TRAJ_FILES + "Anticyclonic_track_too_short.nc"
          )
          cts = TrackEddiesObservations.load_file(
              PATH_TRAJ_FILES + "Cyclonic_track_too_short.nc"
          )
          eddies_ts = ats.merge(cts)

          ### LOAD UNTRACKED EDDIES ###
          ## ata = anticyclonic untracked
          ## cta = cycclonic untracked

          ata = TrackEddiesObservations.load_file(
              PATH_TRAJ_FILES + "Anticyclonic_untracked.nc"
          )
          cta = TrackEddiesObservations.load_file(PATH_TRAJ_FILES + "Cyclonic_untracked.nc")
          eddies_a = ata.merge(cta)

          ########################################################################################################################
          #### MATCHING WITH REFERENCE ####
          ########################################################################################################################

          ###  Data REFERENCE ##

          a_ref = TrackEddiesObservations.load_file(PATH_REF_TRACK + "Anticyclonic.nc")
          c_ref = TrackEddiesObservations.load_file(PATH_REF_TRACK + "Cyclonic.nc")
          a_ref.position_filter(median_half_window=1, loess_half_window=5)
          c_ref.position_filter(median_half_window=1, loess_half_window=5)

          dates = np.arange(a_ref.obs["time"].min(), a_ref.obs["time"].max())
          datesb = np.arange(at.obs["time"].min(), at.obs["time"].max())

          # Hits, Misses, False Alarm
          ## GLO12
          AR_hits = np.ma.masked_array(np.zeros((len(datesb))), mask=True)
          AR_misses = np.ma.masked_array(np.zeros((len(datesb))), mask=True)
          AR_falarm = np.ma.masked_array(np.zeros((len(datesb))), mask=True)
          Hits = []
          Misses = []
          Falarms = []
          ### Radius
          radius_AR_hits = []
          radius_AR_falarm = []
          radius_AR_misses = []

          ### Amplitude
          amplitude_AR_hits = []
          amplitude_AR_falarm = []
          amplitude_AR_misses = []

          i = 0
          for ind_date, date in enumerate(datesb):
            if i < 3:
              print(f"{ind_date} {date}")
              index = int(date - dates[0])
              # Extract by date
              ## Anticyclonic
              reference_ac = a_ref.extract_with_period((date, date))
              model_ac = at.extract_with_period((date, date))

              ## Cyclonic
              reference_cc = c_ref.extract_with_period((date, date))
              model_cc = ct.extract_with_period((date, date))
              # Fill arrays
              ### Anticyclonic
              reference_id, model_id, cost = reference_ac.tracking(model_ac)
              Hits.append(len(reference_id))

              reference_id_junk, model_id_junk = fn.reverse_index(
                  reference_id, len(reference_ac)
              ), fn.reverse_index(model_id, len(model_ac))
              Misses.append(len(reference_id_junk))
              Falarms.append(len(model_id_junk))
              #### Hits, Misses, False Alarm
              AR_hits[index] = len(reference_id)
              AR_misses[index] = len(reference_id_junk)
              AR_falarm[index] = len(model_id_junk)

              #### Radius & Amplitudes of Hits, Misses, & False Alarm
              ##### Subset
              reference_ac_junk = reference_ac.index(reference_id_junk)
              model_ac_junk = model_ac.index(model_id_junk)
              model_ac = model_ac.index(model_id)

              amplitude_AR_hits = np.append(
                  amplitude_AR_hits, model_ac.obs["amplitude"] * 100
              )
              amplitude_AR_misses = np.append(
                  amplitude_AR_misses, reference_ac_junk.obs["amplitude"] * 100
              )
              amplitude_AR_falarm = np.append(
                  amplitude_AR_falarm, model_ac_junk.obs["amplitude"] * 100
              )

              ### Cyclonic
              reference_id, model_id, cost = reference_cc.tracking(model_cc)
              reference_id_junk, model_id_junk = fn.reverse_index(
                  reference_id, len(reference_cc)
              ), fn.reverse_index(model_id, len(model_cc))
              Hits[i] += len(reference_id)
              Misses[i] += len(reference_id_junk)
              Falarms[i] += len(model_id_junk)
              AR_hits[index] += len(reference_id)
              AR_misses[index] += len(reference_id_junk)
              AR_falarm[index] += len(model_id_junk)

              reference_cc_junk = reference_cc.index(reference_id_junk)
              model_cc_junk = model_cc.index(model_id_junk)
              model_cc = model_cc.index(model_id)

              radius_AR_hits = np.append(radius_AR_hits, model_cc.obs["radius_e"] / 1000)
              radius_AR_misses = np.append(
                  radius_AR_misses, reference_cc_junk.obs["radius_e"] / 1000
              )
              radius_AR_falarm = np.append(
                  radius_AR_falarm, model_cc_junk.obs["radius_e"] / 1000
              )

              amplitude_AR_hits = np.append(
                  amplitude_AR_hits, model_cc.obs["amplitude"] * 100
              )
              amplitude_AR_misses = np.append(
                  amplitude_AR_misses, reference_cc_junk.obs["amplitude"] * 100
              )
              amplitude_AR_falarm = np.append(
                  amplitude_AR_falarm, model_cc_junk.obs["amplitude"] * 100
              )

              i += 1
              print("Date OK")
          bins = np.arange(0, 400, 1)
          hist_hits, bins_hits = np.histogram(amplitude_AR_hits, bins=bins)
          hist_misses, bins_misses = np.histogram(amplitude_AR_misses, bins=bins)
          hist_falarm, bins_falarm = np.histogram(amplitude_AR_falarm, bins=bins)
          POD_AR = hist_hits / (hist_hits + hist_misses)
          FAR_AR = hist_falarm / (hist_hits + hist_falarm)

          ### SCORES ###
          # False Alarm Ratio
          AR_FAR = AR_falarm / (AR_hits + AR_falarm)

          # Probability Of Detection
          AR_POD = AR_hits / (AR_hits + AR_misses)

          PRECISION = AR_hits / (AR_hits + AR_falarm)
          F_SCORE = 2 * ((AR_POD * PRECISION) / (AR_POD + PRECISION))
          SR = 1 - AR_FAR
          bias = AR_POD / (1 - AR_FAR)
          CSI = 1 / ((1 / (1 - AR_FAR)) + (1 / AR_POD) - 1)

          ################################################################################################################
          # 						                             PLOTS		                    					       #
          ################################################################################################################
 
          ### PERFORMANCE DIAGRAM ###

          if col == 0:   # To be done only for the 1st iteration
             fig, ax = plt.subplots(figsize=(10, 10))

          ax.scatter(np.mean(SR), np.mean(AR_POD), color=PIX_COLOR[col], s=200, label=MODEL, zorder=3)
          ax.legend()

          col+=1 # end of double loop MODEL/AREA
        
    CSI = np.arange(0.1, 1, 0.1)
    xvals = [0.57, 0.62, 0.77, 0.79, 0.85, 0.9, 0.95, 0.935, 0.96]
    labels = ["0.3", "0.5", "0.8", "1", "1.3", "1.5", "2", "3", "5", "10"]
    for c in CSI:
       i = np.arange(0, 1.1, 0.01)
       y = (c * i) / (c * i - c + i)
       indices = np.where(y <= 0.0)
       y = np.delete(y, indices)
       i = np.delete(i, indices)
       ax.plot(i, y, color="k", linewidth=1.8, label=str(np.round(c, 2)), zorder=2)

    labelLines(ax.get_lines(), xvals=xvals, fontsize=15)

    x = [ 1.01, 1.01, 1.01, 1.01, 0.76,0.65,0.5,0.327,0.2,0.09]
    y_offsets = [0.295, 0.495, 0.795, 1, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01]
    pente = np.arange(0, 1.1, 0.1)
    for i, label in enumerate(labels):
        ax.plot(pente, pente * float(label), linestyle="--", color='k', linewidth=1, zorder=2)
        ax.text(x[i], y_offsets[i], label, size=10)

    ax.set_title("Performance Diagram ", y=1.08)        
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
           f"{PATH_PLOT}PERFORMANCE_DIAG.jpeg",
           bbox_inches="tight",
           dpi=500,
        )

if __name__ == "__main__":
    main()
