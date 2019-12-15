#!/usr/bin/env python3
#############################################################################
############## Helper Library for RULES and COMMANDS ########################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import misc
import Settings
import linux_os as OS
import time
import os
import signal
import rpieGlobals
import re
from datetime import datetime
import rpieTime
import time
import linux_network as Network
import socket
import urllib.request
import threading

GlobalRules = []
SysVars = ["systime","system_hm","lcltime","syshour","sysmin","syssec","sysday","sysmonth",
"sysyear","sysyears","sysweekday","sysweekday_s","unixtime","uptime","rssi","ip","ip4","sysname","unit","ssid","mac","mac_int","build","sunrise","sunset","sun_altitude","sun_azimuth","sun_radiation"]

def doCleanup():
  rulesProcessing("System#Shutdown",rpieGlobals.RULE_SYSTEM)
  Settings.savetasks()
  procarr = []
  for x in range(0,len(Settings.Tasks)):
   if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
    try:
     if (Settings.Tasks[x].enabled): # device enabled
      t = threading.Thread(target=Settings.Tasks[x].plugin_exit)
      t.daemon = True
      procarr.append(t)
      t.start()
    except:
     pass
  if len(procarr)>0:
   for process in procarr:
     process.join(1)
  try:
   for t in range(0,rpieGlobals.RULES_TIMER_MAX):
    rpieTime.Timers[t].pause()
   for t in range(0,rpieGlobals.SYSTEM_TIMER_MAX):
    rpieTime.SysTimers[t].pause()
  except:
   pass
  procarr = []
  for y in range(0,len(Settings.Controllers)):
   if (Settings.Controllers[y]):
    if (Settings.Controllers[y].enabled):
      t = threading.Thread(target=Settings.Controllers[y].controller_exit)
      t.daemon = True
      procarr.append(t)
      t.start()
  if int(Settings.NetMan.WifiDevNum)>=0 and int(Settings.NetMan.APMode>-1):
    apdev = int(Settings.NetMan.WifiDevNum)
    Network.AP_stop(apdev) # try to stop AP mode if needed
  if len(procarr)>0:
   for process in procarr:
     process.join()

def doExecuteCommand(cmdline,Parse=True):
 if Parse:
  retval, state = parseruleline(cmdline)
 else:
  retval = cmdline
 cmdarr = retval.split(",")
 if (" " in retval) and not("," in retval):
  cmdarr = retval.split(" ")
 elif (" " in retval) and ("," in retval): # workaround for possible space instead comma problem
   fsp = retval.find(" ")
   fco = retval.find(",")
   if fsp<fco:
    c2 = retval.split(" ")
    cmdarr = retval[(fsp+1):].split(",")
    cmdarr = [c2[0]] + cmdarr
 cmdarr[0] = cmdarr[0].strip().lower()
 commandfound = False
 misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"CMD: "+cmdline.replace("==","="))
 
 if cmdarr[0] == "delay":
  try:
   s = float(cmdarr[1])
  except:
   s = 1000
  s = (s/1000)
  time.sleep(s)
  commandfound = True
  return commandfound

 elif cmdarr[0] == "taskrun":
  if len(Settings.Tasks)<1:
   return False
  try:
   s = int(cmdarr[1])
  except:
   s = -1
  if s >0 and (s<=len(Settings.Tasks)):
   s = s-1 # array is 0 based, tasks is 1 based
   if (type(Settings.Tasks[s])!=bool) and (Settings.Tasks[s]):
    if (Settings.Tasks[s].enabled):
     Settings.Tasks[s].plugin_read()
   commandfound = True
  return commandfound

 elif cmdarr[0] == "taskvalueset":
  if len(Settings.Tasks)<1:
   return False
  try:
   s = int(cmdarr[1])
  except:
   s = -1
  try:
   v = int(cmdarr[2])
  except:
   v = 1
  #v=v-1
  if s >0 and (s<=len(Settings.Tasks)):
   s = s-1 # array is 0 based, tasks is 1 based
   if (type(Settings.Tasks[s])!=bool) and (Settings.Tasks[s]):
    if v>(Settings.Tasks[s].valuecount):
     v = Settings.Tasks[s].valuecount
    if v<1:
     v = 1
    try:
     Settings.Tasks[s].set_value(v,parsevalue(str(cmdarr[3].strip())),False)
    except Exception as e:
     pass
