#! /bin/bash
PRJ=notify-luma
DESTDIR=/usr/local/lib/${PRJ}
SRCDIR=${HOME}/Projects/iot/dpymsg
LAUNCH=${PRJ}.sh
SERVICE=${PRJ}.service

sudo cp -a ${SRCDIR}/* ${DESTDIR}
sudo systemctl restart ${SERVICE}
