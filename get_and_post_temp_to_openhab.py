#!/usr/bin/python

import glob
import json
import os
import time
import urllib2
import yaml

# class for handling the posting
# I stole this from somewhere but cannot remember where for attribution
class MethodRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        if self._method is not None:
            return self._method
        return urllib2.Request.get_method(self, *args, **kwargs)

def getConfig():
    # read the DS18b20.yaml file from my .config directory
    # doing this in multiple steps because there is no way I'll remember this
    # after I have put the code away for a while and I don't want to spend time
    # in the future to untangle this
    thisScript = os.path.abspath(__file__)
    cwd = os.path.dirname(thisScript)
    parentDirectory = os.path.split(cwd)[0]
    configFile = os.path.join(parentDirectory, '.config', 'DS18b20.yaml')

    with open(configFile, 'r') as f:
        settings = yaml.load(f)

    return settings

def readTempRaw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def readTemp(device_file):
    lines = readTempRaw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = readTempRaw(device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return [temp_c, temp_f]

def postToOpenhab(Turl,payload):
    #need a PUT instead of a POST
    request = MethodRequest(Turl, method='PUT')
    request.add_header('Content-Type', 'text/plain')
    request.add_data(payload)

    try:
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        if hasattr(e,'reason'):
            print "There was an URL error: " + str(e.reason)
            return
        elif hasattr(e,'code'):
            print "There was an HTTP error: " + str(e.code)
            return

#------------------------------------------------------
# Mainline
#------------------------------------------------------
if __name__ == '__main__':
    #initialize the device
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
    #derive the device file name to read from it later
    baseDir = '/sys/bus/w1/devices/'
    #TODO:  this is kind of lazy.  Maybe change this to read from the yaml?
    deviceFolder = glob.glob(baseDir + '28*')[0]
    deviceFile = deviceFolder + '/w1_slave'

    #get the settings for this machine
    setting = getConfig()
    baseUrl = setting["base_url"]
    temperatureItem = setting["temperature_item_name"]
    temperatureUrl = baseUrl + '/rest/items/' + temperatureItem + '/state'

    # do the work
    [tempC, tempF] = readTemp(deviceFile)
    print tempF

    packedTempC = json.dumps(tempC)
    packedTempF = json.dumps(tempF)

    postToOpenhab(temperatureUrl,packedTempF)
