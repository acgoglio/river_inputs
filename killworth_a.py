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
#
###################################################################
# Input values (if you need this script inside a procedure 
# modify the following lines to read the input as line args..)

# List of 12 climatological monthly values
monthly_clim_values=np.array([0.00679197,0.007085083,0.005436324,0.00553839,0.003909914,0.002531368,0.0017822298,0.0014603292,0.0021839512,0.0036325036,0.0052040587,0.0071086367])
# Flag for leap years: if leap set leap_year=1, otherwise set leap_year=0 
leap_year=1

###################################################################
# PRE-PROC 

# Days_per month
if leap_year == 1:
   nov_to_feb=([30,31,31,29,31,30,31,30,31,31,30,31,30,31,31,28])
else:
   nov_to_feb=([30,31,31,28,31,30,31,30,31,31,30,31,30,31,31,28])

# Build the array of output days  
xnew = np.arange(nov_to_feb[1], np.sum(nov_to_feb[1:14]), 1.0)

# Compute the days num in the year
days_of_year=len(xnew)
print('Year len: ',days_of_year)

####################################################################
#
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
#for idx_tmp in range(0,12):
#    print (pseudodischarge[idx_tmp])    

####################################################################
# STEP 2: FROM PSEUDODISCHERGE VALUES TO DAILY CLIMATOLOGICAL VALUES 
#         input: 12 pseudodischarge values
#         output 365/366 daily values

# Extend pseudodischarge series to 14 values
ext_pseudodischarge=np.zeros(14)
ext_pseudodischarge[0]=pseudodischarge[11]
for old_arr in range(0,12):
    ext_pseudodischarge[old_arr+1]=pseudodischarge[old_arr]
ext_pseudodischarge[13]=pseudodischarge[0]

# Half month days (dec to jan)
timeintoout=[15,45,76,106,135,166,196,227,257,288,319,349,380,410]

# Time interpolation
f = interpolate.interp1d(timeintoout,ext_pseudodischarge)
ynew = f(xnew)

# Print the output
for idx_towrite in range(0,days_of_year):
    print(idx_towrite+1,ynew[idx_towrite])

#################################################################
