# imports
import matplotlib.pyplot as plt
import matplotlib as mpl # Palettes
import numpy as np
import netCDF4 as NC
import os
import sys
import warnings
#
warnings.filterwarnings("ignore") # Avoid warnings
#
from scipy.optimize import curve_fit
from scipy import stats
import collections
import pandas as pd
import csv
import math
import datetime
from datetime import date, timedelta
from datetime import datetime
from operator import itemgetter 
import plotly
from plotly import graph_objects as go # for bar plot
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import LogNorm
from operator import itemgetter # to order lists
from statsmodels.distributions.empirical_distribution import ECDF # empirical distribution functions
import re # grep in python
#
#
# by AC Goglio (CMCC)
# annachiara.goglio@cmcc.it
#
# Written: 04/2021
# Modified: 26/04/2021
#
# Script to fit and pre-process Po river data from ARPAE 30 min data
#
#################################################################
# The user should modify the following lines to set his run
#################################################################
# General run parameters:
#---------------------
# Work dir path:
# WARNING: the inputs must be here, the outputs will be moved to subdirs   
workdir=sys.argv[1]

# Year infos
yeartocompute=int(sys.argv[2])
days_of_year=int(sys.argv[3])

# input files infos:
arpae_input_path=sys.argv[4]

arpae_input_filepre=sys.argv[5]
if arpae_input_filepre=='NAN':
   arpae_input_filepre=''

arpae_input_filepost=sys.argv[6]

arpae_input_varcode=int(sys.argv[7])
arpae_input_daily=sys.argv[8]

# NEMO mesh mask
mod_meshmask=sys.argv[9]

# Csv path/file
csv_infofile=sys.argv[10]
csv_infofile=workdir+'/'+csv_infofile
# River prename (in csv file)
river_prename=sys.argv[11]

# Outfile infos 
daily_rivers=sys.argv[12]
runoff_var=sys.argv[13]
clim_1m_runoff_var=sys.argv[14]
clim_1d_runoff_var=sys.argv[15]

# Outfile Dimensions names 
lat_idx=sys.argv[16]
lon_idx=sys.argv[17]
time_idx=sys.argv[18]

########################################################
# DO NOT CHANGE THE CODE BELOW THIS LINE!!!
########################################################
# --------------------------
# Build the daily mean array
# -------------------------
# Inizialize the output array
dailyvals_fromobs=[0 for idx in range(0,days_of_year)]

