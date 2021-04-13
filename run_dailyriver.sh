#!/bin/bash
#
# by AC Goglio (CMCC)
# annachiara.goglio@cmcc.it
#
# Written: 13/04/2021
#
#set -u
set -e
#set -x 
########################
echo "*********** Daily river input 4 EAS System ***********"

####################### SET THE FOLLOWING VARS: ############################################
# Year
YEAR2COMPUTE=2015

# Workdir and your virtual environment
WORKDIR="/users_home/oda/ag15419/river_inputs/Killworth/"
YOUR_PY_ENV="mappyenv"

# Input (EAS system monthly river input file) and output (EAS system daily river input file)
MONTHLY_RIVERS="/data/opa/mfs-dev/Med_static/MFS_EAS6_STATIC_V2/NEMO_DATA0/runoff_1m_nomask.nc"
DAILY_RIVERS="runoff_1d_nomask.nc"

# Executables:
# 1) Py script to extract climatological values from Input file
EXE_CLIM='extract_clim_river.py'
# 2) F90 Script (template) to compute pseudodischarges (Killworth matrix)
EXE_KILLWORTH_TEMP="killworth_temp.F90"
# 3) Py script to interpolate pseudodischarges and built daily file for EAS system 
EXE_INTERP2DAILY="daily_interp.py"


############################ DO NOT CHANGE THE CODE BENEATH THIS LINE ########################## 

# Check the existence of the workdir and mv into it
if [[ -d $WORKDIR ]]; then
   echo "I am moving to $WORKDIR.."
   cd $WORKDIR
else
   echo "ERROR: Work dir $WORKDIR NOT Found! "
   exit
fi

# Check and copy the input file
if [[ -e $MONTHLY_RIVERS ]]; then
   cp -v $MONTHLY_RIVERS $WORKDIR/$DAILY_RIVERS
else 
   echo "ERROR: Input file $MONTHLY_RIVERS NOT Found! "
   exit
fi

# Load the environment for step 1
module load anaconda 
source activate $YOUR_PY_ENV

# Clean the directory from previous outputs
echo "Clean the workdir from previous run outputs.."
sleep 3
for TOBERM in $( ls $WORKDIR/clim_*.txt); do
    rm -vr $TOBERM
done

echo "I am going to extract climatological values from input file: $MONTHLY_RIVERS ..."
python $EXE_CLIM $MONTHLY_RIVERS
echo "...Done!!"


# Load the environment for step 2
module load intel19.5/19.5.281 impi19.5/19.5.281 impi19.5/netcdf/C_4.7.2-F_4.5.2_CXX_4.3.1

# Loop on days and months (from november of year-1 to february year+1 )
# Built start date
START_YEAR=$(( $YEAR2COMPUTE - 1 ))
NEXT_START_MONTH=12
START_DATE=${START_YEAR}${NEXT_START_MONTH}01
# Loop on months
IDX_DATE=$START_DATE
IDX_MONTH=0
while [[ $IDX_MONTH -lt 16 ]]; do   
      echo $( date -u -d "${IDX_DATE} -1 day" +%Y%m%d )
      IDX_DATE=$( date -u -d "${IDX_DATE} 1 month" +%Y%m%d )
      IDX_MONTH=$(( $IDX_MONTH + 1 ))
done

  # Built and Compile the executable

  # Run the executable


# Load the environment for step 3
module load $YOUR_PY_ENV
source activate mappyenv

######################
