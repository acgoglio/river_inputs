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
module purge

echo "*********** Daily river input 4 EAS System ***********"
####################### SET THE FOLLOWING VARS: ############################################

# -----Input infos---------
# Year
YEAR2COMPUTE=2020

# src directory (path of this script!), workdir and your py virtual environment name
SRCDIR="/users_home/oda/ag15419/river_inputs/Killworth/"
WORKDIR="/work/oda/ag15419/tmp/river_inputs/kill_efas/"
# your virtual env
YOUR_PY_ENV="mappyenv"

# Input path/name (EAS system monthly river input file) and output name (EAS system daily river input file)
MONTHLY_RIVERS="/data/opa/mfs-dev/Med_static/MFS_EAS6_STATIC_V2/NEMO_DATA0/runoff_1m_nomask.nc"
DAILY_RIVERS="runoff_1d_nomask_${YEAR2COMPUTE}.nc"

# NEMO mesh mask file (needed for Po river pre-processing)
MOD_MESHMASK="/work/oda/ag15419/PHYSW24_DATA/TIDES/DATA0/mesh_mask.nc"

# -----PO River inputs---------

# Flag to sobstitute observed values to the climatological ones for the Po river (to activate set PORIVER_OBS_FLAG=1)
PORIVER_OBS_FLAG=0
# Prename of the Po river in the csv file
PO_RIVER_PRENAME='Po_' 
PO_LEVANTE_NAME='Po_di_Levante'
# Path of 30m arpae obs and code of runoff field in the database
# WARNING: if pre-name of the file is empty you should put 'NAN' 
PO_INPUT_PATH='/data/oda/ag15419/RIVERS_DATA/PO/30m/'
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
EFAS_FLAG=1
# Path to time-series
EFAS_INPUT_PATH='/users_home/oda/ag15419/river_inputs/Killworth/'
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
# 2) F90 Script (template) to compute pseudodischarges (Killworth matrix)
EXE_KILLWORTH_TEMP="killworth_temp_12.F90" # killworth_temp_12.F90
EXE_KILLWORTH="killworth_${YEAR2COMPUTE}_12.F90" # killworth_${YEAR2COMPUTE}_12.F90
# 3) Py script to interpolate pseudodischarges and built daily file for EAS system 
PY_INTERP2DAILY_TEMP="daily_interp_temp.py" # daily_interp_temp_12.py
PY_INTERP2DAILY="daily_${YEAR2COMPUTE}.py" # daily_${YEAR2COMPUTE}_12.py
# 4) Py script to pre-process Po river obs and substitute the time series in the out file
PY_PORIVER_OBS="po_river_daily.py"
# 5) Py script to substitute the EFAS time seies where available
PY_EFAS="efas.py"


############################ DO NOT CHANGE THE CODE BENEATH THIS LINE ########################## 
# Load the environment for step 1
module load anaconda
source activate $YOUR_PY_ENV


# Check the existence of the workdir and mv into it
if [[ -d $WORKDIR ]]; then
   echo "I am linking files to work dir: $WORKDIR.."
   for TOBELINKED in $EXE_CLIM $EXE_KILLWORTH_TEMP $PY_INTERP2DAILY_TEMP $RIVER_INFO $PY_PORIVER_OBS $PY_EFAS ; do 
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

# Count days in the year
TOT_DOY=365
DAYS_CHECK=$(( ${YEAR2COMPUTE} % 4 ))
if [[ ${DAYS_CHECK} == 0 ]]; then
   TOT_DOY=$(( $TOT_DOY + 1 ))
fi
echo "Days in ${YEAR2COMPUTE} are $TOT_DOY!"

# Loop on days and months (from november of year-1 to february year+1 )
# To extract array of month len
STRING_NUM_OF_DAYS=""
STRING_NUM_OF_DAYS_2=""
# Built start date
START_YEAR=$(( $YEAR2COMPUTE - 1 ))
NEXT_START_MONTH=12
START_DATE=${START_YEAR}${NEXT_START_MONTH}01
# Loop on months
IDX_DATE=$START_DATE
IDX_MONTH=0
while [[ $IDX_MONTH -lt 16 ]]; do   
      DATE2WRITE=$( date -u -d "${IDX_DATE} -1 day" +%Y%m%d )
      # Concatenate strings 
      if [[ $IDX_MONTH -lt 2 ]]; then
         STRING_NUM_OF_DAYS=${STRING_NUM_OF_DAYS}$(echo -en "${DATE2WRITE:6:2},")
      elif [[ $IDX_MONTH -ge 2 ]] && [[ $IDX_MONTH -lt 14 ]]; then
         STRING_NUM_OF_DAYS=${STRING_NUM_OF_DAYS}$(echo -en "${DATE2WRITE:6:2},")
         STRING_NUM_OF_DAYS_2=${STRING_NUM_OF_DAYS_2}$(echo -en "${DATE2WRITE:6:2} ")
      elif [[ $IDX_MONTH -ge 14 ]] && [[ $IDX_MONTH -lt 15 ]]; then
         STRING_NUM_OF_DAYS=${STRING_NUM_OF_DAYS}$(echo -en "${DATE2WRITE:6:2},")
      elif [[ $IDX_MONTH -eq 15 ]]; then
         STRING_NUM_OF_DAYS=${STRING_NUM_OF_DAYS}$(echo -en "${DATE2WRITE:6:2}")
      fi
      IDX_DATE=$( date -u -d "${IDX_DATE} 1 month" +%Y%m%d )
      IDX_MONTH=$(( $IDX_MONTH + 1 ))
done

