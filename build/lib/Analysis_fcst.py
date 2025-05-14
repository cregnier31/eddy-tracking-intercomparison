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
from matplotlib import cm
from datetime import datetime, timedelta
from py_eddy_tracker import data
from py_eddy_tracker.observations.observation import EddiesObservations
from py_eddy_tracker.observations.tracking import TrackEddiesObservations


# Graphics
#matplotlib inline
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import matplotlib
font = {'family' : 'serif',
        'weight' : 'bold',
        'size'   : 14}
matplotlib.rc('font', **font)
import glob

NB_DAYS=37


# Initial start_date
start_date = datetime.strptime("20230510", "%Y%m%d")

input_dirs = [
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_0/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_1/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_2/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_3/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_4/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_5/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_6/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_7/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_8/',
    '/data/rd_exchange/fdubost/EddyDetection/FDUBOST/FORECAST/GLO12/fcst_all/Detect_eddies_GLO_FC_9/',

]

input_dir_analysis='/data/rd_exchange/fdubost/EddyDetection/FDUBOST/nrt/GLO12V4/Detect_eddies_2023_SE70/'

# Define empty lists to store the results for each input directory
Nb_F0=[]
Nb_F1=[]
Nb_F2=[]
Nb_F3=[]
Nb_F4=[]
Nb_F5=[]
Nb_F6=[]
Nb_F7=[]
Nb_F8=[]
Nb_F9=[]
Nb_ANA=[]

Rad_F0=[]
Rad_F1=[]
Rad_F2=[]
Rad_F3=[]
Rad_F4=[]
Rad_F5=[]
Rad_F6=[]
Rad_F7=[]
Rad_F8=[]
Rad_F9=[]
Rad_ANA=[]

for idx, input_dir in enumerate(input_dirs, start=1):
    for i in range(NB_DAYS):
        date = start_date + timedelta(days=i)
    
        date_str = date.strftime("%Y%m%d")

        obs_file_a = input_dir + f"Anticyclonic_GLO12_FC0_{date_str}.nc"
        obs_data_a = EddiesObservations.load_file(obs_file_a)
        obs_file_c = input_dir + f"Cyclonic_GLO12_FC0_{date_str}.nc"
        obs_data_c = EddiesObservations.load_file(obs_file_c)

        try:
            obs_data_a = EddiesObservations.load_file(obs_file_a)
            obs_data_c = EddiesObservations.load_file(obs_file_c)
        except Exception as e:
            print(f"Error loading files for {date}: {e}")
            continue  # Skip to the next date if there's an error loading the files
        obs_eddies = obs_data_a.merge(obs_data_c)
        
        # Append the result to the corresponding list based on the input directory index
        if input_dir == input_dirs[0]:
            Nb_F0.append(len(obs_eddies))
            Rad_F0.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[1]:
            Nb_F1.append(len(obs_eddies))
            Rad_F1.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[2]:
            Nb_F2.append(len(obs_eddies) )
            Rad_F2.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[3]:
            Nb_F3.append(len(obs_eddies)  )
            Rad_F3.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[4]:
            Nb_F4.append(len(obs_eddies) )
            Rad_F4.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[5]:
            Nb_F5.append(len(obs_eddies))
            Rad_F5.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[6]:
            Nb_F6.append(len(obs_eddies))
            Rad_F6.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[7]:
            Nb_F7.append(len(obs_eddies))
            Rad_F7.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[8]:
            Nb_F8.append(len(obs_eddies))
            Rad_F8.append(obs_eddies.radius_e / 1000)
        elif input_dir == input_dirs[9]:
            Nb_F9.append(len(obs_eddies))
            Rad_F9.append(obs_eddies.radius_e / 1000)   



for i in range(NB_DAYS):
    date = start_date + timedelta(days=i)
    
    date_str = date.strftime("%Y%m%d")
    analyse_a  = input_dir_analysis + f"Anticyclonic_GLO12_{date_str}.nc"
    analyse_c  = input_dir_analysis + f"Cyclonic_GLO12_{date_str}.nc"


    obs_data_a = EddiesObservations.load_file(analyse_a)
    obs_data_c = EddiesObservations.load_file(analyse_c)
    obs_eddies = obs_data_a.merge(obs_data_c)
    

    Nb_ANA.append(len(obs_eddies))
    Rad_ANA.append(obs_eddies.radius_e / 1000)    




