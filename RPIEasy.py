#!/usr/bin/env python3
#############################################################################
########################## RPI Easy main program ############################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import rpieGlobals
import time
import threading
import Settings
from rpieTime import *
import webserver
import misc
import glob
import sys, signal, os
import commands
import socket
from datetime import datetime
try:
 import gpios
except Exception as e:
 pass
# sudo apt install python3-pip screen alsa-utils wireless-tools wpasupplicant net-tools zip unzip
# sudo pip3 install jsonpickle

def signal_handler(signal, frame):
  global init_ok
  init_ok = False
  commands.doCleanup()
  webserver.WebServer.stop()
  try:
   gpios.HWPorts.cleanup()
  except:
   pass
  time.sleep(1)
  print("\nProgram exiting gracefully")
  sys.exit(0)

timer100ms = 0
timer20ms  = 0
timer1s    = 0
timer2s    = 0
timer30s   = 0
init_ok    = False
prevminute = -1
netmode    = -1
lastdisconntime = time.time()
lastaptime = 0

def hardwareInit():
 print("Init hardware...")
 rpieGlobals.osinuse = misc.getosname(0)
 rpieGlobals.ossubtype = misc.getsupportlevel(1)
 pinout = "0"
 if rpieGlobals.osinuse=="linux":
  import linux_os as OS
  import linux_network as Network
  Settings.NetMan = Network.NetworkManager()
  if len(OS.getsounddevs())>0:
    Settings.SoundSystem["usable"]=True
  if rpieGlobals.ossubtype == 10: # rpi
   rpv = OS.getRPIVer()
   if rpv:
     pinout = rpv["pins"]
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(rpv["name"])+" "+str(rpv["pins"])+" pins")
  elif rpieGlobals.ossubtype == 3: # opi
   opv = OS.getarmbianinfo()
   if opv:
    pinout = opv["pins"]
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(opv["name"])+" "+str(opv["pins"])+" pins")
 hwtype = rpieGlobals.ossubtype
 if pinout=="0":
  try:
   import lib.lib_ftdigpios as ftdigpio # check for ftdi hwtype?
   ftdigpio.correctdependencies()
   if ftdigpio.get_ftdi_devices(0)>0:
    hwtype = 19
    pinout = "ftdi"
  except Exception as e:
   print(e)
 print("Load network settings...")
 Settings.loadnetsettings()
 Settings.NetMan.networkinit()

 print("Load GPIO settings...")
 if pinout != "0":
  Settings.loadpinout()
  try:
   gpios.preinit(hwtype) # create HWPorts variable
  except Exception as e:
   print("init",e)
  if (("40" in pinout) and (len(Settings.Pinout)<41)) or (("26" in pinout) and (len(Settings.Pinout)<27)) or (pinout=="ftdi" and len(Settings.Pinout)<1):
   print("Creating new pinout")
   try:
    gpios.HWPorts.createpinout(pinout)
   except Exception as e:
    print("Pinout creation error:",e)
  perror = False
  try:
   gpios.HWPorts.readconfig()
  except Exception as e:
#   print(e) # debug
   perror = True
  if perror or len(Settings.Pinout)<1:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Your GPIO can not be identified!")
   Settings.Pinout = []
  else:
   gpios.HWPorts.initpinstates()

 else:
  Settings.Pinout = []
 return 0

def PluginInit():
 tarr = []
 filenames = glob.glob('_P*.py')
 filenames.sort()
 for fname in filenames:
  tarr = [0,0,0]
  tarr[0] = fname
  with open(fname,"r") as fcont:
   for line in fcont:
    if "PLUGIN_ID" in line:
     tarr[1] = line[line.find("=")+1:].strip().replace('"',"")
    if "PLUGIN_NAME" in line:
     tarr[2] = line[line.find("=")+1:].strip().replace('"',"")
     break
  tarr[0] = tarr[0].replace(".py","")
  rpieGlobals.deviceselector.append(tarr) # create list for form select

 print("Load devices from file")
 Settings.loadtasks()

 return 0

