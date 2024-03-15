#!/bin/bash 
PRJ=notify-luma
DESTDIR=/usr/local/lib/${PRJ}
SRCDIR=${HOME}/Projects/iot/dpymsg
LAUNCH=dpyluma.sh
SERVICE=${PRJ}.service

sudo mkdir -p ${DESTDIR}
sudo cp -a ${SRCDIR}/* ${DESTDIR}
sudo chown -R ${USER} ${DESTDIR}
sudo chmod +x ${DESTDIR}/${LAUNCH}
sudo cp ${DESTDIR}/${SERVICE} /etc/systemd/system
sudo systemctl enable ${SERVICE}
sudo systemctl daemon-reload
sudo systemctl restart ${SERVICE}
