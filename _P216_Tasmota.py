#!/usr/bin/env python3
#############################################################################
################## Tasmota URL API plugin for RPIEasy #######################
#############################################################################
#
# Copyright (C) 2022 by Alexander Nagy - https://bitekmindenhol.blog.hu/
# Basic Tasmota relay HTTP API for Tasmota Remota,Tasmota Control and HomeSwitch
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import webserver
import Settings
import rpieTime
import os_os as OS
import os, sys, platform
from datetime import datetime, timedelta

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 216
 PLUGIN_NAME = "API - Tasmota Relay HTTP API (BETA)"
 PLUGIN_VALUENAME1 = "State"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.readinprogress = 0
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = False
  self.timeroptional = True
  self.formulaoption = False
  self._nextdataservetime = 0
  self.datas = [  ["_",""],  ["_",""],  ["_",""],  ["_",""],  ["_",""],  ["_",""],  ["_",""],  ["_",""] ]
  self.modtype = 18
  self.btime = ""

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.taskdevicepluginconfig[0] == 1:
   self.modtype = 1
  elif self.taskdevicepluginconfig[0] == 2:
   self.modtype = 5
  elif self.taskdevicepluginconfig[0] == 3:
   self.modtype = 30
  elif self.taskdevicepluginconfig[0] == 4:
   self.modtype = 7
  else:
   self.modtype = 18
  try:
        self.btime = time.ctime(os.path.getmtime('rpieGlobals.py'))
  except:
        self.btime = ""
  self.initialized = True

 def webform_load(self): # create html page for settings
  try:
   options2 = ["None"]
   optionvalues2 = ["_"]
   for t in range(0,len(Settings.Tasks)):
      if (Settings.Tasks[t] and (type(Settings.Tasks[t]) is not bool)):
       for v in range(0,Settings.Tasks[t].valuecount):
        options2.append("T"+str(t+1)+"-"+str(v+1)+" / "+str(Settings.Tasks[t].taskname)+"-"+str(Settings.Tasks[t].valuenames[v]))
        optionvalues2.append(str(t)+"_"+str(v))
   webserver.addFormNumericBox("Number of relays","p216_relays",self.taskdevicepluginconfig[0],1,8)
   webserver.addFormNote("Basic fake Tasmota HTTP command API for Android apps: Tasmota Remota, Tasmota Control, HomeSwitch")
   webserver.addFormNote("Select tasks below which you need to access from Android app. Only On/Off supported!")
   for r in range(8):
     webserver.addFormSubHeader("Relay "+str(r+1))
     webserver.addHtml("<tr><td>Controlled task:<td>")
     ddata = self.datas[r][0]
     webserver.addSelector_Head("p216_tv_"+str(r),False)
     for o in range(len(options2)):
       webserver.addSelector_Item(options2[o],optionvalues2[o],(str(optionvalues2[o])==str(ddata)),False)
     webserver.addSelector_Foot()
     webserver.addFormTextBox("Relay friendly name","p216_tvn_"+str(r),self.datas[r][1],64)
  except Exception as e:
   return False
  return True

 def webform_save(self,params): # process settings post reply
    try:
     self.taskdevicepluginconfig[0] = int(webserver.arg("p216_relays",params))
    except:
     self.taskdevicepluginconfig[0] = 1
    for r in range(self.taskdevicepluginconfig[0]):
     self.datas[r][0] = str(webserver.arg("p216_tv_"+str(r),params))
     self.datas[r][1] = str(webserver.arg("p216_tvn_"+str(r),params))
     if self.datas[r][1] == "":
       try:
        ti = self.datas[r][0].split("_")
        t = int(ti[0])
        v  = int(ti[1])
        self.datas[r][1] = str(Settings.Tasks[t].taskname)+"-"+str(Settings.Tasks[t].valuenames[v])
       except:
        pass
    if r < 7:
     for s in range((r+1),8):
      self.datas[s][0] = "_"
      self.datas[s][1] = ""
    return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled:
     self._lastdataservetime = rpieTime.millis()
  return result