#     print("Set value error: ",e)
    commandfound = True
  return commandfound

 elif cmdarr[0] == "taskvaluesetandrun":
  if len(Settings.Tasks)<1:
   return False
  try:
   s = int(cmdarr[1])
  except:
   s = -1
  try:
   v = int(cmdarr[2])
  except:
   v = 1
  #v=v-1
  if s >0 and (s<=len(Settings.Tasks)):
   s = s-1 # array is 0 based, tasks is 1 based
   if (type(Settings.Tasks[s])!=bool) and (Settings.Tasks[s]):
    if v>(Settings.Tasks[s].valuecount):
     v = Settings.Tasks[s].valuecount
    if v<1:
     v = 1
    Settings.Tasks[s].set_value(v,parsevalue(str(cmdarr[3]).strip()),True)
    commandfound = True
  return commandfound

 elif cmdarr[0] == "timerpause":
  if len(rpieTime.Timers)<1:
   return False
  try:
   s = int(cmdarr[1])
  except:
   s = -1
  if s>0 and (s<len(rpieTime.Timers)):
   s = s-1 # array is 0 based, timers is 1 based
   rpieTime.Timers[s].pause()
  commandfound = True
  return commandfound

 elif cmdarr[0] == "timerresume":
  if len(rpieTime.Timers)<1:
   return False
  try:
   s = int(cmdarr[1])
  except:
   s = -1
  if s>0 and (s<len(rpieTime.Timers)):
   s = s-1 # array is 0 based, timers is 1 based
   rpieTime.Timers[s].resume()
  commandfound = True
  return commandfound

 elif cmdarr[0] == "timerset":
  if len(rpieTime.Timers)<1:
   return False
  try:
   s = int(cmdarr[1])
  except:
   s = -1
  try:
   v = int(cmdarr[2])
  except:
   v = 1
  if s >0 and (s<len(rpieTime.Timers)):
   s = s-1 # array is 0 based, timers is 1 based
   if v==0:
    rpieTime.Timers[s].stop(False)
   else:
    rpieTime.Timers[s].addcallback(TimerCallback)
    rpieTime.Timers[s].start(v)
  commandfound = True
  return commandfound

 elif cmdarr[0] == "event":
  rulesProcessing(cmdarr[1],rpieGlobals.RULE_USER)
  commandfound = True
  return commandfound

 elif cmdarr[0] == "sendto":
  try:
   unitno = int(cmdarr[1])
  except:
   unitno = -1
  data = ""
  if len(cmdarr)>2:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1]) + 1 )
   sepp = cmdline.find(',',sepp)
   data = cmdline[sepp+1:].replace("==","=")
  else:
   unitno = -1
  if unitno>=0 and unitno<=255:
    cfound = False
    for y in range(len(Settings.Controllers)):
     if (Settings.Controllers[y]):
      if (Settings.Controllers[y].enabled):
       if "ESPEasy P2P" in Settings.Controllers[y].getcontrollername():
        Settings.Controllers[y].udpsender(unitno,data,1)
        cfound = True
    if cfound==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ESPEasy P2P controller not found!")
  commandfound = True
  return commandfound

 elif cmdarr[0] == "blecommand":
  try:
   unitno = int(cmdarr[1])
  except:
   unitno = -1
  data = ""
  if len(cmdarr)>2:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1]) + 1 )
   sepp = cmdline.find(',',sepp)
   data = cmdline[sepp+1:].replace("==","=")
  else:
   unitno = -1
  if unitno>=0 and unitno<=255:
    cfound = False
    for y in range(len(Settings.Controllers)):
     if (Settings.Controllers[y]):
      if (Settings.Controllers[y].enabled):
       if "BLE Direct" in Settings.Controllers[y].getcontrollername():
        Settings.Controllers[y].sendcommand(unitno,data)
        cfound = True
    if cfound==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BLE controller not found!")
  commandfound = True
  return commandfound

 elif cmdarr[0] == "loracommand":
  try:
   unitno = int(cmdarr[1])
  except:
   unitno = -1
  data = ""
  if len(cmdarr)>2:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1]) + 1 )
   sepp = cmdline.find(',',sepp)
   data = cmdline[sepp+1:].replace("==","=")
  else:
   unitno = -1
  if unitno>=0 and unitno<=255:
    cfound = False
    for y in range(len(Settings.Controllers)):
     if (Settings.Controllers[y]):
      if (Settings.Controllers[y].enabled):
       if "LORA Direct" in Settings.Controllers[y].getcontrollername():
        Settings.Controllers[y].sendcommand(unitno,data)
        cfound = True
    if cfound==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LORA controller not found!")
  commandfound = True
  return commandfound

 elif cmdarr[0] == "espnowcommand":
  try:
   unitno = int(cmdarr[1])
  except:
   unitno = -1
  data = ""
  if len(cmdarr)>2:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1]) + 1 )
   sepp = cmdline.find(',',sepp)
   data = cmdline[sepp+1:].replace("==","=")
  else:
   unitno = -1
  if unitno>=0 and unitno<=255:
    cfound = False
    for y in range(len(Settings.Controllers)):
     if (Settings.Controllers[y]):
      if (Settings.Controllers[y].enabled):
       if "ESPNow" in Settings.Controllers[y].getcontrollername():
        Settings.Controllers[y].sendcommand(unitno,data)
        cfound = True
    if cfound==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ESPNow controller not found!")
  commandfound = True
  return commandfound

 elif cmdarr[0] == "serialcommand":
  data = ""
  if len(cmdarr)>1:
   sepp = cmdline.find(',')
   data = cmdline[sepp+1:].replace("==","=")
  else:
   return False
  cfound = False
  for y in range(len(Settings.Controllers)):
     if (Settings.Controllers[y]):
      if (Settings.Controllers[y].enabled):
       if "ESPNow" in Settings.Controllers[y].getcontrollername():
        Settings.Controllers[y].serialcommand(data)
        cfound = True
  if cfound==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ESPNow controller not found!")
  commandfound = True
  return commandfound

 elif cmdarr[0] == "publish":
  topic = cmdarr[1].strip()
  data = ""
  if len(cmdarr)>2:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1]) + 1 )
   sepp = cmdline.find(',',sepp)
   data = cmdline[sepp+1:].replace("==","=")
  else:
   topic = ""
  commandfound = False
  if topic!="":
    cfound = False
    for y in range(len(Settings.Controllers)):
     if (Settings.Controllers[y]):
      if (Settings.Controllers[y].enabled):
       try:
        if Settings.Controllers[y].mqttclient is not None:
         Settings.Controllers[y].mqttclient.publish(topic,data)
         commandfound = True
         cfound = True
         break
       except:
        cfound = False
    if cfound==False:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT capable controller not found!")
  return commandfound

 elif cmdarr[0] == "sendtohttp":
  destaddr = cmdarr[1].strip()
  try:
   destport = int(cmdarr[2])
  except:
   destport = -1
  data = ""
  if len(cmdarr)>3:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1])+ len(cmdarr[2]) + 2 )
   sepp = cmdline.find(',',sepp)
   data = cmdline[sepp+1:].replace("==","=")
  else:
   destport = -1
  if destport > 0:
   commandfound = True
   curl = "http://"+destaddr+":"+str(destport)+data
   t = threading.Thread(target=urlget, args=(curl,))
   t.daemon = True
   t.start()
  else:
   commandfound = False
  return commandfound

 elif cmdarr[0] == "sendtoudp":
  destaddr = cmdarr[1].strip()
  try:
   destport = int(cmdarr[2])
  except:
   destport = -1
  data = ""
  if len(cmdarr)>3:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1])+ len(cmdarr[2]) + 2 )
   sepp = cmdline.find(',',sepp)
   data = cmdline[sepp+1:].replace("==","=")
  else:
   destport = -1
  if destport > 0:
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   for r in range(0,1):
    s.sendto(bytes(data,"utf-8"), (destaddr,int(destport)))
    if r<1:
     time.sleep(0.1)
   commandfound = True
  else:
   commandfound = False
  return commandfound
 elif cmdarr[0] == "wifiapmode":
  if int(Settings.NetMan.WifiDevNum)>=0:
    apdev = int(Settings.NetMan.WifiDevNum)
  else:
    apdev = Settings.NetMan.getfirstwirelessdevnum()
  Network.AP_start(apdev,True)
  commandfound = True
  return commandfound
 elif cmdarr[0] == "wifistamode":
  if int(Settings.NetMan.WifiDevNum)>=0:
    apdev = int(Settings.NetMan.WifiDevNum)
  else:
    apdev = Settings.NetMan.getfirstwirelessdevnum()
  Network.AP_stop(apdev)
  Settings.NetMan.APMode = -1
  commandfound = True
  return commandfound
 elif cmdarr[0] == "wificonnect": # implement it
  commandfound = False
  return commandfound
 elif cmdarr[0] == "wifimode":    # implement it
  commandfound = False
  return commandfound
 elif cmdarr[0] == "reboot":
  doCleanup()
  os.popen(OS.cmdline_rootcorrect("sudo reboot"))
