#!/usr/bin/env python
# coding: utf-8


########################################################################################################################

### 	ANALYSIS ONE MODEL WITH DETECTION AND TRACKING AND MATCHING WITH A REFERENCE 				    ###

########################################################################################################################



### IMPORT ###
#environment with py-eddy-tracker 
#Mason et al. 

import sys
from py_eddy_tracker.appli.grid import eddy_id
from py_eddy_tracker.dataset.grid import RegularGridDataset
from py_eddy_tracker.generic import distance_grid
from datetime import datetime
import glob
from netCDF4 import Dataset
import re
import pandas as pd
import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
from labellines import labelLine, labelLines
from py_eddy_tracker import data
from py_eddy_tracker.observations.observation import EddiesObservations
from py_eddy_tracker.observations.tracking import TrackEddiesObservations

import matplotlib.ticker as mticker
import matplotlib
font = {'family' : 'serif',
        'weight' : 'bold',
        'size'   : 14}
matplotlib.rc('font', **font)
import matplotlib.dates as mdates
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
data_crs=ccrs.PlateCarree()
import cartopy.feature as cfeature
from py_eddy_tracker.gui import GUI_AXES

def plt_cartopy_ibi(ax,labels=True):
    #ax.set_aspect('auto') # The figure will follow the ratio of the figsize
    ax.coastlines()       # Plot the coastlines
    ax.set_xticks([-15,-5,5], crs=data_crs) 		# Set ticks for longitude
    ax.set_yticks([30,40,50], crs=data_crs)             # Set ticks for latitude
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)

def reverse_index(index, nb):
    m = np.ones(nb, dtype="bool")
    m[index] = False
    return np.where(m)[0]


########################################################################################################################

### CONFIG FILE ### 

from configparser import ConfigParser
import argparse

#Read in config file name
parser = argparse.ArgumentParser(description='Script that reads in a config file')
				 #default drifting time 90 days 
				 #model output NEMO Mercator PSY4V3R1_1dAV 
				 #advection in 2D at the surface'''))
#add command line option
parser.add_argument("CONFIG_FILE", help="specify name of configuration file", type=str)
args = parser.parse_args()
CONFIG_FILE=args.CONFIG_FILE
print('read in:', CONFIG_FILE)

#Read in user input arguments
config_object = ConfigParser()
config_object.read(CONFIG_FILE)


### IN CONFIG FILE : 2 sections : GENERAL INFO and PLOT INFO

general_info  = config_object["GENERAL_INFO"]
MODEL	      = str(general_info["MODEL"])
REFERENCE     = str(general_info["REFERENCE"])
YEAR          = int(general_info["YEAR"])
DATE_START    = str(general_info["DATE_START"])
PERIODS       = int(general_info["PERIODS"])
PATH_DETECT_FILES = str(general_info["PATH_DETECT_FILES"])
PATH_TRAJ_FILES = str(general_info["PATH_TRAJ_FILES"])
PATH_REF_TRACK = str(general_info["PATH_REF_TRACK"])

#Geographical extend 
LON_MIN         = int(general_info["LON_MIN"])
LON_MAX         = int(general_info["LON_MAX"])
LAT_MIN         = int(general_info["LAT_MIN"])
LAT_MAX         = int(general_info["LAT_MAX"])


plot_info=config_object["PLOT_INFO"]


PATH_ADT_MODEL = str(plot_info["PATH_ADT_MODEL"])
var_adt	       = str(plot_info["var_adt"])
DIR_PLOT       = str(plot_info["PATH_PLOT"])
DX 	       = int(plot_info["DX"])
DY 	       = int(plot_info["DY"])

#AC_DETECTION   = str(plot_info["AC_DETECTION"])
#CC_DETECTION   = str(plot_info["CC_DETECTION"])

##ONE DAY
AC_DETECTION=PATH_DETECT_FILES+"Anticyclonic_"+MODEL+"_20190101.nc"
CC_DETECTION=PATH_DETECT_FILES+"Cyclonic_"+MODEL+"_20190101.nc"

########################################################################################################################

### NUMBER OF DETECTION ###
NB_AC=[]
NB_CC=[]
NB_EDDIES=[]

input_file_ac = sorted(glob.glob(PATH_DETECT_FILES +'Anticyclonic'+'*.nc'))
for i,file in enumerate(input_file_ac[:]):
    a=EddiesObservations.load_file(file)
    NB_AC.append(len(a))

input_file_cc = sorted(glob.glob(PATH_DETECT_FILES +'Cyclonic'+'*.nc'))
for i,file in enumerate(input_file_cc[:]):
    c=EddiesObservations.load_file(file)
    NB_CC.append(len(c))

