# Install these dependencies: sudo apt-get install cc65 srecord
# Adjust the run address to match the .org in the source code


#DB_PATH=/var/lib/sensor_dashboard
STATIC_PATH=/etc/sensor_dashboard
SCRIPT_PATH=/usr/local/bin/sensor_dashboard
DB_PATH=/media/usbdisks/datadisk2/share1/sensor_dashboard

SERVICE_PATH=/etc/systemd/system

DB_NAME=sensorsite.db
VENV_NAME=.venv
SERVICE_NAME=sensor_dashboard.service
SERVICE_USER=www-data
#SERVICE_USER=artimus
VENV_PATH=$(SCRIPT_PATH)/$(VENV_NAME)
VENV_BIN=$(VENV_PATH)/bin

TEST_PATH=/tmp/sensor_dashboard
TESTVENV_PATH=$(TEST_PATH)/$(VENV_NAME)

define SERVICE_SCRIPT
[Unit]
Description=Sensor Dashboard Server Service
After=network.target

[Service]
Type=simple
User=$(SERVICE_USER)
ExecStart=$(VENV_BIN)/python3 $(SCRIPT_PATH)/src/sensor_dashboard_server.py -d $(DB_PATH)/apprepo.db -s $(STATIC_PATH)/static run
Restart=always
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=sensor_dashboard

[Install]
WantedBy=multi-user.target
endef
export SERVICE_SCRIPT

all: install

console:
	$(VENV_BIN)/python3


testinstall:
	python3 -m venv $(TESTVENV_PATH)
	. $(TESTVENV_PATH)/bin/activate
	$(TESTVENV_PATH)/bin/pip install aiohttp
	$(TESTVENV_PATH)/bin/pip install aiohttp_session
	$(TESTVENV_PATH)/bin/pip install cryptography
	$(TESTVENV_PATH)/bin/pip install sqlite-web

testuninstall:
	rm -R $(TEST_PATH)

run:
	$(TESTVENV_PATH)/bin/python3 ./src/sensor_dashboard_server.py -d $(TEST_PATH)/apprepo.db -s ./static run

views:
	$(TESTVENV_PATH)/bin/python3 ./src/sensor_dashboard_server.py -d $(TEST_PATH)/apprepo.db -s ./static execsql appviews.sql

clearstats:
	$(VENV_BIN)/python3 ./src/sensor_dashboard_server.py -d $(DB_PATH)/apprepo.db -s ./static execsql clearstats.sql

browsedb:
	$(TESTVENV_PATH)/bin/sqlite_web -H 0.0.0.0 -x $(TEST_PATH)/apprepo.db

generate_service:
	@echo "$$SERVICE_SCRIPT" > $(SERVICE_NAME)

install:
	mkdir -p $(SCRIPT_PATH)
	mkdir -p $(DB_PATH)
	mkdir -p $(STATIC_PATH)
	cp -r ./static $(STATIC_PATH)
	cp -r ./src $(SCRIPT_PATH)
	python3 -m venv $(VENV_PATH)
	. $(VENV_BIN)/activate
	$(VENV_BIN)/pip install aiohttp
	$(VENV_BIN)/pip install aiohttp_session
	$(VENV_BIN)/pip install cryptography
	chmod -R 750 $(SCRIPT_PATH)
	chmod -R 750 $(STATIC_PATH)
	chmod -R 770 $(DB_PATH)
	chgrp -R $(SERVICE_USER) $(SCRIPT_PATH)
	chgrp -R $(SERVICE_USER) $(STATIC_PATH)
	chgrp -R $(SERVICE_USER) $(DB_PATH)

upgrade:
	cp -ruv ./static $(STATIC_PATH)
	cp -ruv ./src $(SCRIPT_PATH)
	chmod -R 750 $(SCRIPT_PATH)
	chmod -R 750 $(STATIC_PATH)
	chgrp -R $(SERVICE_USER) $(SCRIPT_PATH)
	chgrp -R $(SERVICE_USER) $(STATIC_PATH)

uninstall:
	rm -R $(SCRIPT_PATH)
	rm -R $(DB_PATH)
	rm -R $(STATIC_PATH)
#	rm $(SERVICE_PATH)/$(SERVICE_NAME)

activate:
	@echo "$$SERVICE_SCRIPT" > $(SERVICE_PATH)/$(SERVICE_NAME)
	systemctl daemon-reload
	systemctl enable $(SERVICE_NAME)

deactivate:
	systemctl stop $(SERVICE_NAME)
	systemctl disable $(SERVICE_NAME)
	rm $(SERVICE_PATH)/$(SERVICE_NAME)


testpost:
	curl -d "identifier=3762djh827sd&room_temperature=26.98&air_pressure=1016.02" http://localhost:8080/sensorreading

testget:
	curl http://localhost:8080/getcurrentstats
#	curl -d "username=John&password=252521" http://localhost:8080/table/add/userlist
#	curl http://localhost:8080/view/select/userlist?username=John
#	curl http://localhost:8080/table/delete/userlist?user_id=2


