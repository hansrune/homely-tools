#!/usr/bin/env python3
import time, sys, os, json , argparse
from HomelyAPI import *

progname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

def on_message(ws, message):
	print(message)

def alarmdomocodes(state):
    return {
        'DISARMED':          '0',
        'ARM_STAY_PENDING':  '1',
        'ARM_NIGHT_PENDING': '1',
        'ARMED_STAY':        '1',
        'ARMED_NIGHT':       '1',
        'ARM_AWAY_PENDING':  '2',
        'ARM_PENDING':       '2',
        'ARMED_AWAY':        '2'
    }.get(state,'')

def alarmlevels(state):
    return {
        'DISARMED':          '0',
        'ARM_STAY_PENDING':  '10',
        'ARMED_STAY':        '10',
        'ARM_NIGHT_PENDING': '20',
        'ARMED_NIGHT':       '20',
        'ARM_AWAY_PENDING':  '30',
        'ARM_PENDING':       '30',
        'ARMED_AWAY':        '30'
    }.get(state,'')

def_user = def_password = seccode  = ""
try:
	def_user = os.environ['HOMELY_USER']
except KeyError:
	pass
try:
	def_password = os.environ['HOMELY_PASSWORD']
except KeyError:
    pass

argp = argparse.ArgumentParser(prog=progname, description='Homely to Domoticz alarm states')
argp.add_argument('-u','--username',    default=def_user,                help="Homely username")
argp.add_argument('-p','--password',    default=def_password,            help="Homely password (only if you are alone on your system)") 
argp.add_argument(     '--domoticzurl', default="http://127.0.0.1:8080", help="Homely password (only if you are alone on your system)") 
argp.add_argument('-l','--load',        default="",                      help="Load json state data from file") 
argp.add_argument(     'stateidx',      metavar='N', type=int, nargs=1,  help="State selector switch index") 
argp.add_argument('-s','--save',        default="",                      help="Save json state data to file") 
argp.add_argument(     '--sleep',       default=120, type=int,           help="Sleep interval") 
argp.add_argument(     '--home',        default="",                      help="Home name in Homely") 
argp.add_argument('-d','--debug',       action="store_true",             help="Debug")
argp.add_argument('-t','--token',       action="store_true",             help="Login and print access token")
argp.add_argument('-v','--verbose',     action="store_true",             help="Verbose")
args=argp.parse_args()

domoticz_stateidx = str(args.stateidx[0])

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


    print('------------------------- Find home  ----------------------------------')
    myhome = h.findhome(args.home)
    print("My home is:",myhome)

    if args.token: 
        print('Access token is:')
        print(token)
        exit(0)

if args.debug:
    print('------------------------- Home devices --------------------------------')
    hs = h.homestatus()
    for i in hs['devices']:
        print(json.dumps(i))

if args.save != "":
    with open(args.save, "w") as wfile:
        json.dump(hs, wfile)
        wfile.close()

print('------------------------- Domoticz settings -------------------------------')
domoticz_settings = h.get("Domoticz settings", args.domoticzurl + '/json.htm?type=settings')

domoticz_seccode  = domoticz_settings['SecPassword']
if args.verbose:
    print("Security setting is",domoticz_seccode)

domoticz_lvl = h.get("Domoticz get Homely switch state", args.domoticzurl + '/json.htm?type=devices&rid=' + domoticz_stateidx)
try:
    prev_lvl = str(domoticz_lvl['result'][0]['Level'])
except KeyError:
    prev_lvl = 'initial state'
if args.verbose:
    print(f"Domoticz's Homely alarm level switch is {prev_lvl} (index {domoticz_stateidx})")

prev_ht = 'initial state'
while True:
    print('------------------------- Alarm state update ------------------------------')
    token = h.tokenrefresh()
    hs    = h.homestatus()
    try:
        ht = hs['alarmState']
    except KeyError:
        ht = ''
    st  = alarmdomocodes(ht)
    lvl = alarmlevels(ht)

    if ht != '' and prev_lvl != lvl:
        print(f"Homely alarm state change from level {prev_lvl} to {lvl} (Homely {ht})")
        prev_lvl = lvl
        prev_ht  = ht
        print(f"Homely alarm state is {ht} --> Domoticz security code {st}")
        domoticz_req = h.get("Domoticz set security state", args.domoticzurl + '/json.htm?type=command&param=setsecstatus&secstatus=' + st + '&seccode=' + domoticz_seccode)
        print(f"Homely alarm state is {ht} --> Domoticz state level {lvl}")
        domoticz_req = h.get("Domoticz set Homely state", args.domoticzurl + '/json.htm?type=command&param=switchlight&idx=' + domoticz_stateidx + '&switchcmd=Set Level&level=' + lvl)
    else:
        print(f"Homely alarm is {ht} and Domoticz switch level is {lvl}, previously {prev_lvl}")
    
    if args.verbose:
        print("Sleep for",args.sleep,"seconds")

    time.sleep(args.sleep)

exit(0)

# vim:ts=4:sw=4
