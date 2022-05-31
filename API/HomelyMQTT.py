#!/usr/bin/env python3
#
#

import time, sys, os, datetime
import yaml, json
import logging
import paho.mqtt.client as mqtt

class Device:
    def __init__(self, mqtt_client, discovery_topic="homeassistant", state_topic=None, config_file=None, debug = False):
        self.debug           = self.verbose = debug
        self.discovery_topic = discovery_topic
        if (state_topic is None):
            self.state_topic = discovery_topic
        else:
            self.state_topic = state_topic
        self.mqtt            = mqtt_client
        return


# dev_unique_id = progname + '.' + hs['name'] + '.alarmstate'
# dev_unique_id = dev_unique_id.replace(" ", "_").lower()
# dev_unique_id = dev_unique_id.replace(".", "_").lower()
# dev_state_topic  = f"{args.stateprefix}/select/{dev_unique_id}"
# dev_config_topic = f"{args.discoveryprefix}/select/{dev_unique_id}/config"
# dev_config_select = { 
#     "name" : "Homely alarm state",
#     "unique_id" : dev_unique_id,
#     "~" : dev_state_topic,
#     "stat_t" : "~",
#     "cmd_t" : "~/set",
#     "options" : [ "Disarmed", "Armed stay", "Armed night", "Armed away", "Transitioning", "Error" ],
#     "initial_option" : "Disarmed",
#     #"dev" : { "ids" : , "name" : , "sw": , "mf" : "Homely"}
#     "device_class" : "selector",
#     "icon": "mdi:alarm-light"
# }

# mclient.publish(dev_config_topic, payload=json.dumps(dev_config_select), qos=0, retain=True)

# for d in hs['devices']:
#     dev_unique_id = d['serialNumber']
#     for feature in d['features'].keys():
#         # if feature not in ['alarm', 'temperature']:
#         #     continue
#         ds=d['features']['diagnostic']['states']
#         if d['online']:
#             online = "online"
#         else:
#             online = "offline"
#         print(f"Serial {dev_unique_id} --> {d['modelName']} name {d['name']}-{feature} link state {online} links to {ds['networklinkaddress']['value']} strenght {ds['networklinkstrength']['value']}")




# vim:ts=4:sw=4
