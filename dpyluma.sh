#!/bin/bash
source /home/ccoupe/tb-env/bin/activate
cd /usr/local/lib/mqttnotify
node=`hostname`
python3 dpyluma.py -s -c ${node}.json