for i in range(len(NB_AC)):
    NB_EDDIES.append(NB_AC[i]+NB_CC[i])

    
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

########################################################################################################################
					#### MATCHING WITH REFERENCE ####
########################################################################################################################

###  Data REFERENCE ##

a_ref= TrackEddiesObservations.load_file(PATH_REF_TRACK+"Anticyclonic.nc")
c_ref=TrackEddiesObservations.load_file(PATH_REF_TRACK+"Cyclonic.nc")
a_ref.position_filter(median_half_window=1, loess_half_window=5)
c_ref.position_filter(median_half_window=1, loess_half_window=5)

dates = np.arange(a_ref.obs['time'].min(),a_ref.obs['time'].max()) 
datesb = np.arange(at.obs['time'].min(),at.obs['time'].max()) 

# Hits, Misses, False Alarm
## GLO12
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

print("GENREAL DETECTION ADN TRACKING INFO")
print("AC stands for AntiCyclonic & CC for CyClonic")
print('---------------------------------------------------------')
print("Number of AC eddies in the period = ",sum(NB_AC))
print("Minimum number of AC eddies detected in one day = ",min(NB_AC))
print("Maximum number of AC eddies detected in one day = ",max(NB_AC))
print("So on average ",np.round(np.mean(NB_AC),0), 'AC eddies per day')
print('---------------------------------------------------------')
print("Number of CC eddies in the period =",sum(NB_CC))
print("Minimum number of CC eddies detected in one day = ",min(NB_CC))
print("Maximum number of CC eddies detected in one day = ",max(NB_CC))
print("So on average" ,np.round(np.mean(NB_CC),0), 'CC eddies per day')
print('---------------------------------------------------------')
print("Number of eddies in the period =",sum(NB_EDDIES))
print("Minimum number of eddies detected in one day = ",min(NB_EDDIES))
print("Maximum number of eddies detected in one day = ",max(NB_EDDIES))
print("So on average",round(np.mean(NB_EDDIES)), 'eddies per day')
print('---------------------------------------------------------')
print("Number of AC tracks =",at.nb_tracks)
print("Number of CC tracks =",ct.nb_tracks)
print("Number of tracks =",at.nb_tracks+ct.nb_tracks)
print('---------------------------------------------------------')
print("Average AC track duration =",round(np.mean((at.nb_obs_by_track))),'jours')
print("Average CC track duration =",round(np.mean((ct.nb_obs_by_track))),'jours')
print("Average track duration =",round(np.mean((eddies.nb_obs_by_track))),'jours')
print('---------------------------------------------------------')
print("Mean AC amplitude =", round(np.mean(at.amplitude*100),2),'cm')
print("Mean AC amplitude =", round(np.mean(ct.amplitude*100),2),'cm')
print("Mean eddy amplitude =", round(np.mean(eddies.amplitude*100),2),'cm')
print('---------------------------------------------------------')
print("Mean AC radius =", round(np.mean(at.effective_radius/1000),2),'km')
print("Mean CC radius =", round(np.mean(ct.effective_radius/1000),2),'km')
print("Mean eddy radius =", round(np.mean(eddies.effective_radius/1000),2),'km')
print('---------------------------------------------------------')
print("Mean surface occupied by AC eddies =", round(np.mean(at.effective_area/(1000*1000)),2),'km^2')
print("Mean surface occupied by CC eddies =", round(np.mean(ct.effective_area/(1000*1000)),2),'km^2')
print("Mean surface occupied by eddies =", round(np.mean(eddies.effective_area/(1000*1000)),2),'km^2')
print('---------------------------------------------------------')
print("Number of AC tracks too short =",ats.nb_tracks)
print("Number of CC tracks too short =",cts.nb_tracks)
print("Number of tracks too short =",ats.nb_tracks+cts.nb_tracks)
print('---------------------------------------------------------')
print("Average AC track too short duration =",round(np.mean((ats.nb_obs_by_track))),'jours')
print("Average CC track too short duration =",round(np.mean((cts.nb_obs_by_track))),'jours')
print("Average track too short duration =",round(np.mean((eddies_ts.nb_obs_by_track))),'jours')
print('---------------------------------------------------------')
print("Mean AC amplitude track too short =", round(np.mean(ats.amplitude*100),2),'cm')
print("Mean CC amplitude track too short =", round(np.mean(cts.amplitude*100),2),'cm')
print("Mean amplitude track too short =", round(np.mean(eddies_ts.amplitude*100),2),'cm')
print('---------------------------------------------------------')
print("Mean AC radius track too short =", round(np.mean(ats.effective_radius/1000),2),'km')
print("Mean CC radius track too short =", round(np.mean(cts.effective_radius/1000),2),'km')
print("Mean radius track too short =", round(np.mean(eddies_ts.effective_radius/1000),2),'km')
print('---------------------------------------------------------')
print("Mean surface occupied by AC eddies from tracks too short =", round(np.mean(ats.effective_area/(1000*1000)),2),'km^2')
print("Mean surface occupied by CC eddies from tracks too short =", round(np.mean(cts.effective_area/(1000*1000)),2),'km^2')
print("Mean surface occupied by eddies from tracks too short =", round(np.mean(eddies_ts.effective_area/(1000*1000)),2),'km^2')
print('---------------------------------------------------------')
print("Number of untracked AC eddies =",len(ata))
print("Number of untracked CC eddies  =",len(cta))
print('---------------------------------------------------------')
print("Mean amplitude of untracked AC eddies =", round(np.mean(ata.amplitude*100),2),'cm')
print("Mean amplitude of untracked CC eddies =", round(np.mean(cta.amplitude*100),2),'cm')
print("Mean amplitude of untracked eddies =", round(np.mean(eddies_a.amplitude*100),2),'cm')
print('---------------------------------------------------------')
print("Mean radius of untracked AC eddies =", round(np.mean(ata.effective_radius/1000),2),'km')
print("Mean radius of untracked CC eddies =", round(np.mean(cta.effective_radius/1000),2),'km')
print("Mean radius of untracked eddies =", round(np.mean(eddies_a.effective_radius/1000),2),'km')
print('---------------------------------------------------------')
print("Mean surface occupied by untracked AC eddies =", round(np.mean(ata.effective_area/(1000*1000)),2),'km^2')
print("Mean surface occupied by untracked CC eddies =", round(np.mean(cta.effective_area/(1000*1000)),2),'km^2')
print("Mean surface occupied by untracked eddies =", round(np.mean(eddies_a.effective_area/(1000*1000)),2),'km^2')
print('---------------------------------------------------------')
print('MATCHING RESULTS')
print('---------------------------------------------------------')
print("Number of hits =",len(amplitude_AR_hits))
print("Number of misses =",len(amplitude_AR_misses))
print("Number of false alarms =",len(amplitude_AR_falarm))
print('---------------------------------------------------------')
print("Average number of hits per day =", round(np.mean(Hits)))
print("Average number of misses per day =", round(np.mean(Misses)))
print("Average number of false alarms per day =",round(np.mean(Falarms)))
print('---------------------------------------------------------')
print("Mean hits amplitude =", round(np.mean(amplitude_AR_hits),2),'cm')
print("Mean misses amplitude =", round(np.mean(amplitude_AR_misses),2),'cm')
print("Mean false alarms amplitude =", round(np.mean(amplitude_AR_falarm),2),'cm')
print('---------------------------------------------------------')
print("Mean hits radius =", round(np.mean(radius_AR_hits),2),'km')
print("Mean misses radius =", round(np.mean(radius_AR_misses),2),'km')
print("Mean false alarms radius=", round(np.mean(radius_AR_falarm),2),'km')
print('---------------------------------------------------------')
print('The mean probablitity of detection (POD) is',round(np.mean(AR_POD),3))
print('The mean false alarm ratio (FAR) is',round(np.mean(AR_FAR),3),'soit un sucess ratio de',round(np.mean(SR),3))
print('The F_Score is', round(np.mean(F_SCORE),3))
print('The critical success index (CSI) is',round(np.mean(CSI),3))

