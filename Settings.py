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
notifiersfile   = 'data/notifiers.json'
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
"portlist":[80,8080,8008,591],
"battery": { "enabled":0,"tasknum":0,"taskvaluenum":0}
}

Pinout = []
PinStatesMax = 13
PinStates = ["Default","Input","Input-Pulldown","Input-Pullup","Output","Output-Lo","Output-Hi","H-PWM","1WIRE","Special","IR-RX","IR-TX","IR-PWM","Reserved","Reserved"]

Tasks = [False]
Controllers = [False]
Notifiers = [False]

NetworkDevices = []
NetMan = None

UpdateString = ""

SoundSystem = { # do not save, filled on startup!
"usable":False,
"inuse":False,
"usingplugintaskindex":-1,
"askplugintorelease":None
}

nodelist = [] # for ESPEasy P2P, fill at runtime!
p2plist = [] # for LORA/P2P peer list
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
    if int(Pinout[p]["altfunc"])!=0:
     n = Pinout[p]["name"]
     for i in range(len(n)):
      if "I2C" in Pinout[p]["name"][i]:
       gplist.append(Pinout[p]["name"][0]+"/"+Pinout[p]["name"][i])
  except:
   pass
  return gplist

def savesettings():
 global Settings, settingsfile
 success = 1
 try:
  f = open(settingsfile,'w',encoding="utf8")
  settingjson = jsonpickle.encode(Settings)
  f.write(settingjson)
 except Exception as e:
  success = 0
 return success

def savetasks():
 global Tasks, tasksfile
 success = 1
 try:
  import copy
  Tasks_Shadow = copy.copy(Tasks) # make a copy of original tasks
 except Exception as e:
  Tasks_Shadow = Tasks.copy() # this method is not working well
 tasktoinit = []
 try:
  if len(Tasks)>0: # debug
   for T in range(len(Tasks_Shadow)):
    try:
     for i in Tasks_Shadow[T].__dict__:
      try:
       test = jsonpickle.encode(Tasks_Shadow[T].__dict__[i]) # check if jsonpickle is needed
      except:
       Tasks_Shadow[T].__dict__[i]=None
       if not T in tasktoinit:
        tasktoinit.append(T)
    except Exception as e:
     pass
  f = open(tasksfile,'w',encoding="utf8")
  settingjson = jsonpickle.encode(Tasks_Shadow)
  f.write(settingjson)
  for t in tasktoinit:
   try:
    Tasks[t].plugin_init()
   except:
    pass
 except Exception as e:
  success = 0
 return success

def loadsettings():
 global Settings, settingsfile, AdvSettings, advsettingsfile
 success = 1
 try:
  f = open(settingsfile,encoding="utf8")
  settingjson = f.read()
  Settings = jsonpickle.decode(settingjson)
 except:
  success = 0
 try:
  f = open(advsettingsfile,encoding="utf8")
  settingjson = f.read()
  AdvSettings = jsonpickle.decode(settingjson)
 except:
  pass
 return success

def loadtasks():
 global Tasks, tasksfile
 success = 1
 tTasks = [False]
 try:
  f = open(tasksfile,encoding="utf8")
  settingjson = f.read()
  tTasks = jsonpickle.decode(settingjson)
  Tasks = tTasks
 except:
  success = 0
 return success

def savecontrollers():
 global Controllers, controllersfile
 success = 1
 try:
  f = open(controllersfile,'w',encoding="utf8")
  settingjson = jsonpickle.encode(Controllers,max_depth=2) # Restrict Jsonpickle to encode vars at first object
  f.write(settingjson)
 except:
  success = 0
 return success

def loadcontrollers():
 global Controllers, controllersfile
 success = 1
 try:
  f = open(controllersfile,encoding="utf8")
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
  f = open(pinoutfile,'w',encoding="utf8")
  settingjson = jsonpickle.encode(Pinout)
  f.write(settingjson)
 except:
  success = 0
 return success

def loadpinout():
 global Pinout, pinoutfile
 success = 1
 try:
  f = open(pinoutfile,encoding="utf8")
  settingjson = f.read()
  Pinout = jsonpickle.decode(settingjson)
 except:
  success = 0
 return success

def loadnetsettings():
 global NetworkDevices, NetMan, netdevfile, netmanfile
 success = 1
 try:
  f = open(netdevfile,encoding="utf8")
  settingjson = f.read()
  NetworkDevices = jsonpickle.decode(settingjson)
 except:
  success = 0
 try:
  f = open(netmanfile,encoding="utf8")
  settingjson = f.read()
  NetMan = jsonpickle.decode(settingjson)
 except:
  success = 0
 return success

def savenetsettings():
 global NetworkDevices, NetMan, netdevfile, netmanfile
 success = 1
 try:
  f = open(netdevfile,"w",encoding="utf8")
  settingjson = jsonpickle.encode(NetworkDevices)
  f.write(settingjson)
 except:
  success = 0
 try:
  f = open(netmanfile,"w",encoding="utf8")
  settingjson = jsonpickle.encode(NetMan)
  f.write(settingjson)
 except:
  success = 0
 return success

def saveadvsettings():
 global AdvSettings, advsettingsfile
 success = 1
 try:
  f = open(advsettingsfile,'w',encoding="utf8")
  settingjson = jsonpickle.encode(AdvSettings)
  f.write(settingjson)
 except:
  success = 0
 return success

def savenotifiers():
 global Notifiers, notifiersfile
 success = 1
 try:
  f = open(notifiersfile,'w',encoding="utf8")
  settingjson = jsonpickle.encode(Notifiers,max_depth=2) # Restrict Jsonpickle to encode vars at first object
  f.write(settingjson)
 except:
  success = 0
 return success

def loadnotifiers():
 global Notifiers, notifiersfile
 success = 1
 try:
  f = open(notifiersfile,encoding="utf8")
  settingjson = f.read()
  Notifiers = jsonpickle.decode(settingjson)
 except Exception as e:
#  print("Critical Jsonpickle error:",str(e))
  success = 0
 return success

def getTaskValueIndex(taskname, valuename):
 tid = -1
 vid = -1
 global Tasks
 for x in range(0,len(Tasks)):
  if (Tasks[x]) and type(Tasks[x]) is not bool:
    try:
     if Tasks[x].enabled:
      if Tasks[x].gettaskname()==taskname:
       tid = x+1
       for u in range(0,Tasks[x].valuecount):
        if Tasks[x].valuenames[u]==valuename:
         vid = u+1
         return tid, vid
    except:
     pass
 return tid, vid
