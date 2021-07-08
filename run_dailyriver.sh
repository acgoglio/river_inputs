#!/bin/bash
#
# by AC Goglio (CMCC)
# annachiara.goglio@cmcc.it
#
# Written: 13/04/2021
# Last Mod: 11/05/2021
#
#set -u
set -e
#set -x 
########################
module purge

echo "*********** Daily river input 4 EAS System ***********"
####################### SET THE FOLLOWING VARS: ############################################

# -----Input infos---------
# Year
YEAR2COMPUTE=2018

# src directory (path of this script!), workdir and your py virtual environment name
SRCDIR="/users_home/oda/ag15419/river_inputs/Killworth_py/"
WORKDIR="/work/oda/ag15419/tmp/river_inputs/new_kpy_code/"

# your virtual python env name
YOUR_PY_ENV="mappyenv"


# ------ Input and output files info---------
# Input path/name (EAS system monthly river input file) and output name (EAS system daily river input file)
MONTHLY_RIVERS="/data/opa/mfs-dev/Med_static/MFS_EAS6_STATIC_V2/NEMO_DATA0/runoff_1m_nomask.nc"
DAILY_RIVERS="runoff_1d_nomask_y${YEAR2COMPUTE}.nc" # WARNING: do not change this name or change the NEMO namelist according to it!

# NEMO mesh mask file (needed for Po river and EFAS pre-processing)
MOD_MESHMASK="/work/oda/ag15419/PHYSW24_DATA/TIDES/DATA0/mesh_mask.nc"

# -----PO River inputs---------

# Flag to sobstitute observed values to the climatological ones for the Po river (to activate set PORIVER_OBS_FLAG=1)
PORIVER_OBS_FLAG=1
# Prename of the Po river in the csv file
PO_RIVER_PRENAME='Po_' 
PO_LEVANTE_NAME='Po_di_Levante'
# Path of 30m arpae obs and code of runoff field in the database
# WARNING: if pre-name of the file is empty you should put 'NAN' 
PO_INPUT_PATH='/data/inputs/metocean/historical/obs/in_situ/buoy/ARPAE/PO_RIVER/30m/' #'/data/oda/ag15419/RIVERS_DATA/PO/30m/'
if [[ $YEAR2COMPUTE -lt 2020 ]]; then
   PO_INPUT_FILE_PRE='NAN'
   PO_INPUT_FILE_POST='-ingv2.txt'
else
   PO_INPUT_FILE_PRE='pontelagoscuro_'
   PO_INPUT_FILE_POST='.txt'
fi
PO_INPUT_VARCODE='512'
# Path of 1 day arpae obs
PO_INPUT_DAILY='/data/oda/ag15419/RIVERS_DATA/PO/daily/Pontelagoscuro_daily_2015_2021.csv'

# -----EFAS Dataset input---------

# Flag to use EFAS Dataset where available instead of climatology (to activate set EFAS_FLAG=1)
EFAS_FLAG=0
# Path to time-series
EFAS_INPUT_PATH='/data/oda/ag15419/RIVERS_DATA/EFAS/'
# Pre and post name of the file storing the EFAS time series
# WARNING: if pre-name of the file is empty you should put 'NAN'
EFAS_INPUT_FILE_PRE='NAN'
EFAS_INPUT_FILE_POST='.txt'

###########################################################################################

# Csv file with rivers info
RIVER_INFO="rivers_info_v2.csv"

# I/O nc dimensions and variables names
# Dimensions names 
LAT_IDX='y'
LON_IDX='x'
TIME_IDX='time_counter'
# Var names
LAT_2D='nav_lat'
LON_2D='nav_lon'
MASK_VAR='river_msk'
RUNOFF_VAR='sorunoff'
SALINITY_VAR='s_river'
CLIM_1M_RUNOFF_VAR='clim_monthly_runoff'
CLIM_1D_RUNOFF_VAR='clim_daily_runoff'
NAME_VAR='river_id' #river_name

# Executables:
# 1) Py script to extract climatological values from Input file
EXE_CLIM='extract_clim_river.py'
# 2) Py script to apply Killworth time interpolation and built daily file for EAS system 
PY_INTERP2DAILY="kill_interp.py" 
# 3) Py script to pre-process Po river obs and substitute the time series in the out file
PY_PORIVER_OBS="po_river_daily.py"
# 4) Py script to substitute the EFAS time seies where available
PY_EFAS="efas.py"


############################ DO NOT CHANGE THE CODE BENEATH THIS LINE ########################## 
# Load the environment
module load anaconda
source activate $YOUR_PY_ENV


