#!/usr/bin/env python3
#############################################################################
##################### MLX90614 plugin for RPIEasy ###########################
#############################################################################
#
# Plugin based on code from:
#  https://github.com/CRImier/python-MLX90614
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import lib.lib_mlxrouter as mlxrouter

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 24
 PLUGIN_NAME = "Environment - MLX90614 sensor"
 PLUGIN_VALUENAME1 = "Temperature"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.mlx = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.initialized = False
  if self.enabled:
   try:
     i2cl = self.i2c
   except:
     i2cl = -1
   try:
    i2cport = gpios.HWPorts.geti2clist()
    if i2cl==-1:
      i2cl = int(i2cport[0])
   except:
    i2cport = []
   if len(i2cport)>0 and i2cl>-1:
     try:
      dport = int(self.taskdevicepluginconfig[0])
     except:
      dport = 0
     if dport == 0:
      dport = 0x5a
      self.mlx = None
     try:
      self.mlx = mlxrouter.request_mlx_device(busnum=int(i2cl),i2caddress=dport)
      self.initialized = True
     except Exception as e:
      self.mlx = None
   if self.mlx is None:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MLX90614 can not be initialized! ")
    return False

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x5a"]
  optionvalues = [0x5a]
  webserver.addFormSelector("I2C address","plugin_024_addr",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  choice2 = self.taskdevicepluginconfig[1]
  options = ["IR object temperature","Ambient temperature"]
  optionvalues = [7,6]
  webserver.addFormSelector("Type","plugin_024_type",2,options,optionvalues,None,int(choice2))
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("plugin_024_addr",params)
   if par == "":
    par = 0x5A
   self.taskdevicepluginconfig[0] = int(par)
   par = webserver.arg("plugin_024_type",params)
   try:
    self.taskdevicepluginconfig[1] = int(par)
   except:
    self.taskdevicepluginconfig[1] = 7
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    if str(self.taskdevicepluginconfig[1]) == "6":
     val1 = self.mlx.get_amb_temp()
    else:
     val1 = self.mlx.get_obj_temp()
   except Exception as e:
    val1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MLX90614: "+str(e))
   if val1 is not None:
    self.set_value(1,val1,True)
    self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result
