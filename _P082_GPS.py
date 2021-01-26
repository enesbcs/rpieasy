#!/usr/bin/env python3
#############################################################################
###################### Serial GPS plugin for RPIEasy ########################
#############################################################################
#
# Serial plugin based on PySerial
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import threading
import serial
import time
import lib.lib_serial as rpiSerial
import json
import commands
import re

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 82
 PLUGIN_NAME = "Position - GPS (TESTING)"
 PLUGIN_VALUENAME1 = "Longitude"
 PLUGIN_VALUENAME2 = "Latitude"
 PLUGIN_VALUENAME3 = "Altitude"
 PLUGIN_VALUENAME4 = "Speed"

 GPSDAT = {
    'strType': None,
    'fixTime': "000000",
    'lat': None,
    'latDir': None,
    'lon': None,
    'lonDir': None,
    'fixQual': None,
    'numSat': "0",
    'horDil': "0",
    'alt': None,
    'altUnit': None,
    'galt': None,
    'galtUnit': None,
    'DPGS_updt': None,
    'DPGS_ID': None
 }
 GPSTRACK = {
    'strType': None,
    'trueTrack': None,
    'trueTrackRel': None,
    'magnetTrack': None,
    'magnetTrackRel': None,
    'speedKnot':None,
    'speedKnotUnit':None,
    'speedKm':None,
    'speedKmUnit':None,
 }
 GPSDATE = {
    'strType': None,
    'fixTime': "000000",
    'day':"0",
    'mon':"0",
    'year':"0",
    'lzoneh':None,
    'lzonem':None
 }

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_SER
   self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
   self.readinprogress = 0
   self.valuecount = 4
   self.senddataoption = True
   self.timeroption = True
   self.timeroptional = False
   self.formulaoption = True
   self.initialized = False
   self.validloc = -1
   self.bgproc = None
   self.serdev = None
   self.baud = 9600
   self.decimals = [6,6,1,1]
   self.lat = 0
   self.lon = 0
   self.devfound = False

 def plugin_exit(self):
   self.initialized = False
   self.validloc = -1
   try:
     self.serdev.close()
     self.serdev = None
   except:
     pass
   try:
    self.bgproc.join()
    self.bgproc = None
   except:
    pass

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.readinprogress = 0
#  self.validloc = False
  self.initialized = False
  self.devfound = False
#  try:
#   self.bgproc.join()
#   time.sleep(1)
#   self.bgproc = None
#  except:
#   pass
  try:
   if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="" and self.baud != 0 and self.enabled:
#    self.serdev = None
    if self.enabled:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Try to init serial "+str(self.taskdevicepluginconfig[0])+" speed "+str(self.baud))
     self.connect()
     if self.initialized:
      pn = self.taskdevicepluginconfig[0].split("/")
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Search for GPS...")
      self.ports = str(pn[-1])
      self.bgproc = threading.Thread(target=self.bgreceiver)
      self.bgproc.daemon = True
      self.bgproc.start()
    else:
     self.ports = 0
     try:
      self.serdev.close() # close in case if already opened by ourself
     except:
      pass
  except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"GPS init error "+str(e))

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = rpiSerial.serial_portlist()
  if len(options)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p082_addr",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
   webserver.addFormNote("For RPI use 'raspi-config' tool: 5- Interfacing Options-P6 Serial- (Kernel logging disabled + serial port hardware enabled) before enable this plugin")
  else:
   webserver.addFormNote("No serial ports found")
  webserver.addHtml("<tr><td>Fix:<td>")
  time.sleep(2) #wait to get reply
  webserver.addHtml(str(self.validloc))
  if self.initialized and self.validloc!=0:
   try:
    webserver.addHtml("<tr><td>Satellites in use:<td>")
    webserver.addHtml(self.GPSDAT["numSat"])
    webserver.addHtml("<tr><td>HDOP:<td>")
    webserver.addHtml(self.GPSDAT["horDil"])
    webserver.addHtml("<tr><td>UTC Time:<td>")
    gpstime = self.GPSDAT["fixTime"][0:2]+":"+ self.GPSDAT["fixTime"][2:4]+":"+self.GPSDAT["fixTime"][4:6]
    webserver.addHtml(self.GPSDATE["year"]+"-"+self.GPSDATE["mon"]+"-"+self.GPSDATE["day"]+" "+gpstime)
   except:
    pass
  return True

 def webform_save(self,params):
  par = webserver.arg("p082_addr",params)
  self.taskdevicepluginconfig[0] = str(par)
