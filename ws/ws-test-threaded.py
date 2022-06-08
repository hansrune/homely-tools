#!/usr/bin/env python3
#
#

# sudo pip3 install "python-socketio[client]<5.0"

import time, sys, os, json, argparse
import socketio
import threading
#import asyncio
from HomelyAPI import *
from MQTT_AD_Devices import *
import logging
import sys

progname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def_user = def_password =  ""
try:
	def_user = os.environ['HOMELY_USER']
except:
	pass
try:
	def_password = os.environ['HOMELY_PASSWORD']
except:pass

argp = argparse.ArgumentParser(prog=progname, description='Homely websocket tests')
argp.add_argument('-u','--username',        default=def_user,                help="Homely username")
argp.add_argument('-p','--password',        default=def_password,            help="Homely password (only if you are alone on your system)") 
argp.add_argument('-l','--load',            default="",                      help="Load json state data from file") 
argp.add_argument('-s','--save',            default="",                      help="Save json state data to file") 
argp.add_argument(     '--home',            default="",                      help="Home name in Homely") 
argp.add_argument(     '--sleep',           default=120, type=int,           help="Sleep interval") 
argp.add_argument('-d','--debug',           action="store_true",             help="Debug")
argp.add_argument('-v','--verbose',         action="store_true",             help="Verbose")
args=argp.parse_args()


h = HomelyAPI(args.debug, args.verbose)

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

    print('------------------------- Find home -----------------------------------')
    myhome = h.findhome(args.home)
    print(myhome)

    print('------------------------- Home state ----------------------------------')
    hs = h.homestatus()


if args.debug:
    print('------------------------- Home devices --------------------------------')
    for i in hs['devices']:
        print(json.dumps(i))

for d in hs['devices']:
    dev_unique_id = d['serialNumber']
    for feature in d['features'].keys():
        # if feature not in ['alarm', 'temperature']:
        #     continue
        ds=d['features']['diagnostic']['states']
        online = 'online' if d['online'] else "offline"
        print(f"Serial {dev_unique_id} --> {d['modelName']} name {d['name']}-{feature} link state {online} links to {ds['networklinkaddress']['value']} strenght {ds['networklinkstrength']['value']}")

if args.save != "":
    with open(args.save, "w") as wfile:
        json.dump(hs, wfile)
        wfile.close()

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print('connected to server')


@sio.event
def disconnect():
    print('disconnected from server')


@sio.event
def message(sid, data):
    print(data)
    return "OK", 123

def siothread():
    curl = f"https://sdk.iotiliti.cloud"
    curl = f"https://sdk.iotiliti.cloud?locationId={myhome['locationId']}&token=Bearer%20{token}"
    hdrs = { 'token' : f"Bearer {token}", 'locationId' : myhome['locationId'] }
    hdrs = { 'Authorization' : f"Bearer {token}", 'locationId' : myhome['locationId'] }
    print("Connect to", curl, "using headers", hdrs)
    sio.connect(curl , headers=hdrs)
    sio.wait()

t = threading.Thread(target=siothread, daemon=True)
t.start()

sleepfor = 15 
prev_st  = ""

while True:
    if args.verbose:
        print("Sleep for",sleepfor,"seconds ... ", end='', flush=True)

    time.sleep(sleepfor)
    sleepfor = args.sleep
    
# vim:ts=4:sw=4
