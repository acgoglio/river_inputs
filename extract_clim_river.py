#
# imports
import sys
import warnings
#
warnings.filterwarnings("ignore") # Avoid warnings
#
import matplotlib.pyplot as plt
import numpy as np
import netCDF4 as NC
import shutil
#from scipy.optimize import curve_fit
from scipy import stats
import collections
import pandas as pd
import csv
import math
from datetime import datetime
from scipy import interpolate
#from operator import itemgetter 
#
# by AC Goglio (CMCC)
# annachiara.goglio@cmcc.it
#
# Written: 13/04/2021
# Last mod: 05/05/2021
#
# This script reads the EAS system monthly river file
# and extracts the climatological values to txt files
#
######################## DO NOT CHANGE THE CODE BENEATH THIS LINE ###########
# Read line args (name of input and output files)
monthly_rivers=sys.argv[1]
print ('Input file is: ',monthly_rivers)

daily_rivers=sys.argv[2]
print ('Output file is: ',daily_rivers)

# days in the requested year
days_in_year=sys.argv[3]
# days per month
days_per_month=sys.argv[14]
days_per_month=eval('[' + days_per_month + ']')
days_per_month=days_per_month[2:14] 

# I/O nc dimensions and variables names
# Dimensions names 
lat_idx=sys.argv[4]
lon_idx=sys.argv[5]
time_idx=sys.argv[6]
# Var names
lat_2d=sys.argv[7]
lon_2d=sys.argv[8]
mask_var=sys.argv[9]
runoff_var=sys.argv[10]
salinity_var=sys.argv[11]
clim_1m_runoff_var=sys.argv[12]
river_name=sys.argv[13]

# Open the file and read the vars
input_monthly = NC.Dataset(monthly_rivers,'r')
#Read variables 
# Read the grid
lons = input_monthly.variables[lon_2d][:]
lats = input_monthly.variables[lat_2d][:]
# Read the mask 
mask = input_monthly.variables[mask_var][:]
# Read the runoff values 
runoff = input_monthly.variables[runoff_var][:]
# Read the salinity 
salinity = input_monthly.variables[salinity_var][:]

# Loop on lat and lon to find and extract river climatological monthly values (1 ts for each grid point)
print ('len(lons): ',len(lons[1]),' len(lats): ',len(lats[:,0]))
river_num=0
for idx_lon in range (0,len(lons[0])):
    for idx_lat in range (0,len(lats)):

        # Read the river_mask value
        mask_val = mask[0,idx_lat,idx_lon]
        if mask_val == 1:
           river_num=river_num+1
           print ('Found river ',river_num)
           print ('River Indexes: ', idx_lon, idx_lat ) 
           # build the climatological file name
           clim_filename='clim_'+str(idx_lat)+'_'+str(idx_lon)+'.txt'
           # Read 12 monthly clim values 
           runoff_clim=runoff[:,idx_lat,idx_lon]
           #runoff_clim_new=runoff_clim*10000.0
           runoff_clim.tolist()
           # Write values to clim file
           clim_file = open(clim_filename,"w")
           print(*runoff_clim,sep = " ",file=clim_file)
           clim_file.close()
      
# Build the new file
fn = daily_rivers
ds = NC.Dataset(fn, 'w', format='NETCDF4')
# New dimensions
time_new = ds.createDimension(time_idx, None)
lat_new = ds.createDimension(lat_idx, len(lats[:,0]))
lon_new = ds.createDimension(lon_idx, len(lons[1]))
# New variables
lats_new = ds.createVariable(lat_2d, 'f4', (lat_idx,lon_idx,))
lons_new = ds.createVariable(lon_2d, 'f4', (lat_idx,lon_idx,))
times_new = ds.createVariable(time_idx, 'f4', (time_idx,))

lats_new[:,:] = lats[:,:]
lons_new[:,:] = lons[:,:]

clim_runoff = ds.createVariable(clim_1m_runoff_var, 'f4', (time_idx, lat_idx , lon_idx,))
clim_runoff.units = 'kg/m2/seconds'

salinity_new = ds.createVariable(salinity_var, 'f4', (time_idx, lat_idx , lon_idx,))
salinity_new.units = 'PSU'

mask_new = ds.createVariable(mask_var, 'f4', (time_idx, lat_idx , lon_idx,))
mask_new.units = ' 1 - 0 '

#name_new = ds.createVariable(river_name, 'S1', (time_idx, lat_idx , lon_idx,))

for day_step in range (0,int(days_in_year)):
    times_new[day_step]=day_step+1
    mask_new[day_step,:,:]=mask[0,:,:]

day_whole_step=0
month_whole_step=0
for monthlen_step in days_per_month:
    for day_step in range (0,int(monthlen_step)):
        clim_runoff[day_whole_step,:,:]=runoff[month_whole_step,:,:]
        salinity_new[day_whole_step,:,:]=salinity[month_whole_step,:,:]
        day_whole_step=day_whole_step+1
    month_whole_step=month_whole_step+1

ds.close()
#################################################################
