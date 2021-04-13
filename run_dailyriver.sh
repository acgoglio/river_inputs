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
YEAR2COMPUTE=2016

# src directory (path of this script!)  workdir and your virtual environment
SRCDIR="/users_home/oda/ag15419/river_inputs/Killworth/"
WORKDIR="/work/oda/ag15419/tmp/river_inputs/"

# your virtual env
YOUR_PY_ENV="mappyenv"

# Input path/name (EAS system monthly river input file) and output name (EAS system daily river input file)
MONTHLY_RIVERS="/data/opa/mfs-dev/Med_static/MFS_EAS6_STATIC_V2/NEMO_DATA0/runoff_1m_nomask.nc"
DAILY_RIVERS="runoff_1d_nomask.nc"

# Csv file with rivers info
RIVER_INFO="rivers_info.csv"

# Executables:
# 1) Py script to extract climatological values from Input file
EXE_CLIM='extract_clim_river.py'
# 2) F90 Script (template) to compute pseudodischarges (Killworth matrix)
EXE_KILLWORTH_TEMP="killworth_temp.F90"
EXE_KILLWORTH="killworth_${YEAR2COMPUTE}.F90"
# 3) Py script to interpolate pseudodischarges and built daily file for EAS system 
PY_INTERP2DAILY_TEMP="daily_interp_temp.py"
PY_INTERP2DAILY="daily_${YEAR2COMPUTE}.py"

############################ DO NOT CHANGE THE CODE BENEATH THIS LINE ########################## 
# Load the environment for step 1
module load anaconda
source activate $YOUR_PY_ENV


# Check the existence of the workdir and mv into it
if [[ -d $WORKDIR ]]; then
   echo "I am linking files to work dir: $WORKDIR.."
   for TOBELINKED in $EXE_CLIM $EXE_KILLWORTH_TEMP $PY_INTERP2DAILY_TEMP $RIVER_INFO ; do 
       ln -svf ${SRCDIR}/${TOBELINKED} ${WORKDIR}/
   done
   echo "I am moving to work dir: $WORKDIR.."
   cd $WORKDIR
else
   echo "ERROR: Work dir $WORKDIR NOT Found! "
   exit
fi

# Check and copy the input file
if [[ -e $MONTHLY_RIVERS ]]; then
   cp -v $MONTHLY_RIVERS ${DAILY_RIVERS}
else 
   echo "ERROR: Input file $MONTHLY_RIVERS NOT Found! "
   exit
fi

# Clean the directory from previous outputs
echo "Clean the workdir from previous run outputs.."
sleep 3
for TOBERM in $( ls clim_*.txt); do
    rm  ${TOBERM}
done

echo "I am going to extract climatological values from input file: $MONTHLY_RIVERS ..."
python $EXE_CLIM $MONTHLY_RIVERS
echo "...Done!!"


# Load the environment for step 2
echo "Loading the environment for step 2.."
module load intel19.5/19.5.281 impi19.5/19.5.281 impi19.5/netcdf/C_4.7.2-F_4.5.2_CXX_4.3.1

echo "Working on year: $YEAR2COMPUTE"
# Loop on days and months (from november of year-1 to february year+1 )
STRING_NUM_OF_DAYS=""
STRING_NUM_OF_DAYS_2=""
# Built start date
START_YEAR=$(( $YEAR2COMPUTE - 1 ))
NEXT_START_MONTH=12
START_DATE=${START_YEAR}${NEXT_START_MONTH}01
# Loop on months
YEARTOTDAYS=0
IDX_DATE=$START_DATE
IDX_MONTH=0
while [[ $IDX_MONTH -lt 16 ]]; do   
      DATE2WRITE=$( date -u -d "${IDX_DATE} -1 day" +%Y%m%d )
      if [[ $IDX_MONTH == 3 ]] && [[ ${DATE2WRITE:6:2} == 29 ]]; then
         YEARTOTDAYS=366
      elif [[ $IDX_MONTH == 3 ]] && [[ ${DATE2WRITE:6:2} == 28 ]]; then
         YEARTOTDAYS=365
      fi
      # Concatenate strings 
      if [[ $IDX_MONTH -lt 2 ]]; then
         STRING_NUM_OF_DAYS=${STRING_NUM_OF_DAYS}$(echo -en "${DATE2WRITE:6:2},")
      elif [[ $IDX_MONTH -ge 2 ]] && [[ $IDX_MONTH -lt 14 ]]; then
         STRING_NUM_OF_DAYS=${STRING_NUM_OF_DAYS}$(echo -en "${DATE2WRITE:6:2},")
         STRING_NUM_OF_DAYS_2=${STRING_NUM_OF_DAYS_2}$(echo -en "${DATE2WRITE:6:2} ")
      elif [[ $IDX_MONTH -ge 14 ]] && [[ $IDX_MONTH -lt 16 ]]; then
         STRING_NUM_OF_DAYS=${STRING_NUM_OF_DAYS}$(echo -en "${DATE2WRITE:6:2}")
      fi
      IDX_DATE=$( date -u -d "${IDX_DATE} 1 month" +%Y%m%d )
      IDX_MONTH=$(( $IDX_MONTH + 1 ))
done

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
    INDEXES_OR=$(echo ${CLIM_FILE} | cut -f 2,3 -d"_" | cut -f 1 -d".")
    INDEXES=$(echo ${CLIM_FILE} | cut -f 2,3 -d"_" | cut -f 1 -d"."| sed -e "s/_/;/g" )
    RIVER_NAME="${INDEXES_OR}_$( grep "${INDEXES}" ${RIVER_INFO} | cut -f 6 -d";" )" || RIVER_NAME="${INDEXES_OR}_${INDEXES_OR}_River"
    echo "INDEXES=$INDEXES RIVER_NAME: $RIVER_NAME"
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
    CLIM_ALL=$(echo ${CLIM_ALL}${CLIM_PER_DAY}$(echo -en ",") | sed -e "s/,,//g" )
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
    # Sed file creation and sobstitution of parematers in the templates  
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
  
    echo "Interpolation.."
    python ${PY_INTERP2DAILY} ${RIVER_NAME} ${YEAR2COMPUTE}
    echo ".. Done"
done

######################
