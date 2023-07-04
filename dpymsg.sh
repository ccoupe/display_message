#!/bin/bash
cd /usr/local/lib/dpymac
node=`hostname`
python3 dpymac.py -s -c ${node}.json
