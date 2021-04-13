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
climatological_values=np.array([%CLIM_ALL%])
pseudodischarge=np.array([%PSEUDO_ALL%])
timeintoout=np.array([%TIMEINOUT_ALL%])
nov_to_feb=([%NOV_TO_FEB_NUM_OF_DAYS%])
river_name=sys.argv[1]
year2comp=sys.argv[2]
#
# Time interpolation
f = interpolate.interp1d(timeintoout,pseudodischarge)
xnew = np.arange(nov_to_feb[1]+1, np.sum(nov_to_feb[1:14]), 1.0)
x_clim=np.arange(1, len(climatological_values), 1.0)
ynew = f(xnew)

# Plots
offset=nov_to_feb[1]

# Plots Per grid and per part
plotname='killworth_'+river_name+'.png'
plt.figure(figsize=(18,12))
plt.rc('font', size=16)
plt.title ('From climatological discharge to daily discharge --- River: '+river_name+'--- Year: '+year2comp)
plt.plot(x_clim,climatological_values[0:-1],label = 'Climatological values')
plt.plot(timeintoout-offset,pseudodischarge,'o',label = 'Pseudodischarge (Killworth)')
plt.plot(xnew-offset,ynew,label = 'Daily values')
#
plt.grid ()
#plt.xlim(1,len(climatological_values)-1)
plt.ylabel ('River discharge [kg/m2/s]')
plt.xlabel ('Days of the year')
plt.legend() 
# Save and close 
plt.savefig(plotname)
plt.clf()

#################################################################
