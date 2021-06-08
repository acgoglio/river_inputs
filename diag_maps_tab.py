#
# Script for HARMONIC ANALYSIS AND POST_PROC
#
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
#
# Import ttide code for Forman harmonic analysis
#import ttide
# Import TPXO and Literature values
#from lit_tpxo import *
#
#
# by AC Goglio (CMCC)
# annachiara.goglio@cmcc.it
#
# Written: 06/2019
# Modified: 11/05/2021
#
# Script to fit and plot the harmonic analisi reults wrt tide gauges data, tpxo model and literature values
#
#################################################################
# The user should modify the following lines to set his run
#################################################################
# General run parameters:
#---------------------
# Work dir path:
workdir= '/work/oda/ag15419/tmp/eas6_efas/maps_ss/' 
subworkdir_name='maps_efas'
# input files:
rivers_coo_file ='/users_home/oda/ag15419/river_inputs/Killworth/rivers_info_v2.csv'
model_bathy='/work/oda/ag15419/PHYSW24_DATA/TIDES/DATA0/bathy_meter.nc'
model_meshmask='/work/oda/ag15419/PHYSW24_DATA/TIDES/DATA0/mesh_mask.nc'
# Area and experiment flags
adriatico_flag=0 # 1 = Po river; 0 = all Med; 2= North Adriatic 
exp=1 # 1 = daily clim and Po obs ; 2 = EFAS daily mod  
#
ini_date='20200101'
last_date='20201231'
delta_date='10'

# Parameter setting
#--------------------
# MODEL DATASETS
mod1_path='/work/oda/ag15419/arc_link/eas6_efas/output/'
mod2_path=' /work/oda/ag15419/arc_link/eas6_drpo_ctrl/output/'
#
mod1_prename1='assw_efas_1d_'
mod1_prename2=mod1_prename1
mod1_prename3=mod1_prename1
mod1_prename4=mod1_prename1
#mod1_prename1='assw_drpo_1d_'
#mod1_prename2='assw_drpo2_1d_'
#mod1_prename3='assw_drpo3_1d_'
#mod1_prename4='assw_drpo4_1d_'

mod2_prename='mfs2_1d_' #'mfs1_v1_1d_'
#
mod1_lab='assw_efas'
mod2_lab='assw_ctrl'

# Field to be analized and type 
mod_field='S'
diff_flag=1

if mod_field == 'S':
   # Grid 
   grid= 'T'
   # field name:
   var_mod='vosaline'
   var_units='PSU'
   var_time_step=0
   var_lev=0 # 0[1m],10[30m],30[150m]

   if var_lev==0:
      var_lev_lab='sfc'
      if adriatico_flag==0:
         var_max=1.0
         var_min=-1.0
      elif adriatico_flag==1:
        var_max=3.0
        var_min=-3.0
      elif adriatico_flag==2:
        var_max=2.0
        var_min=-2.0

   elif var_lev==10:
      var_lev_lab='30m'
      if adriatico_flag==0:
         var_max=0.2
         var_min=-0.2
      elif adriatico_flag==1:
        var_max=0.3
        var_min=-0.3
      elif adriatico_flag==2:
        var_max=0.3
        var_min=-0.3

   elif var_lev==30:
      var_lev_lab='150m'
      if adriatico_flag==0:
         var_max=0.2
         var_min=-0.2
      elif adriatico_flag==1:
        var_max=0.3
        var_min=-0.3
      elif adriatico_flag==2:
        var_max=0.3
        var_min=-0.3

   if diff_flag==1:
      cmap='BrBG'

elif mod_field == 'runoff':
   # Grid 
   grid= 'T'
   # field name:
   var_mod='sorunoff'
   var_units='Kg/m2/s'
   var_time_step=0
   var_lev=0
   var_max=0.01
   var_min=-0.01
   if diff_flag==1:
      cmap='PuOr'

elif mod_field == 'T':
   # Grid 
   grid= 'T'
   # field name:
   var_mod='votemper'
   var_units='deg C'
   var_time_step=0
   var_lev=0
   var_lev_lab='sfc'
   if diff_flag==1:
      cmap='bwr'
   if adriatico_flag!=0:
      var_max=0.4
      var_min=-0.4
   else:
      var_max=0.4
      var_min=-0.4


