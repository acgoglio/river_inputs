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
# Written: 32/04/2021
#
# This script reads the output (txt format) x_killworth_time_interpolation.exe
# does the daily interpolation from monthly pseudodischarge 
# and builds the NETCDF daily river input file for EAS System
#
#################################################################
#climatological_values=np.array([426.3500,370.3400,383.3800,460.9100,481.9800,589.7000,552.0400,358.0800,280.4800,394.3600,530.1700,557.8900,426.3500,370.3400])
climatological_values=np.array([370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,370.3400,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,383.3800,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,460.9100,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,481.9800,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,589.7000,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,552.0400,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,358.0800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,280.4800,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,394.3600,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,530.1700,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,557.8900,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500,426.3500])
pseudodischarge=np.array([451.2103,356.2527,373.1344,476.3719,461.4091,613.7565,576.7563,338.7299,251.6019,393.1775,544.3704,583.7927,412.5397,348.9618])
timeintoout=np.array([15,45,76,106,135,166,196,227,257,288,319,349,380,410])
f = interpolate.interp1d(timeintoout,pseudodischarge)
xnew = np.arange(32, 396, 1.0)
x_clim=np.arange(1, 366, 1.0)
ynew = f(xnew)
offset=31

print ('xnew:',xnew )
print ('ynew:',ynew )

# Plots Per grid and per part
plotname='comp_py.png'
plt.figure(figsize=(18,12))
plt.rc('font', size=16)
plt.title ('From climatological discharge to daily discharge --- Po dritta')
plt.plot(x_clim,climatological_values,label = 'Climatological values')
plt.plot(timeintoout-offset,pseudodischarge,'o',label = 'Pseudodischarge (Killworth)')
plt.plot(xnew-offset,ynew,label = 'Daily values')
#
plt.grid ()
plt.xlim(1,365)
#plt.axhline(y=0 color='black')
plt.ylabel ('River discharge [kg/m2/s]')
plt.xlabel ('Days of the year')
plt.legend() #bbox_to_anchor=(1.04,1), loc="upper left")
# Save and close 
plt.savefig(plotname)
plt.clf()

#fields=['v','u','z']
#grids=['V','U','T']
#udm=['m/s','m/s','m']
#tidal_comp=['M2','S2','N2','K2','K1','O1','P1','Q1']
#
## Loop on grids <-> input tabs
#for idx_grid,grid in enumerate(grids):
#    print ('I am working on grid: ',grid)
#    # Selection of the field 
#    field=fields[idx_grid]
#    # Units
#    units=udm[idx_grid]
#    print ('I am writing Re and Im part of field: ',field,' [',units,']')
#
#    # Build the tab name
#    intab_name='bdytide_tab_grid'+grid+'.txt'
#    print ('Reading filed values from: ',intab_name )
#
#    # Read the values from the input tab
#    intab=pd.read_csv(intab_name,sep=';',usecols=['LAT','LON','M2_RE','M2_IM','S2_RE','S2_IM','N2_RE','N2_IM','K2_RE','K2_IM','K1_RE','K1_IM','O1_RE','O1_IM','P1_RE','P1_IM','Q1_RE','Q1_IM'])
#
#    # Loop on tidal components <-> output files
#    for t_comp in tidal_comp:
#       print ('I am working on tidal componenent: ',t_comp)
#
#       # Build the nc name
#       outnc_name='mfs_bdytide_'+t_comp+'_grid_'+grid+'.nc'
#       print ('I am writing reslts to outfile: ',outnc_name)
#
#       # Open the nc
#       outnc = NC.Dataset(outnc_name,'a')
#
#       # Read the coordinates  
#       b_lat='nav_lat'
#       b_lon='nav_lon'
#       lat_idx='yb'
#       lon_idx='xb'+grid
#       lons = outnc.variables[b_lon][:,:]
#       lats = outnc.variables[b_lat][:,:]
#       print ('The dimension names in the out file are: ',lat_idx,lon_idx)
#       print ('The coordinate names in the out file are: ',b_lat,b_lon)
#
#       # Create the new fields
#       print ('New fileds storing Re and Im part are: ',field,'1',' and ',field,'2')
#       # RE
#       globals()[field+'1']=outnc.createVariable(field+'1',np.float64,(lat_idx,lon_idx))
#       globals()[field+'1'].units = units
#       globals()[field+'1'].standard_name = t_comp+' '+field+' Real part'
#       # IM
#       globals()[field+'2']=outnc.createVariable(field+'2',np.float64,(lat_idx,lon_idx))
#       globals()[field+'2'].units = units
#       globals()[field+'2'].standard_name = t_comp+' '+field+' Immaginary part'
#   
#       # Loop on bdy points:
#       print ('I am going to write the field along the bdy: len(lons): ',len(lons[0,:]),' len(lats): ',len(lats))
#       idx_bdy_coo=0
#   
#       try:
#          for idx_lon in range (0,len(lons[0,:])):
#              for idx_lat in range (0,len(lats)):
#                  print ('Indexes: ', idx_lon, idx_lat )
#    
#                  # Write values in the arrays
#                  globals()[field+'1'][idx_lat,idx_lon]=intab[t_comp+'_'+'RE'][idx_bdy_coo]
#                  globals()[field+'2'][idx_lat,idx_lon]=intab[t_comp+'_'+'IM'][idx_bdy_coo]
#   
#                  idx_bdy_coo=idx_bdy_coo+1
#   
#   
#          outnc.close()
#
#       except:
#          print ('ERROR..')
#          outnc.close()


#################################################################
