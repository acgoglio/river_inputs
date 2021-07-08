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
# WARNING: the inputs must be here, the outputs will be moved to subdirs   
workdir= '/work/oda/ag15419/tmp/river_inputs/' 
# input files:
emodnettg_coo_file ='/users_home/oda/ag15419/river_inputs/Killworth/rivers_info_v2.csv'
model_bathy='/work/oda/ag15419/PHYSW24_DATA/TIDES/DATA0/bathy_meter.nc'
model_meshmask='/work/oda/ag15419/PHYSW24_DATA/TIDES/DATA0/mesh_mask.nc'
#
adriatico_flag=1
exp=2
########################################################
# DO NOT CHANGE THE CODE BELOW THIS LINE!!!
########################################################
# Parameter setting
#--------------------
# MODEL DATASET
# WARNING: this nust be the same as in p_extr.ini file (var ANA_INTAG)
mod_file_template='eas6'
mod1_file='/work/oda/ag15419/arc_link/eas6_drpo/output/201701/assw_drpo_1d_20170101_grid_T.nc'
mod2_file=' /work/oda/ag15419/arc_link/eas6_drpo_ctrl/output/201701/mfs1_v1_1d_20170101_grid_T.nc'
model1 = NC.Dataset(mod1_file,'r')
model2 = NC.Dataset(mod2_file,'r')
field1=model1.variables['vosaline'][0,0,:,:]
field2=model2.variables['vosaline'][0,0,:,:]
field_diff=field1-field2

# Fields to be analized
grid = 'T' # Choose T, U, V or uv2t grid

if grid == 'T':
   # 2D fields:
   var_2d_mod='sossheig'
   field_2d_units='m'
   # WARNING: the sossheig field is supposed to be given in meters 
   time_var_mod='time'
   time_var_mod2='time_counter'
   lat_var_mod='lat'

#--------------------
# OBS DATASET

if grid == 'T':
   var_2d_obs=var_2d_mod # Only for EMODnet dataset
   time_var_obs='TIME' # Only for EMODnet dataset
   fieldobs_2d_units=('cm','m')
   # WARNING: the sossheig field is supposed to be given 
   # in centimeters for ispra and in meters for emodnet  
   var_2d_qf_obs='sossheig_qf'
   pos_2d_qf_obs='pos_qf'

#--------------------
# OTHER PARAM

# Tidal components (WARNING: the script is set to work with the following 8 constituents in the following order!)
tidal_comp=['M2','S2','K1','O1','N2','P1','Q1','K2']

# Domain (Med or AtlBox)
where_box='Med'

# Colors for each sub area

# MED subregions are: Gibraltar, Adriatic, Messina, East, Other
# WARNING: you cannot change the region order!!
#subregions_color=['red','blue','orange','magenta','green','cyan','deeppink','tab:olive']
subregions_color=['red','red','red','red','red','red','red','red']
subregions_labels=['G','A','M','E','O','TA','TG','T']
# Atl Box subregions are: Biscay Bay, Gibraltar Atlantic side, Portugal  
# WARNING: you cannot change the region order!!
#subregions_color.append['cyan','deeppink','tab:olive']
#
# Function to distinghish relevant regions
def which_region(longitude,latitude):
       # Regions 
       # EAST MED:
       if longitude > 30.000:
           color=subregions_color[3]
       # ADRIACTIC SEA:
       elif (longitude < 20.000 and longitude > 12.000 and latitude < 46.000 and latitude > 42.000 ) or (longitude < 20.000 and longitude > 14.000 and latitude < 42.000 and latitude > 41.000 ) or (longitude < 20.000 and longitude > 16.000 and latitude < 42.000 and latitude > 40.000):
           color=subregions_color[1]
       # MESSINA STRAIT AREA:
       elif longitude < 16.500 and longitude > 14.500 and latitude < 38.200 and latitude > 37.800:
           color=subregions_color[2]
       # GIBRALTAR STRAIT AREA:
       elif longitude < -1.800 and longitude > -6.000 and latitude < 37.2630:
           color=subregions_color[0]
       # GIBRALTAR ATLANTIC BOX SIDE
       elif longitude < -6.000 and latitude < 37.2630:
           color=subregions_color[6]
       # PORUGAL ATLANTIC BOX
       elif longitude < -6.000 and latitude > 37.2630 and latitude < 43.2100:
           color=subregions_color[7]
       # BISCAY BAY ATLANTIC BOX
       elif longitude < 0.000 and latitude > 43.2100:
           color=subregions_color[5]
       # OTHER MED REGIONS
       else:
           color=subregions_color[4]
       return color