# Bathymetry and mesh_mask fields
var_bathy='Bathymetry'
var_mesh='tmask'
var_lat='nav_lat'
var_lon='nav_lon'

########################################################
# DO NOT CHANGE THE CODE BELOW THIS LINE!!!
########################################################
# Loop on dates

start_date = date(int(ini_date[0:4]),int(ini_date[4:6]),int(ini_date[6:8]))
end_date = date(int(last_date[0:4]),int(last_date[4:6]),int(last_date[6:8]))
#step=timedelta(days=int(delta_date))
daterange = pd.date_range(start_date, end_date)
for date_idx in daterange:
   print ('I am working on date ',date_idx)
   year=date_idx.strftime("%Y").zfill(2)
   month=date_idx.strftime("%m").zfill(2)
   day=date_idx.strftime("%d").zfill(2)

   # Open the field and, if required, compute the diff

   if year+month == '201701':
      mod1_prename=mod1_prename1
   elif year == 2017:
      mod1_prename=mod1_prename2
   elif year+month == '202001' or year == 2018 or year == 2019:
      mod1_prename=mod1_prename3
   else:
      mod1_prename=mod1_prename4

   mod1_file=mod1_path+'/'+year+month+'/'+mod1_prename+year+month+day+'_grid_'+grid+'.nc'
   mod2_file=mod2_path+'/'+year+month+'/'+mod2_prename+year+month+day+'_grid_'+grid+'.nc'
   
   model1 = NC.Dataset(mod1_file,'r')
   model2 = NC.Dataset(mod2_file,'r')
   
   try:
      field1=model1.variables[var_mod][var_time_step,var_lev,:,:]
      field2=model2.variables[var_mod][var_time_step,var_lev,:,:]
   except:
      field1=model1.variables[var_mod][var_time_step,:,:]
      field2=model2.variables[var_mod][var_time_step,:,:]
   
   if diff_flag == 1:
      field_plot=field1-field2
      field_lab=var_mod+'('+var_lev_lab+')'+' Diff '+'('+mod1_lab+'-'+mod2_lab+')'+'--- '+year+month+day
      bar_label_string=var_mod+' Diff '+'['+var_units+']'
   else:
     field_plot=field1
     field_lab=var_mod+mod1_lab+'('+var_lev_lab+')'+' --- '+year+month+day
     bar_label_string=var_mod+'['+var_units+']'   

   # Open bathymetry and mes_mask
   model3 = NC.Dataset(model_bathy,'r')
   vals_bathy=model3.variables[var_bathy][:]
   lons = model3.variables[var_lon][:]
   lats = model3.variables[var_lat][:]
   #
   model4 = NC.Dataset(model_meshmask,'r')
   landmask_mesh=model4.variables[var_mesh][0,var_lev,:,:]

   # Buil the dir and move in it
   workdir_path = workdir+'/'+subworkdir_name+'/'
   try:
       os.stat(workdir_path)
   except:
       os.mkdir(workdir_path)


   # Open csv file and get rivers values
   river_name=[]
   river_num2=[]
   river_col=[]
   river_sdate=[] 
   fT1_coo = pd.read_csv(rivers_coo_file,sep=';',comment='#',header=None)
   #
   river_inlat = fT1_coo[0][:] 
   river_inlon = fT1_coo[1][:] 
   river_inname = fT1_coo[5][:]
   river_innum = fT1_coo[2][:] 

   river_name=river_inname
   river_num2=river_innum
   river_lon=river_inlon
   river_lat=river_inlat
   river_col=[ 'blue' for i in range(0,len(river_inname))]        
   
   river_num=len(river_name)
   print("Rivers num:",river_num)
   
  
   # Loop on EMODnet tide-gauges
   for stn in range (0,len(river_name)): 
       print(river_name[stn])
   
   ################### SORT the TG, PLOT MAP and TABLES #####################

   # Get the info and sort the tg on longitude order
   ALL_river_name=np.append(river_name,[])
   ALL_river_num2=np.append(river_num2,[])
   ALL_river_col=np.append(river_col,[])
   ALL_river_lon=np.append(river_lon,[])
   ALL_river_lat=np.append(river_lat,[])

   lonsort_idx, river_num2_sorted = zip(*sorted(enumerate(ALL_river_num2), key=itemgetter(1)))
   river_lat_sorted = np.take(ALL_river_lat,lonsort_idx)
   river_lon_sorted = np.take(ALL_river_lon,lonsort_idx)
   river_name_sorted = np.take(ALL_river_name,lonsort_idx)
   river_num2_sorted = np.take(ALL_river_num2,lonsort_idx)
   river_col_sorted = np.take(ALL_river_col,lonsort_idx)


   # Define TG LABELS to be used in plots
   river_lab_sorted=[]
   for river_idx in range(0,len(river_name_sorted)):
       shift_idx=river_idx+1
       river_lab_sorted.append(str(shift_idx)) 

   ALL_river_lat=river_lat_sorted
   ALL_river_lon=river_lon_sorted
   ALL_river_lab=river_lab_sorted
   ALL_river_name=river_name_sorted
   ALL_river_num2=river_num2_sorted
   ALL_river_col=river_col_sorted

   if adriatico_flag == 1:
      plotname=workdir_path+'/rivers_map_adr1_'+var_mod+'_'+var_lev_lab+'_'+year+month+day+'.jpg'
   elif adriatico_flag == 2:
      plotname=workdir_path+'/rivers_map_adr2_'+var_mod+'_'+var_lev_lab+'_'+year+month+day+'.jpg'
   else:
      plotname=workdir_path+'/rivers_map_'+var_mod+'_'+var_lev_lab+'_'+year+month+day+'.jpg'

   # Fig
   plt.figure(figsize=(20,10))
   plt.rc('font', size=13) #  size=12
   # Plot Title
   plt.title (field_lab)
   if adriatico_flag == 1:
      lon_0 = 12.5 #lons.mean() 14
      llcrnrlon = lons.min()
      llcrnrlon = 12.2 #-10.0
      urcrnrlon = 12.8 #lons.max() 16
      lat_0 = 44.9 #lats.mean()
      llcrnrlat = 44.6 #lats.min() 44.0
      urcrnrlat = 45.2 #lats.max() 46.0
   elif adriatico_flag == 2:
      lon_0 = 14 #lons.mean() 14
      llcrnrlon = lons.min()
      llcrnrlon = 12.0 #-10.0
      urcrnrlon = 16 #lons.max() 16
      lat_0 = 44.8 #lats.mean()
      llcrnrlat = 43.8 #lats.min() 44.0
      urcrnrlat = 45.8 #lats.max() 46.0

   else:
      lon_0 = lons.mean()
      llcrnrlon = lons.min()
      llcrnrlon = -10.0
      urcrnrlon = lons.max()
      lat_0 = lats.mean()
      llcrnrlat = lats.min()
      urcrnrlat = lats.max()

   # Create the map
   if adriatico_flag == 1:
      m = Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,resolution='c',projection='merc',lat_0=lat_0,lon_0=lon_0)
      xi, yi = m(lons, lats)
      # Plot the frame to the map
      plt.rcParams["axes.linewidth"]  = 1.25
      m.drawparallels(np.arange(30., 46., 0.2), labels=[1,0,0,0], fontsize=10) # (30., 46., 5.)
      m.drawmeridians(np.arange(-20., 40., 0.2), labels=[0,0,0,1], fontsize=10)# (-20., 40., 10.)
      #contourf = plt.contour(xi,yi,np.squeeze(vals_bathy),5.0,colors='black')
      # Plot the bathy
      #cmap = mpl.cm.Blues(np.linspace(0,1,20))
      #cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
      #cmap =  cmap.reversed()
      #cs = m.pcolor(xi,yi,-np.squeeze(vals_bathy),cmap=cmap,vmax=-40,vmin=0) #vmax=-5000
      cs = m.pcolor(xi,yi,field_plot,cmap=cmap,vmax=var_max,vmin=var_min)
      #contour = plt.contour(xi,yi,landmask_mesh,0.000,colors='black')
      contourf = plt.contourf(xi,yi,landmask_mesh,[0.000,0.999],colors='gray')
      # Plot the legend and its label
      cbar = m.colorbar(cs, location='right', pad="10%")
      cbar.set_label(bar_label_string)
      # Add tide-gauges
      for tg2plot_idx in range(0,len(ALL_river_name)) :
        lon_ok=lons[int(ALL_river_lat[tg2plot_idx]),int(ALL_river_lon[tg2plot_idx])]
        lat_ok=lats[int(ALL_river_lat[tg2plot_idx]),int(ALL_river_lon[tg2plot_idx])]
        xp, yp = m(lon_ok,lat_ok)
        threechar=str(ALL_river_name[tg2plot_idx])
        if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante':
           plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=16,backgroundcolor='red',alpha=1,color='black') #fontsize=12
        elif threechar[0:3] == 'Po_':
           plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=16,backgroundcolor='navy',alpha=1,color='white') #fontsize=12
        #else:
         #  plt.text(xp,yp,ALL_river_num2[tg2plot_idx], fontsize=12,backgroundcolor=ALL_river_col[tg2plot_idx],alpha=1,color='black')
   elif adriatico_flag == 2:
      m = Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,resolution='c',projection='merc',lat_0=lat_0,lon_0=lon_0)
      xi, yi = m(lons, lats)
      # Plot the frame to the map
      plt.rcParams["axes.linewidth"]  = 1.25
      m.drawparallels(np.arange(30., 46., 1), labels=[1,0,0,0], fontsize=10) # (30., 46., 5.)
      m.drawmeridians(np.arange(-20., 40., 1), labels=[0,0,0,1], fontsize=10)# (-20., 40., 10.)
      #contourf = plt.contour(xi,yi,np.squeeze(vals_bathy),0.0,colors='black')
      # Plot the bathy
      #cmap = mpl.cm.Blues(np.linspace(0,1,20))
      #cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
      #cmap =  cmap.reversed()
      #cs = m.pcolor(xi,yi,-np.squeeze(vals_bathy),cmap=cmap,vmax=-200,vmin=0) #vmax=-5000
      cs = m.pcolor(xi,yi,field_plot,cmap=cmap,vmax=var_max,vmin=var_min)
      #contourf = plt.contourf(xi,yi,np.squeeze(vals_bathy),[-1000,0.0],colors='gray')
      contourf = plt.contourf(xi,yi,landmask_mesh,[0.000,0.999],colors='gray')
      # Plot the legend and its label
      cbar = m.colorbar(cs, location='right', pad="10%")
      cbar.set_label(bar_label_string)
      # Add tide-gauges
      for tg2plot_idx in range(0,len(ALL_river_name)) :
        lon_ok=lons[int(ALL_river_lat[tg2plot_idx]),int(ALL_river_lon[tg2plot_idx])]
        lat_ok=lats[int(ALL_river_lat[tg2plot_idx]),int(ALL_river_lon[tg2plot_idx])]
        xp, yp = m(lon_ok,lat_ok)
        threechar=str(ALL_river_name[tg2plot_idx])
        if exp == 1:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante':
           plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=12,backgroundcolor='red',alpha=1,color='black') #fontsize=12
         elif threechar[0:3] == 'Po_':
           plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=12,backgroundcolor='navy',alpha=1,color='white') #fontsize=12
         else:
           plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=12,backgroundcolor='red',alpha=1,color='black')
        elif exp == 2:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante' or threechar == 'Nilo' or threechar == 'Asi_Orontes' :
           plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=12,backgroundcolor='navy',alpha=1,color='white')
         else:
          plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=12,backgroundcolor='red',alpha=1,color='black')
   else:
      m = Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,resolution='c',projection='merc',lat_0=lat_0,lon_0=lon_0)
      xi, yi = m(lons, lats)
      # Plot the frame to the map
      plt.rcParams["axes.linewidth"]  = 1.25
      m.drawparallels(np.arange(30., 46., 5), labels=[1,0,0,0], fontsize=10) # (30., 46., 5.)
      m.drawmeridians(np.arange(-20., 40., 10), labels=[0,0,0,1], fontsize=10)# (-20., 40., 10.)
      contourf = plt.contour(xi,yi,np.squeeze(vals_bathy),0.0,colors='black')
      # Plot the bathy
      #cmap = mpl.cm.Blues(np.linspace(0,1,20))
      #cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
      #cmap =  cmap.reversed()
      #cs = m.pcolor(xi,yi,-np.squeeze(vals_bathy),cmap=cmap,vmax=-5000,vmin=0) #vmax=-5000
      #contourf = plt.contourf(xi,yi,np.squeeze(vals_bathy),[-1000,0.0],colors='gray')
      cs = m.pcolor(xi,yi,field_plot,cmap=cmap,vmax=var_max,vmin=var_min)
      contourf = plt.contourf(xi,yi,landmask_mesh,[0.000,0.999],colors='gray')
      # Plot the legend and its label
      cbar = m.colorbar(cs, location='right', pad="10%")
      cbar.set_label(bar_label_string)
      # Add tide-gauges
      for tg2plot_idx in range(0,len(ALL_river_name)) :
        lon_ok=lons[int(ALL_river_lat[tg2plot_idx]),int(ALL_river_lon[tg2plot_idx])]
        lat_ok=lats[int(ALL_river_lat[tg2plot_idx]),int(ALL_river_lon[tg2plot_idx])]
        xp, yp = m(lon_ok,lat_ok)
        threechar=str(ALL_river_name[tg2plot_idx])
        if exp == 1:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante':
           #plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=2,backgroundcolor='red',alpha=1,color='black') #fontsize=12
           plt.scatter(xp, yp, s=100, alpha=1, c='red')
         elif threechar[0:3] == 'Po_':
           #plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=2,backgroundcolor='navy',alpha=1,color='white') #fontsize=12
           plt.scatter(xp, yp, s=100, alpha=1, c='navy')
         else:
           #plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=2,backgroundcolor='red',alpha=1,color='black')
           plt.scatter(xp, yp, s=100, alpha=1, c='red')
        elif exp == 2:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante' or threechar == 'Nilo' or threechar == 'Asi_Orontes' :
           #plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=2,backgroundcolor='navy',alpha=1,color='white') 
           plt.scatter(xp, yp, s=100, alpha=1, c='navy')
         else:
          #plt.text(xp,yp,str(int(ALL_river_num2[tg2plot_idx])), fontsize=2,backgroundcolor='red',alpha=1,color='black')
          plt.scatter(xp, yp, s=100, alpha=1, c='red')
   # Save and close 
   plt.savefig(plotname)
   plt.clf()

   # Write TAB with names, labels and coordinates
   RIVERTab_filename=workdir_path+'river_tab.txt'
   RIVERTab_file = open(RIVERTab_filename,"w")
   print('\\begin{table}'+'\n',file=RIVERTab_file)
   print('\\# & Name & Label & Longitude & Latitude \\\\'+'\n',file=RIVERTab_file)
   print('\\hline'+'\n',file=RIVERTab_file)
   for tgtab_idx in range(0,len(ALL_river_name)):
       shift_idx=tgtab_idx+1
       print(str(ALL_river_name[tgtab_idx])+' & '+'{\color{'+str(ALL_river_col[tgtab_idx])+'}{'+str(int(ALL_river_num2[tgtab_idx]))+'}} & '+str(round(lons[int(ALL_river_lat[tgtab_idx]),int(ALL_river_lon[tgtab_idx])],4))+' & '+str(round(lats[int(ALL_river_lat[tgtab_idx]),int(ALL_river_lon[tgtab_idx])],4))+'\\\\'+'\n',file=RIVERTab_file)
   print('\\hline'+'\n',file=RIVERTab_file)
   RIVERTab_file.close()
######
print ('Workdir ',workdir)