forecast_lists = [Nb_F0, Nb_F1, Nb_F2, Nb_F3, Nb_F4, Nb_F5, Nb_F6, Nb_F7, Nb_F8, Nb_F9]

differences = []
differences_pc = []
for forecast_list in forecast_lists:
    forecast_array = np.array(forecast_list)
    analyse_array = np.array(Nb_ANA)
    
    diff = np.subtract(forecast_array, analyse_array)
    
    diff_pc= (diff/analyse_array)*100
    differences_pc.append(diff_pc)
    differences.append(diff)

diff_mean= [round(np.nanmean(diff),1) for diff in differences]
diff_pc_mean= [round(np.nanmean(diff),1) for diff in differences_pc]

### PLOT FOR PERCENTAGE OF EDDIES LOST BY FORECAST LEAD TIME ####

plt.figure()

x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

color_map = cm.get_cmap('viridis')

for i in range(len(x)):
    color = color_map(i/len(x))  # Color based on position of point
    plt.scatter(x[i], diff_pc_mean[i], color=color)
    plt.text(x[i], diff_pc_mean[i] + 0.2, str(np.round(diff_pc_mean[i], 1)), ha='center', va='bottom', color=color)


plt.xlabel("Days Forecast")
plt.ylabel("Percentage")
plt.title("Percentage of lost eddies in the forecast compared to the analysis")
plt.savefig(
            f"{self.dir_plot}PERCENTAGE_EDDIES_LOST_{self.model}.png",
            bbox_inches="tight",
            dpi=500,
        )
#plt.show()






##### MATCHING ##### 


# Initialize lists to store results for each forecast directory
results = {
    'AC': [[] for _ in input_dirs],
    'CC': [[] for _ in input_dirs],
    'MEAN': [[] for _ in input_dirs]
}

# Initialize lists to store scores for each forecast directory
Hits = [[] for _ in input_dirs]
Misses = [[] for _ in input_dirs]
Falarms = [[] for _ in input_dirs]
POD = [[] for _ in input_dirs]
SR = [[] for _ in input_dirs]

start_date = datetime.strptime("20230510", "%Y%m%d")
num_days = NB_DAYS


for i in range(num_days):
    # Date courante
    date = start_date + timedelta(days=i)
    date_str = date.strftime("%Y%m%d")
    print(date_str)
    
    # Path for the observation files for anticyclones and cyclones
    obs_file_AC = input_dir_analysis + f"Anticyclonic_GLO12_{date_str}.nc"
    obs_file_CC = input_dir_analysis + f"Cyclonic_GLO12_{date_str}.nc"
    
    # Load observation data
    obs_data_AC = EddiesObservations.load_file(obs_file_AC)
    obs_data_CC = EddiesObservations.load_file(obs_file_CC)

    for idx, input_dir_FC in enumerate(input_dirs):
        # Path for the forecast files for anticyclones and cyclones
        fcst_file_AC = input_dir_FC + f"Anticyclonic_GLO12_FC0_{date_str}.nc"
        fcst_file_CC = input_dir_FC + f"Cyclonic_GLO12_FC0_{date_str}.nc"
        
        # Load forecast data
        fcst_data_AC = EddiesObservations.load_file(fcst_file_AC)
        fcst_data_CC = EddiesObservations.load_file(fcst_file_CC)
        
        # Calculate tracking and cost for anticyclones
        ref_id_AC, model_id_AC, cost_AC = obs_data_AC.tracking(fcst_data_AC)
        mean_cost_AC = np.mean(cost_AC)
        results['AC'][idx].append(mean_cost_AC)
        
        # Calculate tracking and cost for cyclones
        ref_id_CC, model_id_CC, cost_CC = obs_data_CC.tracking(fcst_data_CC)
        mean_cost_CC = np.mean(cost_CC)
        results['CC'][idx].append(mean_cost_CC)
        
        # Calculate mean cost
        mean_cost = (mean_cost_AC + mean_cost_CC) / 2
        results['MEAN'][idx].append(mean_cost)

        # Calculate Hits, Misses, and False Alarms for anticyclones
        reference_id_AC_junk, model_id_AC_junk = reverse_index(ref_id_AC, len(obs_data_AC)), reverse_index(model_id_AC, len(fcst_data_AC))
        
        hits_AC = len(ref_id_AC)
        misses_AC = len(reference_id_AC_junk)
        falarms_AC = len(model_id_AC_junk)

        # Calculate Hits, Misses, and False Alarms for cyclones
        reference_id_CC_junk, model_id_CC_junk = reverse_index(ref_id_CC, len(obs_data_CC)), reverse_index(model_id_CC, len(fcst_data_CC))
        
        hits_CC = len(ref_id_CC)
        misses_CC = len(reference_id_CC_junk)
        falarms_CC = len(model_id_CC_junk)

        # Sum Hits, Misses, and False Alarms
        total_hits = hits_AC + hits_CC
        total_misses = misses_AC + misses_CC
        total_falarms = falarms_AC + falarms_CC

        # Append to results lists
        Hits[idx].append(total_hits)
        Misses[idx].append(total_misses)
        Falarms[idx].append(total_falarms)
        POD[idx].append(total_hits / (total_hits + total_misses) if total_hits + total_misses > 0 else np.nan)
        SR[idx].append(1 - (total_falarms / (total_hits + total_falarms) if total_hits + total_falarms > 0 else np.nan))




