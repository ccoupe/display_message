#!/bin/bash
cd /usr/local/lib/mqttnotify
#cd /home/ccoupe/Projects/iot/dpymsg
node=`hostname`
python3 dpyluma.py -s -c ${node}.json
