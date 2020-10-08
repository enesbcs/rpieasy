#!/usr/bin/env python3
#############################################################################
##################### BLE Sniffer plugin for RPIEasy ########################
#############################################################################
#
# Can be used when BLE compatible Bluetooth dongle, and BluePy is installed.
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import Settings
import lib.lib_blescan as BLEScanner
import lib.lib_blehelper as BLEHelper
import struct
import threading

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 527
 PLUGIN_NAME = "Environment - BLE Xiaomi sniffer (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "Value1"
 PLUGIN_VALUENAME2 = "Value2"
 PLUGIN_VALUENAME3 = "Value3"
 PLUGIN_VALUENAME4 = "Value4"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_BLE
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self.readinprogress = 0
  self._lastdataservetime = 0
  self._nextdataservetime = 0
  self._attribs = {}
  self.blescanner = None
  self.blestatus = None
  self.address = ""
  self.rssi = -1
  self.battery = 255
  self._bgproc = None
  self.startup = 0

 def webform_load(self): # create html page for settings
  bledevs = BLEHelper.find_hci_devices()
  options = []
  optionvalues = []
  if bledevs:
   for bd in bledevs:
    options.append(bd)
    try:
     optionvalues.append(int(bd[3:]))
    except:
     optionvalues.append(bd[3:])
  webserver.addFormSelector("Local Device","plugin_527_dev",len(options),options,optionvalues,None,int(self.taskdevicepluginconfig[4]))
  webserver.addFormTextBox("Remote Device Address","plugin_527_addr",str(self.address),20)
  webserver.addFormNote("Supported device types: LYWSD02, CGQ, CGG1, MiFlora")
  webserver.addFormNote("If you are using Sniffer, its not the best idea to use another BLE plugin at the same time. Although multiple sniffer tasks can be used.")
  choice1 = self.taskdevicepluginconfig[0]
  choice2 = self.taskdevicepluginconfig[1]
  choice3 = self.taskdevicepluginconfig[2]
  choice4 = self.taskdevicepluginconfig[3]
  options = ["None","Temperature","Humidity","Light","Moisture","Fertility","Battery","RSSI"]
  optionvalues = [-1,4,6,7,8,9,10,200]
  webserver.addFormSelector("Indicator1","plugin_527_ind0",len(optionvalues),options,optionvalues,None,choice1)
  webserver.addFormSelector("Indicator2","plugin_527_ind1",len(optionvalues),options,optionvalues,None,choice2)
  webserver.addFormSelector("Indicator3","plugin_527_ind2",len(optionvalues),options,optionvalues,None,choice3)
  webserver.addFormSelector("Indicator4","plugin_527_ind3",len(optionvalues),options,optionvalues,None,choice4)
  try:
   if self.taskdevicepluginconfig[5]<1:
     self.taskdevicepluginconfig[5] = self.blescanner.scantime
  except:
   pass
  try:
   if self.taskdevicepluginconfig[6]<1:
     self.taskdevicepluginconfig[6] = self.blescanner.minsleep
  except:
   pass
  try:
   if self.taskdevicepluginconfig[7]<1:
     self.taskdevicepluginconfig[7] = self.blescanner.maxsleep
  except:
   pass
  if self.taskdevicepluginconfig[5]<1:
   self.taskdevicepluginconfig[5]=5
  if self.taskdevicepluginconfig[6]<1:
   self.taskdevicepluginconfig[6]=10
  if self.taskdevicepluginconfig[7]<1:
   self.taskdevicepluginconfig[7]=30
  webserver.addFormNumericBox("Scan time","plugin_527_scantime",self.taskdevicepluginconfig[5],5,60)
  webserver.addUnit('s')
  webserver.addFormNumericBox("Minimal pause after scan","plugin_527_minsleep",self.taskdevicepluginconfig[6],5,60)
  webserver.addUnit('s')
  webserver.addFormNumericBox("Maximal pause after scan","plugin_527_maxsleep",self.taskdevicepluginconfig[7],10,120)
  webserver.addUnit('s')
  return True

 def webform_save(self,params): # process settings post reply
  self.address = str(webserver.arg("plugin_527_addr",params)).strip()
  try:
   self.taskdevicepluginconfig[4] = int(webserver.arg("plugin_527_dev",params))
  except:
   self.taskdevicepluginconfig[4] = 0
  try:
   self.taskdevicepluginconfig[5] = int(webserver.arg("plugin_527_scantime",params))
  except:
   self.taskdevicepluginconfig[5] = 5
  try:
   self.taskdevicepluginconfig[6] = int(webserver.arg("plugin_527_minsleep",params))
  except:
   self.taskdevicepluginconfig[6] = 10
  try:
   self.taskdevicepluginconfig[7] = int(webserver.arg("plugin_527_maxsleep",params))
  except:
   self.taskdevicepluginconfig[7] = 30
  for v in range(0,4):
   par = webserver.arg("plugin_527_ind"+str(v),params)
   if par == "":
    par = 0
   if str(self.taskdevicepluginconfig[v])!=str(par):
    self.uservar[v] = 0
   self.taskdevicepluginconfig[v] = int(par)
   if int(par)>0:
    self.valuecount = (v+1)
  if self.valuecount == 1:
   self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  elif self.valuecount == 2:
   if int(self.taskdevicepluginconfig[0])==4 and int(self.taskdevicepluginconfig[1])==6:
    self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM
   else:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  elif self.valuecount == 3:
   self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  elif self.valuecount == 4:
   self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.readinprogress = 0
  try:
     devnum = int(self.taskdevicepluginconfig[4])
     self.blestatus  = BLEHelper.BLEStatus[devnum]
  except:
     pass
  c = 0
  if self.enabled:
    self._attribs = {}
    try:
     self.blescanner = BLEScanner.request_blescan_device(devnum,0) #params
     self.blestatus.requestimmediatestopscan = self.blescanner.stop
     self.startsniff(30)
     self.initialized = True
     self.startup = time.time()
     if self.battery<1:
      self.battery=255
     self.ports = str(self.address)
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"BLE sniffer init ok")
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BLE sniffer init error: "+str(e))
     self.initialized = False
  else:
    self.initialized = False
    self.ports = ""

 def AdvDecoder(self,dev,advdat):
     if dev=="":
      return False
     ddat = {}
     for i in range(len(advdat)): #process incoming BLE advertisement packets
       try:
        if advdat[i][0]==22:
         ddat = self.decode_xiaomi(bytes.fromhex(advdat[i][2])) # forward to xiaomi decoder
         break
       except Exception as e:
        print(e)
     if len(ddat)>0:
      try:
       self.dosync(dev.addr,dev.rssi,ddat) # if supported device, sync with all Tasks
      except:
       pass

 def startsniff(self,startwait=0):
    try:
     if self.blescanner._scanning==False:
      self._bgproc = threading.Thread(target=self.blescanner.sniff, args=(self.AdvDecoder,startwait,self.taskdevicepluginconfig[5],self.taskdevicepluginconfig[6],self.taskdevicepluginconfig[7]))
      self._bgproc.daemon = True
      self._bgproc.start()
    except Exception as e:
     print("SniffStart",e)

 def stopsniff(self):
     try:
      if self.blescanner._scanning:
       self.blescanner._scanning = False
       self._bgproc.join()
      self.blescanner.stop()
      self.blestatus.reportscan(0)
     except:
      pass

 def plugin_exit(self):
     self.stopsniff()

 def plugin_read(self):
  result = False
  if self.initialized and self.readinprogress==0:
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(self.address)+" "+str(self._attribs))
   self.startsniff(0)
   self.readinprogress = 1
   lastupdate = 0
   for key in self._attribs.keys():
    if "-t" in key:
     if self._attribs[key]>lastupdate:
      lastupdate = self._attribs[key]
   otime = (3*self.interval)
   if otime<1800:
    otime = 1800
   orssi = self.rssi
   report = True
   if ((time.time()-lastupdate) > otime) and ((time.time()-self.startup) > otime):
    self.rssi= -100
    self.battery = 0
    if self.rssi==orssi:
     report = False
   if report and len(self._attribs)<2:
    report = False
   for v in range(0,4):
    vtype = int(self.taskdevicepluginconfig[v])
    if vtype != 0:
     self.set_value(v+1,self.p527_get_value(vtype),False,susebattery=self.battery,suserssi=self.rssi)
   if report:
    self.plugin_senddata(pusebattery=self.battery,puserssi=self.rssi)
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def p527_get_value(self,ptype):
   value = 0
   if ptype == 4:
    if "temp" in self._attribs:
     value = self._attribs['temp']
    else:
     value = 0
   elif ptype == 6:
    if "hum" in self._attribs:
     value = self._attribs['hum']
    else:
     value = 0
   elif ptype == 7:
    if "light" in self._attribs:
     value = self._attribs['light']
    else:
     value = 0
   elif ptype == 8:
    if "moist" in self._attribs:
     value = self._attribs['moist']
    else:
     value = 0
   elif ptype == 9:
    if "fertil" in self._attribs:
     value = self._attribs['fertil']
    else:
     value = 0
   elif ptype == 10:
    value = self.battery #self._attribs['batt']
   elif ptype == 200:
    value = self.rssi
   return value

 def _updatedevice(self,newvals):
    res = False
    for key in newvals.keys():
     if key=="batt":
      self.battery = newvals[key]
     try:
      if key in self._attribs:
       if time.time()-self._attribs[key+"-t"]>1.5:
        self._attribs[key+"-t"] = time.time()
        self._attribs[key] = newvals[key]
        res = True
      else:
       self._attribs.update({key:newvals[key]})
       key = key + "-t"
       self._attribs.update({key:time.time()})
       res = True
     except Exception as e:
      pass
    return res

 def decode_xiaomi(self,buf):
  res = {}
  ofs = 0
  try:
   if len(buf)>16:
    cdata = struct.unpack_from('<H H H B 6B B B B B',buf)
   elif len(buf)>15:
    cdata = struct.unpack_from('<H H H B 6B B B B ',buf)
   else:
    cdata = [0]
  except:
    cdata = [0]
  if cdata[0] == 0xFE95:
    if cdata[11] != 0x10 and cdata[12] == 0x10:
     ofs = 1
    try:
     if cdata[2] == 0x0576:
      cdata2 = struct.unpack_from('<h H',buf[15:])
      res = {"temp":cdata2[0]/10.0,"hum":cdata2[1]/10.0}
     elif cdata[10+ofs]==0xD and cdata[12+ofs]>3:
      cdata2 = struct.unpack_from('<H H',buf[16+ofs:])
      res = {"temp":cdata2[0]/10.0,"hum":cdata2[1]/10.0}
     elif cdata[10+ofs]==0xA and cdata[12+ofs]>0:
      res = {"batt": buf[16+ofs]}
