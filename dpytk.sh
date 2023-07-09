#!/bin/bash
#cd /usr/local/lib/dpymac
cd /home/ccoupe/Projects/iot/dpymsg
node=`hostname`
python3 dpymsg.py -s -c ${node}.json