def CPluginInit():
 tarr = []
 filenames = glob.glob('_C*.py')
 filenames.sort()
 for fname in filenames:
  tarr = [0,0,0]
  tarr[0] = fname
  with open(fname,"r") as fcont:
   for line in fcont:
    if "CONTROLLER_ID" in line:
     tarr[1] = line[line.find("=")+1:].strip().replace('"',"")
    if "CONTROLLER_NAME" in line:
     tarr[2] = line[line.find("=")+1:].strip().replace('"',"")
     break
  tarr[0] = tarr[0].replace(".py","")
  rpieGlobals.controllerselector.append(tarr) # create list for form select

 print("Load controllers from file")
 Settings.loadcontrollers()

 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   try:
    if (Settings.Tasks[x].enabled): # device enabled
     Settings.Tasks[x].plugin_init(None) # init plugin at startup
     for y in range(len(Settings.Tasks[x].senddataenabled)):
       if (Settings.Tasks[x].senddataenabled[y]):
        if (Settings.Controllers[y]):
         if (Settings.Controllers[y].enabled):
          Settings.Tasks[x].controllercb[y] = Settings.Controllers[y].senddata # assign controller callback to plugins that sends data
   except Exception as e:
    Settings.Tasks[x].enabled = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Task " +str(x+1)+ " disabled! "+str(e))

 for y in range(0,len(Settings.Controllers)):
   if (Settings.Controllers[y]):
    try:
     if (Settings.Controllers[y].enabled): 
       Settings.Controllers[y].controller_init(None) # init controller at startup
       Settings.Controllers[y].setonmsgcallback(Settings.callback_from_controllers) # set global msg callback for 2way comm
    except Exception as e:
       Settings.Controllers[y].enabled = False
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller " +str(y+1)+ " disabled! "+str(e))

 return 0

def NPluginInit():
 tarr = []
 filenames = glob.glob('_N*.py')
 filenames.sort()
 for fname in filenames:
  tarr = [0,0,0]
  tarr[0] = fname
  with open(fname,"r") as fcont:
   for line in fcont:
    if "NPLUGIN_ID" in line:
     tarr[1] = line[line.find("=")+1:].strip().replace('"',"")
    if "NPLUGIN_NAME" in line:
     tarr[2] = line[line.find("=")+1:].strip().replace('"',"")
     break
  tarr[0] = tarr[0].replace(".py","")
  rpieGlobals.notifierselector.append(tarr) # create list for form select

 print("Load notifiers from file")
 Settings.loadnotifiers()

 for x in range(0,len(Settings.Notifiers)):
  if (Settings.Notifiers[x]) and type(Settings.Notifiers[x]) is not bool: # device exists
   try:
    if (Settings.Notifiers[x].enabled): # device enabled
     Settings.Notifiers[x].plugin_init(None) # init plugin at startup
   except Exception as e:
     Settings.Notifiers[x].enabled = False
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Notifier " +str(x+1)+ " disabled! "+str(e))

 return 0

def RulesInit():
 rules = ""
 try:
  with open(rpieGlobals.FILE_RULES,'r') as f:
   rules = f.read()
 except:
  pass
 if rules!="":
  print("Loading rules...")
  commands.splitruletoevents(rules)
 commands.rulesProcessing("System#Boot",rpieGlobals.RULE_SYSTEM)

def timeoutReached(timerval):
 if (millis()>=timerval):
  return True
 return False

def run50timespersecond():
 procarr = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   try:
    if (Settings.Tasks[x].enabled): # device enabled
     if (Settings.Tasks[x].timer20ms): # scheduling needed
      t = threading.Thread(target=Settings.Tasks[x].timer_fifty_per_second)
      t.daemon = True
      procarr.append(t)
      t.start()
   except:
    pass
 if len(procarr)>0:
  for process in procarr:
   process.join(1)
 return 0

def run10timespersecond():
 procarr = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   try:
    if (Settings.Tasks[x].enabled): # device enabled
     if (Settings.Tasks[x].timer100ms): # scheduling needed
      t = threading.Thread(target=Settings.Tasks[x].timer_ten_per_second)
      t.daemon = True
      procarr.append(t)
      t.start()
   except:
    pass
 if len(procarr)>0:
  for process in procarr:
    process.join(1)
 return 0

def runoncepersecond():
 procarr = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   try:
    if (Settings.Tasks[x].enabled): # device enabled
     if (Settings.Tasks[x].timer1s): # scheduling needed
      t = threading.Thread(target=Settings.Tasks[x].timer_once_per_second)
      t.daemon = True
      procarr.append(t)
      t.start()
   except:
    pass
 checkSensors()
 if len(procarr)>0:
  for process in procarr:
    process.join()
 return 0

def runon2seconds():
 procarr = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   try:
    if (Settings.Tasks[x].enabled): # device enabled
     if (Settings.Tasks[x].timer2s): # scheduling needed
      t = threading.Thread(target=Settings.Tasks[x].timer_two_second)
      t.daemon = True
      procarr.append(t)
      t.start()
   except:
    pass
 checkNetwork()
 if len(procarr)>0:
  for process in procarr:
    process.join()
 return 0

def runon30seconds(): # Only controllers has this function # DEBUG!!!
 procarr = []
 for y in range(0,len(Settings.Controllers)):
   if (Settings.Controllers[y]):
    if (Settings.Controllers[y].enabled):
     if (Settings.Controllers[y].timer30s): # scheduling needed
      t = threading.Thread(target=Settings.Controllers[y].timer_thirty_second)
      t.daemon = True
      procarr.append(t)
      t.start()
 if len(procarr)>0:
   for process in procarr:
     process.join()
 return 0

