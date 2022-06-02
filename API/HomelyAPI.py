#
#

import json, requests, time

homely_cloud      = 'sdk.iotiliti.cloud'
homely_sdk_url    = 'https://' + homely_cloud + '/homely'
homely_login_url  = homely_sdk_url + '/oauth/token'
homely_reauth_url = homely_sdk_url + '/oauth/refresh-token'
homely_locations  = homely_sdk_url + '/locations'
homely_homes      = homely_sdk_url + '/home/'
homely_alarmstate = homely_sdk_url + '/alarm/state/'


class HomelyAPI:
    def __init__(self, debug = False, verbose = False ):
        self.debug      = self.verbose = debug
        self.verbose    = verbose
        self.locations  = []
        self.locationid = 'N/A'
        self.homestate  = {}
        self.alarmstate = {}
        self.auth       = None
        self.tokenexp   = 0
        return 

    def response(self, op, url, response):
        if self.debug:
            print("---------------------", op, "---------------------")
            print("URL",url)
            print("Status code",response.status_code)
            print("Response text:")
            print(response.text)
            print("------------------------------------------------------")
        if response.status_code not in [ 200, 201 ]:
            print("Error code",response.status_code, response.text)
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
        if self.verbose:
            print("Access token expiry in", self.tokenexp - epochtime - 300, "seconds")
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
            print("Location name ", location, " not found")
            exit(1)

    def homestatus(self):
        return self.get("Home status", homely_homes + self.locationid, headers={ 'Authorization' : 'Bearer ' + self.auth['access_token'] } )

# vim:ts=4:sw=4
