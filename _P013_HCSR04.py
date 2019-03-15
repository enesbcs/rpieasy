#!/usr/bin/env python3
#############################################################################
##################### HC-SR04 plugin for RPIEasy ############################
#############################################################################
#
# Plugin for using SR04 ultrasonic ranging sensor
#
# Based on Al Audet's code:
#  https://github.com/alaudet/hcsr04sensor/blob/master/hcsr04sensor/sensor.py
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time
import math

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 13
 PLUGIN_NAME = "Distance - HC-SR04 sensor (TESTING)"
 PLUGIN_VALUENAME1 = "mm"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUAL
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.sr = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.initialized = False
  if self.taskdevicepin[0]<0 or self.taskdevicepin[1]<0:
   self.enabled=False
   self.initialized=False
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SR04: No pin selected, aborting!")
  else:
   if self.enabled and gpios.HWPorts.gpioinit:
    pinfunc = gpios.HWPorts.gpio_function(int(self.taskdevicepin[0]))
    astate1 = str(gpios.HWPorts.gpio_function_name(pinfunc))
    pinfunc = gpios.HWPorts.gpio_function(int(self.taskdevicepin[1]))
    astate2 = str(gpios.HWPorts.gpio_function_name(pinfunc))
    if astate1!='Output' or astate2!="Input":
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SR04: PIN mode error, aborting!")
     self.enabled=False
     self.initialized=False
   if self.enabled and gpios.HWPorts.gpioinit:
    if self.interval>2:
     nextr = self.interval-2
    else:
     nextr = 0
    self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    try:
     samples = int(self.taskdevicepluginconfig[0])
     samplewait = float(self.taskdevicepluginconfig[1])/1000
    except:
     samples = 5
     samplewait = 0.1
    self.sr = SR04(self.taskdevicepin[0],self.taskdevicepin[1],samples,samplewait)
    self.initialized = True
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"SR04: Initialized")

 def webform_load(self): # create html page for settings
  webserver.addFormNote("1st GPIO is <b>Trigger</b> pin which has to be an output, and 2nd GPIO is the <b>Echo</b> pin which has to be an input!<br>Make sure to set it up at <a href='pinout'>Pinout settings</a> first! <br>And do not forget about 5V->3.3V level shifting when connecting them!")
  webserver.addFormNumericBox("Samples","p013_samples",self.taskdevicepluginconfig[0],1,30)
  webserver.addFormNote("Number of readings at once, that are averaged.")
  webserver.addFormNumericBox("Cooldown time between samples","p013_ctime",self.taskdevicepluginconfig[1],10,1000)
  webserver.addUnit("ms")
  webserver.addFormNote("Waiting before starting the next sample reading. (100ms recommended)")
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("p013_samples",params)
  if par == "":
    par = 5
  self.taskdevicepluginconfig[0] = int(par)
  par = webserver.arg("p013_ctime",params)
  if par == "":
    par = 100
  self.taskdevicepluginconfig[1] = int(par)
  self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    val1 = self.sr.raw_distance()
   except Exception as e:
    val1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SR04: "+str(e))
   if val1 is not None:
    self.set_value(1,val1,True)
    self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

class SR04:
    def __init__(self, trig_pin, echo_pin, sample_size=5, sample_wait=0.1):
        self.trig_pin = int(trig_pin)
        self.echo_pin = int(echo_pin)
        self.sample_size = sample_size
        self.sample_wait = sample_wait
        self.initialized = True

    def get_numbers_like(self,varr,num):
       c = 0
       for i in range(len(varr)):
        if (varr[i]>=(num*0.9)) and (varr[i]<=(num*1.1)):
         c+=1
       return c

    def get_avg_val(self,valarray):
       if len(valarray)<0:
        return 0
       adist = round( (sum(valarray) / len(valarray)), 0)
       if len(valarray)<3:
        return adist
       if ((max(valarray) - min(valarray))>4): # too much deviation, check it
         if len(valarray)>3: # filter probably false results
          DARR3 = []
          for i in range(0,len(valarray)):
           DARR3.append(self.get_numbers_like(valarray,valarray[i]))
          if len(DARR3)>0:
           maxval = max(DARR3)
           valarray2 = []
           for i in range(0,len(DARR3)): 
            if DARR3[i]==maxval:
             valarray2.append(valarray[i])
           if len(valarray2)>0:
            valarray=valarray2
            adist = round( (sum(valarray) / len(valarray)), 0)
         diffd = abs(max(valarray)-adist)
         if (diffd > abs(adist-min(valarray))): # filter values that too far from each other
          diffd = abs(adist-min(valarray))
         if (diffd<1):
          diffd=1
         if diffd>11:
          diffd=11
         DARR2=[]
         for i in range(0,len(valarray)):
          if (abs(adist-valarray[i])<=diffd):
           DARR2.append(valarray[i])
         if len(DARR2)>0:
          adist = round( (sum(DARR2) / len(DARR2)), 0)
       return adist

    def raw_distance(self,temperature=20):
       if self.initialized:
        speed_of_sound = 331.3 * math.sqrt(1+(temperature / 273.15))
        sample = []

        for distance_reading in range(self.sample_size):
            gpios.HWPorts.output(self.trig_pin, 0)
            time.sleep(self.sample_wait)
            gpios.HWPorts.output(self.trig_pin, 1)
            time.sleep(0.00001)
            gpios.HWPorts.output(self.trig_pin, 0)
            echo_status_counter = 1
            while gpios.HWPorts.input(self.echo_pin) == 0:
                if echo_status_counter < 1000:
                    echo_status_counter += 1
                else:
                    break
            sonar_signal_off = time.time()
            while gpios.HWPorts.input(self.echo_pin) == 1:
                pass
            sonar_signal_on = time.time()
            time_passed = float(sonar_signal_on - sonar_signal_off)
            distance_mm = time_passed * float((speed_of_sound * 1000) / 2)
            if distance_mm>19 and distance_mm<4001:
             sample.append(distance_mm)
        result = self.get_avg_val(sample)
        if result<20 or result>4000:
         return None
        return result
       else:
        return None