#  os.kill(os.getpid(), signal.SIGINT)
  commandfound = True
  return commandfound
 elif cmdarr[0] == "reset":
  os.popen("rm -r data/*.json")
  Settings.Controllers = [False]
  Settings.NetworkDevices = []
  Settings.Pinout = []
  Settings.Settings = {"Name":"RPIEasy","Unit":0,"Password":"","Delay":60}
  Settings.Tasks = [False]
  Settings.NetMan.networkinit()
  commandfound = True
  return commandfound
 elif cmdarr[0] == "halt":
  doCleanup()
  os.popen(OS.cmdline_rootcorrect("sudo shutdown -h now"))
#  os.kill(os.getpid(), signal.SIGINT)
  commandfound = True
  return commandfound
 elif cmdarr[0] == "update":
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Starting git clone")
  os.popen("cp -rf run.sh run.sh.bak && rm -rf update && git clone https://github.com/enesbcs/rpieasy.git update").read()
  time.sleep(2)
  if os.path.isdir("update"):
   misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Download successful, starting to overwrite files")
   os.popen("rm -rf .git && rm -rf update/data update/files && mv -f update/.git .git && cp -rf update/lib/* lib/ && cp -rf update/img/* img/ && rm -rf update/lib update/img && mv -f update/* . && rm -rf update && cp -rf run.sh.bak run.sh").read()
   time.sleep(0.5)
   os.kill(os.getpid(), signal.SIGINT)
  else:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Update failed")
  commandfound = True
  return commandfound
 elif cmdarr[0] == "exit":
  os.kill(os.getpid(), signal.SIGINT)
  commandfound = True
  return commandfound

 elif cmdarr[0] == "notify":
  try:
   plugin = int(cmdarr[1])
  except:
   plugin = 0
  data = ""
  if len(cmdarr)>1 and plugin>0:
   sepp = ( len(cmdarr[0]) + len(cmdarr[1])+ 2 )
   data = cmdline[sepp:].replace("==","=")
   commandfound = doExecuteNotification(plugin-1,data)
  return commandfound

 elif cmdarr[0] == "setvolume":
  vmr = 0
  if "+" in cmdarr[1] or "-" in cmdarr[1]:
   vmr = 1
  try:
   vol = int(cmdarr[1])
  except:
   vol = -200
  if (vmr==0):               # absolute vol
   if (vol>=0 and vol<=100):
    try:
     OS.setvolume(vol)
     commandfound = True
    except Exception as e:
     commandfound = str(e)
  else:
   if (vol>=-100 and vol<=100): # relative vol
    try:
     avol = OS.getvolume()
     OS.setvolume(int(avol)+vol)
     commandfound = True
    except Exception as e:
     commandfound = str(e)
  return commandfound

 if commandfound==False:
  commandfound = doExecutePluginCommand(retval)
 if commandfound==False:
  misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Unknown command: "+cmdline)
 return commandfound

