# river_inputs repository

 by AC Goglio (CMCC)
 annachiara.goglio@cmcc.it

---
## AIM of the PACKAGE, INPUTS and OUTPUTS
 
 The AIM of this code is to build daily river input files for EAS6 system.

 INPUT: 
- Monthly climatological river input (previous EAS6 system river input)
- Po river data from the following sources:
  - 30 min freq. ARPAE Pontelagoscuro discharge obs
  - daily freq. ARPAE Pontelagoscuro discharge obs
  - EFAS model discharge time series
- EFAS model discharge time series
 

 OUTPUT: 

- daily river input files (one file per year) and diagnostic plots 
  
  For each river the user can choose between the following discharge sources:
  - daily climatological inputs obtainet from monthly climatologica values through Killworth time interpolation
  - daily vaues from EFAS Model (stored in single ASCII file)
  - daily obs (ONLY for Po river ) from ARPAE Pontelagoscuro station

---
## PROCEDURE and FUTURE IMPROVEMENTS

 The PROCEDURE, along with the code structure, is diveded into several steps:

 1. Extraction of climatological values from input file for each grid point where the river mask is != 0 [extract_clim_river.py]
 2. Computation of the pseudodischarges (from Killworth matrix) [killworth_temp_12.F90]
 3. Time interpolation of pseudodischarges and bilding of daily file for EAS system [daily_interp_temp.py]
 4. Pre-processing of Po river obs and substitute the time series in the out file if required [po_river_daily.py]
 5. Substitution of EFAS Model time-series where available, if required [efas.py] 

 FUTURE IMPROVEMENTS: 
- Step 2 and step 3 will be joined in a single script: daily_interp_temp.py as soon as possible
- All the scripts exchange values as line arguments. These operation should be done by means of 
                        a py module red by all the scripts or a yaml file
- The 14 months array in step 2 can be reduced to a 12 months one (the 14 solution is a refuse of a previous wrong inplementation 
                        and in the current version the extra ones are ignored )
- The subtraction of the Po_di_Levante discharge from the Pontelagoscuro total discharge was removed so it can also be removed from the code
                        (currently all the code lines concerning this operation are commented ) 
  
 In the package you can also find killworth_a.py script wich is a stand alone script for killworth time interpolation
 and three scripts for validation purposes: river_maps_tab.py to plot a map with the location and info tables of involved rivers,
 diag_maps_tab.py to compare temperature and salinity maps in system outputs
 and diag_plot.py to compare the input values with the soruoff field in NEMO outputs

---
## USAGE:

USAGE STEPS:

 1. Set the input file rivers_info_v2.csv 
    This file MUST contain the following columns in the following order: 
    - py_latidx;py_lonidx;         -> python coo indexes of each grid point associated with a non-zero river discharge value 
    - ID_river;                    -> river id, this will be included as an additional mask field in the outfile 
    - Lat_idx;Lon_idx;             -> coo idexes if the count starts from 1 instead of 0
    - River;                       -> Name of the river. WARNING: no spaces are allowed; WARNING: Po river branches are identified by 'Po_' string: DO NOT change it! 
    - Sal;                         -> ? (NOT USED)
    - Lat_idx_old;Lon_idx_old;     -> old indexes (NOT USED)
    - Branch_perc;                 -> Percentage of discharge to associate to different branches if next column EFAS_flag > 1 or if Po obs are activates
    - EFAS_flag;                   ->  0 => no EFAS, 1=> 1 point EFAS; N=> EFAS to be splitted on N poits
    - EFAS_y_idx_py;EFAS_x_idx_py; -> indexes of the nearest grid point on EFAS model grid (NOT USED)

 2. Open the flow script run_dailyriver.sh and set the parameters following comments  

 3. Run the script: sh run_dailyriver.sh

 (OPTIONAL: set and run river_maps_tab.py to plot the map location and info table)
 (OPTIONAL: set and run diag_maps_tab.py to compare the input values with the soruoff field in NEMO outputs)
 (OPTIONAL: set and run diag_plot.py to compare NEMO input and output runoffs )
