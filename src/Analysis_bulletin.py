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

from plots_bulletin import Plots

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
    
    ### LOAD REFERENCE TRACKS ###
    a_ref= TrackEddiesObservations.load_file(PATH_REF_TRACK+"Anticyclonic.nc")
    c_ref=TrackEddiesObservations.load_file(PATH_REF_TRACK+"Cyclonic.nc")
    a_ref.position_filter(median_half_window=1, loess_half_window=5)
    c_ref.position_filter(median_half_window=1, loess_half_window=5)
    eddies_ref=a_ref.merge(c_ref)

    #### DOMAIN DEFINITION ###  
    
    GS = dict(llcrnrlon=-80, llcrnrlat=30, urcrnrlon=-30, urcrnrlat=60)
    IBI= dict(llcrnrlon=-19, llcrnrlat=26, urcrnrlon=5, urcrnrlat=56)
    AG = dict(llcrnrlon=5, llcrnrlat=-45, urcrnrlon=35, urcrnrlat=-25)
    KOE= dict(llcrnrlon=140, llcrnrlat=28, urcrnrlon=170, urcrnrlat=50)

    zone_params_list = [GS, IBI, AG, KOE]
    
    #### TRACKING DATA ####
    ##### GS ######
    # MODEL #
    at_GS = at.extract_with_area(GS, full_path=False)
    ct_GS = ct.extract_with_area(GS, full_path=False)
    eddies_GS=at_GS.merge(ct_GS)

    # REFERENCE #
    a_GS_ref = a_ref.extract_with_area(GS, full_path=False)
    c_GS_ref = c_ref.extract_with_area(GS, full_path=False)
    eddies_ref_GS= a_GS_ref.merge(c_GS_ref)

    ######################################################
        # MODEL #
    ##### IBI #########
    at_IBI = at.extract_with_area(IBI, full_path=False)
    ct_IBI = ct.extract_with_area(IBI, full_path=False)
    eddies_IBI=at_IBI.merge(ct_IBI)

    # REFERENCE #
    a_IBI_ref = a_ref.extract_with_area(IBI, full_path=False)
    c_IBI_ref = c_ref.extract_with_area(IBI, full_path=False)
    eddies_ref_IBI= a_IBI_ref.merge(c_IBI_ref)

    ######################################################
        # MODEL #
    ##### AG #######
    at_AG = at.extract_with_area(AG, full_path=False)
    ct_AG = ct.extract_with_area(AG, full_path=False)
    eddies_AG=at_AG.merge(ct_AG)

    # REFERENCE #
    a_AG_ref = a_ref.extract_with_area(AG, full_path=False)
    c_AG_ref = c_ref.extract_with_area(AG, full_path=False)
    eddies_ref_AG= a_AG_ref.merge(c_AG_ref)
    #######################################################
        # MODEL #
    ###### KOE######
    at_KOE = at.extract_with_area(KOE, full_path=False)
    ct_KOE = ct.extract_with_area(KOE, full_path=False)
    eddies_KOE=at_KOE.merge(ct_KOE)

    # REFERENCE #
    a_KOE_ref = a_ref.extract_with_area(KOE, full_path=False)
    c_KOE_ref = c_ref.extract_with_area(KOE, full_path=False)
    eddies_ref_KOE= a_KOE_ref.merge(c_KOE_ref)
    #####################################################

    
    ## RECTANGLE IN PLOT ## 
    rect_params_GS=GS
    rect_params_IBI=IBI
    rect_params_AG=AG
    rect_params_KOE=KOE

    ### NUMBER OF DETECTION ###
    NB_AC=[]
    NB_CC=[]
    NB_EDDIES=[]
    
    NB_AC_GS=[]
    NB_CC_GS=[]
    NB_EDDIES_GS=[]

    NB_AC_IBI=[]
    NB_CC_IBI=[]
    NB_EDDIES_IBI=[]

    NB_AC_AG=[]
    NB_CC_AG=[]
    NB_EDDIES_AG=[]

    NB_AC_KOE=[]
    NB_CC_KOE=[]
    NB_EDDIES_KOE=[]
    
    input_file_ac = sorted(glob.glob(PATH_DETECT_FILES +'Anticyclonic'+'*.nc'))
    for i,file in enumerate(input_file_ac[:]):
        a=EddiesObservations.load_file(file)
        NB_AC.append(len(a))
        
        NB_AC_GS.append(len(a.extract_with_area(GS)))
        NB_AC_IBI.append(len(a.extract_with_area(IBI)))
        NB_AC_AG.append(len(a.extract_with_area(AG)))
        NB_AC_KOE.append(len(a.extract_with_area(KOE)))

    
    input_file_cc = sorted(glob.glob(PATH_DETECT_FILES +'Cyclonic'+'*.nc'))
    for i,file in enumerate(input_file_cc[:]):
        c=EddiesObservations.load_file(file)
        NB_CC.append(len(c))
        
        NB_CC_GS.append(len(c.extract_with_area(GS)))
        NB_CC_IBI.append(len(c.extract_with_area(IBI)))
        NB_CC_AG.append(len(c.extract_with_area(AG)))
        NB_CC_KOE.append(len(c.extract_with_area(KOE)))
    
    for i in range(len(NB_AC)):
        NB_EDDIES.append(NB_AC[i]+NB_CC[i])
        
        NB_EDDIES_GS.append(NB_AC_GS[i]+NB_CC_GS[i])
        NB_EDDIES_IBI.append(NB_AC_IBI[i]+NB_CC_IBI[i])
        NB_EDDIES_AG.append(NB_AC_AG[i]+NB_CC_AG[i])
        NB_EDDIES_KOE.append(NB_AC_KOE[i]+NB_CC_KOE[i])



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

    ###### GULF STREAM ##########
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
        reference_ac = a_GS_ref.extract_with_period((date,date))
        model_ac = at_GS.extract_with_period((date,date))
    
        ## Cyclonic
        reference_cc = c_GS_ref.extract_with_period((date,date))
        model_cc = ct_GS.extract_with_period((date,date))
        
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
    
       
    # False Alarm Ratio
    AR_FAR_GS = AR_falarm / (AR_hits + AR_falarm)
    
    # Probability Of Detection
    AR_POD_GS = AR_hits / (AR_hits + AR_misses)
    
    PRECISION_GS = AR_hits / (AR_hits + AR_falarm)
    F_SCORE_GS = 2 * ((AR_POD_GS * PRECISION_GS) / (AR_POD_GS + PRECISION_GS))
    SR_GS = 1 - AR_FAR_GS
    bias_GS = AR_POD_GS / (1 - AR_FAR_GS)
    CSI_GS = 1 / ((1 / (1 - AR_FAR_GS)) + (1 / AR_POD_GS) - 1)



    ############################################################################
    ############################################################################

    ############################################################
    ########### MATCHING WITH JUST DOMAIN ######################
    ############################################################

    ###### IBI ##########
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
        reference_ac = a_IBI_ref.extract_with_period((date,date))
        model_ac = at_IBI.extract_with_period((date,date))
    
        ## Cyclonic
        reference_cc = c_IBI_ref.extract_with_period((date,date))
        model_cc = ct_IBI.extract_with_period((date,date))
        
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
    
       
    # False Alarm Ratio
    AR_FAR_IBI = AR_falarm / (AR_hits + AR_falarm)
    
    # Probability Of Detection
    AR_POD_IBI = AR_hits / (AR_hits + AR_misses)
    
    PRECISION_IBI = AR_hits / (AR_hits + AR_falarm)
    F_SCORE_IBI = 2 * ((AR_POD_IBI * PRECISION_IBI) / (AR_POD_IBI + PRECISION_IBI))
    SR_IBI = 1 - AR_FAR_IBI
    bias_IBI = AR_POD_IBI / (1 - AR_FAR_IBI)
    CSI_IBI = 1 / ((1 / (1 - AR_FAR_IBI)) + (1 / AR_POD_IBI) - 1)

    ########################################################
    ########################################################

    

      ###### AG ##########
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
        reference_ac = a_AG_ref.extract_with_period((date,date))
        model_ac = at_AG.extract_with_period((date,date))
    
        ## Cyclonic
        reference_cc = c_AG_ref.extract_with_period((date,date))
        model_cc = ct_AG.extract_with_period((date,date))
        
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
    
       
    # False Alarm Ratio
    AR_FAR_AG = AR_falarm / (AR_hits + AR_falarm)
    
    # Probability Of Detection
    AR_POD_AG = AR_hits / (AR_hits + AR_misses)
    
    PRECISION_AG = AR_hits / (AR_hits + AR_falarm)
    F_SCORE_AG = 2 * ((AR_POD_AG * PRECISION_AG) / (AR_POD_AG + PRECISION_AG))
    SR_AG = 1 - AR_FAR_AG
    bias_AG = AR_POD_AG / (1 - AR_FAR_AG)
    CSI_AG = 1 / ((1 / (1 - AR_FAR_AG)) + (1 / AR_POD_AG) - 1)
    
    #################################################################################
    #################################################################################

     ###### KOE ##########
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
        reference_ac = a_KOE_ref.extract_with_period((date,date))
        model_ac = at_KOE.extract_with_period((date,date))
    
        ## Cyclonic
        reference_cc = c_KOE_ref.extract_with_period((date,date))
        model_cc = ct_KOE.extract_with_period((date,date))
        
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
    
 
    # False Alarm Ratio
    AR_FAR_KOE = AR_falarm / (AR_hits + AR_falarm)
    
    # Probability Of Detection
    AR_POD_KOE = AR_hits / (AR_hits + AR_misses)
    
    PRECISION_KOE = AR_hits / (AR_hits + AR_falarm)
    F_SCORE_KOE = 2 * ((AR_POD_KOE * PRECISION_KOE) / (AR_POD_KOE + PRECISION_KOE))
    SR_KOE = 1 - AR_FAR_KOE
    bias_KOE = AR_POD_KOE / (1 - AR_FAR_KOE)
    CSI_KOE = 1 / ((1 / (1 - AR_FAR_KOE)) + (1 / AR_POD_KOE) - 1)


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
    # plots.plot_all_tracks_period(at_zone, ct_zone,rect_params)

    ## PLOT HEATMAPS FOR NUMBER, RADIUS & AMPLITUDE ###
    plots.plot_heatmap_model_and_ref()
    plots.plot_multiple_heatmaps(zone_params_list,2)
    
    plots.plot_heatmap_radius_model_and_ref(100)
    plots.plot_multiple_heatmaps_radius(zone_params_list,100)

    plots.plot_heatmap_amplitude_model_and_ref(8)
    plots.plot_multiple_heatmaps_amplitude(zone_params_list,8)
    
    ### NUMBER OF DETECTION BY TIME WITH MEAN ###
    plots.plot_number_detection_time(NB_EDDIES)
    plots.plot_number_detection_multizone(NB_EDDIES_GS,NB_EDDIES_IBI,NB_EDDIES_AG,NB_EDDIES_KOE)

    ### COUNT 
    plots.plot_count_log_amp(eddies,eddies_ref)
    plots.plot_count_log_amp_multiple(eddies_GS, eddies_IBI, eddies_AG, eddies_KOE)

    plots.plot_count_log_rad(eddies,eddies_ref)
    plots.plot_count_log_rad_multiple(eddies_GS, eddies_IBI, eddies_AG, eddies_KOE)
    plots.plot_count_lifetime(eddies,eddies_ref)
    plots.plot_count_lifetime_multiple(eddies_GS, eddies_IBI, eddies_AG, eddies_KOE)

    ### HISTOGRAM HITS MISSES & FALSE ALARMS BY RADIUS (KM) ###
    plots.plot_histo_matching(radius_AR_hits_glo, radius_AR_misses_glo, radius_AR_falarm_glo)


    ### POD & FAR BY AMPLITUDE (CM) ###
    # plots.plot_pod_far_amplitude(POD_AR, FAR_AR)

    ### POD & FAR BY TIME ###
    plots.plot_pod_far_time(AR_POD, AR_FAR)
    plots.plot_pod_far_time(AR_POD_GLO, AR_FAR_GLO)

    ### PERFORMANCE DIAGRAM ###
    plots.perf_diag(SR_GS, AR_POD_GS, SR_IBI, AR_POD_IBI, SR_AG, AR_POD_AG, SR_KOE, AR_POD_KOE ,SR_GLO,AR_POD_GLO)


if __name__ == "__main__":
    analysis_eddies()








