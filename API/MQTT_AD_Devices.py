import json
import yaml
import time
import logging
import paho.mqtt.client as mqtt

default_logger = logging.getLogger(__name__)

def devtype_component(dt):
    return {
        'selector':         'select',
        'switch':           'switch',
        'tamper':           'binary_sensor',
        'connectivity':     'binary_sensor',
        'battery':          'binary_sensor',
        'motion':           'binary_sensor',
        'door':             'binary_sensor',
        'window':           'binary_sensor',
        'linkpercent':      'sensor',
        'temperature':      'sensor',
        'temp':             'sensor',
        'dummy':            None
    }.get(dt, dt)

def devtype_class(dt):
    return {
        'selector':         'select',
        'temp':             'temperature',
        'linkpercent':      None,
        'dummy':            None
    }.get(dt, dt)

def devtype_icons(dt):
    return {
        'selector':         'mdi:alarm-light',
        'linkpercent':      'mdi:signal',
        'door':             'mdi:door',
        'motion':           'mdi:motion-sensor',
        'dummy':            None
    }.get(dt, None)

def devtype_units(dt):
    return {
        'linkpercent':      '%',
        'temperature':      '°C',
        'temp':             '°C',
        'dummy':            None
    }.get(dt, None)

def devtype_value_template(dt):
    return {
        'linkpercent':      '{{ value_json.linkquality }}',
        'temperature':      '{{ value_json.temperature }}',
        'temp':             '{{ value_json.temperature }}',
        'dummy':            None
    }.get(dt, None)

def normalized_name(name):
    to_replace = { " " : "_",  "." : "_", "-" : "_", "æ" : "a", "ø" : "o", "å" : "a", "Æ" : "A", "Ø" : "O",  "Å" : "A" }
    
    for c in to_replace.keys():
      name = name.replace(c, to_replace[c])
    return name

class MQTT_AD_Config(dict):

    def __init__(self, sitename, mqtt_client, discovery_topic="homeassistant", state_topic=None, config_filename=None, logger=None):
        self.site = sitename
        if logger is None:
            self.logger = default_logger
        else:
            self.logger = logger

        self.discovery_topic = discovery_topic
        if (state_topic is None):
            self.state_topic = 'homely'
        else:
            self.state_topic = state_topic
        if self.state_topic == self.discovery_topic:
            self.hass = True
            self.logger.info("Home assistant mode")
        else:
            self.hass = False
            self.logger.info("Domoticz mode")
        self.mqttclient      = mqtt_client
        self.repeat_timeout  = 1200
        if config_filename is not None:
            self.logger.info("Reading device config from %s",config_file)
            with open(config_filename) as f_config:
                self.device_config = yaml.safe_load(f_config)
        global mqconf
        mqconf = self  
        return
        

class MQTT_AD_Device:

    def __init__(self, main_name, object_name, component, devattr={}):
        self.friendly_name   = normalized_name(f"{mqconf.site} {main_name} {object_name}")
        #self.friendly_name   = normalized_name(f"{mqconf.site} {main_name}")
        main_name            = normalized_name(f"{mqconf.site}_{main_name}")
        device_component     = devtype_component(component)
        device_topic         = f"{mqconf.state_topic}/{main_name}/{object_name}"
        self.state_topic     = f"{device_topic}/state"
        self.discovery_topic = f"{mqconf.discovery_topic}/{device_component}/{main_name}/{object_name}/config"
        self.send_interval   = 1200
        self.last_update     = 0
        self.last_timestamp  = 'init time'
        self.last_state      = 'init state'
        self.config = { 
            "name": f"{mqconf.site}_{main_name}",
            "unique_id": f"{mqconf.site}_{main_name}_{object_name}",
            #"object_id": f"{mqconf.site}_{main_name}_{object_name}",
            "state_topic" : f"{device_topic}/state",
            "command_topic" : f"{device_topic}/set",
            "device" : {
                "identifiers" : [ main_name ],
                "name" : main_name,
                "manufacturer" : "Homely provided",
                "model" : "Internal device"
            }
        }

        device_class = devtype_class(component)
        if device_class is not None:
            self.config['device_class'] = device_class

        icon = devtype_icons(component)
        if icon is not None:
            self.config['icon'] = icon

        unit = devtype_units(component)
        if unit is not None:
            self.config['unit_of_measurement'] = unit

        value_template = devtype_value_template(component)
        if value_template is not None:
            self.config['value_template'] = value_template
        
        try:
            self.config['device']['model'] = devattr['modelName']
        except KeyError:
            pass
            
    
    def device_config_append(self, attributes):
        for a in attributes:
            self.config[a] = attributes[a]

    def device_config_publish(self):
        mqconf.logger.debug("%s topic %s publish config %s", self.friendly_name,self.discovery_topic,self.config)
        mqconf.mqttclient.publish(self.discovery_topic, payload=json.dumps(self.config), qos=0, retain=True)
    
    def device_message(self, message, timestamp=None):
        epoch_time = int(time.time())
        if timestamp is not None:
            if timestamp != self.last_timestamp:
                mqconf.logger.info("%s topic %s update time %s != %s publish value %s", self.friendly_name, self.state_topic, timestamp, self.last_timestamp, message)
                mqconf.mqttclient.publish(self.state_topic, message)
                self.last_update= epoch_time
                self.last_timestamp = timestamp
            else:
                mqconf.logger.debug("%s topic %s has identical update timestamp %s",self.friendly_name,self.state_topic,timestamp)
            return True

        if self.last_state != message or epoch_time > self.last_update + self.send_interval:
            mqconf.logger.info("%s topic %s publish value %s", self.friendly_name,self.state_topic, message)
            mqconf.mqttclient.publish(self.state_topic, message)
            self.last_state = message
            self.last_update= epoch_time
            return True
        else:
            mqconf.logger.debug("%s topic %s same value %s",self.friendly_name,self.state_topic, message)
            return False

    def device_json(self, values, timestamp=None):
        return self.device_message(json.dumps(values), timestamp)

# vim:ts=4:sw=4
