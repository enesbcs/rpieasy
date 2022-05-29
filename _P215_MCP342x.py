#!/usr/bin/env python3
#############################################################################
######################## MCP342x plugin for RPIEasy #########################
#############################################################################
#
# Copyright (C) 2022 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import lib.lib_mcp342xrouter as mcp342x
import gpios

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 215
 PLUGIN_NAME = "Analog input - MCP342x"
 PLUGIN_VALUENAME1 = "Analog"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.ports = 0
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self.adc = None
  self._nextdataservetime = 0
  self.lastread = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.enabled:
   try:
     i2cl = self.i2c
   except:
     i2cl = -1
   self.i2cbus = gpios.HWPorts.i2c_init(i2cl)
   if i2cl==-1:
     self.i2cbus = gpios.HWPorts.i2cbus
   if self.i2cbus is not None:
    if self.interval>2:
      nextr = self.interval-2
    else:
      nextr = self.interval
    self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    self.ports = str(self.taskdevicepluginconfig[3])
    try:
      self.adc = mcp342x.request_mcpad_device_byaddr(bus=self.i2cbus,i2caddress=int(self.taskdevicepluginconfig[1]),device=str(self.taskdevicepluginconfig[0]),gain=int(self.taskdevicepluginconfig[2]))
      self.initialized = True
    except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MCP can not be initialized! "+str(e))
      self.initialized = False

 def webform_load(self): # create html page for settings
  options = ['MCP3422', 'MCP3423', 'MCP3424','MCP3426', 'MCP3427', 'MCP3428']
  webserver.addHtml("<tr><td>Type:<td>")
  webserver.addSelector_Head("plugin_215_type",False)
  for o in range(len(options)):
    webserver.addSelector_Item(str(options[o]),str(options[o]),(str(options[o])==str(self.taskdevicepluginconfig[0])),False)
  webserver.addSelector_Foot()
  choice2 = self.taskdevicepluginconfig[1]
  options = ["0x68","0x69","0x6A","0x6B","0x6C","0x6D","0x6E","0x6F"]
  optionvalues = [0x68,0x69,0x6A,0x6B,0x6C,0x6D,0x6E,0x6F]
  webserver.addFormSelector("Address","plugin_215_addr",len(optionvalues),options,optionvalues,None,int(choice2))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  choice3 = self.taskdevicepluginconfig[2]
  options =      ["2/3","1","2","4","8","16"]
  optionvalues = [(2/3),1,2,4,8,16]
  webserver.addFormSelector("Gain","plugin_215_gain",len(optionvalues),options,optionvalues,None,float(choice3))
  choice4 = self.taskdevicepluginconfig[3]
  options = ["CH1","CH2","CH3","CH4"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Channel","plugin_215_apin",4,options,optionvalues,None,int(choice4))
  return True

 def webform_save(self,params): # process settings post reply
   par = str(webserver.arg("plugin_215_type",params))
   if par == "" or par== "0":
    par = "MCP3424"
   self.taskdevicepluginconfig[0] = par

   par = webserver.arg("plugin_215_addr",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[1] = int(par)

   par = webserver.arg("plugin_215_gain",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[2] = float(par)

   par = webserver.arg("plugin_215_apin",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[3] = int(par)
   self.plugin_init()
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.enabled:
   val = self.mcp_get_value()
   if val != -1:
    self.set_value(1,val,False)
    self.plugin_senddata()
    result = True
    self._lastdataservetime = rpieTime.millis()
    self._nextdataservetime = self._lastdataservetime + (self.interval*1000)
  return result

 def mcp_get_value(self):
  val = -1
  try:
   val = self.adc.convert_and_read(int(self.taskdevicepluginconfig[3]),samples=3)
#   print("mcp val",val)#debug
  except Exception as e:
#   print(e)
   val = -1
  return val
