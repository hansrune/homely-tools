#!/usr/bin/env python3

import time, sys, os, json, argparse, logging
import paho.mqtt.client as mqtt
from HomelyAPI import *
from MQTT_AD_Devices import *

progname  = os.path.splitext(os.path.basename(sys.argv[0]))[0]
component = {}
sleepfor  = 15 
alarm_previous_state = "in startup state"

# Set up root logger
logger = logging.getLogger(progname)
logging.basicConfig(stream=sys.stdout)

def alarmstates(state):
    return {
        'DISARMED':          'Disarmed',
        'ARM_PENDING':       'Disarmed',
        'ARM_STAY_PENDING':  'Armed stay',
        'ARMED_STAY':        'Armed stay',
        'ARM_NIGHT_PENDING': 'Armed night',
        'ARMED_NIGHT':       'Armed night',
        'ARM_AWAY_PENDING':  'Armed away',
        'ARMED_AWAY':        'Armed away',
        'BREACHED':          'Alarmed'
    }.get(state,"Error")

def alarmdomocodes(state):
    return {
        'DISARMED':          '0',
        'ARM_PENDING':       '0',
        'ARM_STAY_PENDING':  '0',
        'ARMED_STAY':        '0',
        'ARM_NIGHT_PENDING': '1',
        'ARMED_NIGHT':       '1',
        'ARM_AWAY_PENDING':  '2',
        'ARMED_AWAY':        '2'
    }.get(state,'')

def_user   = def_password =  ""
try:
	def_user = os.environ['HOMELY_USER']
except:
	pass
try:
	def_password = os.environ['HOMELY_PASSWORD']
except:pass

def_homename = ""
try: 
    def_homename = os.environ['HOMELY_HOME']
except:pass

def_discovery_prefix = "homeassistant"
try: 
    def_discovery_prefix = os.environ['MQTT_DISCOVERY']
except:pass

def_state_prefix = "homely"
try:
    def_state_prefix = os.environ['MQTT_STATE']
except:pass

def_mqtt_server="127.0.0.1"
try:
    def_mqtt_server = os.environ['MQTT_SERVER']
except:pass

def_mqtt_port=1883
try:
    def_mqtt_port = os.environ['MQTT_PORT']
except:pass

argp = argparse.ArgumentParser(prog=progname, description='Homely to MQTT Auto Discovery')
argp.add_argument('-u','--username',        default=def_user,                help="Homely username")
argp.add_argument('-p','--password',        default=def_password,            help="Homely password (only if you are alone on your system)") 
argp.add_argument('-l','--load',            default="",                      help="Load json state data from file") 
argp.add_argument('-s','--save',            default="",                      help="Save json state data to file") 
argp.add_argument(     '--home',            default=def_homename,            help="Home name in Homely") 
argp.add_argument(     '--siteprefix',      default="",                      help="Site prefix / home name") 
argp.add_argument(     '--domoticzurl',     default="",                      help="Homely password (only if you are alone on your system)") 
argp.add_argument(     '--sleep',           default=120, type=int,           help="Sleep interval") 
argp.add_argument('-d','--debug',           action="store_true",             help="Debug")
argp.add_argument('-v','--verbose',         action="store_true",             help="Verbose")
argp.add_argument(     '--discoveryprefix', default=def_discovery_prefix,    help="MQTT HA discovery prefix")
argp.add_argument(     '--stateprefix',     default=def_state_prefix,        help="MQTT HA state prefix")
argp.add_argument(     '--mqttserver',      default=def_mqtt_server,         help="MQTT server name or address")
argp.add_argument(     '--mqttport',        default=def_mqtt_port, type=int, help="MQTT server port")
args=argp.parse_args()


if args.debug:
    logger.setLevel(logging.DEBUG)
elif args.verbose:
    logger.setLevel(logging.INFO)

h = HomelyAPI(logger=logger)

if args.domoticzurl != "":
    domoticz_settings = h.get("Domoticz settings", args.domoticzurl + '/json.htm?type=command&param=getsettings')
    domoticz_seccode  = domoticz_settings['SecPassword']
    logger.debug("Domoticz security setting is %s",domoticz_seccode)

if args.load != "":
    with open(args.load, "r") as rfile:
        hs = json.load(rfile)
        rfile.close()
    if args.verbose: print(json.dumps(hs)) 