##### PLOT EVOLUTION COST FUNCTION #####
num_forecasts = len(results['MEAN'])


plt.figure(figsize=(10, 6))
for fc_idx in range(num_forecasts):
    for day_idx in range(len(results['MEAN'][fc_idx])):
        plt.scatter(fc_idx, results['MEAN'][fc_idx][day_idx], color='grey', s=10)

# Calcul de la moyenne pour chaque p�riode de pr�vision
mean_values = [np.mean(results['MEAN'][i]) for i in range(num_forecasts)]

# Ajout des points rouges pour la moyenne de chaque p�riode de pr�vision
plt.scatter(range(num_forecasts), mean_values, color='red', label='Mean', marker='o', s=100)

# Personnalisation du graphique
plt.xlabel('Forecast lead time')
plt.ylabel('Mean Cost Function')
plt.title('Mean Cost Function vs Forecast')
plt.xticks(range(num_forecasts), [f'FC{i}' for i in range(num_forecasts)])  
plt.grid(False)
plt.tight_layout()
plt.show()




#### PLOT PERFORMANCE DIAGRAM #### 

CSI = np.arange(0.1, 1, 0.1)
xvals = [0.57, 0.62, 0.77, 0.79, 0.85, 0.9, 0.95, 0.935, 0.96]
labels = ["0.3", "0.5", "0.8", "1", "1.3", "1.5", "2", "3", "5", "10"]


fig, ax = plt.subplots(figsize=(6, 6))

# Plot CSI
for c in CSI:
    i = np.arange(0, 1.1, 0.01)
    y = (c * i) / (c * i - c + i)
    indices = np.where(y <= 0.0)
    y = np.delete(y, indices)
    i = np.delete(i, indices)
    ax.plot(i, y, color="k", linewidth=1, label=str(np.round(c, 2)))

x = [1.01, 1.01, 1.01, 1.01, 0.76, 0.65, 0.5, 0.327, 0.2, 0.09]
y_offsets = [0.295, 0.495, 0.795, 1, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01]
pente = np.arange(0, 1.1, 0.1)
for i, label in enumerate(labels):
    ax.plot(pente, pente * float(label), linestyle="--", color="k", linewidth=1)
    ax.text(x[i], y_offsets[i], label, size=10)


colors = plt.cm.viridis(np.linspace(0, 1, 10))
for idx in range(10):
    ax.scatter(np.mean(SR[idx]), np.mean(POD[idx]), color=colors[idx], s=100, label=f'F{idx}')

ax.text(np.mean(SR[0]), np.mean(POD[0]), "F0", fontsize=10, ha='right', va='bottom')
ax.text(np.mean(SR[-1]), np.mean(POD[-1]), "F9", fontsize=10, ha='left', va='bottom')

ax.set_title("Performance Diagram", y=1.08)
ax.set_xlabel("Success Ratio (1-FAR)", fontsize=10)
ax.set_ylabel("Probability of Detection (POD)", fontsize=10)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xticks(np.arange(0, 1.1, step=0.1))
ax.set_yticks(np.arange(0, 1.1, step=0.1))
ax.tick_params(axis="both", which="both", labelsize=10)
ax.minorticks_on()


plt.tight_layout()
plt.show()