def urlget(url):
  try:
   urllib.request.urlopen(url,None,1)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))

def TimerCallback(tid):
  rulesProcessing("Rules#Timer="+str(tid),rpieGlobals.RULE_TIMER)

def doExecutePluginCommand(cmdline):
  retvalue = False
  if len(Settings.Tasks)<1:
   return False
  for s in range(len(Settings.Tasks)):
    if (type(Settings.Tasks[s])!=bool) and (Settings.Tasks[s].enabled):
     try:
      retvalue = Settings.Tasks[s].plugin_write(cmdline)
     except Exception as e:
      retvalue = str(e)
     if retvalue!=False:
      return retvalue
  return retvalue

def doExecuteNotification(num,cmdline):
  retvalue = False
  if len(Settings.Notifiers)<1:
   return False
  try:
   num=int(num)
   if num>=0 and num<len(Settings.Notifiers) and (Settings.Notifiers[num].enabled):
    retvalue = Settings.Notifiers[num].notify(cmdline)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Notification error: "+str(e))
  return retvalue

def decodeeventname(eventname):
 ten = eventname.strip().lower()
 ec = -1
 if ("system#" in ten) or ("mqtt#connected" in ten) or ("mqtt#disconnected" in ten):
   ec = rpieGlobals.RULE_SYSTEM
 elif ("clock#time" in ten):
   ec = rpieGlobals.RULE_CLOCK
 elif ("rules#timer" in ten):
   ec = rpieGlobals.RULE_TIMER
 else:
  ec = rpieGlobals.RULE_USER
 return ec

