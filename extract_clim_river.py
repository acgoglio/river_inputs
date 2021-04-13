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
#
# This script reads the EAS system monthly river file
# and extracts the climatological values to txt files
#
#################################################################
# Read line arg (name of input file)

monthly_rivers=sys.argv[1]
print ('Input file is: ',monthly_rivers)

# Open the file and read the vars
input_monthly = NC.Dataset(monthly_rivers,'r')
# Read the grid
lat_2d='nav_lat'
lon_2d='nav_lon'
lons = input_monthly.variables[lon_2d][:]
lats = input_monthly.variables[lat_2d][:]
lat_idx='y'
lon_idx='x'
# Read the mask and the runoff values 
mask_var='river_msk'
mask = input_monthly.variables[mask_var][:]
#
runoff_var='sorunoff'
runoff = input_monthly.variables[runoff_var][:]
# Loop on lat and lon to find and extract river climatological monthly values (1 ts for each grid point)
print ('len(lons): ',len(lons[1]),' len(lats): ',len(lats[:,0]))
river_num=0
for idx_lon in range (0,len(lons[0])):
    for idx_lat in range (0,len(lats)):
        print ('Indexes: ', idx_lon, idx_lat )

        # Read the river_mask value
        mask_val = mask[0,idx_lat,idx_lon]
        if mask_val == 1:
           river_num=river_num=+1
           print ('Found river ',river_num) 
           # build the climatological file name
           clim_filename='clim_'+str(idx_lon)+'_'+str(idx_lat)+'.txt'
           # Read 12 monthly clim values 
           runoff_clim=runoff[:,idx_lat,idx_lon]
           #runoff_clim_new=runoff_clim*10000.0
           runoff_clim.tolist()
           # Write values to clim file
           clim_file = open(clim_filename,"w")
           print(*runoff_clim,sep = " ",file=clim_file)
           clim_file.close()
      
#################################################################
