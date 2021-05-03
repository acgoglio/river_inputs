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
import os
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
# Written: 12/04/2021
#
# This script reads the output (txt format) x_killworth_time_interpolation.exe
# does the daily interpolation from monthly pseudodischarge 
# and builds the NETCDF daily river input file for EAS System
#
#################################################################
# Ini values
climatological_values=np.array([%CLIM_ALL%])
pseudodischarge=np.array([%PSEUDO_ALL%])
timeintoout=np.array([%TIMEINOUT_ALL%])
nov_to_feb=([%NOV_TO_FEB_NUM_OF_DAYS%])
# Read args
# River infos
river_lat=int(sys.argv[1])
river_lon=int(sys.argv[2])
river_name=sys.argv[3]
# Name of the new file
daily_rivers=sys.argv[4]
print ('I am writing the daily runoff to file: ',daily_rivers,'_tmp')
# Year
year2comp=sys.argv[5]
# Field to be read and written
clim_1d_runoff_var=sys.argv[6]
clim_1m_runoff_var=sys.argv[7]
# Outfile Dimensions names 
lat_idx=sys.argv[8]
lon_idx=sys.argv[9]
time_idx=sys.argv[10]

#-------------------------------------
# Time interpolation
f = interpolate.interp1d(timeintoout,pseudodischarge)
xnew = np.arange(nov_to_feb[1], np.sum(nov_to_feb[1:14]), 1.0)
x_clim=np.arange(0, len(climatological_values), 1.0)
ynew = f(xnew)
print('Year len: ',len(ynew))

#--------------------------------------
## Plots
#offset=nov_to_feb[1]
## Plots Per grid and per part
#plotname='killworth_'+str(river_lat)+'_'+str(river_lon)+'_'+river_name+'_'+year2comp+'.png'
#plt.figure(figsize=(18,12))
#plt.rc('font', size=16)
#plt.title ('From climatological discharge to daily discharge --- River: '+river_name+'--- Year: '+year2comp)
#plt.plot(x_clim,climatological_values,label = 'Climatological values')
#plt.plot(timeintoout-offset,pseudodischarge,'o',label = 'Pseudodischarge (Killworth)')
#plt.plot(xnew-offset,ynew,label = 'Daily values')
#plt.grid ()
#plt.xlim(1,len(climatological_values)-1)
#plt.ylabel ('River discharge [kg/m2/s]')
#plt.xlabel ('Days of the year')
#plt.legend() 
## Save and close 
#plt.savefig(plotname)
#plt.clf()
#-------------------------------------
# Write runoff values and name of the river to the new file
# If there is a tmp file open it and read the field
upd_file=daily_rivers+'_upd.nc'
tmp_file=daily_rivers+'_tmp.nc'
if os.path.exists(upd_file):
   upd_daily=NC.Dataset(upd_file,'r')
   upd_runoff=upd_daily.variables[clim_1d_runoff_var][:]
   upd_daily.close()
   # Open the new file template and add the new var
   tmp_daily = NC.Dataset(tmp_file,'r+')
   # Add the new daily clim field
   tmp_runoff = tmp_daily.createVariable(clim_1d_runoff_var, 'f4', (time_idx, lat_idx , lon_idx,))
   tmp_runoff.units = 'kg/m2/seconds'
   # Put the values in the field adding the new river
   tmp_field=upd_runoff
   tmp_field[:,river_lat,river_lon]=ynew[:]
   tmp_runoff[:]=tmp_field[:]
   # close the files
   tmp_daily.close()
# Otherwise (first occurence) copy the monthly clim
else:
   # Read monthly clim
   tmp_daily = NC.Dataset(tmp_file,'r')
   upd_runoff=tmp_daily.variables[clim_1m_runoff_var][:]
   tmp_daily.close()
   # Open the new file template and add the new var
   tmp_daily = NC.Dataset(tmp_file,'r+')
   # Add the new daily clim field
   tmp_runoff = tmp_daily.createVariable(clim_1d_runoff_var, 'f4', (time_idx, lat_idx , lon_idx,))
   tmp_runoff.units = 'kg/m2/seconds'
   # Put the monthly clim values in the field adding the new river
   tmp_field=upd_runoff
   tmp_field[:,river_lat,river_lon]=ynew[:]
   tmp_runoff[:]=tmp_field[:]
   #close the files
   tmp_daily.close()

# TMP
tmp_daily = NC.Dataset(tmp_file,'r')
daily=tmp_daily.variables[clim_1d_runoff_var][:]
monthly=tmp_daily.variables[clim_1m_runoff_var][:]

tmp_daily.close()

#################################################################
