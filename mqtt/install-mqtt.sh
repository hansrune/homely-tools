#!/bin/bash
PROG=$( basename $0 .sh )
SERVICE="homely2mqtt"
REQUIREMENTS="requests paho.mqtt.client:paho-mqtt socketio:python-socketio[client]<5.0"

SRCDIR=$( dirname $0 )
DESTDIR="/opt/${SERVICE}/"

echo "${PROG}: Checking prereqs ..." >&2

if [ ! -f "/etc/default/${SERVICE}" ]
then
    echo "${PROG}: There is no configuration file in /etc/default/${SERVICE}" >&2
    echo "${PROG}: Please create from ${SRCDIR}/defaults-${SERVICE}-template, and make sure it is readable only from the ${SERVICE} service" >&2
    exit 1
fi

for R in ${REQUIREMENTS}
do 
   python3 -c "import ${R%:*}" >& /dev/null && continue
   echo "${PROG}: python3 cannot import ${R%:*}. Please install with \"pip3 install '${R#*:}'\" or similar" >&2
   exit 1
done

set -x
sudo mkdir -p ${DESTDIR}
sudo chown ${USER} ${DESTDIR}

if [ -f "${DESTDIR}/${SERVICE}.service" ] 
then
    echo "${PROG}: Leaving existing ${DESTDIR}/${SERVICE}.service as is. To update: cp -v ${SRCDIR}/${SERVICE}.service ${DESTDIR}/${SERVICE}.service"
else
    cp -v ${SRCDIR}/${SERVICE}.service ${DESTDIR}/${SERVICE}.service
fi
cp -v ${SRCDIR}/${SERVICE}.py ${SRCDIR}/../API/HomelyAPI.py ${SRCDIR}/../API/MQTT_AD_Devices.py ${DESTDIR}/
chmod u=rwx,go=rx ${DESTDIR}/*.py
chmod a+rX ${DESTDIR} ${DESTDIR}/*
sudo cp -v ${DESTDIR}/${SERVICE}.service /lib/systemd/system/${SERVICE}.service
sudo systemctl daemon-reload
sudo systemctl restart ${SERVICE}
sudo systemctl enable ${SERVICE}
sudo journalctl -fu ${SERVICE}

# vim:ts=4:sw=4
