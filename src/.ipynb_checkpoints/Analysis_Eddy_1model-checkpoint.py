#!/usr/bin/env python
# coding: utf-8


########################################################################################################################

### 	ANALYSIS ONE MODEL WITH DETECTION AND TRACKING AND MATCHING WITH A REFERENCE 				    ###

########################################################################################################################


### IMPORT ###
# environment with py-eddy-tracker
# Mason et al.

import glob
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

from plots import Plots


def reverse_index(index, nb):
    m = np.ones(nb, dtype="bool")
    m[index] = False
    return np.where(m)[0]


def analysis_eddies():

    # Read in config file name
    parser = argparse.ArgumentParser(description="Script that reads in a config file")
    # default drifting time 90 days
    # model output NEMO Mercator PSY4V3R1_1dAV
    # advection in 2D at the surface'''))
    # add command line option
    parser.add_argument(
        "CONFIG_FILE", help="specify name of configuration file", type=str
    )
    args = parser.parse_args()
    CONFIG_FILE = args.CONFIG_FILE
    print("read in:", CONFIG_FILE)

    # Read in user input arguments
    config_object = ConfigParser()
    config_object.read(CONFIG_FILE)

    ### IN CONFIG FILE : 2 sections : GENERAL INFO and PLOT INFO

    general_info = config_object["GENERAL_INFO"]
    MODEL = str(general_info["MODEL"])
    REFERENCE = str(general_info["REFERENCE"])
    PATH_DETECT_FILES = str(general_info["PATH_DETECT_FILES"])
    PATH_TRAJ_FILES = str(general_info["PATH_TRAJ_FILES"])
    PATH_REF_TRACK = str(general_info["PATH_REF_TRACK"])

    plot_info = config_object["PLOT_INFO"]
    PATH_ADT_MODEL = str(plot_info["PATH_ADT_MODEL"])
    var_adt = str(plot_info["var_adt"])
    GRID_SIZE=int(general_info["GRID_SIZE"])

    ##ONE DAY
    AC_DETECTION = PATH_DETECT_FILES + "Anticyclonic_" + MODEL + "_20230101.nc"
    CC_DETECTION = PATH_DETECT_FILES + "Cyclonic_" + MODEL + "_20230101.nc"

    ########################################################################################################################

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
    for date in datesb:
        index = int(date - dates[0])
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

        reference_id_junk, model_id_junk = reverse_index(
            reference_id, len(reference_ac)
        ), reverse_index(model_id, len(model_ac))
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
        reference_id_junk, model_id_junk = reverse_index(
            reference_id, len(reference_cc)
        ), reverse_index(model_id, len(model_cc))
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

    print("GENREAL DETECTION ADN TRACKING INFO")
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
    # 						PLOTS							       #
    ################################################################################################################

    plots = Plots(config_object, True)

    ### PLOT ONE DAY DETECTION WITH ADT ###

    # Make sure the filtering parameters are the same as in the detection script

    h = RegularGridDataset(PATH_ADT_MODEL, "longitude", "latitude")
    h.bessel_high_filter(var_adt, 500, order=1)

    a = EddiesObservations.load_file(AC_DETECTION)
    c = EddiesObservations.load_file(CC_DETECTION)

    plots.plot_one_day_adt(h, var_adt, a, c)

    ### PLOT ALL TRACKS FOR THE PERIOD ###
    plots.plot_all_tracks_period(at, ct)

    ### PLOT HEATMAP FOR MODEL 
    plots.plot_heatmap()

    plots.plot_heatmap_radius()
    
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

    ### POD & FAR BY AMPLITUDE (CM) ###
    plots.plot_pod_far_amplitude(POD_AR, FAR_AR)

    ### POD & FAR BY TIME ###
    plots.plot_pod_far_time(AR_POD, AR_FAR)

    ### PERFORMANCE DIAGRAM ###
    plots.perf_diag(SR, AR_POD)


if __name__ == "__main__":
    analysis_eddies()
