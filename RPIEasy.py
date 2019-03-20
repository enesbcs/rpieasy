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
  gpios.HWPorts.cleanup()
  time.sleep(1)
  print("\nProgram exiting gracefully")
  sys.exit(0)

timer100ms = 0
timer20ms  = 0
timer1s    = 0
timer2s    = 0
timer30s   = 0
init_ok = False
prevminute = -1

def hardwareInit():
 #print("Init hardware...")
 rpieGlobals.osinuse = misc.getosname(0)
 rpieGlobals.ossubtype = misc.getsupportlevel(1)
 pinout = "0"
 if rpieGlobals.osinuse=="linux":
  import linux_os as OS
  import linux_network as Network
  Settings.NetMan = Network.NetworkManager()
  if len(OS.getsounddevs())>0:
    Settings.SoundSystem["usable"]=True
  if rpieGlobals.ossubtype == 10:
   rpv = OS.getRPIVer()
   if rpv:
     pinout = rpv["pins"]
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(rpv["name"])+" "+str(rpv["pins"])+" pins")

 Settings.loadnetsettings()
 Settings.NetMan.networkinit()

 if pinout != "0":
  Settings.loadpinout()
  if pinout == "40" and len(Settings.Pinout)!=41:
     Settings.Pinout=gpios.PINOUT40
  elif pinout == "26R1" and len(Settings.Pinout)!=27:
     for p in range(27):
      Settings.Pinout.append(gpios.PINOUT40[p])
     for p in range(len(gpios.PINOUT26R1_DELTA)):
      pi = int(gpios.PINOUT26R1_DELTA[p]["ID"])
      Settings.Pinout[pi] = gpios.PINOUT26R1_DELTA[p]
  elif pinout == "26R2" and len(Settings.Pinout)!=27:
     for p in range(27):
      Settings.Pinout.append(gpios.PINOUT40[p])
     for p in range(len(gpios.PINOUT26R2_DELTA)):
      pi = int(gpios.PINOUT26R2_DELTA[p]["ID"])
      Settings.Pinout[pi] = gpios.PINOUT26R2_DELTA[p]
  perror = False
  try:
   gpios.HWPorts.readconfig()
  except:
   perror = True
  if perror or len(Settings.Pinout)<26:
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

 #print("Load devices from file")
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

 #print("Load controllers from file")
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
    Settings.Tasks[x] = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Task" +str(x+1)+ " is malformed, deleted! "+str(e))

 for y in range(0,len(Settings.Controllers)):
   if (Settings.Controllers[y]):
    if (Settings.Controllers[y].enabled): 
     try:
      Settings.Controllers[y].controller_init(None) # init controller at startup
      Settings.Controllers[y].setonmsgcallback(Settings.callback_from_controllers) # set global msg callback for 2way comm
     except Exception as e:
      Settings.Controllers[y] = False
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller" +str(y+1)+ " is malformed, deleted! "+str(e))

 return 0

def NPluginInit():
 return 0

def RulesInit():
 rules = ""
 try:
  with open(rpieGlobals.FILE_RULES,'r') as f:
   rules = f.read()
 except:
  pass
 if rules!="":
  #print("Loading rules...")
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
   if (Settings.Tasks[x].enabled): # device enabled
    if (Settings.Tasks[x].timer20ms): # scheduling needed
     t = threading.Thread(target=Settings.Tasks[x].timer_fifty_per_second)
     t.daemon = True
     procarr.append(t)
     t.start()
 if len(procarr)>0:
  for process in procarr:
    process.join(1)
 return 0

def run10timespersecond():
 procarr = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   if (Settings.Tasks[x].enabled): # device enabled
    if (Settings.Tasks[x].timer100ms): # scheduling needed
     t = threading.Thread(target=Settings.Tasks[x].timer_ten_per_second)
     t.daemon = True
     procarr.append(t)
     t.start()
 if len(procarr)>0:
  for process in procarr:
    process.join(1)
 return 0

def runoncepersecond():
 procarr = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   if (Settings.Tasks[x].enabled): # device enabled
    if (Settings.Tasks[x].timer1s): # scheduling needed
     t = threading.Thread(target=Settings.Tasks[x].timer_once_per_second)
     t.daemon = True
     procarr.append(t)
     t.start()
 checkSensors()
 if len(procarr)>0:
  for process in procarr:
    process.join()
 return 0

def runon2seconds():
 procarr = []
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   if (Settings.Tasks[x].enabled): # device enabled
    if (Settings.Tasks[x].timer2s): # scheduling needed
     t = threading.Thread(target=Settings.Tasks[x].timer_two_second)
     t.daemon = True
     procarr.append(t)
     t.start()
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
   if (Settings.Tasks[x].enabled): # device enabled
    if (Settings.Tasks[x].is_read_timely()): # check if device update needed
#     print("pluginread task"+str(x)+" "+str(Settings.Tasks[x]._lastdataservetime)) # DEBUG ONLY!
     t2 = threading.Thread(target=Settings.Tasks[x].plugin_read)
     t2.daemon = True
     procarr2.append(t2)
     t2.start()
 if len(procarr2)>0:
  for process2 in procarr2:
    process2.join()
 return True

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
 Settings.loadsettings()
 hardwareInit()
 PluginInit()
 CPluginInit()
 NPluginInit()
 RulesInit()
 timer100ms = millis()
 timer20ms  = timer100ms
 timer1s    = timer100ms
 timer2s    = timer100ms
 timer30s   = timer100ms
 init_ok = True
 t = threading.Thread(target=mainloop)  # starting sensors and background functions
 t.daemon = True
 t.start()
 ports = [80,8080,8008] # check for usable ports
 up = 0
 for p in ports:
  up = p
  try:
   serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
   serversocket.bind((socket.gethostname(), up))
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