def splitruletoevents(rulestr): # parse rule string into array of events
 global GlobalRules
 GlobalRules = []
 rcount = -1
 evfound = False
 ename = ""
 evarr = []
 rulearr = rulestr.splitlines()
 for line in rulearr:
  linelower = line.strip().lower()
  if linelower.startswith("on ") and linelower.endswith(" do"):
   rcount += 1
   evfound = True
   tstr = line.strip().split(" ")
   ename = tstr[1]
  elif evfound:
   if linelower.startswith("endon"):
    evfound = False
    GlobalRules.append({"ename":ename,"ecat":decodeeventname(ename), "ecode":evarr,"lastcheck":0,"evalue":-1})
    evarr = []
    ename = ""
   else:
    evarr.append(line.strip())

def getfirstequpos(cstr):
 res = -1
 for c in range(len(cstr)):
  if cstr[c] in "<>=!":
   res = c
   break
 return res

def removeequchars(cstr):
 remc = getequchars(cstr)
 res = cstr
 for c in range(len(remc)):
  res = res.replace(remc[c],"")
 return res

def getequchars(cstr,arr=False):
 res = ""
 res2 = []
 equs = "<>=!"
 for c in range(len(equs)):
  if equs[c] in cstr:
   if equs[c] not in res:
    res += equs[c]
    res2.append(equs[c])
 if arr:
  return res2
 else:
  return res

def gettaskvaluefromname(taskname): # taskname#valuename->value
 res = -1
 try:
  taskprop = taskname.split("#")
  taskprop[0] = taskprop[0].strip().lower()
  taskprop[1] = taskprop[1].strip().lower() 
 except:
  res = -1
  return res
 try:
  for s in range(len(Settings.Tasks)):
   if type(Settings.Tasks[s]) is not bool:
    if Settings.Tasks[s].taskname.lower()==taskprop[0]:
     for v in range(len(Settings.Tasks[s].valuenames)):
      if Settings.Tasks[s].valuenames[v].lower() == taskprop[1]:
       res = Settings.Tasks[s].uservar[v]
       break
 except:
   res=-1
 return res

suntimesupported = -1

def addtoTime(basetime, deltastr): # -1h +2h -10m +3m ...
 sign = 1
 multi = 1
 deltastr = str(deltastr).lower()
 if "-" in deltastr:
  sign = -1
  deltastr = deltastr.replace("-","")
 else:
  deltastr = deltastr.replace("+","")
 if "h" in deltastr:
  multi = 3600
  deltastr = deltastr.replace("h","")
 if "m" in deltastr:
  multi = 60
  deltastr = deltastr.replace("m","")
 try:
  from datetime import timedelta
  td = int(deltastr)
  if sign==1:
   return basetime + timedelta(seconds=(td*multi))
  else:
   return basetime - timedelta(seconds=(td*multi))
 except:
  return basetime


