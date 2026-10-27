#!/usr/bin/env python3
# coding: utf-8
########################################################################################################################
#                                              EDDY ANALYSIS                                                           #
########################################################################################################################
#
#   Description : 	             ANALYSIS ONE MODEL WITH DETECTION AND TRACKING AND MATCHING WITH A REFERENCE OBS
#
#   Authors     :                S. Cailleau, F. Dubost, C. Reignier
#   Version     :                05/2025
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

from py_eddy_tracker import data
from py_eddy_tracker.observations.observation import EddiesObservations
from py_eddy_tracker.observations.tracking import TrackEddiesObservations
from py_eddy_tracker.appli.grid import eddy_id
from py_eddy_tracker.dataset.grid import RegularGridDataset
from py_eddy_tracker.generic import distance_grid
from py_eddy_tracker.gui import GUI_AXES

sys.path.append("./")
from eddy_diags.my_classes import Plots
import eddy_diags.my_functions as fn
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
    if (len(sys.argv)==9):
       # Considered period (in arguments)
       date_start = str(sys.argv[1])
       xmin = float(sys.argv[2])
       xmax = float(sys.argv[3])
       ymin = float(sys.argv[4])
       ymax = float(sys.argv[5]) 
       model_acro = str(sys.argv[6])
       obs_acro = str(sys.argv[7])
       data_dir = str(sys.argv[8])
       print ("Date start = ",date_start)
       print ("Longitude min = ",xmin)
       print ("Longitude max = ",xmax)
       print ("Latitude min = ",ymin)
       print ("Latitude max = ",ymax)
       print ("Analysis & Forecasting system = ",model_acro)
       print ("Altimetric satellite data = ",obs_acro)
       print ("Downloaded file directory = ",data_dir)
    else:
       print ("!!! ERROR: 8 arguments to be chosen !!!")
       print ("Argument 1 = Date start (yyyy-mm-dd)")
       print ("Argument 2 = Longitude min (-180/180° longitude convention)")
       print ("Argument 3 = Longitude max (-180/180° longitude convention)")
       print ("Argument 4 = Latitude min (-90/90° latitude convention)")
       print ("Argument 5 = Latitude max (-90/90° latitude convention)")
       print ("Argument 6 = Analysis & Forecasting system (GLO, IBI)")
       print ("Argument 7 = Altimetric satellite data (AVISO, AVISO_EU)")
       print ("Argument 8 = Downloaded file directory")
       sys.exit()
    #
    # ----------------------------------
    #
    DATE_START = date_start
    YEAR = DATE_START[0:4]
    LON_MIN = xmin
    LON_MAX = xmax
    LAT_MIN = ymin
    LAT_MAX = ymax
    MODEL = str(model_acro)
    REFERENCE = str(obs_acro)
    # Data directories
    PATH_DETECT_FILES = data_dir+"/"+MODEL+"/DETECT/"
    PATH_DETECT_FILES_REF = data_dir+"/"+REFERENCE+"/DETECT/"
    PATH_TRAJ_FILES = data_dir+"/"+MODEL+"/TRACK/"
    PATH_REF_TRACK = data_dir+"/"+REFERENCE+"/TRACK/"
    #path for output stats
    PATH_STATS = data_dir+"/"+MODEL+"/STATS/"
    PATH_PLOT = data_dir+"/"+MODEL+"/PLOTS/"
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
    ##ONE DAY
    d_start = date_start[0:4]+date_start[5:7]+date_start[8:10]
    # PATH_ADT_MODEL = data_dir+"/"+MODEL+"/"+MODEL+"_"+d_start+".nc"
    AC_DETECTION = PATH_DETECT_FILES + "Anticyclonic_"+MODEL+"_"+d_start+".nc"
    CC_DETECTION = PATH_DETECT_FILES + "Cyclonic_"+MODEL+"_"+d_start+".nc"
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

    datesb = np.arange(at.obs["time"].min(), at.obs["time"].max() + 1)
    # Compare only days covered by both model and reference observations.
    reference_days = set(np.arange(a_ref.obs["time"].min(), a_ref.obs["time"].max() + 1))

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

    for ind_date, date in enumerate(datesb):
        if date not in reference_days:
            continue
        print(f"{ind_date} {date}")
        index = ind_date
        # Extract by date
        ## Anticyclonic
        reference_ac = a_ref.extract_with_period((date, date))
        model_ac = at.extract_with_period((date, date))

        ## Cyclonic
        reference_cc = c_ref.extract_with_period((date, date))
        model_cc = ct.extract_with_period((date, date))
        # Fill arrays
        ## GLO12
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

        radius_AR_hits = np.append(radius_AR_hits, model_ac.obs["radius_e"] / 1000)
        radius_AR_misses = np.append(radius_AR_misses, reference_ac_junk.obs["radius_e"] / 1000)
        radius_AR_falarm = np.append(radius_AR_falarm, model_ac_junk.obs["radius_e"] / 1000)

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
        Hits[-1] += len(reference_id)
        Misses[-1] += len(reference_id_junk)
        Falarms[-1] += len(model_id_junk)
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

    # Open an output diag file in write mode
    output_file = PATH_STATS+"eddy_tracking_summary.txt"
    #with open(f"eddy_tracking_summary.txt", "w") as file:
    with open(output_file, "w") as file:
        
        # General detection and tracking information
        file.write("GENERAL DETECTION AND TRACKING INFO\n")
        file.write("AC stands for AntiCyclonic & CC for CyClonic\n")
        file.write("---------------------------------------------------------\n\n")
        
        file.write("The following information applies to the chosen domain\n")
        
        # AC eddies information
        file.write(f"Number of AC eddies in the period = {sum(NB_AC)}\n")
        file.write(f"Minimum number of AC eddies detected in one day = {min(NB_AC)}\n")
        file.write(f"Maximum number of AC eddies detected in one day = {max(NB_AC)}\n")
        file.write(f"So on average {round(np.mean(NB_AC), 0)} AC eddies per day\n")
        file.write("---------------------------------------------------------\n\n")
        
        # CC eddies information
        file.write(f"Number of CC eddies in the period = {sum(NB_CC)}\n")
        file.write(f"Minimum number of CC eddies detected in one day = {min(NB_CC)}\n")
        file.write(f"Maximum number of CC eddies detected in one day = {max(NB_CC)}\n")
        file.write(f"So on average {round(np.mean(NB_CC), 0)} CC eddies per day\n")
        file.write("---------------------------------------------------------\n\n")
        
        # All eddies information
        file.write(f"Number of eddies in the period = {sum(NB_EDDIES)}\n")
        file.write(f"Minimum number of eddies detected in one day = {min(NB_EDDIES)}\n")
        file.write(f"Maximum number of eddies detected in one day = {max(NB_EDDIES)}\n")
        file.write(f"So on average {round(np.mean(NB_EDDIES))} eddies per day\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Track information
        file.write(f"Number of AC tracks = {at.nb_tracks}\n")
        file.write(f"Number of CC tracks = {ct.nb_tracks}\n")
        file.write(f"Number of tracks = {at.nb_tracks + ct.nb_tracks}\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Average track duration
        file.write(f"Average AC track duration = {round(np.mean(at.nb_obs_by_track))} jours\n")
        file.write(f"Average CC track duration = {round(np.mean(ct.nb_obs_by_track))} jours\n")
        file.write(f"Average track duration = {round(np.mean(eddies.nb_obs_by_track))} jours\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean amplitude
        file.write(f"Mean AC amplitude = {round(np.mean(at.amplitude * 100), 2)} cm\n")
        file.write(f"Mean CC amplitude = {round(np.mean(ct.amplitude * 100), 2)} cm\n")
        file.write(f"Mean eddy amplitude = {round(np.mean(eddies.amplitude * 100), 2)} cm\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean radius
        file.write(f"Mean AC radius = {round(np.mean(at.effective_radius / 1000), 2)} km\n")
        file.write(f"Mean CC radius = {round(np.mean(ct.effective_radius / 1000), 2)} km\n")
        file.write(f"Mean eddy radius = {round(np.mean(eddies.effective_radius / 1000), 2)} km\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean surface area
        file.write(f"Mean surface occupied by AC eddies = {round(np.mean(at.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write(f"Mean surface occupied by CC eddies = {round(np.mean(ct.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write(f"Mean surface occupied by eddies = {round(np.mean(eddies.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Tracks too short
        file.write(f"Number of AC tracks too short = {ats.nb_tracks}\n")
        file.write(f"Number of CC tracks too short = {cts.nb_tracks}\n")
        file.write(f"Number of tracks too short = {ats.nb_tracks + cts.nb_tracks}\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Average duration of tracks too short
        file.write(f"Average AC track too short duration = {round(np.mean(ats.nb_obs_by_track))} jours\n")
        file.write(f"Average CC track too short duration = {round(np.mean(cts.nb_obs_by_track))} jours\n")
        file.write(f"Average track too short duration = {round(np.mean(eddies_ts.nb_obs_by_track))} jours\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean amplitude of tracks too short
        file.write(f"Mean AC amplitude track too short = {round(np.mean(ats.amplitude * 100), 2)} cm\n")
        file.write(f"Mean CC amplitude track too short = {round(np.mean(cts.amplitude * 100), 2)} cm\n")
        file.write(f"Mean amplitude track too short = {round(np.mean(eddies_ts.amplitude * 100), 2)} cm\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean radius of tracks too short
        file.write(f"Mean AC radius track too short = {round(np.mean(ats.effective_radius / 1000), 2)} km\n")
        file.write(f"Mean CC radius track too short = {round(np.mean(cts.effective_radius / 1000), 2)} km\n")
        file.write(f"Mean radius track too short = {round(np.mean(eddies_ts.effective_radius / 1000), 2)} km\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean surface area of tracks too short
        file.write(f"Mean surface occupied by AC eddies from tracks too short = {round(np.mean(ats.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write(f"Mean surface occupied by CC eddies from tracks too short = {round(np.mean(cts.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write(f"Mean surface occupied by eddies from tracks too short = {round(np.mean(eddies_ts.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Untracked eddies
        file.write(f"Number of untracked AC eddies = {len(ata)}\n")
        file.write(f"Number of untracked CC eddies = {len(cta)}\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean amplitude of untracked eddies
        file.write(f"Mean amplitude of untracked AC eddies = {round(np.mean(ata.amplitude * 100), 2)} cm\n")
        file.write(f"Mean amplitude of untracked CC eddies = {round(np.mean(cta.amplitude * 100), 2)} cm\n")
        file.write(f"Mean amplitude of untracked eddies = {round(np.mean(eddies_a.amplitude * 100), 2)} cm\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean radius of untracked eddies
        file.write(f"Mean radius of untracked AC eddies = {round(np.mean(ata.effective_radius / 1000), 2)} km\n")
        file.write(f"Mean radius of untracked CC eddies = {round(np.mean(cta.effective_radius / 1000), 2)} km\n")
        file.write(f"Mean radius of untracked eddies = {round(np.mean(eddies_a.effective_radius / 1000), 2)} km\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Mean surface area of untracked eddies
        file.write(f"Mean surface occupied by untracked AC eddies = {round(np.mean(ata.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write(f"Mean surface occupied by untracked CC eddies = {round(np.mean(cta.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write(f"Mean surface occupied by untracked eddies = {round(np.mean(eddies_a.effective_area / (1000 * 1000)), 2)} km^2\n")
        file.write("---------------------------------------------------------\n\n")
        
        # Matching results
        file.write("MATCHING RESULTS\n")
        file.write("---------------------------------------------------------\n")
        file.write(f"Number of hits = {len(amplitude_AR_hits)}\n")
        file.write(f"Number of misses = {len(amplitude_AR_misses)}\n")
        file.write(f"Number of false alarms = {len(amplitude_AR_falarm)}\n")
        file.write("---------------------------------------------------------\n\n")
    
        # Inform the user
        print("Data has been saved to 'eddy_tracking_summary.txt'")

    # Same info than ones saved in eddy_tracking_summary.txt displayed at screen for the user    
    #
    print("GENERAL DETECTION AND TRACKING INFO")
    print("AC stands for AntiCyclonic & CC for CyClonic")
    print("---------------------------------------------------------")

    # Print information for AC eddies
    print("Number of AC eddies in the period =", sum(NB_AC))
    print("Minimum number of AC eddies detected in one day =", min(NB_AC))
    print("Maximum number of AC eddies detected in one day =", max(NB_AC))
    print("So on average {} AC eddies per day".format(round(np.mean(NB_AC), 0)))
    print("---------------------------------------------------------")

    # Print information for CC eddies
    print("Number of CC eddies in the period =", sum(NB_CC))
    print("Minimum number of CC eddies detected in one day =", min(NB_CC))
    print("Maximum number of CC eddies detected in one day =", max(NB_CC))
    print("So on average {} CC eddies per day".format(round(np.mean(NB_CC), 0)))
    print("---------------------------------------------------------")

    # Print information for all eddies
    print("Number of eddies in the period =", sum(NB_EDDIES))
    print("Minimum number of eddies detected in one day =", min(NB_EDDIES))
    print("Maximum number of eddies detected in one day =", max(NB_EDDIES))
    print("So on average {} eddies per day".format(round(np.mean(NB_EDDIES))))
    print("---------------------------------------------------------")

    # Print information for tracks
    print("Number of AC tracks =", at.nb_tracks)
    print("Number of CC tracks =", ct.nb_tracks)
    print("Number of tracks =", at.nb_tracks + ct.nb_tracks)
    print("---------------------------------------------------------")

    # Print information for average track duration
    print("Average AC track duration =", round(np.mean(at.nb_obs_by_track)), "jours")
    print("Average CC track duration =", round(np.mean(ct.nb_obs_by_track)), "jours")
    print("Average track duration =", round(np.mean(eddies.nb_obs_by_track)), "jours")
    print("---------------------------------------------------------")

    # Print information for mean amplitude
    print("Mean AC amplitude =", round(np.mean(at.amplitude * 100), 2), "cm")
    print("Mean AC amplitude =", round(np.mean(ct.amplitude * 100), 2), "cm")
    print("Mean eddy amplitude =", round(np.mean(eddies.amplitude * 100), 2), "cm")
    print("---------------------------------------------------------")

    # Print information for mean radius
    print("Mean AC radius =", round(np.mean(at.effective_radius / 1000), 2), "km")
    print("Mean CC radius =", round(np.mean(ct.effective_radius / 1000), 2), "km")
    print("Mean eddy radius =", round(np.mean(eddies.effective_radius / 1000), 2), "km")
    print("---------------------------------------------------------")

    # Print information for mean surface occupied
    print(
        "Mean surface occupied by AC eddies =",
        round(np.mean(at.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print(
        "Mean surface occupied by CC eddies =",
        round(np.mean(ct.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print(
        "Mean surface occupied by eddies =",
        round(np.mean(eddies.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print("---------------------------------------------------------")

    # Print information for tracks too short
    print("Number of AC tracks too short =", ats.nb_tracks)
    print("Number of CC tracks too short =", cts.nb_tracks)
    print("Number of tracks too short =", ats.nb_tracks + cts.nb_tracks)
    print("---------------------------------------------------------")

    # Print information for average track duration of tracks too short
    print(
        "Average AC track too short duration =",
        round(np.mean((ats.nb_obs_by_track))),
        "jours",
    )
    print(
        "Average CC track too short duration =",
        round(np.mean((cts.nb_obs_by_track))),
        "jours",
    )
    print(
        "Average track too short duration =",
        round(np.mean((eddies_ts.nb_obs_by_track))),
        "jours",
    )
    print("---------------------------------------------------------")

    # Print information for mean amplitude of tracks too short
    print(
        "Mean AC amplitude track too short =",
        round(np.mean(ats.amplitude * 100), 2),
        "cm",
    )
    print(
        "Mean CC amplitude track too short =",
        round(np.mean(cts.amplitude * 100), 2),
        "cm",
    )
    print(
        "Mean amplitude track too short =",
        round(np.mean(eddies_ts.amplitude * 100), 2),
        "cm",
    )
    print("---------------------------------------------------------")

    # Print information for mean radius of tracks too short
    print(
        "Mean AC radius track too short =",
        round(np.mean(ats.effective_radius / 1000), 2),
        "km",
    )
    print(
        "Mean CC radius track too short =",
        round(np.mean(cts.effective_radius / 1000), 2),
        "km",
    )
    print(
        "Mean radius track too short =",
        round(np.mean(eddies_ts.effective_radius / 1000), 2),
        "km",
    )
    print("---------------------------------------------------------")

    # Print information for mean surface occupied by tracks too short
    print(
        "Mean surface occupied by AC eddies from tracks too short =",
        round(np.mean(ats.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print(
        "Mean surface occupied by CC eddies from tracks too short =",
        round(np.mean(cts.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print(
        "Mean surface occupied by eddies from tracks too short =",
        round(np.mean(eddies_ts.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print("---------------------------------------------------------")

    # Print information for untracked eddies
    print("Number of untracked AC eddies =", len(ata))
    print("Number of untracked CC eddies  =", len(cta))
    print("---------------------------------------------------------")

    # Print information for mean amplitude of untracked eddies
    print(
        "Mean amplitude of untracked AC eddies =",
        round(np.mean(ata.amplitude * 100), 2),
        "cm",
    )
    print(
        "Mean amplitude of untracked CC eddies =",
        round(np.mean(cta.amplitude * 100), 2),
        "cm",
    )
    print(
        "Mean amplitude of untracked eddies =",
        round(np.mean(eddies_a.amplitude * 100), 2),
        "cm",
    )
    print("---------------------------------------------------------")

    # Print information for mean radius of untracked eddies
    print(
        "Mean radius of untracked AC eddies =",
        round(np.mean(ata.effective_radius / 1000), 2),
        "km",
    )
    print(
        "Mean radius of untracked CC eddies =",
        round(np.mean(cta.effective_radius / 1000), 2),
        "km",
    )
    print(
        "Mean radius of untracked eddies =",
        round(np.mean(eddies_a.effective_radius / 1000), 2),
        "km",
    )
    print("---------------------------------------------------------")

    # Print information for mean surface occupied by untracked eddies
    print(
        "Mean surface occupied by untracked AC eddies =",
        round(np.mean(ata.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print(
        "Mean surface occupied by untracked CC eddies =",
        round(np.mean(cta.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print(
        "Mean surface occupied by untracked eddies =",
        round(np.mean(eddies_a.effective_area / (1000 * 1000)), 2),
        "km^2",
    )
    print("---------------------------------------------------------")

    # Print matching results
    print("MATCHING RESULTS")
    print("---------------------------------------------------------")
    print("Number of hits =", len(amplitude_AR_hits))
    print("Number of misses =", len(amplitude_AR_misses))
    print("Number of false alarms =", len(amplitude_AR_falarm))
    print("---------------------------------------------------------")

    # Print average number of hits, misses, and false alarms per day
    print("Average number of hits per day =", round(np.mean(Hits)))
    print("Average number of misses per day =", round(np.mean(Misses)))
    print("Average number of false alarms per day =", round(np.mean(Falarms)))
    print("---------------------------------------------------------")

    # Print mean amplitude of hits, misses, and false alarms
    print("Mean hits amplitude =", round(np.mean(amplitude_AR_hits), 2), "cm")
    print("Mean misses amplitude =", round(np.mean(amplitude_AR_misses), 2), "cm")
    print("Mean false alarms amplitude =", round(np.mean(amplitude_AR_falarm), 2), "cm")
    print("---------------------------------------------------------")

    # Print mean radius of hits, misses, and false alarms
    print("Mean hits radius =", round(np.mean(radius_AR_hits), 2), "km")
    print("Mean misses radius =", round(np.mean(radius_AR_misses), 2), "km")
    print("Mean false alarms radius =", round(np.mean(radius_AR_falarm), 2), "km")
    print("---------------------------------------------------------")

    # Print mean probability of detection (POD), false alarm ratio (FAR), success ratio (SR), F-Score, and critical success index (CSI)
    print("The mean probability of detection (POD) is", round(np.mean(AR_POD), 3))
    print(
        "The mean false alarm ratio (FAR) is",
        round(np.mean(AR_FAR), 3),
        "so a success ratio of",
        round(np.mean(SR), 3),
    )
    print("The F_Score is", round(np.mean(F_SCORE), 3))
    print("The critical success index (CSI) is", round(np.mean(CSI), 3))

    ################################################################################################################
    # 						                             PLOTS		                    					       #
    ################################################################################################################

    plots = Plots(DATE_START, MODEL, REFERENCE, YEAR, PATH_DETECT_FILES, PATH_DETECT_FILES_REF, PATH_TRAJ_FILES, PATH_REF_TRACK, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, PATH_PLOT, GRID_SIZE, True)
    
    ### PLOT ONE DAY DETECTION WITH ADT ###

    # Make sure the filtering parameters are the same as in the detection script

    # h = RegularGridDataset(PATH_ADT_MODEL, "longitude", "latitude")
    # h.bessel_high_filter(var_adt, 500, order=1)
    # a = EddiesObservations.load_file(AC_DETECTION)
    # c = EddiesObservations.load_file(CC_DETECTION)

    #plots.plot_one_day_adt(h, var_adt, a, c)
    print("plot_all_tracks_period")
    ### PLOT ALL TRACKS FOR THE PERIOD ###
    plots.plot_all_tracks_period(at, ct)
    ### PLOT HEATMAP FOR MODEL 
    plots.plot_heatmap_model()
    plots.plot_heatmap_ref()
    plots.plot_heatmap_radius_model()
    plots.plot_heatmap_radius_ref()
    plots.plot_heatmap_amplitude_model()
    plots.plot_heatmap_amplitude_ref()
    
    ### NUMBER OF DETECTION BY TIME WITH MEAN ###
    plots.plot_number_detection_time_mean(NB_EDDIES)

    ### 2D HISTOGRAM RADIUS AMPLITUDE ###
    plots.plot_2d_histo(at)

    ### COUNT 
    plots.plot_count_log_amp(at,ct,a_ref,c_ref) 
    plots.plot_count_speed_radius(at,ct,a_ref,c_ref)
    plots.plot_count_lifetime(at,ct,a_ref,c_ref)


    ### HISTOGRAM HITS MISSES & FALSE ALARMS BY RADIUS (KM) ###
    plots.plot_histo_hits_false(radius_AR_hits, radius_AR_misses, radius_AR_falarm)
    plots.plot_histo_lisse(radius_AR_hits, radius_AR_misses, radius_AR_falarm)

    
    ### POD & FAR BY AMPLITUDE (CM) ###
    plots.plot_pod_far_amplitude(POD_AR, FAR_AR)

    ### POD & FAR BY TIME ###
    plots.plot_pod_far_time(AR_POD, AR_FAR)

    ### PERFORMANCE DIAGRAM ###
    plots.perf_diag(SR, AR_POD)


if __name__ == "__main__":
    main()
