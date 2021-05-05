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
# Written: 05/2021
# Modified: 04/05/2021
#
# Script to substitute EFAS time-series into the river input file 
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
efas_input_path=sys.argv[4]

efas_input_filepre=sys.argv[5]
if efas_input_filepre=='NAN':
   efas_input_filepre=''

efas_input_filepost=sys.argv[6]

# NEMO mesh mask
mod_meshmask=sys.argv[7]

# Csv path/file
csv_infofile=sys.argv[8]
csv_infofile=workdir+'/'+csv_infofile

# Outfile infos 
daily_rivers=sys.argv[9]
runoff_var=sys.argv[10]
pre_runoff_var=sys.argv[11]

# Outfile Dimensions names 
lat_idx=sys.argv[12]
lon_idx=sys.argv[13]
time_idx=sys.argv[14]

########################################################
# DO NOT CHANGE THE CODE BELOW THIS LINE!!!
########################################################

# Open the outfile with climatological values and Po river values and read these
output_daily = NC.Dataset(daily_rivers,'r')
pre_runoff=output_daily.variables[pre_runoff_var][:]

# Inizialize the new field to the daily clim + Po river obs
new_field=[0 for idx in range(0,days_of_year)]
new_field[:]=pre_runoff[:]
new_field=np.array(new_field)

# close 
output_daily.close()


# Open the file to write the EFAS time series
output_daily = NC.Dataset(daily_rivers,'r+') 
# Build the new field
runoff = output_daily.createVariable(runoff_var, 'f4', (time_idx, lat_idx , lon_idx,))
runoff.units = 'kg/m2/seconds'

# Loop on EFAS rivers in csv file
print ('Working on available EFAS rivers..')
# Look for csv and mesmask files
if os.path.exists(csv_infofile) and os.path.exists(mod_meshmask):
      print ('Found mesh_mask and info csv files!')
      # Open the mesh mask file
      model = NC.Dataset(mod_meshmask,'r')
      mod_e1t = model.variables['e1t'][:]
      mod_e2t = model.variables['e2t'][:]
      # Open the csv file
      with open(csv_infofile) as infile:
        # Loop on rivers
        for line in infile:
            if line[0] != '#':
               # If EFAS data are available
               efas_flag=line.split(';')[10]
               # For discharges on single grid point 
               if int(efas_flag) == 1:
                  efas_name=line.split(';')[5]
                  # Idx in MED grid
                  efas_lat_idx=line.split(';')[0]
                  efas_lon_idx=line.split(';')[1]
                  # Idx in EFAS grid
                  efas_lat_efasidx=line.split(';')[11]
                  efas_lon_efasidx=line.split(';')[12]
                  # Build the path/name of the input efas file
                  efas_filetoread=efas_input_path+'/'+efas_input_filepre+efas_name+'_'+efas_lat_efasidx+'_'+efas_lon_efasidx+efas_input_filepost
                  print (efas_name,efas_lat_idx,efas_lon_idx)
                  print (efas_filetoread)
                  if os.path.exists(efas_filetoread):
                     # Inizialize the output arrays
                     dailyvals_fromefas=[0 for idx in range(0,days_of_year)]
                     efas_runoff=[0 for idx in range(0,days_of_year)]
                     # Open efas file and get values
                     efas_tsfile = pd.read_csv(efas_filetoread,sep=' ',comment='#',header=None)
                     in_data = efas_tsfile[0][:]
                     in_values = efas_tsfile[1][:]
                     # Select the year and count the num of values 
                     year_val_num=0
                     for csv_idx in range(0,len(in_data)): 
                         if int(in_data[csv_idx][0:4]) == yeartocompute:
                            dailyvals_fromefas[year_val_num]=in_values[csv_idx]
                            year_val_num=year_val_num+1 
                     # Check the num of values
                     if year_val_num != int(days_of_year):
                        print ('ERROR: missing efas values!!')
                     # From m**3/s to kg/m**2/s 
                     efas_e1t=mod_e1t[0,int(efas_lat_idx),int(efas_lon_idx)]
                     efas_e2t=mod_e2t[0,int(efas_lat_idx),int(efas_lon_idx)]
                     efas_runoff=1000.0*np.array(dailyvals_fromefas)/(float(efas_e1t)*float(efas_e2t))
                     efas_runoff=np.array(efas_runoff)

                     # Build the new field
                     for idx_out in range (0,len(efas_runoff)):
                         new_field[int(idx_out),int(efas_lat_idx),int(efas_lon_idx)]=efas_runoff[int(idx_out)]


                  else:
                     print ('ERROR: efas input file NOT FOUND!!')

               # For discharges on multiple grid points 
               if efas_flag == 2:
                  print ('Discharge on multiple grid points..')
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
oldout=output_daily.variables[pre_runoff_var][:]
newout=output_daily.variables[runoff_var][:]
diff=newout-oldout
std_diff=np.std(diff)
# Build date array
start_date = date(yeartocompute, 1, 1)
end_date = date(yeartocompute+1, 1, 1)-timedelta(days=1)
daterange = pd.date_range(start_date, end_date)

with open(csv_infofile) as infile:
     for line in infile:
       if line[0] != '#':
         river_name=line.split(';')[5]
         river_lat_idx=line.split(';')[0]
         river_lon_idx=line.split(';')[1]
         print ('I am working on ', river_name,river_lat_idx,river_lon_idx)

         # Plot 
         plotname='efas_'+river_name+'_'+str(yeartocompute)+'.png'
         plt.figure(figsize=(18,12))
         plt.rc('font', size=16)
         #
         plt.subplot(2,1,1)
         plt.title ('Climatological river forcing Vs EFAS river forcing --- River: '+river_name+'--- Year: '+str(yeartocompute)) 
         plt.plot(daterange,oldout[:,int(river_lat_idx),int(river_lon_idx)],'-o',label = 'Clim river forcing')
         plt.plot(daterange,newout[:,int(river_lat_idx),int(river_lon_idx)],'-o',label = 'EFAS river forcing')
         plt.grid ()
         plt.ylabel ('River runoff [kg/m2/s]')
         plt.xlabel ('Date')
         plt.legend()
         #
         plt.subplot(2,1,2)
         plt.plot(daterange,diff[:,int(river_lat_idx),int(river_lon_idx)],label = 'EFAS-Clim STD DEV: '+str(std_diff))
         plt.grid ()
         plt.ylabel ('River runoff difference [kg/m2/s]')
         plt.xlabel ('Date')
         plt.legend()
         # Save and close 
         plt.savefig(plotname)
         plt.clf()

# Close the outfile
output_daily.close()

