#!/bin/bash

WORKING_PATH=/opt/ametro-services/manual
INNOEX_FILE=${WORKING_PATH}/innoextract
INNO_FILE=${WORKING_PATH}/innoextract-1.7-linux/innoextract
PMETRO_FILE=${WORKING_PATH}/pMetroSetup.exe

if [ -f $INNO_FILE ]; then
    echo "File $INNO_FILE exists, download skipped."
else
    echo "File $INNO_FILE does not exist, download."
    wget http://constexpr.org/innoextract/files/innoextract-1.7-linux.tar.xz -O ${INNOEX_FILE}.tar.xz -q
    unxz ${INNOEX_FILE}.tar.xz
    tar -xvf ${INNOEX_FILE}.tar
fi

if [ -f $PMETRO_FILE ]; then
    echo "File $PMETRO_FILE exists, removing."
    rm $PMETRO_FILE
fi

wget http://pmetro.su/download/pMetroSetup.exe -O ${PMETRO_FILE} -q

${INNO_FILE} ${PMETRO_FILE}