#  self.plugin_init()
  return True

 def plugin_read(self):
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   if self.validloc==1:
    self.set_value(1,self.lon,False)
    self.set_value(2,self.lat,False)
    self.set_value(3,self.GPSDAT['alt'],False)
    self.set_value(4,self.GPSTRACK['speedKm'],False)
    self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def connect(self):
    try:
     if self.serdev.isopened():
      self.initialized = True
      return True
    except:
     pass
    try:
     self.serdev.close() # close in case if already opened by ourself
     self.serdev = None
    except:
     pass
    try:
     self.serdev = rpiSerial.SerialPort(self.taskdevicepluginconfig[0],self.baud,ptimeout=1,pbytesize=rpiSerial.EIGHTBITS,pstopbits=rpiSerial.STOPBITS_ONE)
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Serial connected "+str(self.taskdevicepluginconfig[0]))
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Serial failed "+str(e))
    try:
     self.initialized = self.serdev.isopened()
    except Exception as e:
     self.initialized = False
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Open failed "+str(e))

 def bgreceiver(self):
  if self.initialized:
   self.validloc = -1
   while self.enabled and self.initialized:
    if self.serdev is not None:
     try:
      reading = self.serdev.readline()
      if reading:
       recdata = reading.decode("utf-8")
       self.parseResponse(recdata)
      else:
       time.sleep(0.001)
     except:
      time.sleep(0.5)

   try:
     self.serdev.close()
   except:
     pass

 def parseResponse(self,gpsLine):
 #    global lastLocation
 #    gpsChars = ''.join(chr(c) for c in gpsLine)
 #    if "*" not in gpsChars:
 #        return False
    gpsChars = str(gpsLine)
    try:
     if '*' in gpsChars:
      gpsStr, chkSum = gpsChars.split('*')
     elif '_' in gpsChars:
      gpsStr, chkSum = gpsChars.split('_')
     else:
      chkSum = gpsChars[-2:]
      gpsStr = gpsChars[:-2]
    except:
      chkSum = gpsChars[-2:]
      gpsStr = gpsChars[:-2]
    gpsComponents = gpsStr.split(',')
    gpsStart = gpsComponents[0]
#    print(gpsLine)#debug
    if ("GGA" in gpsStart):
#        print("Valid GGA from GPS") # DEBUG
        if self.devfound==False:
         misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"GPS found")
         self.devfound=True
        prevval = self.validloc
        self.validloc = 0
        chkVal = 0
        for ch in gpsStr[1:]: # Remove the $
            chkVal ^= ord(ch)
        if (chkVal == int(chkSum, 16)):
            for i, k in enumerate(
                ['strType', 'fixTime', 
                'lat', 'latDir', 'lon', 'lonDir',
                'fixQual', 'numSat', 'horDil', 
                'alt', 'altUnit', 'galt', 'galtUnit',
                'DPGS_updt', 'DPGS_ID']):
                self.GPSDAT[k] = gpsComponents[i]
            try:
             if int(self.GPSDAT['fixQual'])>0:
              self.validloc = 1
            except:
             self.validloc = 0
            if self.validloc==1: # refresh values
#             print("GPS fix OK") # debug
             lon = float(self.GPSDAT['lon'])
             self.lon = dm_to_sd(str(lon))
             if str(self.GPSDAT['lonDir']) == 'W':
              self.lon = self.lon * -1
             lat = float(self.GPSDAT['lat'])
             self.lat = dm_to_sd(str(lat))
             if self.GPSDAT['latDir'] == 'S':
              self.lat = self.lat * -1
        if self.validloc != prevval: # status changed
             if self.validloc==1:
              commands.rulesProcessing("GPS#GotFix",rpieGlobals.RULE_SYSTEM)
             else:
              commands.rulesProcessing("GPS#LostFix",rpieGlobals.RULE_SYSTEM)
            #print(gpsChars)
            #print(json.dumps(self.GPSDAT, indent=2))
    elif ("ZDA" in gpsStart):
#        print("ZDA")#debug
        chkVal = 0
        for ch in gpsStr[1:]: # Remove the $
            chkVal ^= ord(ch)
        if (chkVal == int(chkSum, 16)):
            for i, k in enumerate(
                ['strType', 'fixTime', 
                'day', 'mon', 'year', 'lzoneh',
                'lzonem']):
                self.GPSDATE[k] = gpsComponents[i]
            #print(gpsChars)
            #print(json.dumps(self.GPSDATE, indent=2))
    elif ("VTG" in gpsStart):
#        print("VTG")#debug
        chkVal = 0
        for ch in gpsStr[1:]: # Remove the $
            chkVal ^= ord(ch)
        if (chkVal == int(chkSum, 16)):
            for i, k in enumerate(
                ['strType','trueTrack', 'trueTrackRel',
                'magnetTrack','magnetTrackRel','speedKnot',
                'speedKnotUnit','speedKm','speedKmUnit']):
                self.GPSTRACK[k] = gpsComponents[i]
            #print(gpsChars)
            #print(json.dumps(self.GPSTRACK, indent=2))

def dm_to_sd(dm):
    '''
    Converts a geographic co-ordinate given in "degrees/minutes" dddmm.mmmm
    format (eg, "12319.943281" = 123 degrees, 19.943281 minutes) to a signed
    decimal (python float) format
    '''
    # '12319.943281'
    if not dm or dm == '0':
        return 0
    try:
     d, m = re.match(r'^(\d+)(\d\d\.\d+)$', dm).groups()
     return float(d) + float(m) / 60
    except:
     return 0
