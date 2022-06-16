# homely-tools

## Introduction

These Homely alarm services uses the Homely API to check on status of the alarm system, components and zigbee network - reporting statuses into home automations that use Home Asstant style MQTT with automatic device discovery.

The Homely API is available for subscribers from [Homely support](mailto:kundeservice@homely.no) upon request. It is probably not not the final API. The API is currently read-only, i.e. you cannot use these tools to change the state of the Homely alarm system. All API usage included here is based on periodic polls from the API servers provided. They are separate from the endpoints used by the alarm central and the Homely app.

It is recommended that you run these services provided here, the MQTT servers and the home automation services on the same host.Distributing the services is absolutely possible, but some further security measures should be taken.

## Features

For now, these services are implemented as Linux systemctl services only. Being small and simple, they should be pretty easy to set up if you have some basic Linux skills at hand. 

By default, the services will automatically start on system startup as well as restart upon failure. You can easily follow the status from `systemctl -fu homely2mqtt` or `systemctl -fu homely2domoticz`

### Domoticz alarm status updates

This part was the initial exploration of the Homely API. This service will simply updates the Domoticz alarm state, and a virtual multiselect switch based on the polled Homely alarm state

### Homely to MQTT alarm state and components monitor

This service will provide:

- Alarm status updates
    - In Domoticz, the built-in alarm state is directly updated using the JSON API 
- A switch to monitor that all components reports being online from your alarm central
- A switch to monitor that all components have an OK battery status
- A switch to monitor that no components have been tampered with
- A measurement device for the lowest link quality (in %) reported for all alarm components
- Reporting all the temperature values for all alarm components that have a temp sensor 
- At service startup, a topology listing of the Homely zigbee components is also provided (you can find it later from `journalctl -u homely2mqtt`)

This service uses the MQTT Auto Discovery features in Home Assistant and recent releases of Domoticz (and probably more systems) for fully automatic device creation

The service will listen for web socket events as well as poll the home / device statuses. The web socket will deliver updates in near real time. The polled status is a fallback for the websocket not being updated as well as populating MQTT auto discovery devices that do not appear until a payload message is received.

## Download, update and install 

Please download locally to a user with sudo root privileges, and install from there:

```bash
git clone https://github.com/hansrune/homely-tools.git
cd homely-tools
```

... or update your local source using `git pull`

### Initial tests

You can test the communication with the API services as follows:

```bash
export HOMELY_USER=<your Homely login name (email)
export HOMELY_PASSWORD=<your password>
export PYTHONPATH="$PWD/API"
./ws/ws-test-threaded.py -d
```

This should list some home details, device details, a device table, then start the websocket communication, ending something like this:

```txt
INFO:engineio.client:WebSocket upgrade was successful
INFO:engineio.client:Sending packet PING data None
INFO:engineio.client:Received packet PONG data None
INFO:engineio.client:Received packet MESSAGE data 2["event",{"type":"device-state-changed","data":{"deviceId":"e143ddc5-33e9-492c-b1be-...","gatewayId":"5e2eed4f-f018-4c8f-ba37-...","locationId":"fb324b11-8301-4749-8a8f-...","modelId":"87fa1ae0-824f-4d42-be7a-...","rootLocationId":"5b11a8b9-e90c-40b5-b2d0-...","changes":[{"feature":"temperature","stateName":"temperature","value":19.2,"lastUpdated":"2022-HH-MMT06:36:04.875Z"}]}}]
INFO:socketio.client:Received event "event" [/]
websocket callback: {'type': 'device-state-changed', 'data': {'deviceId': 'e143ddc5-33e9-492c-b1be-...', 'gatewayId': '5e2eed4f-f018-4c8f-ba37-...', 'locationId': 'fb324b11-8301-4749-8a8f-...', 'modelId': '87fa1ae0-824f-4d42-be7a-...', 'rootLocationId': '5b11a8b9-e90c-40b5-b2d0-...', 'changes': [{'feature': 'temperature', 'stateName': 'temperature', 'value': 19.2, 'lastUpdated': '2022-XX-09T06:36:04.875Z'}]}}
INFO:engineio.client:Sending packet PING data None
INFO:engineio.client:Received packet PONG data None
.
.
INFO:engineio.client:Sending packet PING data None
INFO:engineio.client:Received packet PONG data None
websocket callback: {'type': 'alarm-state-changed', 'data': {'locationId': '5b11a8b9-e90c-40b5-b2d0-...', 'state': 'ARM_NIGHT_PENDING', 'timestamp': '2022-HH-MMT06:52:23.656Z'}}
INFO:engineio.client:Received packet MESSAGE data 2["event",{"type":"alarm-state-changed","data":{"locationId":"5b11a8b9-e90c-40b5-b2d0-...","state":"ARMED_NIGHT","userId":"1985b1af-62de-4cc2-8fe7-...","userName":"Your full name","timestamp":"2022-HH-MMT06:52:23.605Z","eventId":1249}}]
INFO:socketio.client:Received event "event" [/]
websocket callback: {'type': 'alarm-state-changed', 'data': {'locationId': '5b11a8b9-e90c-40b5-b2d0-...', 'state': 'ARMED_NIGHT', 'userId': '1985b1af-62de-4cc2-8fe7-...', 'userName': 'Your full name', 'timestamp': '2022-HH-MMT06:52:23.605Z', 'eventId': 1249}}
INFO:engineio.client:Sending packet PING data None
INFO:engineio.client:Received packet PONG data None
```

### Initial installation steps

On initial setup, some prereqs need to be provided:

1. You will need to copy the settings template and modify that with your own values. For example:

    ```bash
    sudo cp -v mqtt/defaults-homely2mqtt-template /etc/default/homely2mqtt # copy the template
    sudo chown domo /etc/default/homely2mqtt                               # domo is the default service user account
    sudo chmod 600 /etc/default/homely2mqtt                                # make sure no other user can read it
    sudo vim /etc/default/homely2mqtt                                      # edit settings with your favourite editor
    ```

2. You will also need to install required python3 modules. Currently something like this:

    ```bash
    sudo pip3 install request pahoo-mqtt "python-socketio[client]<5.0"
    ```

3. A separate user account for running the service is recommended. The default setup assumes that user `domo` exists

### Install or update steps

If you are happy with running the service from `/opt/homely2mqtt` as the user `domo`, you can install or update as follows:

```bash
mqtt/install-mqtt.sh
```

After some prereq tests, the commands in effect are echoed. The intent is simply to make it easier to understand the setup process, and possibly adapt things as needed.

You will have to break the `journalctl -fu` command being run at the end of this install / update script.

### Configuration options

Available command line options can be found from `/opt/homely2mqtt/homely2mqtt.py -h`

Normally, command line options will be added to `FLAGS` settings in the systemctl service definition file (`homely2mqtt.service`)

Settings like username and password should be added to the service environment file (`/etc/default/homely2mqtt`) with strict permissions (`chmod 600 /etc/default/homely2mqtt`). 

You should also run the service as a dedicated user (default *domo*) to avoid exposing the environment to non-root users. If you want to change this username, modify `homely2mqtt.service`

Available environment settings:

* `HOMELY_USER` - Your Homely username (normally your email address)
* `HOMELY_PASSWORD` - Your Homely password
* `MQTT_DISCOVERY` - The MQTT discovery topic prefix, normally *homeassistant* 
* `MQTT_STATE` - The MQTT state topic prefix. For HA users, this is normally also *homeassistant* or *hass/status*
* `MQTT_SERVER` - Defaults to 127.0.0.1
* `MQTT_PORT` - Defaults to 1883
