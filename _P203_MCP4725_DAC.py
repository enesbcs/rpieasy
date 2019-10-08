#!/usr/bin/env python3
#############################################################################
##################### MCP4725 DAC plugin for RPIEasy ########################
#############################################################################
#
# Analog output device (0..Vdd V) 0=0V, 4095=Vdd V
#
# Available commands: (for example http or rules based controlling)
#  dac,<number>,<value>                    - Number of the DAC can be 0 or 1 (0= address 0x60, 1= address 0x61),
#                                          value can be 0-4095
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
#import fcntl

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 203
 PLUGIN_NAME = "Output - MCP4725 DAC (TESTING)"
 PLUGIN_VALUENAME1 = "Analog"
 WRITEDAC         = 0x40
 WRITEDACEEPROM   = 0x60

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_DIMMER
  self.valuecount = 0
  self.senddataoption = False
  self.recdataoption = False
  self.timeroption = False
  self.formulaoption = False
  self.bus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.enabled:
   try:
    i2cok = gpios.HWPorts.i2c_init()
    if i2cok:
     self.bus = gpios.HWPorts.i2cbus
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C can not be initialized!")
     self.enabled = False
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
     self.enabled = False

 def webform_load(self):
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!<br>0x60 is number 0 DAC, 0x61 is number 1.")
  return True

 def set_dac(self, address, value, persist=False):
     value = value & 0xFFF
     reg_data = [(value >> 4) & 0xFF, (value << 4) & 0xFF]
     try:
      if persist:
         self.bus.write_i2c_block_data(0x60+address, self.WRITEDACEEPROM, reg_data)
      else:
         self.bus.write_i2c_block_data(0x60+address, self.WRITEDAC, reg_data)
     except Exception as e:
      print(e)

 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "dac":
   try:
    rnum  = int(cmdarr[1].strip())
    val   = int(cmdarr[2].strip())
   except:
    rnum = -1
   if val<0:
    val = 0
   elif val>4095:
    val=4095
   if rnum in [0,1,2,3]:  # 0 and 1 is valid, but
    self.set_dac(rnum,val,True)
    res = True
  return res