else:
    if args.username != "":
        homely_user = args.username

    if args.password != "":
        homely_password = args.password

    if args.username == "" or args.password == "":
        argp.print_help();
        exit(1)

    token = h.login(args.username, args.password)
    token = h.tokenrefresh()

    print('------------------------- My home quewry ---------------------------')
    myhome = h.findhome(args.home)
    print('------------------------- My home result ---------------------------')
    print(myhome)

    print('------------------------- Home state ----------------------------------')
    hs = h.homestatus()

    if args.save != "":
        with open(args.save, "w") as wfile:
            json.dump(hs, wfile)
            wfile.close()

logger.debug("------------------------- Device dump -------------------------")
for i in hs['devices']:
    logger.debug(json.dumps(i))

print("------------------------- Device table -------------------------")
for d in hs['devices']:
    dev_unique_id = d['serialNumber']
    for feature in d['features'].keys():
        # if feature not in ['alarm', 'temperature']:
        #     continue
        ds=d['features']['diagnostic']['states']
        online = 'online' if d['online'] else "offline"
        print(f"Serial {dev_unique_id} --> {d['modelName']} name {d['name']}-{feature} link state {online} links to {ds['networklinkaddress']['value']} strenght {ds['networklinkstrength']['value']}")

if args.siteprefix != "":
    sitename = args.siteprefix
else:
    sitename = hs['name']

mq = mqtt.Client(progname)
mq.connect(args.mqttserver, port=args.mqttport, keepalive=600)
mq.loop_start()
hm = MQTT_AD_Config(
    sitename,
    mq, 
    discovery_topic = args.discoveryprefix,
    state_topic = args.stateprefix,
    logger = logger
)

main_alarm = MQTT_AD_Device("Gateway", "Alarm", "alarmstate", "selector")
main_alarm.device_config_append({ 
    "options" : [ "Disarmed", "Armed stay", "Armed night", "Armed away", "Alarmed", "Transitioning", "Error" ],
    "initial_option" : "Transitioning"
})
main_alarm.device_config_publish()

devices_lqi = MQTT_AD_Device("Gateway", "Minimum link quality", "links", "linkpercent")
devices_lqi.device_config_publish()

devices_tamper = MQTT_AD_Device("Gateway", "Tamper switches", "tamper", "tamper")
devices_tamper.device_config_publish()

devices_online = MQTT_AD_Device("Gateway", "Connectivities", "connectivity", "connectivity")
devices_online.device_config_publish()

devices_lowbat = MQTT_AD_Device("Gateway", "Battery states", "battery", "battery")
devices_lowbat.device_config_publish()

for d in hs['devices']:
    serial    = d['serialNumber']
    devid     = d['id']
    devname   = d['name']
    modelname = d['modelName']
    for feature in d['features'].keys():
        ds=d['features'][feature]['states']
        for state in ds.keys():
            if state not in ['alarm','temperature']:
                continue
            dv = ds[state]['value']
            name_model = f"{devname}_{modelname}"
            logger.debug(f"Serial {serial} --> {modelname} name {devname} feature {feature} {state} {dv}")
            if feature == 'temperature':
                sub_device="temp"
                component[f"{devid}_{sub_device}"] = MQTT_AD_Device(devname, modelname, feature, sub_device, d)
                component[f"{devid}_{sub_device}"].device_config_publish()
            elif modelname == "Motion Sensor Mini" and state == 'alarm':
                sub_device="motion"
                component[f"{devid}_{sub_device}"] = MQTT_AD_Device(devname, modelname, feature, sub_device, d)
                component[f"{devid}_{sub_device}"].device_config_publish()
            elif modelname == "Window Sensor" and state == 'alarm':
                sub_device="door"
                component[f"{devid}_{sub_device}"] = MQTT_AD_Device(devname, modelname, feature, sub_device, d)
                component[f"{devid}_{sub_device}"].device_config_publish()