# Signal-to-noise ration threshold
# WARNING: if any component shows a fit snr lower than this the fit is not perfomed
snr_thershold=0.1

# FLAG or loop on analysis type
# Options:
# lit       --> Compare the common datasets with respect to literature 
# anatpxo   --> Apply all the analysis and compare datasets with TPXO model results
# all       --> Linear regression concerning all avalilable tide-gauges
for anatype_flag in ('all','all'):

   # Buil the dir and move in it
   workdir_path = workdir+'/maps_bathy/'
   try:
       os.stat(workdir_path)
   except:
       os.mkdir(workdir_path)

   print ('##############################')
   # for each type of analysis set the parameters and print the function
   if anatype_flag=='anatpxo':
      tpxo_flag = 1 # to compare also wrt TPXO data
      flag_15stats = 0 # to compare results with literature
      print ('Comparison wrt obs and TPXO model results.. Results in ',workdir_path)
      fontsize_tg=40
   elif anatype_flag=='lit':
      tpxo_flag = 0 # to compare also wrt TPXO data
      flag_15stats = 1 # to compare results with literature
      print ('Comparison wrt obs and literature results.. Results in ',workdir_path)
      fontsize_tg=40
   elif anatype_flag=='all':
      tpxo_flag = 0 # to compare also wrt TPXO data
      flag_15stats = 0 # to compare results with literature
      print ('Comparison wrt all available obs.. Results in ',workdir_path)
      fontsize_tg=20

      # Check on Domain
      if where_box=='AtlBox':
         tpxo_flag = 0
         flag_15stats = 0
         anatype_flag = 'all'
   

      # Open file and get values
      tg_name=[]
      tg_num2=[]
      tg_col=[]
      tg_sdate=[]
      fT1_coo = pd.read_csv(emodnettg_coo_file,sep=';',comment='#',header=None)
      #
      tg_inlat = fT1_coo[0][:] 
      tg_inlon = fT1_coo[1][:] 
      tg_inname = fT1_coo[5][:]
      tg_innum = fT1_coo[2][:] 
      anatpxo_inflag ='0'
      lit_inflag = '0'
   
      if anatype_flag=='lit':
         for idx_tg in range (0,len(lit_inflag)):
             if lit_inflag[idx_tg] == 1 :
   
                tg_name.append(tg_inname[idx_tg])
                tg_num2.append(tg_innum[idx_tg])
                tg_lon.append(tg_inlon[idx_tg])
                tg_lat.append(tg_inlat[idx_tg])

                tg_col.append(which_region(tg_inlon[idx_tg],tg_inlat[idx_tg]))

      elif anatype_flag=='anatpxo':
         for idx_tg in range (0,len(anatpxo_inflag)):
             if anatpxo_inflag[idx_tg] == 1 :
                tg_name.append(tg_inname[idx_tg])
                tg_num2.append(tg_innum[idx_tg])
                tg_lon.append(tg_inlon[idx_tg])
                tg_lat.append(tg_inlat[idx_tg])
   
                tg_col.append(which_region(tg_inlon[idx_tg],tg_inlat[idx_tg]))
   
      elif anatype_flag=='all':
         tg_name=tg_inname
         tg_num2=tg_innum
         tg_lon=tg_inlon
         tg_lat=tg_inlat
         
         for idx_tg in range (0,len(tg_inname)):

            tg_col.append(which_region(tg_inlon[idx_tg],tg_inlat[idx_tg]))
   
   elif where_box == 'AtlBox':

       if anatype_flag=='all':
         tg_name=tg_inname
         tg_num2=tg_innum
         tg_lon=tg_inlon
         tg_lat=tg_inlat

         for idx_tg in range (0,len(tg_inname)):
            tg_col.append(which_region(tg_inlon[idx_tg],tg_inlat[idx_tg]))
   
   
   tg_num=len(tg_name)
   print("EmodNET Stations num:",tg_num)
   
  
   # Loop on EMODnet tide-gauges
   for stn in range (0,len(tg_name)): 
       print(tg_name[stn])
   
   ################### SORT the TG, PLOT MAP and TABLES #####################

   # Get the info and sort the tg on longitude order
   ALL_tg_name=np.append(tg_name,[])
   ALL_tg_num2=np.append(tg_num2,[])
   ALL_tg_col=np.append(tg_col,[])
   ALL_tg_lon=np.append(tg_lon,[])
   ALL_tg_lat=np.append(tg_lat,[])

   lonsort_idx, tg_num2_sorted = zip(*sorted(enumerate(ALL_tg_num2), key=itemgetter(1)))
   tg_lat_sorted = np.take(ALL_tg_lat,lonsort_idx)
   tg_lon_sorted = np.take(ALL_tg_lon,lonsort_idx)
   tg_name_sorted = np.take(ALL_tg_name,lonsort_idx)
   tg_num2_sorted = np.take(ALL_tg_num2,lonsort_idx)
   tg_col_sorted = np.take(ALL_tg_col,lonsort_idx)


   # Define TG LABELS to be used in plots
   tg_lab_sorted=[]
   if anatype_flag=='lit':
      tg_lab_sorted = tg_name_sorted
   elif anatype_flag=='anatpxo':
      for tg_idx in range(0,len(tg_name_sorted)):
          shift_idx=tg_idx+1
          tg_lab_sorted.append(str(shift_idx))
   elif anatype_flag=='all':
      for tg_idx in range(0,len(tg_name_sorted)):
          shift_idx=tg_idx+1
          tg_lab_sorted.append(str(shift_idx)) 

   ALL_tg_lat=tg_lat_sorted
   ALL_tg_lon=tg_lon_sorted
   ALL_tg_lab=tg_lab_sorted
   ALL_tg_name=tg_name_sorted
   ALL_tg_num2=tg_num2_sorted
   ALL_tg_col=tg_col_sorted

   # PLOT THE MAP of tide-gauge location
   nc2open3=model_bathy # tidal bathimetry
   model3 = NC.Dataset(nc2open3,'r')
   vals_bathy=model3.variables['Bathymetry'][:]
   lons = model3.variables['nav_lon'][:]
   lats = model3.variables['nav_lat'][:]
   #
   nc2open4=model_meshmask # mesh mask
   model4 = NC.Dataset(nc2open4,'r')
   landmask_mesh=model4.variables['tmask'][0,0,:,:]   
   print ('PROVA ',landmask_mesh)

   if anatype_flag == 'lit':
      plotname=workdir_path+anatype_flag+'_tg.jpg'
   elif anatype_flag == 'anatpxo':
      plotname=workdir_path+anatype_flag+'_tg.jpg'
   elif anatype_flag == 'all':
      plotname=workdir_path+'/rivers_map_adr.jpg'
   # Fig
   plt.figure(figsize=(20,10))
   plt.rc('font', size=13) #  size=12
   # Plot Title
   if adriatico_flag == 1:
      plt.title ('Bathymetry and Po River branches location') #('Bathymetry [m] and Rivers location')
      lon_0 = 12.5 #lons.mean() 14
      llcrnrlon = lons.min()
      llcrnrlon = 12.2 #-10.0
      urcrnrlon = 12.8 #lons.max() 16
      if where_box=='Med':
        urcrnrlon = 12.8 #lons.max() 18
      elif where_box=='AtlBox':
       urcrnrlon = 0.0
      lat_0 = 44.9 #lats.mean()
      llcrnrlat = 44.6 #lats.min() 44.0
      urcrnrlat = 45.2 #lats.max() 46.0
   elif adriatico_flag == 2:
      plt.title ('Bathymetry and Rivers location') #('Bathymetry [m] and Rivers location')
      lon_0 = 14 #lons.mean() 14
      llcrnrlon = lons.min()
      llcrnrlon = 12.0 #-10.0
      urcrnrlon = 16 #lons.max() 16
      if where_box=='Med':
        urcrnrlon = 16 #lons.max() 18
      elif where_box=='AtlBox':
       urcrnrlon = 0.0
      lat_0 = 44.8 #lats.mean()
      llcrnrlat = 43.8 #lats.min() 44.0
      urcrnrlat = 45.8 #lats.max() 46.0

   else:
      plt.title ('Bathymetry and Rivers location')
      lon_0 = lons.mean()
      llcrnrlon = lons.min()
      llcrnrlon = -10.0
      urcrnrlon = lons.max()
      if where_box=='Med':
        urcrnrlon = lons.max()
      elif where_box=='AtlBox':
       urcrnrlon = 0.0
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
      cmap = mpl.cm.Blues(np.linspace(0,1,20))
      cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
      cmap =  cmap.reversed()
      cs = m.pcolor(xi,yi,-np.squeeze(vals_bathy),cmap=cmap,vmax=-40,vmin=0) #vmax=-5000
      #cs = m.pcolor(xi,yi,field_diff,cmap='bwr')
      #contour = plt.contour(xi,yi,landmask_mesh,0.000,colors='black')
      contourf = plt.contourf(xi,yi,landmask_mesh,[0.000,0.999],colors='gray')
      # Plot the legend and its label
      cbar = m.colorbar(cs, location='right', pad="10%")
      bar_label_string='Bathymetry [m]'
      cbar.set_label(bar_label_string)
      # Add tide-gauges
      for tg2plot_idx in range(0,len(ALL_tg_name)) :
        lon_ok=lons[int(ALL_tg_lat[tg2plot_idx]),int(ALL_tg_lon[tg2plot_idx])]
        lat_ok=lats[int(ALL_tg_lat[tg2plot_idx]),int(ALL_tg_lon[tg2plot_idx])]
        xp, yp = m(lon_ok,lat_ok)
        threechar=str(ALL_tg_name[tg2plot_idx])
        if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante':
           if exp==1:
              plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=16,backgroundcolor=ALL_tg_col[tg2plot_idx],alpha=1,color='black') #fontsize=12
           else:
              plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=16,backgroundcolor='navy',alpha=1,color='white') #fontsize=12
        elif threechar[0:3] == 'Po_':
           if exp==1:
              plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=16,backgroundcolor='navy',alpha=1,color='white') #fontsize=12
           else:
              plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=16,backgroundcolor=ALL_tg_col[tg2plot_idx],alpha=1,color='black')
   elif adriatico_flag == 2:
      m = Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,resolution='c',projection='merc',lat_0=lat_0,lon_0=lon_0)
      xi, yi = m(lons, lats)
      # Plot the frame to the map
      plt.rcParams["axes.linewidth"]  = 1.25
      m.drawparallels(np.arange(30., 46., 1), labels=[1,0,0,0], fontsize=10) # (30., 46., 5.)
      m.drawmeridians(np.arange(-20., 40., 1), labels=[0,0,0,1], fontsize=10)# (-20., 40., 10.)
      contourf = plt.contour(xi,yi,np.squeeze(vals_bathy),0.0,colors='black')
      # Plot the bathy
      cmap = mpl.cm.Blues(np.linspace(0,1,20))
      cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
      cmap =  cmap.reversed()
      cs = m.pcolor(xi,yi,-np.squeeze(vals_bathy),cmap=cmap,vmax=-200,vmin=0) #vmax=-5000
      contourf = plt.contourf(xi,yi,np.squeeze(vals_bathy),[-1000,0.0],colors='gray')
      # Plot the legend and its label
      cbar = m.colorbar(cs, location='right', pad="10%")
      bar_label_string='Bathymetry [m]'
      cbar.set_label(bar_label_string)
      # Add tide-gauges
      for tg2plot_idx in range(0,len(ALL_tg_name)) :
        lon_ok=lons[int(ALL_tg_lat[tg2plot_idx]),int(ALL_tg_lon[tg2plot_idx])]
        lat_ok=lats[int(ALL_tg_lat[tg2plot_idx]),int(ALL_tg_lon[tg2plot_idx])]
        xp, yp = m(lon_ok,lat_ok)
        threechar=str(ALL_tg_name[tg2plot_idx])
        if exp == 1:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante':
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=12,backgroundcolor=ALL_tg_col[tg2plot_idx],alpha=1,color='black') #fontsize=12
         elif threechar[0:3] == 'Po_':
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=12,backgroundcolor='navy',alpha=1,color='white') #fontsize=12
         else:
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=12,backgroundcolor=ALL_tg_col[tg2plot_idx],alpha=1,color='black')
        elif exp == 2:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante' or threechar == 'Nilo' or threechar == 'Asi_Orontes' :
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=12,backgroundcolor='navy',alpha=1,color='white')
         else:
          plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=12,backgroundcolor='red',alpha=1,color='black')
   else:
      m = Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,resolution='c',projection='merc',lat_0=lat_0,lon_0=lon_0)
      xi, yi = m(lons, lats)
      # Plot the frame to the map
      plt.rcParams["axes.linewidth"]  = 1.25
      m.drawparallels(np.arange(30., 46., 5), labels=[1,0,0,0], fontsize=10) # (30., 46., 5.)
      m.drawmeridians(np.arange(-20., 40., 10), labels=[0,0,0,1], fontsize=10)# (-20., 40., 10.)
      contourf = plt.contour(xi,yi,np.squeeze(vals_bathy),0.0,colors='black')
      # Plot the bathy
      cmap = mpl.cm.Blues(np.linspace(0,1,20))
      cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
      cmap =  cmap.reversed()
      cs = m.pcolor(xi,yi,-np.squeeze(vals_bathy),cmap=cmap,vmax=-5000,vmin=0) #vmax=-5000
      contourf = plt.contourf(xi,yi,np.squeeze(vals_bathy),[-1000,0.0],colors='gray')
      # Plot the legend and its label
      cbar = m.colorbar(cs, location='right', pad="10%")
      bar_label_string='Bathymetry [m]'
      cbar.set_label(bar_label_string)
      # Add tide-gauges
      for tg2plot_idx in range(0,len(ALL_tg_name)) :
        lon_ok=lons[int(ALL_tg_lat[tg2plot_idx]),int(ALL_tg_lon[tg2plot_idx])]
        lat_ok=lats[int(ALL_tg_lat[tg2plot_idx]),int(ALL_tg_lon[tg2plot_idx])]
        xp, yp = m(lon_ok,lat_ok)
        threechar=str(ALL_tg_name[tg2plot_idx])
        if exp == 1:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante':
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=10,backgroundcolor=ALL_tg_col[tg2plot_idx],alpha=1,color='black') #fontsize=12
         elif threechar[0:3] == 'Po_':
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=10,backgroundcolor='navy',alpha=1,color='white') #fontsize=12
         else:
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=10,backgroundcolor=ALL_tg_col[tg2plot_idx],alpha=1,color='black')
        elif exp == 2:
         if threechar == 'Po_di_Volano' or threechar == 'Po_di_Levante' or threechar == 'Nilo' or threechar == 'Asi_Orontes' :
           plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=10,backgroundcolor='navy',alpha=1,color='white') 
         else:
          plt.text(xp,yp,str(int(ALL_tg_num2[tg2plot_idx])), fontsize=10,backgroundcolor='red',alpha=1,color='black')
   # Save and close 
   plt.savefig(plotname)
   plt.clf()

   # Write TAB with names, labels and coordinates
   TGTab_filename=workdir_path+'river_tab.txt'
   TGTab_file = open(TGTab_filename,"w")
   print('\\begin{table}'+'\n',file=TGTab_file)
   print('\\# & Name & Label & Longitude & Latitude \\\\'+'\n',file=TGTab_file)
   print('\\hline'+'\n',file=TGTab_file)
   for tgtab_idx in range(0,len(ALL_tg_name)):
       shift_idx=tgtab_idx+1
       print(str(ALL_tg_name[tgtab_idx])+' & '+'{\color{'+str(ALL_tg_col[tgtab_idx])+'}{'+str(int(ALL_tg_num2[tgtab_idx]))+'}} & '+str(round(lons[int(ALL_tg_lat[tgtab_idx]),int(ALL_tg_lon[tgtab_idx])],4))+' & '+str(round(lats[int(ALL_tg_lat[tgtab_idx]),int(ALL_tg_lon[tgtab_idx])],4))+'\\\\'+'\n',file=TGTab_file)
   print('\\hline'+'\n',file=TGTab_file)
   TGTab_file.close()