# Loop on days of the year (to be searched and read from obs)
start_date = date(yeartocompute, 1, 1)
end_date = date(yeartocompute+1, 1, 1)-timedelta(days=1)
daterange = pd.date_range(start_date, end_date)
for idx_outarr,idx_date in enumerate(daterange):
    found_num=0 # Num of 30 min values found per day
    found_val=[] # Array to store available obs per day
    #
    idx_year=idx_date.strftime("%Y").zfill(2)
    idx_month=idx_date.strftime("%m").zfill(2)
    idx_day=idx_date.strftime("%d").zfill(2)
    print ('I am working on date: ',idx_year,idx_month,idx_day)
    # Loop on 30 min scad in the input files
    start_dayhour=datetime(int(idx_year),int(idx_month),int(idx_day), 0, 0, 0)
    for idx_datetime in (start_dayhour + timedelta(minutes=30*it) for it in range(0,48)):
        found_scad=0 # Flag to know if the line was found
        date_string=idx_datetime.strftime("%Y/%m/%d:%H:%M")

        # Look for the string in the first file
        arpae_input=arpae_input_path+'/'+str(idx_year)+'/'+str(idx_month)+'/'+arpae_input_filepre+str(idx_year)+str(idx_month)+str(idx_day)+arpae_input_filepost
        if os.path.exists(arpae_input): 
           with open(arpae_input) as origin_file:
             for line in origin_file:
                 line_flag = re.findall(r"{}".format(date_string), line)
                 if line_flag:
                    var_code = line.split(',')[2]
                    # Select the field
                    if var_code == str(arpae_input_varcode):
                       found_scad=found_scad+1
                       found_val.append(line.split(',')[3])

        # Look for the file in the next day (if not found in the current one)
        if found_scad == 0:
           next_day=idx_date+timedelta(days=1)
           next_dayday=next_day.strftime("%d").zfill(2)
           next_daymonth=next_day.strftime("%m").zfill(2)
           next_dayyear=next_day.strftime("%Y").zfill(2)
           arpae_input=arpae_input_path+'/'+str(next_dayyear)+'/'+str(next_daymonth)+'/'+arpae_input_filepre+str(next_dayyear)+str(next_daymonth)+str(next_dayday)+arpae_input_filepost
           if os.path.exists(arpae_input):
              with open(arpae_input) as origin_file:
                for line in origin_file:
                    line_flag = re.findall(r"{}".format(date_string), line)
                    if line_flag:
                       var_code = line.split(',')[2]
                       # Select the field
                       if var_code == str(arpae_input_varcode):
                          found_scad=found_scad+1
                          found_val.append(line.split(',')[3])

        # Look for the file in the following day (if not found in the current one and in the next one)
        if found_scad == 0:
           next_day=idx_date+timedelta(days=2)
           next_dayday=next_day.strftime("%d").zfill(2)
           next_daymonth=next_day.strftime("%m").zfill(2)
           next_dayyear=next_day.strftime("%Y").zfill(2)
           arpae_input=arpae_input_path+'/'+str(next_dayyear)+'/'+str(next_daymonth)+'/'+arpae_input_filepre+str(next_dayyear)+str(next_daymonth)+str(next_dayday)+arpae_input_filepost
           if os.path.exists(arpae_input):
              with open(arpae_input) as origin_file:
                for line in origin_file:
                    line_flag = re.findall(r"{}".format(date_string), line)
                    if line_flag:
                       var_code = line.split(',')[2]
                       # Select the field
                       if var_code == str(arpae_input_varcode):
                          found_scad=found_scad+1
                          found_val.append(line.split(',')[3])
 
        # Update the num of 30 min obs per day
        if found_scad != 0:
           found_num=found_num+1

    # Check if there is at least one obs value per day
    if found_num != 0:
       print('OBS per day found in 30m dataset: ',found_num)
       # Compute the DAILY MEAN over the available obs values
       daily_mean=round(np.mean(np.array(found_val).astype(np.float)),2)
       #print ('I am computing the daily mean',found_val,daily_mean)
       # Write the daily mean to the out array
       dailyvals_fromobs[idx_outarr]=daily_mean

    # If there are no 30 min obs look for values in the daily dataset downloaded from https://simc.arpae.it/dext3r/ (Pontelagoscuro)
    else:
       print('Value from daily dataset')
       if os.path.exists(arpae_input_daily):       
          next_date=idx_date+timedelta(days=1)
          next_day=next_date.strftime("%d").zfill(2)
          next_daymonth=next_date.strftime("%m").zfill(2)
          next_dayyear=next_date.strftime("%Y").zfill(2)
          date_string1=idx_year+'-'+idx_month+'-'+idx_day 
          date_string2=next_dayyear+'-'+next_daymonth+'-'+next_day
          # look for the value 
          with open(arpae_input_daily) as origin_dailyfile:
                for line in origin_dailyfile:
                    line_flag1 = re.findall(r"{}".format(date_string1),line)
                    line_flag2 = re.findall(r"{}".format(date_string2),line)
                    if line_flag1 and line_flag2:
                       valtowrite=line.split(',')[2]
                       try:
                         dailyvals_fromobs[idx_outarr]=round(float(valtowrite),2)
                       except:
                         print ('OBS not found: value from climatology!')
                          

# Open the outfile with climatological values and read these
output_daily = NC.Dataset(daily_rivers,'r')
clim_1d_runoff=output_daily.variables[clim_1d_runoff_var][:]
clim_1m_runoff=output_daily.variables[clim_1m_runoff_var][:]

# Inizialize the new field to the daily clim
new_field=clim_1d_runoff[:]

# close 
output_daily.close()

# Open the file to write the Po obs 
output_daily = NC.Dataset(daily_rivers,'r+') 
# Build the new field:/new_f
runoff = output_daily.createVariable(runoff_var, 'f4', (time_idx, lat_idx , lon_idx,))
runoff.units = 'kg/m2/seconds'

