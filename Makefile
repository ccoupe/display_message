#
# Makefile for notify-luma aka dpymsg
#
PRJ=notify-luma
DESTDIR=/usr/local/lib/mqttnotify
SRCDIR=$(HOME)/Projects/iot/dpymsg
LAUNCH=dpyluma.sh
SERVICE=$(PRJ).service

NODE := $(shell hostname)
SHELL := /bin/bash 

$(HOME)/dpyluma:
	sudo apt install -y python3-venv
	python -m venv $(HOME)/dpyluma
	( \
	set -e ;\
	source $(HOME)/dpyluma/bin/activate; \
	pip install -r $(SRCDIR)/requirements.txt; \
	)

$(DESTDIR):
	sudo mkdir -p ${DESTDIR}
	sudo mkdir -p ${DESTDIR}/lib	
	sudo mkdir -p ${DESTDIR}/images
	sudo cp ${SRCDIR}/images/* ${DESTDIR}/images
	sudo cp ${SRCDIR}/lib/demo_opts.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/Homie_MQTT.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/LumaMessageDevice.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/Settings.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/dpyluma.py ${DESTDIR}
	sudo cp ${SRCDIR}/Makefile ${DESTDIR}
	sudo cp ${SRCDIR}/${NODE}.json ${DESTDIR}
	sudo cp ${SRCDIR}/requirements.txt ${DESTDIR}
	sudo cp ${SRCDIR}/${SERVICE} ${DESTDIR}
	sudo chown -R ${USER} ${DESTDIR}
	sed  s/{NODE}/$(NODE)/ <$(SRCDIR)/$(LAUNCH) >$(DESTDIR)/$(LAUNCH)
	sudo chmod +x ${DESTDIR}/${LAUNCH}
	sudo cp ${DESTDIR}/${SERVICE} /etc/systemd/system
	sudo systemctl enable ${SERVICE}
	sudo systemctl daemon-reload
	sudo systemctl restart ${SERVICE}
	
install: $(HOME)/dpyluma $(DESTDIR)

update: 
	sudo cp ${SRCDIR}/lib/Audio.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/MqttMycroft.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/Chatbot.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/Settings.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/bridge.py ${DESTDIR}
