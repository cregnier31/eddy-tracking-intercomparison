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



from plots_glo2reg import Plots

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
    DOMAIN = str(general_info["DOMAIN"])
    PATH_DETECT_FILES = str(general_info["PATH_DETECT_FILES"])
    PATH_TRAJ_FILES = str(general_info["PATH_TRAJ_FILES"])
    PATH_REF_TRACK = str(general_info["PATH_REF_TRACK"])
    GRID_SIZE=int(general_info["GRID_SIZE"])
    plot_info = config_object["PLOT_INFO"]
    PATH_ADT_MODEL = str(plot_info["PATH_ADT_MODEL"])
    var_adt = str(plot_info["var_adt"])

    ### LOAD TRACKS ###
    ## at = anticyclonic tracked
    ## ct = cyclonic tracked
    at= TrackEddiesObservations.load_file(PATH_TRAJ_FILES+"Anticyclonic.nc")
    ct=TrackEddiesObservations.load_file(PATH_TRAJ_FILES+"Cyclonic.nc")
    at.position_filter(median_half_window=1, loess_half_window=5)
    ct.position_filter(median_half_window=1, loess_half_window=5)
    eddies=at.merge(ct)
    
    ### LOAD TRACKS TOO SHORT ###
    ## ats = anticyclonic tracks too short : tracks lifetime < TRACK_DURATION_MIN in tracking file
    ## cts = cyclonic tracks too short
    
    ats= TrackEddiesObservations.load_file(PATH_TRAJ_FILES+"Anticyclonic_track_too_short.nc")
    cts=TrackEddiesObservations.load_file(PATH_TRAJ_FILES+"Cyclonic_track_too_short.nc")
    eddies_ts=ats.merge(cts)
    
    ### LOAD UNTRACKED EDDIES ###
    ## ata = anticyclonic untracked 
    ## cta = cycclonic untracked
    
    ata= TrackEddiesObservations.load_file(PATH_TRAJ_FILES+"Anticyclonic_untracked.nc")
    cta=TrackEddiesObservations.load_file(PATH_TRAJ_FILES+"Cyclonic_untracked.nc")
    eddies_a=ata.merge(cta)
    
    
    ### LOAD REFERENCE TRACKS ###
    a_ref= TrackEddiesObservations.load_file(PATH_REF_TRACK+"Anticyclonic.nc")
    c_ref=TrackEddiesObservations.load_file(PATH_REF_TRACK+"Cyclonic.nc")
    a_ref.position_filter(median_half_window=1, loess_half_window=5)
    c_ref.position_filter(median_half_window=1, loess_half_window=5)

    #### DOMAIN DEFINITION ###  
    
    GS = dict(llcrnrlon=-80, llcrnrlat=30, urcrnrlon=-30, urcrnrlat=60)
    IBI= dict(llcrnrlon=-19, llcrnrlat=26, urcrnrlon=5, urcrnrlat=56)
    AG = dict(llcrnrlon=5, llcrnrlat=-45, urcrnrlon=35, urcrnrlat=-25)
    KOE= dict(llcrnrlon=140, llcrnrlat=28, urcrnrlon=170, urcrnrlat=50)
        
    if DOMAIN == 'GS':
        zone_params = GS
    elif DOMAIN == 'IBI':
        zone_params = IBI
    elif DOMAIN == 'AG':
        zone_params = AG 
    elif DOMAIN =='KOE':
        zone_params = KOE
    else:
        raise ValueError("DOMAIN is not defined.")


    ######### DATA EXTRACTION #########
        
    #### ONE DAY DATA ####
    # a_zone = a.extract_with_area(zone_params)
    # c_zone = c.extract_with_area(zone_params)
    
    #### TRACKING DATA ####
    # MODEL #
    at_zone = at.extract_with_area(zone_params, full_path=False)
    ct_zone = ct.extract_with_area(zone_params, full_path=False)
    eddies_zone=at_zone.merge(ct_zone)

    # REFERENCE #
    a_zone_ref = a_ref.extract_with_area(zone_params, full_path=False)
    c_zone_ref = c_ref.extract_with_area(zone_params, full_path=False)
    eddies_ref_zone= a_zone_ref.merge(c_zone_ref)


    ### TRACKS TOO SHORT EXTRACT ON DOMAIN 

    ats_zone= ats.extract_with_area(zone_params, full_path=False)
    cts_zone=cts.extract_with_area(zone_params, full_path=False)
    eddies_ts_zone= eddies_ts.extract_with_area(zone_params, full_path=False)

    ### UNTRACKED EDDIES ### 
    ata_zone=ata.extract_with_area(zone_params, full_path=False)
    cta_zone=cta.extract_with_area(zone_params, full_path=False)
    eddies_a_zone=eddies_a.extract_with_area(zone_params, full_path=False)
    
    
    ## RECTANGLE IN PLOT ## 
    rect_params=zone_params

    ### NUMBER OF DETECTION ###
    NB_AC=[]
    NB_CC=[]
    NB_EDDIES=[]
    
    NB_AC_ZONE=[]
    NB_CC_ZONE=[]
    NB_EDDIES_ZONE=[]
    
    input_file_ac = sorted(glob.glob(PATH_DETECT_FILES +'Anticyclonic'+'*.nc'))
    for i,file in enumerate(input_file_ac[:]):
        a=EddiesObservations.load_file(file)
        NB_AC.append(len(a))
        a_zone = a.extract_with_area(zone_params)
        NB_AC_ZONE.append(len(a_zone))
    
    input_file_cc = sorted(glob.glob(PATH_DETECT_FILES +'Cyclonic'+'*.nc'))
    for i,file in enumerate(input_file_cc[:]):
        c=EddiesObservations.load_file(file)
        NB_CC.append(len(c))
        c_zone = a.extract_with_area(zone_params)
        NB_CC_ZONE.append(len(c_zone))
    
    for i in range(len(NB_AC)):
        NB_EDDIES.append(NB_AC[i]+NB_CC[i])
        NB_EDDIES_ZONE.append(NB_AC_ZONE[i]+NB_CC_ZONE[i])




    ########################################################################################################################
                                                #### MATCHING WITH REFERENCE ####
    ########################################################################################################################

    
    dates = np.arange(a_ref.obs['time'].min(),a_ref.obs['time'].max()) 
    datesb = np.arange(at.obs['time'].min(),at.obs['time'].max()) 
    
    # Hits, Misses, False Alarm
    ## MODEL
    AR_hits   = np.ma.masked_array(np.zeros((len(datesb))),mask=True)
    AR_misses = np.ma.masked_array(np.zeros((len(datesb))),mask=True)
    AR_falarm = np.ma.masked_array(np.zeros((len(datesb))),mask=True)
    Hits=[]
    Misses=[]
    Falarms=[]
    ### Radius
    radius_AR_hits      = []
    radius_AR_falarm     = []
    radius_AR_misses     = []
    ### Amplitude
    amplitude_AR_hits    = []
    amplitude_AR_falarm = []
    amplitude_AR_misses  = []
    
    i=0
    for date in datesb:
        index = int(date - dates[0])
        # Extract by date
        ## Anticyclonic
        reference_ac = a_ref.extract_with_period((date,date))
        model_ac = at.extract_with_period((date,date))
    
        
        ## Cyclonic
        reference_cc = c_ref.extract_with_period((date,date))
        model_cc = ct.extract_with_period((date,date))
        # Fill arrays
        ## GLO12
        ### Anticyclonic
        reference_id, model_id, cost = reference_ac.tracking(model_ac)
        Hits.append(len(reference_id))
        
        reference_id_junk, model_id_junk = reverse_index(reference_id, len(reference_ac)), reverse_index(model_id, len(model_ac))
        Misses.append(len(reference_id_junk))
        Falarms.append(len(model_id_junk))
        #### Hits, Misses, False Alarm
        AR_hits[index]   = len(reference_id)
        AR_misses[index] = len(reference_id_junk)
        AR_falarm[index] = len(model_id_junk)
    
        #### Radius & Amplitudes of Hits, Misses, & False Alarm
        ##### Subset
        reference_ac_junk = reference_ac.index(reference_id_junk)
        model_ac_junk = model_ac.index(model_id_junk)
        model_ac = model_ac.index(model_id)
        for item in model_ac.obs['radius_e']/1000:
            radius_AR_hits.append(item)
        for item in reference_ac_junk.obs['radius_e']/1000:
            radius_AR_misses.append(item)
        for item in model_ac_junk.obs['radius_e']/1000:
            radius_AR_falarm.append(item)    
            
        for item in model_ac.obs['amplitude']*100:
            amplitude_AR_hits.append(item)
        for item in reference_ac_junk.obs['amplitude']*100:
            amplitude_AR_misses.append(item)
        for item in model_ac_junk.obs['amplitude']*100:
            amplitude_AR_falarm.append(item) 
        
        ### Cyclonic
        reference_id, model_id, cost = reference_cc.tracking(model_cc)
        reference_id_junk, model_id_junk = reverse_index(reference_id, len(reference_cc)), reverse_index(model_id, len(model_cc))      
        Hits[i]+=len(reference_id)
        Misses[i]+=len(reference_id_junk)
        Falarms[i]+=len(model_id_junk)
        AR_hits[index]   += len(reference_id)
        AR_misses[index] += len(reference_id_junk)
        AR_falarm[index] += len(model_id_junk)
        
        reference_cc_junk = reference_cc.index(reference_id_junk)
        model_cc_junk = model_cc.index(model_id_junk)
        model_cc = model_cc.index(model_id)
        for item in model_cc.obs['radius_e']/1000:
            radius_AR_hits.append(item)
        for item in reference_cc_junk.obs['radius_e']/1000:
            radius_AR_misses.append(item)
        for item in model_cc_junk.obs['radius_e']/1000:
            radius_AR_falarm.append(item)    
            
        for item in model_cc.obs['amplitude']*100:
            amplitude_AR_hits.append(item)
        for item in reference_cc_junk.obs['amplitude']*100:
            amplitude_AR_misses.append(item)
        for item in model_cc_junk.obs['amplitude']*100:
            amplitude_AR_falarm.append(item)
        i+=1
    
        
    bins = np.arange(0,400,1)
    hist_hits,   bins_hits    = np.histogram(amplitude_AR_hits ,bins=bins)
    hist_misses , bins_misses  = np.histogram(amplitude_AR_misses ,bins=bins)
    hist_falarm  ,bins_falarm  = np.histogram(amplitude_AR_falarm,bins=bins)
    POD_AR  = hist_hits    / (hist_hits  + hist_misses )
    FAR_AR  = hist_falarm  / (hist_hits + hist_falarm )
    
    ### SCORES ###
    # False Alarm Ratio
    AR_FAR = AR_falarm / (AR_hits + AR_falarm)
    
    # Probability Of Detection
    AR_POD = AR_hits / (AR_hits + AR_misses)
    
    PRECISION= AR_hits / (AR_hits + AR_falarm)
    F_SCORE= 2 * ( (AR_POD * PRECISION) / ( AR_POD + PRECISION) ) 
    SR=1-AR_FAR
    bias=AR_POD/(1-AR_FAR)
    CSI=1/((1/(1-AR_FAR))+(1/AR_POD)-1)

    ######## STOCK VALUES FOR GLOBAL ########
    
    SR_GLO=SR
    AR_POD_GLO=AR_POD
    AR_FAR_GLO=AR_FAR

    POD_AR_GLO=POD_AR
    FAR_AR_GLO=FAR_AR

    CSI_GLO=CSI
    PRECISION_GLO=PRECISION
    F_SCORE_GLO=F_SCORE
    bias_glo=bias
    
    radius_AR_hits_glo= radius_AR_hits
    radius_AR_falarm_glo=radius_AR_falarm
    radius_AR_misses_glo=radius_AR_misses

    amplitude_AR_hits_glo= amplitude_AR_hits
    amplitude_AR_falarm_glo=amplitude_AR_falarm
    amplitude_AR_misses_glo=amplitude_AR_misses
    
    ############################################################
    ########### MATCHING WITH JUST DOMAIN ######################
    ############################################################

    
    # Hits, Misses, False Alarm
    ## MODEL
    AR_hits   = np.ma.masked_array(np.zeros((len(datesb))),mask=True)
    AR_misses = np.ma.masked_array(np.zeros((len(datesb))),mask=True)
    AR_falarm = np.ma.masked_array(np.zeros((len(datesb))),mask=True)
    Hits=[]
    Misses=[]
    Falarms=[]
    ### Radius
    radius_AR_hits      = []
    radius_AR_falarm     = []
    radius_AR_misses     = []
    ### Amplitude
    amplitude_AR_hits    = []
    amplitude_AR_falarm = []
    amplitude_AR_misses  = []
    
    i=0
    for date in datesb:
        index = int(date - dates[0])
        # Extract by date
        ## Anticyclonic
        reference_ac = a_zone_ref.extract_with_period((date,date))
        model_ac = at_zone.extract_with_period((date,date))
    
        
        ## Cyclonic
        reference_cc = c_zone_ref.extract_with_period((date,date))
        model_cc = ct_zone.extract_with_period((date,date))
        # Fill arrays
        ## GLO12
        ### Anticyclonic
        reference_id, model_id, cost = reference_ac.tracking(model_ac)
        Hits.append(len(reference_id))
        
        reference_id_junk, model_id_junk = reverse_index(reference_id, len(reference_ac)), reverse_index(model_id, len(model_ac))
        Misses.append(len(reference_id_junk))
        Falarms.append(len(model_id_junk))
        #### Hits, Misses, False Alarm
        AR_hits[index]   = len(reference_id)
        AR_misses[index] = len(reference_id_junk)
        AR_falarm[index] = len(model_id_junk)
    
        #### Radius & Amplitudes of Hits, Misses, & False Alarm
        ##### Subset
        reference_ac_junk = reference_ac.index(reference_id_junk)
        model_ac_junk = model_ac.index(model_id_junk)
        model_ac = model_ac.index(model_id)
        for item in model_ac.obs['radius_e']/1000:
            radius_AR_hits.append(item)
        for item in reference_ac_junk.obs['radius_e']/1000:
            radius_AR_misses.append(item)
        for item in model_ac_junk.obs['radius_e']/1000:
            radius_AR_falarm.append(item)    
            
        for item in model_ac.obs['amplitude']*100:
            amplitude_AR_hits.append(item)
        for item in reference_ac_junk.obs['amplitude']*100:
            amplitude_AR_misses.append(item)
        for item in model_ac_junk.obs['amplitude']*100:
            amplitude_AR_falarm.append(item) 
        
        ### Cyclonic
        reference_id, model_id, cost = reference_cc.tracking(model_cc)
        reference_id_junk, model_id_junk = reverse_index(reference_id, len(reference_cc)), reverse_index(model_id, len(model_cc))      
        Hits[i]+=len(reference_id)
        Misses[i]+=len(reference_id_junk)
        Falarms[i]+=len(model_id_junk)
        AR_hits[index]   += len(reference_id)
        AR_misses[index] += len(reference_id_junk)
        AR_falarm[index] += len(model_id_junk)
        
        reference_cc_junk = reference_cc.index(reference_id_junk)
        model_cc_junk = model_cc.index(model_id_junk)
        model_cc = model_cc.index(model_id)
        for item in model_cc.obs['radius_e']/1000:
            radius_AR_hits.append(item)
        for item in reference_cc_junk.obs['radius_e']/1000:
            radius_AR_misses.append(item)
        for item in model_cc_junk.obs['radius_e']/1000:
            radius_AR_falarm.append(item)    
            
        for item in model_cc.obs['amplitude']*100:
            amplitude_AR_hits.append(item)
        for item in reference_cc_junk.obs['amplitude']*100:
            amplitude_AR_misses.append(item)
        for item in model_cc_junk.obs['amplitude']*100:
            amplitude_AR_falarm.append(item)
        i+=1
    
        
    bins = np.arange(0,400,1)
    hist_hits,   bins_hits    = np.histogram(amplitude_AR_hits ,bins=bins)
    hist_misses , bins_misses  = np.histogram(amplitude_AR_misses ,bins=bins)
    hist_falarm  ,bins_falarm  = np.histogram(amplitude_AR_falarm,bins=bins)
    POD_AR  = hist_hits    / (hist_hits  + hist_misses )
    FAR_AR  = hist_falarm  / (hist_hits + hist_falarm )
    
    ### SCORES ###
    # False Alarm Ratio
    AR_FAR = AR_falarm / (AR_hits + AR_falarm)
    
    # Probability Of Detection
    AR_POD = AR_hits / (AR_hits + AR_misses)
    
    PRECISION= AR_hits / (AR_hits + AR_falarm)
    F_SCORE= 2 * ( (AR_POD * PRECISION) / ( AR_POD + PRECISION) ) 
    SR=1-AR_FAR
    bias=AR_POD/(1-AR_FAR)
    CSI=1/((1/(1-AR_FAR))+(1/AR_POD)-1)

    


    print("GENREAL DETECTION ADN TRACKING INFO")
    print("AC stands for AntiCyclonic & CC for CyClonic")
    print("---------------------------------------------------------")

    print("The following information applies to the chosen domain")
    # Print information for AC eddies
    print("Number of AC eddies in the period =", sum(NB_AC_ZONE))
    print("Minimum number of AC eddies detected in one day =", min(NB_AC_ZONE))
    print("Maximum number of AC eddies detected in one day =", max(NB_AC_ZONE))
    print("So on average {} AC eddies per day".format(round(np.mean(NB_AC_ZONE), 0)))
    print("---------------------------------------------------------")

    # Print information for CC eddies
    print("Number of CC eddies in the period =", sum(NB_CC_ZONE))
    print("Minimum number of CC eddies detected in one day =", min(NB_CC_ZONE))
    print("Maximum number of CC eddies detected in one day =", max(NB_CC_ZONE))
    print("So on average {} CC eddies per day".format(round(np.mean(NB_CC_ZONE), 0)))
    print("---------------------------------------------------------")

    # Print information for all eddies
    print("Number of eddies in the period =", sum(NB_EDDIES_ZONE))
    print("Minimum number of eddies detected in one day =", min(NB_EDDIES_ZONE))
    print("Maximum number of eddies detected in one day =", max(NB_EDDIES_ZONE))
    print("So on average {} eddies per day".format(round(np.mean(NB_EDDIES_ZONE))))
    print("---------------------------------------------------------")

    # Print information for tracks
    print("Number of AC tracks =", at_zone.nb_tracks)
    print("Number of CC tracks =", ct_zone.nb_tracks)
    print("Number of tracks =", at_zone.nb_tracks + ct_zone.nb_tracks)
    print("---------------------------------------------------------")

    # Print information for average track duration
    print("Average AC track duration =", round(np.mean(at_zone.nb_obs_by_track)), "jours")
    print("Average CC track duration =", round(np.mean(ct_zone.nb_obs_by_track)), "jours")
    print("Average track duration =", round(np.mean(eddies_zone.nb_obs_by_track)), "jours")
    print("---------------------------------------------------------")

    # Print information for mean amplitude
    print("Mean AC amplitude =", round(np.mean(at_zone.amplitude * 100), 2), "cm")
    print("Mean AC amplitude =", round(np.mean(ct_zone.amplitude * 100), 2), "cm")
    print("Mean eddy amplitude =", round(np.mean(eddies_zone.amplitude * 100), 2), "cm")
    print("---------------------------------------------------------")

    # Print information for mean radius
    print("Mean AC radius =", round(np.mean(at_zone.effective_radius / 1000), 2), "km")
    print("Mean CC radius =", round(np.mean(ct_zone.effective_radius / 1000), 2), "km")
    print("Mean eddy radius =", round(np.mean(eddies_zone.effective_radius / 1000), 2), "km")
    print("---------------------------------------------------------")

    # Print information for mean surface occupied
    print("Mean surface occupied by AC eddies =", round(np.mean(at_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("Mean surface occupied by CC eddies =", round(np.mean(ct_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("Mean surface occupied by eddies =", round(np.mean(eddies_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("---------------------------------------------------------")

    # Print information for tracks too short
    print("Number of AC tracks too short =", ats_zone.nb_tracks)
    print("Number of CC tracks too short =", cts_zone.nb_tracks)
    print("Number of tracks too short =", ats_zone.nb_tracks + cts_zone.nb_tracks)
    print("---------------------------------------------------------")

    # Print information for average track duration of tracks too short
    print("Average AC track too short duration =", round(np.mean((ats_zone.nb_obs_by_track))), "jours")
    print("Average CC track too short duration =", round(np.mean((cts_zone.nb_obs_by_track))), "jours")
    print("Average track too short duration =", round(np.mean((eddies_ts_zone.nb_obs_by_track))), "jours")
    print("---------------------------------------------------------")

    # Print information for mean amplitude of tracks too short
    print("Mean AC amplitude track too short =", round(np.mean(ats_zone.amplitude * 100), 2), "cm")
    print("Mean CC amplitude track too short =", round(np.mean(cts_zone.amplitude * 100), 2), "cm")
    print("Mean amplitude track too short =", round(np.mean(eddies_ts_zone.amplitude * 100), 2), "cm")
    print("---------------------------------------------------------")

    # Print information for mean radius of tracks too short
    print("Mean AC radius track too short =", round(np.mean(ats_zone.effective_radius / 1000), 2), "km")
    print("Mean CC radius track too short =", round(np.mean(cts_zone.effective_radius / 1000), 2), "km")
    print("Mean radius track too short =", round(np.mean(eddies_ts_zone.effective_radius / 1000), 2), "km")
    print("---------------------------------------------------------")

    # Print information for mean surface occupied by tracks too short
    print("Mean surface occupied by AC eddies from tracks too short =", round(np.mean(ats_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("Mean surface occupied by CC eddies from tracks too short =", round(np.mean(cts_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("Mean surface occupied by eddies from tracks too short =", round(np.mean(eddies_ts_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("---------------------------------------------------------")

    # Print information for untracked eddies
    print("Number of untracked AC eddies =", len(ata_zone))
    print("Number of untracked CC eddies  =", len(cta_zone))
    print("---------------------------------------------------------")

    # Print information for mean amplitude of untracked eddies
    print("Mean amplitude of untracked AC eddies =", round(np.mean(ata_zone.amplitude * 100), 2), "cm")
    print("Mean amplitude of untracked CC eddies =", round(np.mean(cta_zone.amplitude * 100), 2), "cm")
    print("Mean amplitude of untracked eddies =", round(np.mean(eddies_a_zone.amplitude * 100), 2), "cm")
    print("---------------------------------------------------------")

    # Print information for mean radius of untracked eddies
    print("Mean radius of untracked AC eddies =", round(np.mean(ata_zone.effective_radius / 1000), 2), "km")
    print("Mean radius of untracked CC eddies =", round(np.mean(cta_zone.effective_radius / 1000), 2), "km")
    print("Mean radius of untracked eddies =", round(np.mean(eddies_a_zone.effective_radius / 1000), 2), "km")
    print("---------------------------------------------------------")

    # Print information for mean surface occupied by untracked eddies
    print("Mean surface occupied by untracked AC eddies =", round(np.mean(ata_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("Mean surface occupied by untracked CC eddies =", round(np.mean(cta_zone.effective_area / (1000 * 1000)), 2), "km^2")
    print("Mean surface occupied by untracked eddies =", round(np.mean(eddies_a_zone.effective_area / (1000 * 1000)), 2), "km^2")
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
    print("The mean false alarm ratio (FAR) is", round(np.mean(AR_FAR), 3), "so a success ratio of", round(np.mean(SR), 3))
    print("The F_Score is", round(np.mean(F_SCORE), 3))
    print("The critical success index (CSI) is", round(np.mean(CSI), 3))

    


    ################################################################################################################
    # 						PLOTS							       #
    ################################################################################################################

    plots = Plots(config_object, True)


    ### PLOT ALL TRACKS FOR THE PERIOD ###

    ### PLOT HEATMAP FOR MODEL 
    plots.plot_heatmap(zone_params)
    plots.plot_heatmap_radius(zone_params)
    
    ### NUMBER OF DETECTION BY TIME WITH MEAN ###
    plots.plot_number_detection_time_mean(NB_EDDIES_ZONE)

    ### COUNT 
    plots.plot_count_log_amp(at, ct, a_ref, c_ref, at_zone, ct_zone, a_zone_ref, c_zone_ref) 
    plots.plot_count_speed_radius(at, ct, a_ref, c_ref, at_zone, ct_zone, a_zone_ref, c_zone_ref)
    plots.plot_count_lifetime(at, ct, a_ref, c_ref, at_zone, ct_zone, a_zone_ref, c_zone_ref)


    ### 2D HISTOGRAM RADIUS AMPLITUDE ###
    plots.plot_2d_histo(eddies_zone)

    ### HISTOGRAM HITS MISSES & FALSE ALARMS BY RADIUS (KM) ###
    plots.plot_histo_hits_false(radius_AR_hits_glo, radius_AR_misses_glo, radius_AR_falarm_glo,radius_AR_hits, radius_AR_misses, radius_AR_falarm)

    ### POD & FAR BY AMPLITUDE (CM) ###
    plots.plot_pod_far_amplitude(POD_AR, FAR_AR)

    ### POD & FAR BY TIME ###
    plots.plot_pod_far_time(AR_POD, AR_FAR)

    ### PERFORMANCE DIAGRAM ###
    plots.perf_diag(SR, AR_POD,SR_GLO,AR_POD_GLO)



if __name__ == "__main__":
    analysis_eddies()