def getglobalvar(varname):
 global SysVars, suntimesupported
 svname = varname.strip().lower()
 par = ""
 if ("-" in svname):
  resarr = svname.split("-")
  svname = resarr[0]
  par = "-"+resarr[1]
 if ("+" in svname):
  resarr = svname.split("+")
  svname = resarr[0]
  par = "+"+resarr[1]
 res = ""
 if svname in SysVars:
   if svname==SysVars[0]: #%systime%	01:23:54
    return datetime.now().strftime('%H:%M:%S')
   elif svname==SysVars[1]: #%systm_hm% 	01:23 
    return datetime.now().strftime('%H:%M')
   elif svname==SysVars[2]: #%lcltime% 	2018-03-16 01:23:54 
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   elif svname==SysVars[3]: #%syshour% 	11 	Current hour (hh)
    return int(datetime.now().strftime('%H'))
   elif svname==SysVars[4]: #%sysmin% 	22 	Current minute (mm)
    return int(datetime.now().strftime('%M'))
   elif svname==SysVars[5]: #%syssec% 	33 	Current second (ss)
    return int(datetime.now().strftime('%S'))
   elif svname==SysVars[6]: #%sysday% 	16 	Current day of month (DD)
    return int(datetime.now().strftime('%d'))
   elif svname==SysVars[7]: #%sysmonth% 	3 	Current month (MM)
    return int(datetime.now().strftime('%m'))
   elif svname==SysVars[8]: #%sysyear% 	2018 	4 digits (YYYY)
    return datetime.now().strftime('%Y')
   elif svname==SysVars[9]: #%sysyears% 	18 	2 digits (YY)
    return datetime.now().strftime('%y')
   elif svname==SysVars[10]: #%sysweekday% 	5 	Weekday (integer) - 1, 2, 3... (1=Sunday, 2=Monday etc.)
    return str(int(datetime.now().strftime('%w'))+1)
   elif svname==SysVars[11]: #%sysweekday_s% 	Fri 	Weekday (verbose) - Sun, Mon, Tue
    return datetime.now().strftime('%a')
   elif svname==SysVars[12]: #%unixtime% 	1521731277 	Unix time (seconds since epoch, 1970-01-01 00:00:00)
    return str(int(time.time()))
   elif svname==SysVars[13]: #%uptime% 	3244 	Uptime in minutes
    return str(rpieTime.getuptime(2))
   elif svname==SysVars[14]: #%rssi% 	-45 	WiFi signal strength (dBm)
    return str(OS.get_rssi())
   elif svname==SysVars[15]: #%ip% 	192.168.0.123 	Current IP address
    return str(OS.get_ip())
   elif svname==SysVars[16]: #%ip4% ipcim 4.byte
    res2 = str(OS.get_ip())
    resarr = res2.split(".")
    if len(resarr)>3:
     return resarr[3]
   elif svname==SysVars[17]: #%sysname%	name
    return Settings.Settings["Name"]
   elif svname==SysVars[18]: #%unit% 	32 	Unit number
    return Settings.Settings["Unit"]
   elif svname==SysVars[19]: #%ssid% 	H4XX0R njietwork! 
    wdev = False
    try:
     wdev = Settings.NetMan.getfirstwirelessdev()
    except:
     wdev = False
    if wdev:
     res = str(Network.get_ssid(wdev))
   elif svname==SysVars[20]: #%mac% 	00:14:22:01:23:45 	MAC address
    pd = -1
    try:
     pd = Settings.NetMan.getprimarydevice()
    except:
     pd = -1
    if pd<0 and len(Settings.NetworkDevices)>0:
     pd = 0
    if pd!="" and pd>=0:
     return Settings.NetworkDevices[pd].mac
   elif svname==SysVars[21]: #%mac_int% 	2212667 	MAC address in integer to be used in rules (only the last 24 bit)
    pd = -1
    try:
     pd = Settings.NetMan.getprimarydevice()
    except:
     pd = -1
    if pd<0 and len(Settings.NetworkDevices)>0:
     pd = 0
    if pd>=0:
     try:
      res2 = Settings.NetworkDevices[pd].mac
      resarr = res2.split(":")
      if len(resarr)>5:
       res = str(int("0x"+resarr[3]+resarr[4]+resarr[5],16))
     except:
      res = ""
    return res
   elif svname==SysVars[22]: #%build%
    bstr = str(rpieGlobals.BUILD)
    return bstr
   elif svname==SysVars[23]: #sunrise
    try:
      from suntime import Sun
      suntimesupported = 1
    except:
      suntimesupported = 0
    if suntimesupported==1:
     try:
      sun = Sun(Settings.AdvSettings["Latitude"],Settings.AdvSettings["Longitude"])
      abd_sr = sun.get_local_sunrise_time(datetime.now())
      if par!="":
       abd_sr = addtoTime(abd_sr,par)
      res = abd_sr.strftime('%H:%M')
     except Exception as e:
      res = "00:00"
     return res
   elif svname==SysVars[24]: #sunset
    try:
      from suntime import Sun
      suntimesupported = 1
    except:
      suntimesupported = 0
    if suntimesupported==1:
     try:
      sun = Sun(Settings.AdvSettings["Latitude"],Settings.AdvSettings["Longitude"])
      abd_ss = sun.get_local_sunset_time(datetime.now())
      if par!="":
       abd_ss = addtoTime(abd_ss,par)
      res = abd_ss.strftime('%H:%M')
     except Exception as e:
      res = "00:00"
     return res

   elif svname==SysVars[25]: #sun altitude
    try:
      from pytz import reference
      from pysolar.solar import get_altitude
      pysolarsupported = 1
    except:
      pysolarsupported = 0
    res = "0"
    if pysolarsupported==1:
     try:
      localtime = reference.LocalTimezone()
      today = datetime.now(localtime)
      res = get_altitude(Settings.AdvSettings["Latitude"],Settings.AdvSettings["Longitude"], today)
     except Exception as e:
      print(e)
      res = "0"
     return res

   elif svname==SysVars[26]: #sun azimuth
    try:
      from pytz import reference
      from pysolar.solar import get_azimuth
      pysolarsupported = 1
    except:
      pysolarsupported = 0
    res = "0"
    if pysolarsupported==1:
     try:
      localtime = reference.LocalTimezone()
      today = datetime.now(localtime)
      res = get_azimuth(Settings.AdvSettings["Latitude"],Settings.AdvSettings["Longitude"], today)
     except Exception as e:
      print(e)
      res = "0"
     return res

   elif svname==SysVars[27]: #sun radiation
    try:
      from pytz import reference
      from pysolar.solar import get_altitude
      from pysolar.radiation import get_radiation_direct
      pysolarsupported = 1
    except:
      pysolarsupported = 0
    res = "-1"
    if pysolarsupported==1:
     try:
      localtime = reference.LocalTimezone()
      today = datetime.now(localtime)
      altitude_deg = get_altitude(Settings.AdvSettings["Latitude"],Settings.AdvSettings["Longitude"], today)
      res = get_radiation_direct(today, altitude_deg)
     except Exception as e:
      print(e)
     return res

 return res

