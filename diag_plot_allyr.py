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
import matplotlib.dates as mdates # To plot dates
#
#
# by AC Goglio (CMCC)
# annachiara.goglio@cmcc.it
#
# Written: 04/2021
# Modified: 20/05/2021
#
##################################################################
start_year=int(sys.argv[1])
end_year=int(sys.argv[2])

# Static vars
workdir='/work/oda/ag15419/tmp/river_inputs/plots4slides_efas/'
daily_rivers_path='/work/oda/ag15419/PHYSW24_DATA/RIVERS/NEMO_DATA0_EAS6_PO/'
daily_rivers_path2='/work/oda/ag15419/PHYSW24_DATA/RIVERS/NEMO_DATA0_EAS6_EFAS/'
clim_1m_runoff_var='clim_monthly_runoff'
runoff_var='sorunoff'
csv_infofile='rivers_info_v2.csv'

# Loop on yearly files:
for yeartocompute in range(start_year,end_year+1):
   daily_rivers='runoff_1d_nomask_y'+str(yeartocompute)+'.nc' 
   daily_rivers2='runoff_1d_nomask_y'+str(yeartocompute)+'.nc'
   # ------------------------------------
   # Check the whole outfile
   # ------------------------------------
   print ('I am going to plot the diagnostic plots to validate the outfile: ',daily_rivers)
   # Open the outfile 
   output_daily = NC.Dataset(daily_rivers_path+daily_rivers,'r')
   output_daily2 = NC.Dataset(daily_rivers_path2+daily_rivers2,'r')

   if yeartocompute == start_year:
      oldout=output_daily.variables[clim_1m_runoff_var][:,:,:]
      newout=output_daily.variables[runoff_var][:,:,:]
      newout2=output_daily2.variables[runoff_var][:,:,:]
   else:
      oldout=np.append(oldout,output_daily.variables[clim_1m_runoff_var][:,:,:], axis=0)
      newout=np.append(newout,output_daily.variables[runoff_var][:,:,:], axis=0)
      newout2=np.append(newout2,output_daily2.variables[runoff_var][:,:,:], axis=0)

   # Close the outfile
   output_daily.close()
   output_daily2.close()

print ('Prova post 1',oldout.shape)
oldout=np.array(oldout)
newout=np.array(newout)
newout2=np.array(newout2)
print ('Prova post 2',oldout.shape)

# choose the dates
plotstart_date = date(int(start_year), 1, 1)
plotend_date = date(int(end_year), 12, 31)
plotdaterange = pd.date_range(plotstart_date, plotend_date)


# Open the NEMO outfile
# MODEL DATASETS
mod1_path='/work/oda/ag15419/arc_link/eas6_drpo/output/'
mod2_path=' /work/oda/ag15419/arc_link/eas6_drpo_ctrl/output/'
mod3_path='/work/oda/ag15419/arc_link/eas6_efas/output/'
#
mod1_prename1='assw_drpo2_1d_'
mod1_prename2='assw_drpo2_1d_'
mod1_prename3='assw_drpo3_1d_'
mod1_prename4='assw_drpo4_1d_'
mod2_prename1='mfs1_v1_1d_'
mod2_prename2='mfs2_1d_'
mod3_prename='assw_efas_1d_'
#
mod1_lab='assw_drpo'
mod2_lab='assw_ctrl'
mod3_label='assw_efas'
#
mod_field = 'runoff'
grid= 'T'
var_mod='sorunoff'
var_units='Kg/m2/s'

# Loop on dates
field1=[]
field2=[]
field3=[]
daterange = pd.date_range(plotstart_date, plotend_date)
for numofdays,date_idx in enumerate(daterange):
   year=date_idx.strftime("%Y").zfill(2)
   month=date_idx.strftime("%m").zfill(2)
   day=date_idx.strftime("%d").zfill(2)

   # Open the field and, if required, compute the diff

   # Set the file prename
   if year+month == '201701':
      mod1_prename=mod1_prename1
   elif year == '2017':
      mod1_prename=mod1_prename2
   elif year+month == '202001' or year == '2018' or year == '2019':
      mod1_prename=mod1_prename3
   else:
      mod1_prename=mod1_prename4

   # Set the file prename
   if year == '2020':
     mod2_prename=mod2_prename2
   else:
     mod2_prename=mod2_prename1


   mod1_file=mod1_path+'/'+year+month+'/'+mod1_prename+year+month+day+'_grid_'+grid+'.nc'
   mod2_file=mod2_path+'/'+year+month+'/'+mod2_prename+year+month+day+'_grid_'+grid+'.nc'
   mod3_file=mod3_path+'/'+year+month+'/'+mod3_prename+year+month+day+'_grid_'+grid+'.nc'

   model1 = NC.Dataset(mod1_file,'r')
   model2 = NC.Dataset(mod2_file,'r')
   model3 = NC.Dataset(mod3_file,'r')

   field1.append(model1.variables[var_mod][:,:,:])
   field2.append(model2.variables[var_mod][:,:,:])
   field3.append(model3.variables[var_mod][:,:,:])  

print('Num of days: ',numofdays)

field1=np.array(field1)
field2=np.array(field2)
field3=np.array(field3)

with open(csv_infofile) as infile:
     for line in infile:
       if line[0] != '#':
         river_name=line.split(';')[5]
         river_lat_idx=line.split(';')[0]
         river_lon_idx=line.split(';')[1]
         print ('I am working on ', river_name,river_lat_idx,river_lon_idx)
         
         # Plot 
         plotname=workdir+'inout_'+river_name+'_'+str(start_year)+'-'+str(end_year)+'.png'
         plt.figure(figsize=(18,12))
         plt.rc('font', size=14)
         plt.title ('Old river forcing Vs New river forcing --- River: '+river_name+'--- Period: '+str(start_year)+'-'+str(end_year))
         # 
         plt.xticks(rotation=45)
         #
         plt.plot(plotdaterange,oldout[0:numofdays+1,int(river_lat_idx),int(river_lon_idx)],label = 'Climatology')
         plt.plot(plotdaterange,newout[0:numofdays+1,int(river_lat_idx),int(river_lon_idx)],label = 'Obs')
         plt.plot(plotdaterange,newout2[0:numofdays+1,int(river_lat_idx),int(river_lon_idx)],label = 'EFAS Model')
         plt.plot(plotdaterange,np.squeeze(field1[:,0,int(river_lat_idx),int(river_lon_idx)]),label = 'sorunoff assw_drpo')
         plt.plot(plotdaterange,np.squeeze(field2[:,0,int(river_lat_idx),int(river_lon_idx)]),label = 'sorunoff assw_ctrl')
         plt.plot(plotdaterange,np.squeeze(field3[:,0,int(river_lat_idx),int(river_lon_idx)]),label = 'sorunoff assw_efas')
         plt.grid ()
         plt.ylabel ('River runoff [kg/m2/s]')
         plt.xlabel ('Date')
         plt.legend()
         # Save and close 
         plt.savefig(plotname)
         plt.clf()


