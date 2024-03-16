#
# Makefile for notify-luma aka dpymsg
#
PRJ ?= notify-luma
DESTDIR ?= /usr/local/lib/mqttnotify
SRCDIR ?= $(HOME)/Projects/iot/dpymsg
LAUNCH ?= dpyluma.sh
SERVICE ?= $(PRJ).service
PYENV ?= ${DESTDIR}/luma-env

NODE := $(shell hostname)
SHELL := /bin/bash 

${PYENV}:
	sudo mkdir -p ${PYENV}
	sudo chown ${USER} ${PYENV}
	python -m venv ${PYENV}
	( \
	set -e ;\
	source ${PYENV}/bin/activate; \
	pip install -r $(SRCDIR)/requirements.txt; \
	)

setup_launch:
	sudo systemctl enable ${SERVICE}
	sudo systemctl daemon-reload
	sudo systemctl restart ${SERVICE}
	
setup_dir:
	sudo mkdir -p ${DESTDIR}
	sudo mkdir -p ${DESTDIR}/lib	
	sudo mkdir -p ${DESTDIR}/images
	sudo cp ${SRCDIR}/images/* ${DESTDIR}/images
	sudo cp ${SRCDIR}/Makefile ${DESTDIR}
	sudo cp ${SRCDIR}/${NODE}.json ${DESTDIR}
	sudo cp ${SRCDIR}/requirements.txt ${DESTDIR}
	sudo cp ${SRCDIR}/${SERVICE} ${DESTDIR}
	sudo chown -R ${USER} ${DESTDIR}
	sed  s!PYENV!${PYENV}! <${SRCDIR}/launch.sh >$(DESTDIR)/$(LAUNCH)
	sudo chmod +x ${DESTDIR}/${LAUNCH}
	sudo cp ${DESTDIR}/${SERVICE} /etc/systemd/system
	
update: 
	sudo cp ${SRCDIR}/lib/demo_opts.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/Homie_MQTT.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/LumaMessageDevice.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/Settings.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/dpyluma.py ${DESTDIR}

install: ${PYENV} setup_dir update setup_launch

clean: 
	sudo systemctl stop ${SERVICE}
	sudo systemctl disable ${SERVICE}
	sudo rm -f /etc/systemd/system/${SERVICE}
	sudo rm -rf ${DESTDIR}

realclean: clean
	rm -rf ${PYENV}
