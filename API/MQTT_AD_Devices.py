import json
import yaml, time
# import os
# from numpy import dtype
# from datetime import datetime

import paho.mqtt.client as mqtt

def devtype_component(dt):
    return {
        'selector':         'select',
        'switch':           'switch',
        'tamper':           'binary_sensor',
        'connectivity':     'binary_sensor',
        'battery':          'binary_sensor',
        'linkpercent':      'sensor',
        'temperature':      'sensor',
        'dummy':            None
    }.get(dt, dt)

def devtype_class(dt):
    return {
        'selector':         'select',
        # 'switch':           'switch',
        # 'tamper':           'tamper',
        'linkpercent':      None,
        'dummy':            None
    }.get(dt, dt)

def devtype_icons(dt):
    return {
        'selector':         'mdi:alarm-light',
        'linkpercent':      'mdi:signal',
        'dummy':            None
    }.get(dt, None)

def devtype_units(dt):
    return {
        'linkpercent':      '%',
        'temperature':      '°C',
        'dummy':            None
    }.get(dt, None)

def devtype_value_template(dt):
    return {
        'linkpercent':      '{{ value_json.linkquality }}',
        'temperature':      '{{ value_json.temperature }}',
        'dummy':            None
    }.get(dt, None)

def normalized_name(name):
    name = name.replace(" ", "_").lower()
    name = name.replace(".", "_")
    name = name.replace("-", "_")
    return name

class MQTT_AD_Config(dict):

    def __init__(self, mqtt_client, discovery_topic="homeassistant", state_topic=None, config_file=None, debug = False, verbose = False):
        self.debug           = debug
        self.verbose         = verbose
        self.discovery_topic = discovery_topic
        if (state_topic is None):
            self.state_topic = discovery_topic
        else:
            self.state_topic = state_topic
        if self.state_topic == self.discovery_topic:
            self.hass = True
            print("Home assistant mode")
        else:
            self.hass = False
            print("Domoticz mode")
        self.mqttclient      = mqtt_client
        self.repeat_timeout  = 1200
        if config_file is not None:
            print("Reading device connfig from",config_file)
            with open(config_yaml_path) as config_file:
                self.device_config = yaml.safe_load(config_file)
        global mqconf
        mqconf = self  
        return
        

class MQTT_AD_Device:

    def __init__(self, friendly_name, unique_name, device_type):
        self.friendly_name   = normalized_name(friendly_name)
        unique_name          = normalized_name(unique_name)
        device_component     = devtype_component(device_type)
        device_topic         = f"{mqconf.state_topic}/{unique_name}_{device_type}"
        self.state_topic     = f"{device_topic}/state"
        self.discovery_topic = f"{mqconf.discovery_topic}/{device_component}/{unique_name}/{device_type}/config"
        self.send_interval   = 1200
        self.last_update     = 0
        self.last_state      = ''
        self.config = { 
            "name": self.friendly_name,
            "unique_id": unique_name,
            "~": device_topic,
            "stat_t" : "~/state",
            "cmd_t" : "~/set"
        }

        device_class = devtype_class(device_type)
        if device_class is not None:
            self.config['device_class'] = device_class

        icon = devtype_icons(device_type)
        if icon is not None:
            self.config['icon'] = icon

        unit = devtype_units(device_type)
        if unit is not None:
            self.config['unit_of_measurement'] = unit

        value_template = devtype_value_template(device_type)
        if value_template is not None:
            self.config['value_template'] = value_template
    
    def device_config_append(self, attributes):
        for a in attributes:
            self.config[a] = attributes[a]

    def device_config_publish(self):
        if mqconf.debug:
            print(self.friendly_name,"topic",self.discovery_topic,"publish config", self.config)

        mqconf.mqttclient.publish(self.discovery_topic, payload=json.dumps(self.config), qos=0, retain=True)
    
    def device_message(self, message, timestamp=None):
        if timestamp is not None:
            if timestamp != str(self.last_update):
                if mqconf.verbose:
                    print(self.friendly_name,"topic",self.state_topic,"update time",timestamp,"!=",self.last_update,"publish value", message)
                mqconf.mqttclient.publish(self.state_topic, message)
            else:
                if mqconf.debug:
                    print(self.friendly_name,"topic",self.state_topic,"same update timestamp",timestamp)

            self.last_update = timestamp
            return True

        epoch_time = int(time.time())
        if self.last_state != message or epoch_time > self.last_update + self.send_interval:
            if mqconf.verbose:
                print(self.friendly_name,"topic",self.state_topic,"publish value", message)
            mqconf.mqttclient.publish(self.state_topic, message)
            self.last_state = message
            self.last_update= epoch_time
            return True
        else:
            if mqconf.debug:
                print(self.friendly_name,"topic",self.state_topic,"same value", message)
            return False

    def device_json(self, values, timestamp=None):
        return self.device_message(json.dumps(values), timestamp)