################################################################################################################
#						PLOTS							       #
################################################################################################################

### PLOT ONE DAY DETECTION WITH ADT ###

# Make sure the filtering parameters are the same as in the detection script

h = RegularGridDataset(PATH_ADT_MODEL, 'longitude', 'latitude')
h.bessel_high_filter(var_adt,500,order=1)

a=EddiesObservations.load_file(AC_DETECTION)
c=EddiesObservations.load_file(CC_DETECTION)

fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
ax.set_extent([LON_MIN,LON_MAX,LAT_MIN,LAT_MAX])
AC_x, AC_y =  a.effective_contour_longitude, a.effective_contour_latitude
CC_x, CC_y =  c.effective_contour_longitude, c.effective_contour_latitude
for i in range(len(AC_x)):
    ax.plot(AC_x[i,:],AC_y[i,:], color='k', linestyle='-', linewidth=1, transform=data_crs)
for i in range(len(CC_y)):
    ax.plot(CC_x[i,:],CC_y[i,:], color='k', linestyle=':', linewidth=1.5, transform=data_crs)
ax.set_title(str(MODEL))
im = h.display(ax,var_adt, vmin=-0.15, vmax=0.15)
plt_cartopy_ibi(ax,labels=False)
plt.suptitle("Detection Cyclonic (Dotted) & Anticyclonic (Solid)")
cbar = fig.colorbar(im,ticks=[-.1, 0, .1]) 
cbar.ax.set_ylabel('ADT (m) Filtered (500 km)')     # Colorbar label