# Loop on Po branches in csv file
print ('Working on sigle Po river branches..')
# Read the perc per branch and split the whole discharge among these
if os.path.exists(csv_infofile) and os.path.exists(mod_meshmask):
      print ('Found mesh_mask and info csv files!')
      # Open the mesh mask file
      model = NC.Dataset(mod_meshmask,'r')
      mod_e1t = model.variables['e1t'][:]
      mod_e2t = model.variables['e2t'][:]
      # Open the csv file
      with open(csv_infofile) as infile:
        for line in infile:
            line_flag = re.findall(r"{}".format(river_prename),line)
            if line_flag:
               branch_name=line.split(';')[5]
               branch_lat_idx=line.split(';')[0]
               branch_lon_idx=line.split(';')[1]
               branch_perc=line.split(';')[9]
               print (branch_name,branch_lat_idx,branch_lon_idx,branch_perc)

               # split the discharge 
               branch_fromobs=np.array(dailyvals_fromobs)*(float(branch_perc)/100.0)

               # From m**3/s to kg/m**2/s 
               branch_e1t=mod_e1t[0,int(branch_lat_idx),int(branch_lon_idx)]
               branch_e2t=mod_e2t[0,int(branch_lat_idx),int(branch_lon_idx)]
               branch_runoff=np.where(branch_fromobs!=0.000000000,1000.0*branch_fromobs/(branch_e1t*branch_e2t),'nan')

               # TMP: and store the daily and monthly clim values for the plot!
               clim_1d_runoff_branch=clim_1d_runoff[:,int(branch_lat_idx),int(branch_lon_idx)]
               clim_1m_runoff_branch=clim_1m_runoff[:,int(branch_lat_idx),int(branch_lon_idx)] 

               # Plot 
               plotname='obsclim_'+branch_name+'_'+str(yeartocompute)+'.png'
               plt.figure(figsize=(18,12))
               plt.rc('font', size=16)
               plt.title ('Climatological values Vs Obs --- River: '+branch_name+'--- Year: '+str(yeartocompute))
               # 
               plt.plot(daterange,clim_1m_runoff_branch[:],label = 'Climatological monthly values')
               plt.plot(daterange,clim_1d_runoff_branch[:],label = 'Killworth daily values')

               # Build the new field
               # If not nan modify the field in the netcdf file and close it
               for idx_out in range (0,len(branch_runoff)):
                  if branch_runoff[idx_out] != 'nan':
                     new_field[idx_out,int(branch_lat_idx),int(branch_lon_idx)]=branch_runoff[idx_out]

               # Add the new field to the plot
               plt.plot(daterange,new_field[:,int(branch_lat_idx),int(branch_lon_idx)],label = 'OBS/Daily clim values')
               plt.grid ()
               plt.ylabel ('River runoff [kg/m2/s]')
               plt.xlabel ('Date')
               plt.legend()
               # Save and close 
               plt.savefig(plotname)
               plt.clf()
else:
   print ('ERROR: Check mesh_mask and info csv files! ')

# Write the new field to the netCDF
runoff[:]=new_field[:]
# Close the mod outfile
output_daily.close()
#
# Validation check of the outfile
print ('I am going to plot the diagnostic plots to validate the outfile: ',daily_rivers)
# Open the outfile 
output_daily = NC.Dataset(daily_rivers,'r')
oldout=output_daily.variables[clim_1m_runoff_var][:]
newout=output_daily.variables[runoff_var][:]

with open(csv_infofile) as infile:
     for line in infile:
       if line[0] != '#':
         river_name=line.split(';')[5]
         river_lat_idx=line.split(';')[0]
         river_lon_idx=line.split(';')[1]
         print ('I am working on ', river_name,river_lat_idx,river_lon_idx)


         # Plot 
         plotname='diagplot_'+river_name+'_'+str(yeartocompute)+'.png'
         plt.figure(figsize=(18,12))
         plt.rc('font', size=16)
         plt.title ('Old river forcing Vs New river forcing --- River: '+river_name+'--- Year: '+str(yeartocompute))
         # 
         plt.plot(daterange,oldout[:,int(river_lat_idx),int(river_lon_idx)],label = 'Old river forcing')
         plt.plot(daterange,newout[:,int(river_lat_idx),int(river_lon_idx)],'-o',label = 'New river forcing')
         plt.grid ()
         plt.ylabel ('River runoff [kg/m2/s]')
         plt.xlabel ('Date')
         plt.legend()
         # Save and close 
         plt.savefig(plotname)
         plt.clf()

# Close the outfile
output_daily.close()