# Check the existence of the workdir and mv into it
if [[ -d $WORKDIR ]]; then
   echo "I am linking files to work dir: $WORKDIR.."
   for TOBELINKED in $EXE_CLIM $EXE_KILLWORTH_TEMP $PY_INTERP2DAILY $RIVER_INFO $PY_PORIVER_OBS $PY_EFAS ; do 
       ln -svf ${SRCDIR}/${TOBELINKED} ${WORKDIR}/
   done
   echo "I am moving to work dir: $WORKDIR.."
   cd $WORKDIR
else
   echo "ERROR: Work dir $WORKDIR NOT Found! "
   exit
fi

# Check the river input file
if [[ ! -e ${MONTHLY_RIVERS} ]]; then
   echo "ERROR: Input file $MONTHLY_RIVERS NOT Found! "
   exit
fi

# Tot and monthly number of days in the year
DAYS_CHECK=$(( ${YEAR2COMPUTE} % 4 ))
if [[ ${DAYS_CHECK} != 0 ]]; then
   TOT_DOY=365
   STRING_NUM_OF_DAYS="31 28 31 30 31 30 31 31 30 31 30 31"
else
   TOT_DOY=366
   STRING_NUM_OF_DAYS="31 29 31 30 31 30 31 31 30 31 30 31"
fi
echo "Days in ${YEAR2COMPUTE} are $TOT_DOY!"

# Clean the directory from previous outputs
echo "Clean the workdir from previous run outputs.."
sleep 3
for TOBERM in $( ls clim_*.txt); do
    rm  ${TOBERM}
done

echo "I am going to extract climatological values from input file: $MONTHLY_RIVERS and built the output file template: ${DAILY_RIVERS}_temp ..."
# Run the code wich needs as args input and output names + num of days + all the dimension and variables names of input and output fields
python $EXE_CLIM $MONTHLY_RIVERS ${DAILY_RIVERS}_temp.nc $TOT_DOY $LAT_IDX $LON_IDX $TIME_IDX $LAT_2D $LON_2D $MASK_VAR $RUNOFF_VAR $SALINITY_VAR $CLIM_1M_RUNOFF_VAR $NAME_VAR $TOT_DOY
echo "...Done!!"

# Build arrays for step 2
for CLIM_FILE in $(ls clim_*.txt); do
    PSEUDO_FILENAME=$(echo ${CLIM_FILE} | sed -e "s/clim_/pseudo_/g" )
    # Look for the name of the river in river_info.csv file
    RIVER_LAT=$(echo ${CLIM_FILE} | cut -f 2 -d"_")
    RIVER_LON=$(echo ${CLIM_FILE} | cut -f 3 -d"_" | cut -f 1 -d".")
    INDEXES_OR=$(echo ${CLIM_FILE} | cut -f 2,3 -d"_" | cut -f 1 -d".")
    INDEXES=$(echo ${CLIM_FILE} | cut -f 2,3 -d"_" | cut -f 1 -d"."| sed -e "s/_/;/g" )
    RIVER_NAME="$( grep "^${INDEXES}" ${RIVER_INFO} | cut -f 6 -d";" )" || RIVER_NAME="Unknown_River"
    RIVER_NUM="$( grep "^${INDEXES}" ${RIVER_INFO} | cut -f 3 -d";" )" || RIVER_NAME=0
    echo "RIVER_ID=$RIVER_NUM INDEXES=$INDEXES RIVER_NAME: $RIVER_NAME"
    # Read climatologica values and built climatological intervals
    # 12 values array with monthly climatology:
    VAL=$( cat $CLIM_FILE )
    CLIM_12=$(echo ${VAL}$(echo -en ",") | sed -e "s/ /,/g" )
    # 365/366 values array with monthly climatology:
    IDX_VAL=1
    CLIM_ALL=""
    for DAYS_TOT in $STRING_NUM_OF_DAYS; do
       for IDX_DAYS in $( seq 1 1 $DAYS_TOT ); do
           CLIM_PER_DAY=$( echo -en $( echo "${VAL}" | cut -f $IDX_VAL -d " "))
           CLIM_ALL=${CLIM_ALL}${CLIM_PER_DAY}$(echo -en ",")
       done
       IDX_VAL=$(( $IDX_VAL + 1 ))
    done
    CLIM_ALL=$(echo ${CLIM_ALL}$(echo -en ",") | sed -e "s/,,//g" )

    echo "I am running the Killworth time Interpolation.."
    cp ${DAILY_RIVERS}_temp.nc ${DAILY_RIVERS}_tmp.nc
    python ${PY_INTERP2DAILY} ${RIVER_LAT} ${RIVER_LON} ${RIVER_NAME} ${RIVER_NUM} ${DAILY_RIVERS} ${YEAR2COMPUTE} ${CLIM_1D_RUNOFF_VAR} ${CLIM_1M_RUNOFF_VAR} ${MASK_VAR} ${NAME_VAR} ${LAT_IDX} ${LON_IDX} ${TIME_IDX} ${TOT_DOY} ${CLIM_12}
    mv ${DAILY_RIVERS}_tmp.nc ${DAILY_RIVERS}_upd.nc
    echo ".. Done"
