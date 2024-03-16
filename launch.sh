#!/bin/bash
source PYENV/bin/activate
cd /usr/local/lib/mqttnotify
node=`hostname`
python3 dpyluma.py -s -c ${node}.json
