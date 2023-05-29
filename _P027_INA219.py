#!/usr/bin/env python3
#############################################################################
##################### INA219 plugin for RPIEasy #############################
#############################################################################
#
# Plugin based on library:
#  https://github.com/chrisb2/pi_ina219/
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
from ina219 import INA219

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 27
 PLUGIN_NAME = "Energy (DC) - INA219"
 PLUGIN_VALUENAME1 = "Voltage"
 PLUGIN_VALUENAME2 = "Current"
 PLUGIN_VALUENAME3 = "Power"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  self.readinprogress = 0
  self.valuecount = 3
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.ina = None
  self.decimals = [3,3,3,0]
  self.shuntohms = 0.1

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
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
    if self.interval>2:
      nextr = self.interval-2
    else:
      nextr = self.interval
    self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    self.lastread = 0
    try:
     shunt = self.shuntohms
    except:
     shunt = 0.1
     self.shuntohms = shunt

    try:
     pgain = int(self.taskdevicepluginconfig[6])
    except:
     pgain = -1
    try:
     padc = int(self.taskdevicepluginconfig[7])
    except:
     padc = 3
    try:
     amps = int(self.taskdevicepluginconfig[1])
     if amps<1:
      amps = None
     else:
      try:
       amps = float(amps) / 1000
      except:
       amps = None
     vrange = int(self.taskdevicepluginconfig[2])
     if vrange not in [0,1]:
      vrange = 1
     if int(self.taskdevicepluginconfig[0])>0x39:
      self.ina = INA219(shunt,busnum=i2cl, address=int(self.taskdevicepluginconfig[0]), max_expected_amps=amps)
      self.ina.configure(voltage_range=vrange, gain=pgain, bus_adc=padc, shunt_adc=padc)
      self.initialized = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"INA219 can not be initialized: "+str(e))
     self.ina = None
     self.initialized = False

 def webform_load(self): # create html page for settings
  try:
     shunt = self.shuntohms
  except:
     shunt = 0.1
     self.shuntohms = shunt
  choice1 = self.taskdevicepluginconfig[0]
  optionvalues = [0x40,0x41,0x44,0x45,0x42,0x43,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F]
  options = []
  for o in range(len(optionvalues)):
   options.append( hex(optionvalues[o]) )
  webserver.addFormSelector("I2C address","plugin_027_addr",len(options),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")

  choice2 = self.taskdevicepluginconfig[1]
  options = ["AUTO","200","400","800","1000","1600","2000","3200"]
  optionvalues = [0,200,400,800,1000,1600,2000,3200]
  webserver.addFormSelector("Maximum current","plugin_027_amp",len(options),options,optionvalues,None,int(choice2))
  webserver.addUnit("mA")

  choice3 = self.taskdevicepluginconfig[2]
  options = ["32","16"]
  optionvalues = [1,0]
  webserver.addFormSelector("Max voltage","plugin_027_volt",len(options),options,optionvalues,None,int(choice3))
  webserver.addUnit("V")

  webserver.addFormTextBox("Shunt resistor","plugin_027_shuntohm",self.shuntohms,12)
  webserver.addUnit("Ohm")
  if self.ina is not None:
   choice7 = self.taskdevicepluginconfig[6]
   options = ["AUTO","40mV","80mV","160mV","320mV"]
   optionvalues = [ self.ina.GAIN_AUTO, self.ina.GAIN_1_40MV, self.ina.GAIN_2_80MV, self.ina.GAIN_4_160MV, self.ina.GAIN_8_320MV]
   webserver.addFormSelector("Gain","plugin_027_gain",len(options),options,optionvalues,None,int(choice7))
   choice8 = self.taskdevicepluginconfig[7]
   options = ["9bit","10bit","11bit","12bit","2SAMP","4SAMP","8SAMP","16SAMP","32SAMP","64SAMP","128SAMP"]
   optionvalues = [self.ina.ADC_9BIT,self.ina.ADC_10BIT,self.ina.ADC_11BIT,self.ina.ADC_12BIT,self.ina.ADC_2SAMP,self.ina.ADC_4SAMP,self.ina.ADC_8SAMP,self.ina.ADC_16SAMP,self.ina.ADC_32SAMP,self.ina.ADC_64SAMP,self.ina.ADC_128SAMP]
   webserver.addFormSelector("ADC resolution","plugin_027_adc",len(options),options,optionvalues,None,int(choice8))

  choice4 = self.taskdevicepluginconfig[3]
  options = ["None","Voltage","Current","Power"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Param1","plugin_027_p1",len(options),options,optionvalues,None,int(choice4))
  choice5 = self.taskdevicepluginconfig[4]
  webserver.addFormSelector("Param2","plugin_027_p2",len(options),options,optionvalues,None,int(choice5))
  choice6 = self.taskdevicepluginconfig[5]
  webserver.addFormSelector("Param3","plugin_027_p3",len(options),options,optionvalues,None,int(choice6))
  return True

 def webform_save(self,params): # process settings post reply
  try:
   shunt = float(webserver.arg("plugin_027_shuntohm",params))
   if shunt <= 0:
    shunt = 0.1
  except:
   shunt = 0.1
  self.shuntohms = shunt

  try:
   par = int(webserver.arg("plugin_027_gain",params))
   self.taskdevicepluginconfig[6] = par
  except:
   pass
  try:
   par = int(webserver.arg("plugin_027_adc",params))
   self.taskdevicepluginconfig[7] = par
  except:
   pass

  par = webserver.arg("plugin_027_addr",params)
  if par == "":
    par = 0x40
  self.taskdevicepluginconfig[0] = int(par)

  par = webserver.arg("plugin_027_amp",params)
  if par == "":
    par = 0
  self.taskdevicepluginconfig[1] = int(par)

  par = webserver.arg("plugin_027_volt",params)
  if par == "":
    par = 1
  self.taskdevicepluginconfig[2] = int(par)

  par = webserver.arg("plugin_027_p1",params)
  if par == "":
    par = 1
  self.taskdevicepluginconfig[3] = int(par)
  par = webserver.arg("plugin_027_p2",params)
  if par == "":
    par = 0
  self.taskdevicepluginconfig[4] = int(par)
  par = webserver.arg("plugin_027_p3",params)
  if par == "":
    par = 0
  self.taskdevicepluginconfig[5] = int(par)

  self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  if self.taskdevicepluginconfig[5]==0:
   self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  if self.taskdevicepluginconfig[4]==0:
   self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE

  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    v1 = None
    if self.ina is not None:
     for i in range(0,3):
      vtype = self.taskdevicepluginconfig[3+i]
      if vtype==1:
       self.set_value(i+1,self.ina.supply_voltage(),False)
      elif vtype==2:
       self.set_value(i+1,float(self.ina.current()/1000),False)
       v1 = 1
      elif vtype==3:
       self.set_value(i+1,float(self.ina.power()/1000),False)
       v1 = 1
   except Exception as e:
    v1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"INA219: "+str(e))
   if v1 is not None:
    self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