done
# Remove the netcdf template
rm ${DAILY_RIVERS}_temp.nc
# Move the ultimate output to the final output file
mv ${DAILY_RIVERS}_upd.nc ${DAILY_RIVERS}

################ PO RIVER OBS #############
if [[ $PORIVER_OBS_FLAG == 1 ]]; then
   echo "I am going to extract, pre-process and sobstitute observed values for the Po river.."
   # Define the name of the output field storing the values
   if [[ $EFAS_FLAG == 1 ]]; then
      NEXT_RUNOFF_VAR="po_${RUNOFF_VAR}"
   else
      NEXT_RUNOFF_VAR=${RUNOFF_VAR}
   fi

   # Build the EFAS Po file to be used where ARPAE obs are missing..
   if [[ ${EFAS_INPUT_FILE_PRE} != 'NAN'  ]]; then
      EFAS_INPUT_POFILE_TEMP="${EFAS_INPUT_PATH}/${EFAS_INPUT_FILE_PRE}_${PO_RIVER_PRENAME}*_*${EFAS_INPUT_FILE_POST}"
   else
      EFAS_INPUT_POFILE_TEMP="${EFAS_INPUT_PATH}/${PO_RIVER_PRENAME}*_*${EFAS_INPUT_FILE_POST}"
   fi
   EFAS_INPUT_POFILE=$( ls ${EFAS_INPUT_POFILE_TEMP} )

   mv ${DAILY_RIVERS} ${DAILY_RIVERS}_POtmp.nc
   python ${PY_PORIVER_OBS} ${WORKDIR} ${YEAR2COMPUTE} ${TOT_DOY} ${PO_INPUT_PATH} ${PO_INPUT_FILE_PRE} ${PO_INPUT_FILE_POST} ${PO_INPUT_VARCODE} ${PO_INPUT_DAILY} ${EFAS_INPUT_POFILE} ${MOD_MESHMASK} ${RIVER_INFO} ${PO_RIVER_PRENAME} ${PO_LEVANTE_NAME} ${DAILY_RIVERS}_POtmp.nc ${NEXT_RUNOFF_VAR} ${CLIM_1M_RUNOFF_VAR} ${CLIM_1D_RUNOFF_VAR} ${LAT_IDX} ${LON_IDX} ${TIME_IDX}
   echo ".. Done"
   # Move the ultimate output to the final output file
   mv ${DAILY_RIVERS}_POtmp.nc ${DAILY_RIVERS}
fi


################ EFAS #############
if [[ $EFAS_FLAG == 1 ]]; then
   echo "I am going to substitute EFAS values where available.. python ${PY_EFAS} ${WORKDIR} ${YEAR2COMPUTE} ${TOT_DOY} ${EFAS_INPUT_PATH} ${EFAS_INPUT_FILE_PRE} ${EFAS_INPUT_FILE_POST} ${MOD_MESHMASK} ${RIVER_INFO} ${DAILY_RIVERS}_EFAStmp.nc ${RUNOFF_VAR} ${PRE_RUNOFF_VAR} ${LAT_IDX} ${LON_IDX} ${TIME_IDX}"

   # Define the name of the input field storing the values
   if [[ $PORIVER_OBS_FLAG == 1 ]]; then
      PRE_RUNOFF_VAR="po_${RUNOFF_VAR}"
   else
      PRE_RUNOFF_VAR=${CLIM_1D_RUNOFF_VAR}
   fi

   mv ${DAILY_RIVERS} ${DAILY_RIVERS}_EFAStmp.nc
   python ${PY_EFAS} ${WORKDIR} ${YEAR2COMPUTE} ${TOT_DOY} ${EFAS_INPUT_PATH} ${EFAS_INPUT_FILE_PRE} ${EFAS_INPUT_FILE_POST} ${MOD_MESHMASK} ${RIVER_INFO} ${DAILY_RIVERS}_EFAStmp.nc ${RUNOFF_VAR} ${PRE_RUNOFF_VAR} ${LAT_IDX} ${LON_IDX} ${TIME_IDX}
   echo ".. Done"
   # Move the ultimate output to the final output file
   mv ${DAILY_RIVERS}_EFAStmp.nc ${DAILY_RIVERS}
fi
######################
echo "Output dir: $WORKDIR.."
######################