def alarm_state(ht):
    global alarm_previous_state
    try:
        st = alarmstates(ht)
        if st != alarm_previous_state:
            logger.info(f"Homely alarm state change to {ht} (previous state {alarm_previous_state})")
            alarm_previous_state = st
            main_alarm.device_message(st)
            if args.domoticzurl != "":
                ds = alarmdomocodes(ht)
                logger.info(f"Homely alarm state is {ht} --> Domoticz security code {st}")
                dr = h.get("Domoticz set security state", args.domoticzurl + '/json.htm?type=command&param=setsecstatus&secstatus=' + ds + '&seccode=' + domoticz_seccode)
    except KeyError:
        pass  

#
# SocketIO message handler - running in separate thread
#
def siomsg(smsg):
    logger.info('websocket callback:', smsg)
    t = smsg['type']
    d = smsg['data']
    if t == 'device-state-changed':
        devid = d['deviceId']
        for c in d['changes']:
            if c['stateName'] == 'temperature':
                id_subdevice=f"{devid}_temp"
                if id_subdevice in component:
                    component[id_subdevice].device_json({ "temperature": c['value'] }, timestamp = c['lastUpdated'])
                else:
                    logger.warning("Unknown temperature device id", devid)
            elif c['stateName'] == 'alarm':
                onoff = 'ON' if c['value'] else 'OFF'
                # 
                # Only motion sensors and window/door sensors supported
                #
                for sub_device in ['motion', 'door']:
                    id_subdevice=f"{devid}_{sub_device}"
                    if id_subdevice in component:
                        component[id_subdevice].device_message(onoff, timestamp = c['lastUpdated'])
                        break
    elif t == 'alarm-state-changed': 
        alarm_state(d['state'])

h.startsio(siomsg)

while True:
    logger.info("Sleep for %d seconds ... ", sleepfor)

    sleepsec = 0
    #
    # Chop it into 5 sec intervals to check for socketio disconnects
    #
    while (sleepsec < sleepfor):
        time.sleep(5)
        sleepsec = sleepsec + 5
        siorc = h.sioexit()
        if siorc > 0:
            logger.error("SocketIO initiated exit ... ")
            sys.exit(siorc)

    sleepfor = args.sleep

    logger.info("Refreshing alarm status ... ")
    token = h.tokenrefresh()
    hs    = h.homestatus()
    alarm_state(hs['alarmState'])

    devs_online  = "ON"
    devs_lowbat  = "OFF"
    devs_tamper  = "OFF"
    devs_lqi     = 100
    for d in hs['devices']:
        serial = d['serialNumber']
        devid     = d['id']
        devname   = d['name']
        modelname = d['modelName']

        if not d['online']:
            devs_online = "OFF"
        for feature in d['features'].keys():
            ds=d['features'][feature]['states']
            for state in ds.keys():
                dv = ds[state]['value']       if 'value'       in ds[state] else None 
                dt = ds[state]['lastUpdated'] if 'lastUpdated' in ds[state] else None
                if dv is None or dt is None:
                    logger.info(f"No value or lastUpdated for feature={feature}: device state ds={ds} state={state} ds[state]={ds[state]}")
                    continue
                name_model = f"{devname}_{modelname}"
                logger.debug(f"Serial {serial} --> {modelname} name {devname} feature {feature} {state} {dv}")
                
                #
                # Should not be needed any more , and is a good GUI indicator of socketio problems
                # Still handy to include as device creation may not happen until a value is sent
                #
                if feature == 'temperature':
                    component[f"{devid}_temp"].device_json({ "temperature": dv }, timestamp=dt)
                elif state == 'alarm':
                    onoff = 'ON' if dv else 'OFF'
                    if modelname == "Motion Sensor Mini":
                        component[f"{devid}_motion"].device_message(onoff, timestamp=dt)
                    elif modelname == "Window Sensor":
                        # Used mostly for doors - even if model name is Window Sensor
                        component[f"{devid}_door"].device_message(onoff, timestamp=dt)
                elif state == 'networklinkstrength' and int(dv) < devs_lqi:
                    devs_lqi = int(dv)
                elif state == 'low' and dv:
                    devs_lowbat = "ON"
                elif state == 'tamper' and dv:
                    devs_tamper = "ON"



    devices_lqi.device_json({ "linkquality": devs_lqi })
    devices_online.device_message(devs_online)
    devices_tamper.device_message(devs_tamper)
    devices_lowbat.device_message(devs_lowbat)
    
# vim:ts=4:sw=4