def getswitchstate(num, globdata):
  if num >= int(globdata.taskdevicepluginconfig[0]):
    num = 0
  try:
    ti = globdata.datas[num][0].split("_")
    t = int(ti[0])
    v  = int(ti[1])
    state = int(float(Settings.Tasks[t].uservar[v]))
    return state
  except Exception as e:
    pass
  return 0

def setswitchstate(num, nstate, globdata):
#  print("SET ", (num+1), " to ", nstate)
  if num > globdata.taskdevicepluginconfig[0]:
    num = 0
  try:
    ti = globdata.datas[num][0].split("_")
    t = int(ti[0])
    v  = int(ti[1])
    if str(nstate) == "2":
     ostate = int(float(Settings.Tasks[t].uservar[v]))
     nstate = 1-ostate
#    print(t,v,int(nstate))#debug
    Settings.Tasks[t].set_value(v+1,int(nstate),True)
    return nstate
  except Exception as e:
    pass
  return 0

def getstatusjson(st,globdata):
 rstr = ""
 if st=="Status":
    rstr +='"Status": {"Module": '+str(globdata.modtype)+ ',"DeviceName":"' + str(Settings.Settings["Name"]) + '",'
    rstr += '"FriendlyName": ["' + str(globdata.datas[0][1]) + '"'
    if globdata.taskdevicepluginconfig[0]>1:
     for n in range(1,globdata.taskdevicepluginconfig[0]):
         rstr += ',"' + str(globdata.datas[n][1]) + '"'
    rstr += '],"Topic": "","ButtonTopic": "0","PowerOnState": 0,"LedState": 0,"SaveData": 1,"SaveState": 1,"ButtonRetain": 0,"PowerRetain": 0,'
    if getswitchstate(0,globdata):
     s = 1
    else:
     s = 0
    rstr += '"Power": ' +str(s) + '}'

 elif st=="StatusPRM":
    rstr += '"StatusPRM": {"Baudrate": 115200,"GroupTopic": "","OtaUrl": "","Sleep": 0,"BootCount": 1,"SaveCount": 1,"SaveAddress": "FB000",'
    rstr += '"Uptime": "' + rpieTime.getuptime(3) + '"}'

 elif st=="StatusNET":
    try:
      defaultdev = Settings.NetMan.getprimarydevice()
      if Settings.NetworkDevices[defaultdev].ip=="":
       defaultdev = -1
    except:
      defaultdev = -1
    if defaultdev==-1:
      try:
       defaultdev = Settings.NetMan.getsecondarydevice()
      except:
       defaultdev = -1
    rstr += '"StatusNET": {"Webserver": 2,"WifiConfig": 4,'
    rstr += '"Hostname": "' + str(Settings.Settings["Name"]) + '",'
    rstr += '"IPAddress": "' + str(Settings.NetworkDevices[defaultdev].ip) + '",'
    rstr += '"Gateway": "' + str(Settings.NetworkDevices[defaultdev].gw) + '",'
    rstr += '"Subnetmask": "' + str(Settings.NetworkDevices[defaultdev].mask) + '",'
    dnss = Settings.NetworkDevices[defaultdev].dns.strip().split(" ")
    rstr += '"DNSServer": "' +str(dnss[0]) + '",'
    rstr += '"Mac": "' + str(Settings.NetworkDevices[defaultdev].mac).upper() + '"}'

 elif st=="StatusSNS":
     rstr += '"StatusSNS": {"Time": "' +datetime.now().strftime('%Y-%m-%dT%H:%M:%S') + '",'
     if globdata.taskdevicepluginconfig[0]==1:
       if getswitchstate(0,globdata)==1:
         st = "ON"
       else:
         st = "OFF"
       rstr += '"Switch1": "' + st + '"'
     else:
      for s in range (int(globdata.taskdevicepluginconfig[0])):
       if getswitchstate(s,globdata)==1:
         st = "ON"
       else:
         st = "OFF"
       rstr += '"Switch' + str(s+1) +'": "' + st + '"'
       if s < (int(globdata.taskdevicepluginconfig[0])-1):
        rstr += ","
     rstr += '}'

 elif st=="StatusSTS":
      rstr += '"StatusSTS": {"Vcc": 3.1415,' # Pi= 3.14
      rstr += '"Time": "' +str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S')) + '",'
      rstr += '"Uptime": "' + rpieTime.getuptime(3) + '",'
      if globdata.taskdevicepluginconfig[0]==1:
         rstr += '"POWER": "'
         if getswitchstate(0,globdata)==1:
           rstr += "ON"
         else:
           rstr += "OFF"
         rstr += '",'
      else:
         for s in range (globdata.taskdevicepluginconfig[0]):
          rstr += '"POWER'+ str(s+1) +'": "'
          if getswitchstate(s,globdata)==1:
           rstr += "ON"
          else:
           rstr += "OFF"
          rstr += '",'
      rstr += '"Wifi": {"AP": 1,'
      rstr += '"SSId": "' + str(Settings.NetMan.WifiSSID) + '",'
      rstr += '"RSSI": ' + str(OS.get_rssi()) + ','
      rstr += '"APMac": "","Channel":1}}'

 elif st=="StatusTIM":
      rstr +=  '"StatusTIM": {'
      rstr += '"UTC": "' + str(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')) + '",'
      rstr += '"Local": "' +str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S')) + '",'
      rstr += '"StartDST": "1970-01-01T00:00:00","EndDST": "1970-01-01T00:00:00",'
      rstr += '"Timezone": "+00:00"}'
 
 elif st=="StatusMEM":
      rstr += '"StatusMEM": {"ProgramSize": 2048,"Free": 2048,"ProgramFlashSize": 4096,"FlashSize": 4096,"FlashMode": 3,'
      rstr += '"Heap": ' + str( OS.FreeMem() ) + '}'

 elif st=="StatusFWR":
    rstr += '"StatusFWR": {"Version": "5.12.0a","Boot": 1,'
    rstr += '"BuildDateTime": "' + str(globdata.btime) + '",'
    rstr += '"Core": "'+ rpieGlobals.PROGNAME + ' ' + rpieGlobals.PROGVER + '",'
    rstr += '"SDK": "Python '+ sys.version.replace('\n','')+" "+platform.platform() + '",'
    cpui = OS.get_cpu()
    frarr = str(cpui["speed"]).split()
    try:
     fr = str(int(misc.str2num(frarr[0])))
    except:
     fr = str(frarr[0])
    rstr += '"CpuFrequency": "' + fr  + '","Hardware":"'+ str(cpui["model"]) +'"}'

 return rstr


@webserver.WebServer.route('/cm')
def handle_tasmotacm(self):
  try:
   dashtask = None
   for t in range(0,len(Settings.Tasks)):
     if (Settings.Tasks[t] and (type(Settings.Tasks[t]) is not bool)):
      try:
       if Settings.Tasks[t].enabled:
        if Settings.Tasks[t].pluginid==216:
         dashtask = Settings.Tasks[t]
         break
      except:
       pass
   self.set_mime('application/json')
   if self.type == "GET":
    responsearr = self.get
   else:
    responsearr = self.post
   webserver.TXBuffer = ""

   if dashtask.enabled and dashtask.initialized:

    cmnd = webserver.arg("cmnd",responsearr)
#    print("e",cmnd)#debug
    cmdline = cmnd.split()
    if len(cmdline)<1: #unknown
      print("Unknown command: ",cmnd)
      webserver.TXBuffer = '{"Command":"Error"}'
      return webserver.TXBuffer
    if cmdline[0].lower() == "status": #get status
     if len(cmdline)==1 or cmdline[1]== "1": #statusprm
      webserver.TXBuffer = "{" + getstatusjson("StatusPRM",dashtask) + "}"
     elif cmdline[1] == "2": #fwr
      webserver.TXBuffer = "{" + getstatusjson("StatusFWR",dashtask) + "}"
     elif cmdline[1] == "4": #mem
      webserver.TXBuffer = "{" + getstatusjson("StatusMEM",dashtask) + "}"
     elif cmdline[1] == "5": #net
      webserver.TXBuffer = "{" + getstatusjson("StatusNET",dashtask) + "}"
     elif cmdline[1] == "7": #tim
      webserver.TXBuffer = "{" + getstatusjson("StatusTIM",dashtask) + "}"
     elif cmdline[1] == "8" or cmdline[1] == "10": #sns
      webserver.TXBuffer = "{" + getstatusjson("StatusSNS",dashtask) + "}"
     elif cmdline[1] == "11": #sts
      webserver.TXBuffer = "{" + getstatusjson("StatusSTS",dashtask) + "}"
     elif cmdline[1] == "0": #all
      webserver.TXBuffer = "{" + getstatusjson("Status",dashtask)+ ","
      webserver.TXBuffer += getstatusjson("StatusPRM",dashtask) + ","
      webserver.TXBuffer += getstatusjson("StatusFWR",dashtask) + ","
      webserver.TXBuffer += getstatusjson("StatusMEM",dashtask) + ","
      webserver.TXBuffer += getstatusjson("StatusNET",dashtask) + ","
      webserver.TXBuffer += getstatusjson("StatusTIM",dashtask) + ","
      webserver.TXBuffer += getstatusjson("StatusSNS",dashtask) + ","
      webserver.TXBuffer += getstatusjson("StatusSTS",dashtask) + "}"
     else: #error
      print("Unknown command: ",cmnd)
      webserver.TXBuffer = '{"Command":"Error"}'
    elif cmdline[0].lower() == "state": #get status old mode
      resp = getstatusjson("StatusSTS",dashtask)
      webserver.TXBuffer = "{" + resp[14:].strip()[:-1]+ ","
      resp = getstatusjson("StatusFWR",dashtask)
      webserver.TXBuffer += resp[14:].strip()[:-1] +","
      resp = getstatusjson("StatusNET",dashtask)
      webserver.TXBuffer += resp[14:].strip()[:-1] +"}"
    elif cmdline[0].lower()[:5] == "power": #change status
     if len(cmdline)>1: #set if we get params
      try:
       snstr = cmdline[0].strip()
       sn = int(snstr[5])
       sn = sn - 1
       if sn < 0 or sn > 7:
        sn = 0
      except:
       sn = 0

      par = str(cmdline[1])[:2].upper()
      if par == "0" or par == "OF":
       par2 = 0
      elif par == "1" or par == "ON":
       par2 = 1
      elif par == "2" or par == "TO":
       par2 = 2
      setswitchstate(sn,par2,dashtask)
     resp = getstatusjson("StatusSTS",dashtask)
     webserver.TXBuffer = resp[12:].strip()
    elif cmdline[0].lower()[:9] == "pulsetime":
     try:
      snstr = cmdline[0].strip()
      sn = int(snstr[9])
      if sn < 1 or sn > 8:
       sn = 1
     except:
      sn = 0
     if sn == 0: #all
      webserver.TXBuffer = '{'
      for p in range(8):
       webserver.TXBuffer += '"PulseTime' + str(p+1) + '": {"Set":0, "Remaining":0}'
       if p<7:
        webserver.TXBuffer += ","
      webserver.TXBuffer += '}'
     else:
      webserver.TXBuffer = '{"PulseTime' + str(sn) + '": {"Set":0, "Remaining":0}}'
    else: #unknown
      print("Unknown command: ",cmnd)
      webserver.TXBuffer = '{"Command":"Error"}'
   else:
      print("Uninitialized")
      webserver.TXBuffer = '{"Command":"Internal error"}'
  except Exception as e:
   print("/cm",e)#debug

  return webserver.TXBuffer
