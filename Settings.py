#!/usr/bin/env python3
#############################################################################
####################### Global Settings for RPIEasy #########################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import sys
import rpieGlobals
try:
 import jsonpickle # pip3 install jsonpickle
except:
 print("JSONPickle not found!\nsudo pip3 install jsonpickle")
 sys.exit(0)

settingsfile    = 'data/settings.json'
tasksfile       = 'data/tasks.json'
controllersfile = 'data/controllers.json'
pinoutfile      = 'data/pinout.json'
netdevfile      = 'data/netdev.json'
netmanfile      = 'data/netman.json'
advsettingsfile = 'data/advsettings.json'

Settings = {
"Name":"RPIEasy",
"Unit":0,
"Password":"",
"Delay":60
}

AdvSettings = {
"serialloglevel":0,
"webloglevel":2,
"consoleloglevel":2,
"fileloglevel":0,
"sysloglevel":0,
"syslogip":"",
"battery": { "enabled":0,"tasknum":0,"taskvaluenum":0}
}

Pinout = []
PinStatesMax = 9
PinStates = ["Default","Input","Input-Pulldown","Input-Pullup","Output","Output-Lo","Output-Hi","H-PWM","1WIRE","Special","Reserved"]

Tasks = [False]
Controllers = [False]

NetworkDevices = []
NetMan = None

SoundSystem = { # do not save, filled on startup!
"usable":False,
"inuse":False,
"usingplugintaskindex":-1,
"askplugintorelease":None
}

nodelist = [] # for ESPEasy P2P, fill at runtime!
WebUIPort = 0 # filled at startup!

# msg arrived from a controller->reroute data to the destination device
# this will do the magic of the two way communication
def callback_from_controllers(controllerindex,idx,values,taskname="",valuename=""):
 global Tasks
 for x in range(len(Tasks)):
  if (Tasks[x] and type(Tasks[x]) is not bool): # device exists
   if (Tasks[x].enabled) and (Tasks[x].recdataoption): # device enabled and able to receive data, enable recdataoption at plugin!
    if taskname == "": # search task by idx
      if (str(Tasks[x].controlleridx[controllerindex])==str(idx)):
        Tasks[x].plugin_receivedata(values)            # implement plugin_receivedata() at plugin side!
        break
    else:             # search task by name
      if (Tasks[x].gettaskname().strip() == taskname.strip()): # match with taskname, case sensitive????
        tvalues = []
        for u in range(rpieGlobals.VARS_PER_TASK):     # fill unused values with -9999, handle at plugin side!!!
         tvalues.append(-9999)
        for v in range(Tasks[x].valuecount):           # match with valuename
         if Tasks[x].valuenames[v]==valuename:
          tvalues[v] = values
          Tasks[x].plugin_receivedata(tvalues)
          break
        break

def get_i2c_pins():                    # get list of enabled i2c pin numbers
  global Pinout
  gplist = []
  try:
   for p in range(len(Pinout)):
    if int(Pinout[p]["altfunc"])==1:
     if "I2C" in Pinout[p]["name"][1]:
      gplist.append(Pinout[p]["name"][0]+"/"+Pinout[p]["name"][1])
  except:
   pass
  return gplist

def savesettings():
 global Settings, settingsfile
 success = 1
 try:
  f = open(settingsfile,'w')
  settingjson = jsonpickle.encode(Settings)
  f.write(settingjson)
 except:
  success = 0
 return success

def savetasks():
 global Tasks, tasksfile
 success = 1
 try:
  f = open(tasksfile,'w')
  settingjson = jsonpickle.encode(Tasks)
  f.write(settingjson)
 except:
  success = 0
 return success

def loadsettings():
 global Settings, settingsfile, AdvSettings, advsettingsfile
 success = 1
 try:
  f = open(settingsfile)
  settingjson = f.read()
  Settings = jsonpickle.decode(settingjson)
 except:
  success = 0
 try:
  f = open(advsettingsfile)
  settingjson = f.read()
  AdvSettings = jsonpickle.decode(settingjson)
 except:
  pass
 return success

def loadtasks():
 global Tasks, tasksfile
 success = 1
 try:
  f = open(tasksfile)
  settingjson = f.read()
  Tasks = jsonpickle.decode(settingjson)
 except:
  success = 0
 return success

def savecontrollers():
 global Controllers, controllersfile
 success = 1
 try:
  f = open(controllersfile,'w')
  settingjson = jsonpickle.encode(Controllers,max_depth=2) # Restrict Jsonpickle to encode vars at first object
  f.write(settingjson)
 except:
  success = 0
 return success

def loadcontrollers():
 global Controllers, controllersfile
 success = 1
 try:
  f = open(controllersfile)
  settingjson = f.read()
  Controllers = jsonpickle.decode(settingjson)
 except Exception as e:
#  print("Critical Jsonpickle error:",str(e))
  success = 0
 return success

def savepinout():
 global Pinout, pinoutfile
 success = 1
 try:
  f = open(pinoutfile,'w')
  settingjson = jsonpickle.encode(Pinout)
  f.write(settingjson)
 except:
  success = 0
 return success

def loadpinout():
 global Pinout, pinoutfile
 success = 1
 try:
  f = open(pinoutfile)
  settingjson = f.read()
  Pinout = jsonpickle.decode(settingjson)
 except:
  success = 0
 return success

def loadnetsettings():
 global NetworkDevices, NetMan, netdevfile, netmanfile
 success = 1
 try:
  f = open(netdevfile)
  settingjson = f.read()
  NetworkDevices = jsonpickle.decode(settingjson)
 except:
  success = 0
 try:
  f = open(netmanfile)
  settingjson = f.read()
  NetMan = jsonpickle.decode(settingjson)
 except:
  success = 0
 return success

def savenetsettings():
 global NetworkDevices, NetMan, netdevfile, netmanfile
 success = 1
 try:
  f = open(netdevfile,"w")
  settingjson = jsonpickle.encode(NetworkDevices)
  f.write(settingjson)
 except:
  success = 0
 try:
  f = open(netmanfile,"w")
  settingjson = jsonpickle.encode(NetMan)
  f.write(settingjson)
 except:
  success = 0
 return success

def saveadvsettings():
 global AdvSettings, advsettingsfile
 success = 1
 try:
  f = open(advsettingsfile,'w')
  settingjson = jsonpickle.encode(AdvSettings)
  f.write(settingjson)
 except:
  success = 0
 return success
