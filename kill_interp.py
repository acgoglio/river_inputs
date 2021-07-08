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
from numpy.linalg import inv
#from operator import itemgetter 
#
# by AC Goglio (CMCC)
# annachiara.goglio@cmcc.it
#
# Written: 12/04/2021
# Last Mod: 05/05/2021
#
# This script reads the output (txt format) x_killworth_time_interpolation.exe
# does the daily interpolation from monthly pseudodischarge 
# and builds the NETCDF daily river input file for EAS System
#
#################################################################
# Ini values:
# Monthly climatology:
monthly_clim_values=np.array(eval('[' + sys.argv[15] + ']'))
# Half month days (dec to jan):
timeintoout=[15,45,76,106,135,166,196,227,257,288,319,349,380,410]
# days per month from Dec to Jan (14 months)
tot_days_per_year=sys.argv[14]
if tot_days_per_year == 366:
   days_per_month=([31,31,29,31,30,31,30,31,31,30,31,30,31,31])
else:
   days_per_month=([31,31,28,31,30,31,30,31,31,30,31,30,31,31])
days_per_month=np.array(days_per_month)
# Read other args:
# River infos
river_lat=int(sys.argv[1])
river_lon=int(sys.argv[2])
river_name=sys.argv[3]
river_num=sys.argv[4]
# Name of the new file
daily_rivers=sys.argv[5]
print ('I am writing the daily runoff to file: ',daily_rivers,'_tmp')
# Year
year2comp=sys.argv[6]
# Field to be read and written
clim_1d_runoff_var=sys.argv[7]
clim_1m_runoff_var=sys.argv[8]
mask_var=sys.argv[9]
name_var=sys.argv[10]
# Outfile Dimensions names 
lat_idx=sys.argv[11]
lon_idx=sys.argv[12]
time_idx=sys.argv[13]
#-------------------------------------
# Pseudodischarge computation
# STEP 1: FROM MONTHLY CLIMATOLOGICAL VALUES TO PSEUDODISCHARGES
#         input: 12 monthly climatological values and array of months lenght
#         output: 12 pseudodischarge values 

# Build the matrix coeff
e=np.zeros(12)
g=np.zeros(12)
f=np.zeros(12)

e[0]=monthly_clim_values[0]/(4.0*(monthly_clim_values[11]+monthly_clim_values[0]))
g[0]=monthly_clim_values[0]/(4.0*(monthly_clim_values[1]+monthly_clim_values[0]))
f[0]=1.0-e[0]-g[0]

for matrix_idx in range(1,11):
    e[matrix_idx]=monthly_clim_values[matrix_idx]/(4.0*(monthly_clim_values[matrix_idx-1]+monthly_clim_values[matrix_idx]))
    g[matrix_idx]=monthly_clim_values[matrix_idx]/(4.0*(monthly_clim_values[matrix_idx+1]+monthly_clim_values[matrix_idx]))
    f[matrix_idx]=1.0-e[matrix_idx]-g[matrix_idx]

e[11]=monthly_clim_values[11]/(4.0*(monthly_clim_values[10]+monthly_clim_values[11]))
g[11]=monthly_clim_values[11]/(4.0*(monthly_clim_values[0]+monthly_clim_values[11]))
f[11]=1.0-e[11]-g[11]

# Define the Matrix
KA=np.zeros((12,12))

for row_idx in range(0,12):
    for col_idx in range(0,12):
        # Diag (f el)
        if row_idx == col_idx :
           KA[row_idx,col_idx]=f[row_idx]
        # g el 
        elif col_idx == (row_idx+1):
           KA[row_idx,col_idx]=g[row_idx]
        elif col_idx == 0 and row_idx == 11 :
           KA[row_idx,col_idx]=g[11]
        # e el
        elif row_idx == (col_idx+1):
           KA[row_idx,col_idx]=e[row_idx]
        elif col_idx == 11 and row_idx == 0 :
           KA[row_idx,col_idx]=e[0]
        else:
           KA[row_idx,col_idx]=0.0

# Invert the matrix
INV_KA=np.zeros((12,12))
INV_KA=inv(np.matrix(KA))

# Compute the pseudodischarges
pseudodischarge=np.zeros(12)
pseudodischarge=np.squeeze(np.array(INV_KA.dot(monthly_clim_values)))

#-------------------------------------
# Time interpolation
# STEP 2: FROM PSEUDODISCHERGE VALUES TO DAILY CLIMATOLOGICAL VALUES 
#         input: 12 pseudodischarge values
#         output 365/366 daily values

# Extend pseudodischarge series to 14 values
ext_pseudodischarge=np.zeros(14)
ext_pseudodischarge[0]=pseudodischarge[11]
for old_arr in range(0,12):
    ext_pseudodischarge[old_arr+1]=pseudodischarge[old_arr]
ext_pseudodischarge[13]=pseudodischarge[0]

# Time interpolation
f = interpolate.interp1d(timeintoout,ext_pseudodischarge)
xnew = np.arange(days_per_month[0], np.sum(days_per_month[0:13]), 1.0)
ynew = f(xnew)
#xnew = np.arange(nov_to_feb[1], np.sum(nov_to_feb[1:14]), 1.0)
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
   upd_mask=upd_daily.variables[mask_var][:]
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
   #
   # Add the river num or name new var
   tmp_name = tmp_daily.createVariable(name_var, 'f4', (time_idx, lat_idx , lon_idx,))
   tmp_name.units = 'river_num'
   # Put the name of the river in the new field
   tmp_field2=upd_mask
   tmp_field2[:,river_lat,river_lon]=int(river_num)
   tmp_name[:]=tmp_field2[:]
   #
   # close the files
   tmp_daily.close()

# Otherwise (first occurence) copy the monthly clim
else:
   # Read monthly clim
   tmp_daily = NC.Dataset(tmp_file,'r')
   upd_runoff=tmp_daily.variables[clim_1m_runoff_var][:]
   upd_mask=tmp_daily.variables[mask_var][:]
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
   #
   # Add the river name new var
   tmp_name = tmp_daily.createVariable(name_var, 'f4', (time_idx, lat_idx , lon_idx,))
   tmp_name.units = 'river_num'
   # Put the name of the river in the new field
   tmp_field2=upd_mask
   tmp_field2[:,river_lat,river_lon]=int(river_num)
   tmp_name[:]=tmp_field2[:]
   #
   #close the files
   tmp_daily.close()

#################################################################