def parsevalue(pvalue):
   retval = pvalue
   if ('%' in pvalue) or ('[' in pvalue):
    retval, state = parseruleline(pvalue) # replace variables
   oparr = "+-*/%&|^~<>"
   op = False
   for o in oparr:
    if o in retval:
     op = True
     break
   try:
    if op:
     retval = eval(retval)  # evaluate expressions
   except:
     retval = str(retval)
   return retval

def parseconversions(cvalue):
 retval = cvalue
 if ("%c_" in retval):
  cf = retval.find("%c_m2day%")
  if cf>=0:
   ps = retval.find("(",cf)
   pe = -1
   if ps >=0:
    pe = retval.find(")",ps)
   if pe >= 0:
    param = retval[ps+1:pe].strip()
   try:
    param = float(param)
   except:
    param = 0
   retval = retval[:cf]+str(misc.formatnum((param/1440),2))+retval[pe+1:]
  cf = retval.find("%c_m2dh%")
  if cf>=0:
   ps = retval.find("(",cf)
   pe = -1
   if ps >=0:
    pe = retval.find(")",ps)
   if pe >= 0:
    param = retval[ps+1:pe].strip()
   try:
    param = float(param)
   except:
    param = 0
   days, remainder = divmod(param, 1440)
   hours, minutes = divmod(remainder, 60)
   retval = retval[:cf]+str(int(days))+"d "+str(int(hours))+"h"+retval[pe+1:]
  cf = retval.find("%c_m2dhm%")
  if cf>=0:
   ps = retval.find("(",cf)
   pe = -1
   if ps >=0:
    pe = retval.find(")",ps)
   if pe >= 0:
    param = retval[ps+1:pe].strip()
   try:
    param = float(param)
   except:
    param = 0
   days, remainder = divmod(param, 1440)
   hours, minutes = divmod(remainder, 60)
   retval = retval[:cf]+str(int(days))+"d "+str(int(hours))+"h "+str(int(minutes))+"m"+retval[pe+1:]
 return retval

def parseruleline(linestr,rulenum=-1):
 global GlobalRules
 cline = linestr.strip()
 state = "CMD"
 if "[" in linestr:
  m = re.findall(r"\[([A-Za-z0-9_#]+)\]", linestr)
  if len(m)>0: # replace with values
   for r in range(len(m)):
    tval = str(gettaskvaluefromname(m[r]))
    if tval=="None":
     state = "INV"
    cline = cline.replace("["+m[r]+"]",tval)
 if ("%eventvalue%" in linestr) and (rulenum!=-1):
  cline = cline.replace("%eventvalue%",str(GlobalRules[rulenum]["evalue"]))
 if "%" in cline:
  m = re.findall(r"\%([A-Za-z0-9_#\+\-]+)\%", cline)
  if len(m)>0: # replace with values
   for r in range(len(m)):
    if m[r] in SysVars:
     cline = cline.replace("%"+m[r]+"%",str(getglobalvar(m[r])))
    elif ("-" in m[r]) or ("+" in m[r]):
     val = str(getglobalvar(m[r]))
     if val != "":
      cline = cline.replace("%"+m[r]+"%",val)
 cline = parseconversions(cline)
 equ = getfirstequpos(cline)
 if equ!=-1:
  if cline[:3].lower() == "if ":
   if "=" in getequchars(cline,True):
    cline = cline.replace("=","==") # prep for python interpreter
    cline = cline.replace("!==","!=") # revert invalid operators
    cline = cline.replace(">==",">=")
    cline = cline.replace("<==","<=")
   tline = cline
   state = "IFST"
   try:
    cline = eval(cline[3:])
   except:
    cline = False                 # error checking?
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Parsed condition: "+str(tline)+" "+str(cline))
 elif "endif" in cline:
  cline = True
  state = "IFEN"
 elif "else" in cline:
  cline = False
  state = "IFEL"
 return cline,state

def isformula(line):
 if "%value%" in line.lower():
  return True
 else:
  return False