# Clean the directory from previous outputs
echo "Clean the workdir from previous run outputs.."
sleep 3
for TOBERM in $( ls clim_*.txt); do
    rm  ${TOBERM}
done

echo "I am going to extract climatological values from input file: $MONTHLY_RIVERS and built the output file template: ${DAILY_RIVERS}_temp ..."
# Run the code wich needs as args input and output names + num of days + all the dimension and variables names of input and output fields
python $EXE_CLIM $MONTHLY_RIVERS ${DAILY_RIVERS}_temp.nc $TOT_DOY $LAT_IDX $LON_IDX $TIME_IDX $LAT_2D $LON_2D $MASK_VAR $RUNOFF_VAR $SALINITY_VAR $CLIM_1M_RUNOFF_VAR $NAME_VAR $STRING_NUM_OF_DAYS
echo "...Done!!"


# Load the environment for step 2
echo "Loading the environment for step 2.."
module load intel19.5/19.5.281 impi19.5/19.5.281 impi19.5/netcdf/C_4.7.2-F_4.5.2_CXX_4.3.1


# Built and Compile the executable
echo "I am building the Killworth executable.."
# Sed file creation and sobstitution of parematers in the templates  
SED_FILE=sed_file.txt
cat << EOF > ${SED_FILE}
   s/%NOV_TO_FEB_NUM_OF_DAYS%/${STRING_NUM_OF_DAYS}/g
EOF
sed -f ${SED_FILE} ${EXE_KILLWORTH_TEMP} > ${EXE_KILLWORTH}
rm ${SED_FILE}
echo ".. Done"

# Compile the code
echo "Compiling the code.."
NEW_EXECUTABLE="x_killworth_${YEAR2COMPUTE}.exe"
ifort -g -CB ${EXE_KILLWORTH} -o ${NEW_EXECUTABLE} ${FFLAGS} ${LDFLAGS} || echo "ERROR in compiling ${EXE_KILLWORTH}..."
echo "...Done!!"

# Run the executable to generate txt pseudodischearge files
echo "Clean the workdir from previous run outputs.."
sleep 3
for TOBERM in $( ls pseudo_*.txt); do
    rm  ${TOBERM}
done

echo "Computing the pseudodischarges.."
for CLIM_FILE in $(ls clim_*.txt); do
    PSEUDO_FILENAME=$(echo ${CLIM_FILE} | sed -e "s/clim_/pseudo_/g" )
    ./${NEW_EXECUTABLE} ${CLIM_FILE} > ${PSEUDO_FILENAME}
done
echo "...Done!!"

# Load the environment for step 3
#module load $YOUR_PY_ENV
#source activate mappyenv

# Build arrays for step 3
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
    VAL=$( cat $CLIM_FILE )
    IDX_VAL=1
    CLIM_ALL=""
    for DAYS_TOT in $STRING_NUM_OF_DAYS_2; do
       for IDX_DAYS in $( seq 1 1 $DAYS_TOT ); do
           CLIM_PER_DAY=$( echo -en $( echo "${VAL}" | cut -f $IDX_VAL -d " "))
           CLIM_ALL=${CLIM_ALL}${CLIM_PER_DAY}$(echo -en ",")
       done
       IDX_VAL=$(( $IDX_VAL + 1 ))
    done
    CLIM_ALL=$(echo ${CLIM_ALL}$(echo -en ",") | sed -e "s/,,//g" )
    # Read pseudodischarges 
    PSEUDO_ALL=""
    TIMEINOUT_ALL=""
    while read LINE; do
         TIME_PER_MONTH=$( echo $LINE | cut -f 1 -d" ")
         PSEUDO_PER_MONTH=$( echo $LINE | cut -f 2 -d" ")
         PSEUDO_ALL=${PSEUDO_ALL}${PSEUDO_PER_MONTH}$(echo -en ",")
         TIMEINOUT_ALL=${TIMEINOUT_ALL}${TIME_PER_MONTH}$(echo -en ",")
    done < ${PSEUDO_FILENAME}
    PSEUDO_ALL=$(echo ${PSEUDO_ALL}$(echo -en ",") | sed -e "s/,,//g" )
    TIMEINOUT_ALL=$(echo ${TIMEINOUT_ALL}$(echo -en ",") | sed -e "s/,,//g" )

    # Built the script
    echo "I am building the script.."
    # Sed file creation and sobstitution of parameters in the templates  
    SED_FILE=sed_file.txt
    cat << EOF > ${SED_FILE}
    s/%CLIM_ALL%/${CLIM_ALL}/g
    s/%PSEUDO_ALL%/${PSEUDO_ALL}/g
    s/%TIMEINOUT_ALL%/${TIMEINOUT_ALL}/g
    s/%NOV_TO_FEB_NUM_OF_DAYS%/${STRING_NUM_OF_DAYS}/g
EOF
    sed -f ${SED_FILE} ${PY_INTERP2DAILY_TEMP} > ${PY_INTERP2DAILY}
    rm ${SED_FILE}
    echo ".. Done"
  
    echo "I am doing the Interpolation and the plot.."
    cp ${DAILY_RIVERS}_temp.nc ${DAILY_RIVERS}_tmp.nc
    python ${PY_INTERP2DAILY} ${RIVER_LAT} ${RIVER_LON} ${RIVER_NAME} ${RIVER_NUM} ${DAILY_RIVERS} ${YEAR2COMPUTE} ${CLIM_1D_RUNOFF_VAR} ${CLIM_1M_RUNOFF_VAR} ${MASK_VAR} ${NAME_VAR} ${LAT_IDX} ${LON_IDX} ${TIME_IDX}
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