#      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(res)+" "+str(cdata))
     elif cdata[10+ofs]==6 and cdata[12+ofs]>0:
      cdata2 = struct.unpack_from('<H',buf[16+ofs:])
      res = {"hum":cdata2[0]/10.0}
     elif cdata[10+ofs]==4 and cdata[12+ofs]>0:
      cdata2 = struct.unpack_from('<H',buf[16+ofs:])
      res = {"temp":cdata2[0]/10.0}
     elif cdata[10+ofs]==7 and cdata[12+ofs]>0:
      try:
       cdata2 = struct.unpack_from('<3B',buf[16+ofs:])
       res = cdata2[0]+cdata2[1]*256+cdata2[2]*65535
      except:
       res = buf[16+ofs]
      res = {"light":res} # 3byte
     elif cdata[10+ofs]==8 and cdata[12+ofs]>0:
      res = {"moist":buf[16+ofs]} #1byte
     elif cdata[10+ofs]==9 and cdata[12+ofs]>0:
      try:
       cdata2 = struct.unpack_from('<H',buf[16+ofs:])
       res = cdata2[0]
      except:
       res = buf[16+ofs]
      res = {"fertil":res} #2byte
     elif cdata[10+ofs]==5 and cdata[12+ofs]>0:
      res = {"stat":buf[16+ofs],"temp":buf[17+ofs]}
    except:
     res = {}
  else:
    if buf[0]==0x1A and buf[1]==0x18: # ATC
     try:
      cdata = struct.unpack_from('>H 6B h B B H B',buf)
     except:
      cdata = [0]
     res = {"temp":cdata[7]/10.0,"hum":cdata[8],"batt":cdata[9]}
  return res

 def dosync(self,addr,rssi,values):
  for x in range(0,len(Settings.Tasks)):
   if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
    if (Settings.Tasks[x].enabled):
      if (Settings.Tasks[x].pluginid==self.pluginid):
       if str(Settings.Tasks[x].address) == str(addr):
        try:
         if Settings.Tasks[x]._updatedevice(values):
          Settings.Tasks[x].rssi = rssi
         else:
          break
        except:
         pass