def parseformula(line,value):
 fv = False
 if "%value%" in line.lower():
  l2 = line.replace("%value%",str(value))
  fv = parsevalue(l2)
 return fv

def rulesProcessing(eventstr,efilter=-1): # fire events
 global GlobalRules
 rfound = -1
 retval = 0
 misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Event: "+eventstr)
 estr=eventstr.strip().lower()
 if len(GlobalRules)<1:             # if no rules found, exit
  return False
 for r in range(len(GlobalRules)):
  if efilter!=-1:
   if GlobalRules[r]["ecat"]==efilter:  # check event based on filter
     if efilter == rpieGlobals.RULE_TIMER:
        if GlobalRules[r]["ename"].lower() == estr.lower():
         rfound = r
         break
     elif efilter == rpieGlobals.RULE_CLOCK: # check time strings equality
      fe1 = getfirstequpos(estr)
      invalue = removeequchars(estr[fe1:].replace("=","").strip())
      fe2 = getfirstequpos(GlobalRules[r]["ename"])
      tes = invalue+GlobalRules[r]["ename"][fe2:]
      if comparetime(tes):
        rfound = r
        break
     else:
       fe1 = getfirstequpos(estr)
       if fe1 ==-1:
        fe1 = len(estr)
       if fe1<=len(GlobalRules[r]["ename"]):
        if GlobalRules[r]["ename"][:fe1].lower()==estr[:fe1].lower():
         rfound = r
         break
  else:                                      # it is general event, without filter
    fe1 = getfirstequpos(estr)
    if fe1 ==-1:
     fe1 = len(estr)
    if fe1<=len(GlobalRules[r]["ename"]):
      if GlobalRules[r]["ename"][:fe1].lower()==estr[:fe1].lower():
       rfound = r
       break
 if rfound>-1: # if event found, analyze that
  fe1 = getfirstequpos(estr)
  if (fe1>-1): # value found
    if GlobalRules[rfound]["ecat"] == rpieGlobals.RULE_CLOCK: # check time strings equality
      pass
    elif GlobalRules[rfound]["ecat"] == rpieGlobals.RULE_TIMER: # check timer
      pass
    else:
      invalue = ""
#      print("ename ",GlobalRules[rfound]["ename"]) # debug
      if getfirstequpos(str(GlobalRules[rfound]["ename"]))>-1:
       invalue = removeequchars(estr[fe1:].replace("=","").strip())
#      print("i1 ",invalue)                     # debug
#      print("estr ",estr,getfirstequpos(estr)) # debug
      if getfirstequpos(estr)>-1:
       if getfirstequpos(GlobalRules[rfound]["ename"][fe1:])>-1:
        invalue = removeequchars(estr[fe1:].replace("=","").strip())
       else:
        GlobalRules[rfound]["evalue"]=removeequchars(estr[fe1:].replace("=","").strip())
#      print("i2 ",invalue)                     # debug
      if invalue != "":
       GlobalRules[rfound]["evalue"]=invalue                 # %eventvalue%
       tes = str(invalue)+str(GlobalRules[rfound]["ename"][fe1:])
       try:
        if "=" == getequchars(tes):
         tes = tes.replace("=","==") # prepare line for python interpreter
        if eval(tes)==False:         # ask the python interpreter to eval conditions
         return False                # if False, than exit - it looks like a good idea, will see...
       except:
        return False
  if len(GlobalRules[rfound]["ecode"])>0:
   ifbool = True
   for rl in range(len(GlobalRules[rfound]["ecode"])):
     retval, state = parseruleline(GlobalRules[rfound]["ecode"][rl],rfound) # analyze condition blocks
     if state=="IFST":
       ifbool = retval
     elif state=="IFEL":
       ifbool = not(ifbool)
     elif state=="IFEN":
       ifbool = True
     elif ifbool:
      if state=="INV":
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Invalid command: "+retval)
      else:
       cret = doExecuteCommand(retval,False) # execute command

def comparetime(tstr):
 result = True
 try:
  tstr2 = tstr.replace(":",",")
  tstr2 = tstr2.replace("==","=")
  sides = tstr2.split("=")
  tleft = sides[0].split(",")
  tright = sides[1].split(",")
  tleft[0] = tleft[0].lower()
  tright[0] = tright[0].lower()
  l1 = len(tleft)
  l2 = len(tright)
  if l2<l1:
   l1 = l2
  for t in range(l1):
   if 'all' not in tright[t] and '**' not in tright[t]:
    if str(tright[t]).strip() != str(tleft[t]).strip():
     result = False
     break
 except:
  result = False
 return result