# Save or show
plt.savefig(DIR_PLOT+MODEL+'_Detection.jpeg',bbox_inches='tight',dpi=600)
#plt.show()

################################################################################################################

### PLOT ALL TRACKS FOR THE PERIOD ###

fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
ax.set_extent([LON_MIN,LON_MAX,LAT_MIN,LAT_MAX])
at.plot(ax, ref=-10, label="Anticyclonic {nb_tracks} tracks", color="r", lw=0.9,transform=data_crs)
ct.plot(ax, ref=-10, label="Cyclonic {nb_tracks} tracks",color="b", lw=0.9,transform=data_crs)
ax.legend()
ax.set_title('Tracks '+str(MODEL)+' '+ str (YEAR) )
plt_cartopy_ibi(ax,labels=False)
plt.savefig(DIR_PLOT+MODEL+'_TRACKS_'+str(YEAR)+'.jpeg',bbox_inches='tight',dpi=600)
# plt.show()

################################################################################################################

### NUMBER OF DETECTION BY TIME WITH MEAN ### 

t_data = pd.date_range(DATE_START, periods=PERIODS, freq='D') 
NB_mean = [np.mean(NB_EDDIES)]*len(t_data)

fig ,ax = plt.subplots(figsize=(12,6))
#ax = fig.add_axes([.03,.03,.94,.94])
ax.plot(t_data,NB_EDDIES,color='black')
ax.xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.ylabel('Nb eddy detected')
ax.plot(t_data,NB_mean, label='Mean', linestyle='--')
ax.legend()

plt.savefig(DIR_PLOT+'NB_EDDIES_'+MODEL+'_'+str(YEAR)+'.jpeg',bbox_inches='tight')
#plt.show()

################################################################################################################

### 2D HISTOGRAM RADIUS AMPLITUDE ###

fig, ax = plt.subplots()
counts, xedges, yedges, im = ax.hist2d(at['effective_radius']/1000, at['amplitude']*100, bins=200, cmap=plt.cm.jet, cmin=1)
ax.set_xlabel('Radius (km)')
ax.set_ylabel('Amplitude (cm)')

fig.colorbar(im, ax=ax)
plt.title(str(MODEL))
plt.savefig(DIR_PLOT+'HIST2D_AMP_RAD_'+MODEL+'_'+str(YEAR)+'.jpeg',bbox_inches='tight')
#plt.show()

################################################################################################################

### HISTOGRAM HITS MISSES & FALSE ALARMS BY RADIUS (KM) ### 

bins = np.arange(0,400,3)

plt.subplots(figsize=(6,4))
#plt.subplot(111)
plt.hist(radius_AR_hits ,  bins=bins,fill=False,linewidth=3,histtype='step',label='hits',color='green')
plt.hist(radius_AR_misses ,bins=bins,fill=False,linewidth=3,histtype='step',label='misses',color='red')
plt.hist(radius_AR_falarm ,bins=bins,fill=False,linewidth=3,histtype='step',label='false alarm',color='orange')
plt.gca().set(ylim=(0,4500),xlim=(0,100),xlabel='Radius (km)')
plt.legend()
plt.suptitle(MODEL+' Reference '+ REFERENCE)
plt.savefig(DIR_PLOT+'HIST_MATCHING_'+MODEL+'_'+str(YEAR)+'.jpeg',bbox_inches='tight')
#plt.show()

################################################################################################################

### POD & FAR BY AMPLITUDE (CM) ###

bins = np.arange(0,400,1)
plt.subplots(figsize=(10,4))
plt.subplot(121)
plt.step(bins[:-1], POD_AR,color='black',linewidth=2)
plt.gca().set(ylim=(np.nanmin(POD_AR)-0.2,1.05),ylabel='Probability of Detection',xlim=(0,20),xlabel='Amplitude (cm)')
plt.xticks(np.arange(0,20,5))
plt.grid()