def checkSensors():
 procarr2 = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   try:
    if (Settings.Tasks[x].enabled): # device enabled
     if (Settings.Tasks[x].is_read_timely()): # check if device update needed
#     print("pluginread task"+str(x)+" "+str(Settings.Tasks[x]._lastdataservetime)) # DEBUG ONLY!
      t2 = threading.Thread(target=Settings.Tasks[x].plugin_read)
      t2.daemon = True
      procarr2.append(t2)
      t2.start()
   except:
    pass
 if len(procarr2)>0:
  for process2 in procarr2:
    process2.join()
 return True

def checkNetwork():
 global netmode, lastdisconntime, lastaptime
 try:
   if Settings.NetMan.WifiDevWatch>=0 and Settings.NetMan.WifiDevNum>=0:
    if Settings.NetworkDevices[Settings.NetMan.WifiDevNum].apmode==0:
     anetmode = Settings.NetworkDevices[Settings.NetMan.WifiDevWatch].isconnected()
     if anetmode!=netmode: # network mode changed
      netmode=anetmode
      if netmode: # if connected
       lastdisconntime = 0 # forgive last disconnect time
       commands.rulesProcessing("Network#Connected",rpieGlobals.RULE_SYSTEM)
       return True
      else:
       lastdisconntime = time.time() # store last disconnect time
       commands.rulesProcessing("Network#Disconnected",rpieGlobals.RULE_SYSTEM)
       return True
     elif anetmode==False: # otherwise, if in disconnect state
      if Settings.NetMan.APMode not in [-1,100]:
       if lastdisconntime!=0:
        if (time.time()-lastdisconntime)>int(Settings.NetMan.APModeTime):
           from linux_network import AP_start
           AP_start(Settings.NetMan.WifiDevNum)
           lastdisconntime = 0 # forgive last disconnect time
           lastaptime = time.time()
       else:
        lastdisconntime = time.time() # store last disconnect time
    else: # apmode active
     if Settings.NetMan.APStopTime>-1:
      if Settings.NetMan.APMode not in [-1,100]:
       if lastaptime!=0:
        if (time.time()-lastaptime)>int(Settings.NetMan.APStopTime):
           from linux_network import AP_stop
           AP_stop(Settings.NetMan.WifiDevNum)
           lastaptime = 0
           lastdisconntime = 0 # forgive last disconnect time
 except Exception as e:
  print(e)

def mainloop():
 global timer100ms, timer20ms, timer1s, timer2s, timer30s, init_ok, prevminute
 while init_ok:
        time.sleep(0.05)
        if (timeoutReached(timer20ms)):
         run50timespersecond()
         timer20ms = millis()+20
         if (timeoutReached(timer100ms)):
          run10timespersecond()
          timer100ms = millis()+100
         if (timeoutReached(timer1s)):
          runoncepersecond()
          timer1s = millis()+1000
          if (str(prevminute) != str(datetime.now().strftime('%M'))):
           commands.rulesProcessing("Clock#Time="+str(datetime.now().strftime('%a,%H:%M')),rpieGlobals.RULE_CLOCK)
           prevminute = datetime.now().strftime('%M')
          if (timeoutReached(timer30s)):
           runon30seconds()
           timer30s = millis()+30000
         if (timeoutReached(timer2s)):
          runon2seconds()
          timer2s = millis()+2000

def initprogram():
 global timer100ms, timer20ms, timer1s, timer2s, timer30s, init_ok

 try:
  os.chdir(os.path.dirname(os.path.realpath(__file__)))
 except:
  pass
 #print("Loading settings")
 try:
  Settings.loadsettings()
  hardwareInit()
  PluginInit()
  CPluginInit()
  NPluginInit()
  RulesInit()
  signal.signal(signal.SIGINT, signal_handler) # avoid stoling by a plugin
  timer100ms = millis()
  timer20ms  = timer100ms
  timer1s    = timer100ms
  timer2s    = timer100ms
  timer30s   = timer100ms
  init_ok = True
 except:
  init_ok = False
 t = threading.Thread(target=mainloop)  # starting sensors and background functions
 t.daemon = True
 t.start()
 try:
  ports = Settings.AdvSettings["portlist"]
 except:
  ports = [80,8080,8008,591] # check for usable ports
 up = 0
 try:
  ownaddr = socket.gethostname()
 except:
  ownaddr = '127.0.0.1'
 for p in ports:
  up = p
  try:
   serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
   serversocket.bind((ownaddr, up))
   serversocket.close()
  except:
   up = 0
  if up>0:
   break
 if up == 0:
  misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Webserver can not be started, no available port found!")
 else:
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Webserver starting at port "+str(up))
  Settings.WebUIPort = up
  webserver.WebServer.start('', up) # starts webserver GUI

# MAIN
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
initprogram()
