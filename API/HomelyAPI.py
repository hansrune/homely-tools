#

import json, requests, time, sys, logging
import socketio
import threading

default_logger = logging.getLogger(__name__)

homely_cloud      = 'sdk.iotiliti.cloud'
homely_sdk_url    = 'https://' + homely_cloud + '/homely'
homely_login_url  = homely_sdk_url + '/oauth/token'
homely_reauth_url = homely_sdk_url + '/oauth/refresh-token'
homely_locations  = homely_sdk_url + '/locations'
homely_homes      = homely_sdk_url + '/home/'
homely_alarmstate = homely_sdk_url + '/alarm/state/'


class HomelyAPI:
    def __init__(self, logger = None ):
        self.locations   = []
        self.locationid  = 'N/A'
        self.homestate   = {}
        self.alarmstate  = {}
        self.auth        = None
        self.tokenexp    = 0
        self.sioexitcode = 0
        if logger is None:
            self.logger = default_logger
        else:
            self.logger = logger

        return 

    def response(self, op, url, response):
        self.logger.debug("--------------------- %s ---------------------", op)
        self.logger.debug("URL %s",url)
        self.logger.debug("Status code %d",response.status_code)
        self.logger.debug("Response text:\n%s",response.text)
        self.logger.debug("------------------------------------------------------")
        if response.status_code not in [ 200, 201 ]:
            self.logger.error("Error code %ss\n%s",response.status_code, response.text)
            exit(2)
        return json.loads(response.text)

    def get(self, op, url, params=None, **kwargs):
        #print("Get ", op, "url", url)
        try:
            r=requests.get(url, params=params, **kwargs)
            return self.response(op, url, r)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def post(self, op, url, data=None, json=None, **kwargs):
        #print("Post ", op, "url", url)
        try:
            r=requests.post(url, data=data, json=json, **kwargs)
            return self.response(op, url, r)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def login(self, username, password):
        self.auth       = self.post("Login", homely_login_url, json={ 'username' : username, 'password' : password })
        self.tokenexp   = int(time.time()) + self.auth['expires_in']
        return self.auth['access_token']

    def tokenrefresh(self):
        epochtime = int(time.time())
        # Give it 5 minutes of margin
        if epochtime + 300 >= self.tokenexp:
            self.auth      = self.post("Refresh access", homely_reauth_url, json={ 'refresh_token' : self.auth['refresh_token'] })
            self.tokenexp  = epochtime + self.auth['expires_in']
        self.logger.info("Access token expiry in %d seconds", self.tokenexp - epochtime - 300)

        #
        # Update also socketio connection data - in case of restart
        #
        self.siourl = f"https://{homely_cloud}?locationId={self.locationid}&token=Bearer%20{self.auth['access_token']}"
        self.siohdrs = { 'Authorization' : f"Bearer {self.auth['access_token']}", 'locationId' : self.locationid }

        return self.auth['access_token']

    def findhome(self, location = ""):
        locations = self.get("Locations", homely_locations, headers={ 'Authorization' : 'Bearer ' + self.auth['access_token'] } )
        locfound  = False
        if location == "":
            locobj   = locations[0]
            locfound = True
        else:
            for locobj in locations:
                if locobj['name'] == location:
                    locfound = True
                    break
        if locfound:
            self.locationid = locobj['locationId']
            return locobj
        else:
            self.logger.error("Location name %s not found", location)
            exit(1)

    def homestatus(self):
        self.homestate = self.get("Home status", homely_homes + self.locationid, headers={ 'Authorization' : 'Bearer ' + self.auth['access_token'] } )
        return self.homestate

    def sio_calls(self):
        @self.sio.event
        def connect():
            self.logger.info('websocket: connected to server')

        @self.sio.event
        def disconnect():
            self.logger.error('websocket: disconnected from server')
            # We're exiting - let systemctl take care of restart
            self.sioexitcode = 2

        @self.sio.on('event')
        def on_message(data):
            self.siomsg(data)

        def siothread():
            self.logger.debug("Connect to %s using headers %s", self.siourl, self.siohdrs)
            self.sio.connect(self.siourl , headers=self.siohdrs)
            self.sio.wait()

        self.sthread = threading.Thread(target=siothread, daemon=True)
        self.sthread.start()
        self.sioexitcode = 0

    def sioexit(self):
        return self.sioexitcode

    def startsio(self, msg_callback):
        self.sio = socketio.Client(logger=self.logger, engineio_logger=self.logger)
        self.siomsg = msg_callback
        # These are updated also on token refresh ....
        self.siourl = f"https://{homely_cloud}?locationId={self.locationid}&token=Bearer%20{self.auth['access_token']}"
        self.siohdrs = { 'Authorization' : f"Bearer {self.auth['access_token']}", 'locationId' : self.locationid }
        self.sio_calls()

# vim:ts=4:sw=4