plt.subplot(122)
plt.step(bins[:-1], FAR_AR ,color='black',linewidth=2)
plt.gca().set(ylim=(0,np.nanmax(FAR_AR)+0.2),ylabel='False Alarm Ratio',xlim=(0,20),xlabel='Amplitude (cm)')
plt.xticks(np.arange(0,20,5))

plt.grid()
plt.suptitle(MODEL+' Reference '+ REFERENCE)
plt.tight_layout()
plt.savefig(DIR_PLOT+'POD_FAR_AMP_'+MODEL+'_'+str(YEAR)+'.jpeg',bbox_inches='tight')
#plt.show()

################################################################################################################

### POD & FAR BY TIME ###

t_data = pd.date_range(DATE_START, periods= PERIODS - 1, freq='D') 
t_data_obs = pd.date_range(DATE_START, periods=PERIODS - 1, freq='D') 

fig, axes = plt.subplots(1,2,figsize=(17,3))

axes[0].plot(t_data_obs,AR_POD,color='black')
axes[0].set_ylim(0,1)
axes[0].xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
axes[0].set_title('Probability Of Detection')

axes[1].plot(t_data_obs,AR_FAR,color='black')
axes[1].set_ylim(0,1)
axes[1].xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
axes[1].set_title('False Alarm Ratio')


plt.savefig(DIR_PLOT+'POD_FAR_TEMP_'+MODEL+'_'+str(YEAR)+'.jpeg',bbox_inches='tight')
#plt.show()
################################################################################################################

################################################################################################################

### PERFORMANCE DIAGRAM ###
plt.subplots(figsize=(10,10))
i=np.arange(0,1.1,0.01)
CSI=np.arange(0.1,1,0.1)
for c in CSI:
    y=(c*i)/(c*i - c +i)
    indices = np.where(y<=0.0)
    y= np.delete(y, indices)
    i = np.delete(i,indices)
    y
    plt.plot(i,y,color='k',linewidth=1.8,label=str(np.round(c,2)))

xvals=[0.57,0.62,0.77,0.79,0.85,0.9,0.95,0.935,0.96]

labelLines(plt.gca().get_lines(),xvals=xvals,fontsize=15)

x=np.arange(0,1.1,0.1)

plt.plot(x,x*0.3,linestyle='--',color='k',linewidth=1.8)
plt.text(1.01,0.295,'0.3',size=13)
plt.plot(x,x*0.5,linestyle='--',color='k',linewidth=1.8)
plt.text(1.01,0.495,'0.5',size=13)
plt.plot(x,x*0.8,linestyle='--',color='k',linewidth=1.8)
plt.text(1.01,0.795,'0.8',size=13)
plt.plot(x,x,linestyle='--',color='k',linewidth=1.8)
plt.text(1,1,'1',size=13)
plt.plot(x,x*1.3,linestyle='--',color='k',linewidth=1.8)
plt.text(0.76,1.01,'1.3',size=13)
plt.plot(x,x*1.5,linestyle='--',color='k',linewidth=1.8)
plt.text(0.65,1.01,'1.5',size=13)
plt.plot(x,x*2,linestyle='--',color='k',linewidth=1.8)
plt.text(0.5,1.01,'2',size=13)
plt.plot(x,x*3,linestyle='--',color='k',linewidth=1.8)
plt.text(0.327,1.01,'3',size=13)
plt.plot(x,x*5,linestyle='--',color='k',linewidth=1.8)
plt.text(0.2,1.01,'5',size=13)
plt.plot(x,x*10,linestyle='--',color='k',linewidth=1.8)
plt.text(0.09,1.01,'10',size=13)

plt.title('Performance Diagram '+MODEL+' '+str(YEAR),y=1.08)
plt.scatter(np.mean(SR),np.mean(AR_POD),color='blue',s=200)
plt.scatter(0.995,0.995,color='orange',s=200,marker='D')
plt.text(0.8,0.96,'Perfect match',size=15)
plt.xlabel('Success Ratio (1-FAR)',fontsize=20)
plt.ylabel('Probability of detection (POD)',fontsize=20)
plt.xlim(0,1)
plt.xticks((np.arange(0, 1.1, step=0.1)), fontsize=20)
plt.yticks((np.arange(0, 1.1, step=0.1)), fontsize=20)
plt.minorticks_on()
plt.ylim(0,1)


plt.savefig(DIR_PLOT+'PERFORMANCE_DIAG_'+MODEL+'_'+str(YEAR)+'.jpeg',bbox_inches='tight',dpi=600)    
#plt.show()

