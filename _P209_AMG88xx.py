#!/usr/bin/env python3
#############################################################################
##################### AMG88xx plugin for RPIEasy ############################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
from Adafruit_AMG88xx import Adafruit_AMG88xx
import time
import webserver
import Settings
from PIL import Image, ImageDraw
from io import BytesIO

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 209
 PLUGIN_NAME = "Environment - AMG88xx sensor"
 PLUGIN_VALUENAME1 = "Min"
 PLUGIN_VALUENAME2 = "Max"
 PLUGIN_VALUENAME3 = "Average"
 PLUGIN_VALUENAME4 = "Range"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.amg = None
  self._min = 80
  self._max = 0
  self._avg = 0
  self._reftemp = 0
  self._devc = 0
  self._dev = 0
  self.heatdata = []
  self.therm = 0
  self.thermtime = 0
  self.timer100ms = False
  self.MinTemp = 18
  self.MaxTemp = 35
  self.rotateangle = 0
  self.a = 0
  self.b = 0
  self.c = 0
  self.d = 0
  self.detdev = 0
  self.detrange = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.initialized = False
  self.readinprogress = 0
  self.timer100ms = False
  if self.enabled:
   i2cport = -1
   try:
    for i in range(0,2):
     if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
      i2cport = i
      break
   except:
    i2cport = -1
   if i2cport>-1:
     try:
      dport = int(self.taskdevicepluginconfig[0])
     except:
      dport = 0
     if dport == 0:
      dport = 0x69
      self.amg = None
     try:
      self.amg = Adafruit_AMG88xx(address=dport)
      self.initialized = True
     except Exception as e:
      self.amg = None
     try:
      self.heatdata = self.amg.readPixels()
      self.getabcd()
     except:
      pass
     if self.interval==0:
      self.timer100ms = True # enable periodic check if interval not specified
   if self.amg is None:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"AMG88xx can not be initialized! ")
    return False

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x69","0x68"]
  optionvalues = [0x69,0x68]
  webserver.addFormSelector("I2C address","plugin_209_addr",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  options = ["None","Min","Max","Average","Temp range","Thermistor","# of greater values than reference temp","Deviance from reference temp","Temp median","Heatsource detection"]
  optionvalues = [0,1,2,3,4,5,6,7,8,9]
  webserver.addFormSelector("Value1","plugin_209_func0",len(optionvalues),options,optionvalues,None,int(self.taskdevicepluginconfig[1]))
  webserver.addFormSelector("Value2","plugin_209_func1",len(optionvalues),options,optionvalues,None,int(self.taskdevicepluginconfig[2]))
  webserver.addFormSelector("Value3","plugin_209_func2",len(optionvalues),options,optionvalues,None,int(self.taskdevicepluginconfig[3]))
  webserver.addFormSelector("Value4","plugin_209_func3",len(optionvalues),options,optionvalues,None,int(self.taskdevicepluginconfig[4]))
  webserver.addFormFloatNumberBox("Reference temperature","plugin_209_reftemp",self._reftemp,0,80)
  webserver.addFormNote("Set this to 0 to use built-in thermistor as reference!")
  webserver.addFormNumericBox("Number of + deviances means heatsource detected","plugin_209_detdev",self.detdev,0,64)
  webserver.addFormNote("0 means disable this parameter!")
  webserver.addFormNumericBox("Temperature range means heatsource detected","plugin_209_detrange",self.detrange,0,30)
  webserver.addFormNote("0 means disable this parameter!")

  webserver.addFormSubHeader("Snapshot options")
  options = ["Disable","160x160","320x320"]
  optionvalues = [0,160,320]
  webserver.addFormSelector("Output size","plugin_209_psize",len(optionvalues),options,optionvalues,None,int(self.taskdevicepluginconfig[5]))
  options = ["None","Rotate by 90","Rotate by 180","Rotate by 270"]
  optionvalues = [0,90,180,270]
  webserver.addFormSelector("Rotation","plugin_209_rot",len(optionvalues),options,optionvalues,None,int(self.rotateangle))
  webserver.addFormFloatNumberBox("Min temp for color calc","plugin_209_mintemp",self.MinTemp,-20,100)
  webserver.addFormFloatNumberBox("Max temp for color calc","plugin_209_maxtemp",self.MaxTemp,-20,100)
  try:
   if self.initialized and self.enabled and int(self.taskdevicepluginconfig[5])>0:
    webserver.addHtml("<tr><td colspan=2><a href='heatcam.jpg'><img src='heatcam.jpg'></a></td></tr>")
  except:
   pass
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("plugin_209_addr",params)
   if par == "":
    par = 0x69
   self.taskdevicepluginconfig[0] = int(par)

   par = webserver.arg("plugin_209_func0",params)
   try:
    self.taskdevicepluginconfig[1] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1
   except:
    self.taskdevicepluginconfig[1] = 0

   par = webserver.arg("plugin_209_func1",params)
   try:
    self.taskdevicepluginconfig[2] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_DUAL
    self.valuecount=2
   except:
    self.taskdevicepluginconfig[2] = 0
    self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1

   par = webserver.arg("plugin_209_func2",params)
   try:
    self.taskdevicepluginconfig[3] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_TRIPLE
    self.valuecount=3
   except:
    self.taskdevicepluginconfig[3] = 0
    self.vtype=rpieGlobals.SENSOR_TYPE_DUAL
    self.valuecount=2

   par = webserver.arg("plugin_209_func3",params)
   try:
    self.taskdevicepluginconfig[4] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_QUAD
    self.valuecount=4
   except:
    self.taskdevicepluginconfig[4] = 0
    self.vtype=rpieGlobals.SENSOR_TYPE_TRIPLE
    self.valuecount=3

   try:
    self._reftemp = float(webserver.arg("plugin_209_reftemp",params))
   except:
    self._reftemp = 0
   try:
    self.detdev = float(webserver.arg("plugin_209_detdev",params))
   except:
    self.detdev = 0
   try:
    self.detrange = float(webserver.arg("plugin_209_detrange",params))
   except:
    self.detrange = 0

   try:
    self.taskdevicepluginconfig[5] = int(webserver.arg("plugin_209_psize",params))
   except:
    self.taskdevicepluginconfig[5] = 0

   try:
    self.rotateangle = int(webserver.arg("plugin_209_rot",params))
   except:
    self.rotateangle = 0

   try:
    self.MinTemp = float(webserver.arg("plugin_209_mintemp",params))
   except:
    self.MinTemp = 0
   try:
    self.MaxTemp = float(webserver.arg("plugin_209_maxtemp",params))
   except:
    self.MaxTemp = 0

   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized:
   try:
     self.therm = self.amg.readThermistor()
     self.readdata()
     for i in range(0,4):
      val = int(self.taskdevicepluginconfig[i+1])
      if val>0:
       self.set_value(i+1,self.getvalue(val),False)
       result = True
   except Exception as e:
    print(e)
   if result:
     self._lastdataservetime = rpieTime.millis()
     self.plugin_senddata()
  return result

 def readdata(self):
   if self.readinprogress == 0:
    self.readinprogress = 1
    try:
     self.heatdata = self.amg.readPixels()
     dsum = 0
     self._min = 80
     self._max = 0
     self._devc = 0
     self._dev = 0
     for d in range(0,len(self.heatdata)):
      if self.heatdata[d] < self._min:
        self._min = self.heatdata[d]
      if self.heatdata[d] > self._max:
        self._max = self.heatdata[d]
      if self._reftemp==0:
       if self.heatdata[d] > self.therm:
         self._devc += 1
         self._dev += (self.heatdata[d] - self.therm)
      else:
       if self.heatdata[d] > self._reftemp:
         self._devc += 1
         self._dev += (self.heatdata[d] - self._reftemp)
      dsum += self.heatdata[d]
     self._avg = dsum / len(self.heatdata)
    except:
     pass
    self.readinprogress = 0

 def getvalue(self,val):
  res = 0
  if val==1:
   res=self._min
  elif val==2:
   res=self._max
  elif val==3:
   res=self._avg
  elif val==4:
   res= (self._max - self._min)
  elif val==5:
   res=self.therm
  elif val==6:
   res=self._dev
  elif val==7:
   if self._devc>0:
    res= (self._dev / self._devc)
   else:
    res = 0
  elif val==8:
   tarr = sorted(self.heatdata)
   midx = round(len(self.heatdata)/2)
   res = tarr[midx]
  elif val==9: # human/heatsource detection
   if self.detdev > 0:
    if self._dev >= self.detdev:
     res = 1
   if self.detrange > 0:
    if (self._max - self._min)>=self.detrange:
     res = 1
  return res

 def timer_ten_per_second(self):
  if self.enabled and self.initialized:
   changed = False
   if time.time()-self.thermtime > 1:
     self.therm = self.amg.readThermistor()
     self.thermtime=time.time()
   self.readdata()
   for i in range(0,4):
      val = int(self.taskdevicepluginconfig[i+1])
      if val>0:
       if abs(float(self.uservar[i])-float(self.getvalue(val)))>=0.2:
        self.set_value(i+1,self.getvalue(val),False)
        changed = True
   if changed:
     self._lastdataservetime = rpieTime.millis()
     self.plugin_senddata()
  return self.timer100ms

 def getabcd(self):
    self.a = self.MinTemp + (self.MaxTemp - self.MinTemp) * 0.2121
    self.b = self.MinTemp + (self.MaxTemp - self.MinTemp) * 0.3182
    self.c = self.MinTemp + (self.MaxTemp - self.MinTemp) * 0.4242
    self.d = self.MinTemp + (self.MaxTemp - self.MinTemp) * 0.8182

 def getcolor(self,val):
    try:
     red = constrain(255.0 / (self.c - self.b) * val - ((self.b * 255.0) / (self.c - self.b)), 0, 255)
    except:
     red = 0

    try:
     if ((val > self.MinTemp) and (val < self.a)):
      green = constrain(255.0 / (self.a - self.MinTemp) * val - (255.0 * self.MinTemp) / (self.a - self.MinTemp), 0, 255)
     elif ((val >= self.a) & (val <= self.c)):
      green = 255
     elif (val > self.c):
      green = constrain(255.0 / (self.c - self.d) * val - (self.d * 255.0) / (self.c - self.d), 0, 255)
     elif ((val > self.d) | (val < self.a)):
      green = 0
    except:
     green = 0

    try:
     if (val <= self.b):
      blue = constrain(255.0 / (self.a - self.b) * val - (255.0 * self.b) / (self.a - self.b), 0, 255)
     elif ((val > self.b) & (val <= self.d)):
      blue = 0
     elif (val > self.d):
      blue = constrain(240.0 / (self.MaxTemp - self.d) * val - (self.d * 240.0) / (self.MaxTemp - self.d), 0, 240)
    except:
     blue = 0

#    return ((red & 31) << 11) + ((green & 63) << 8) + (blue & 31) # 565
    return (int(red),int(green),int(blue)) # rgb

def constrain(val, minval, maxval):
    res = val
    if val<minval:
     res = minval
    if val>maxval:
     res = maxval
    return res

@webserver.WebServer.route('/heatcam.jpg')
def handle_heatcam(self):
  if (not webserver.isLoggedIn(self.get,self.cookie)):
    return self.redirect('/login')
  camtask = None
  for x in range(0,len(Settings.Tasks)):
    if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool:
     try:
      if Settings.Tasks[x].enabled:
       if Settings.Tasks[x].pluginid==209:
        camtask = Settings.Tasks[x]
        break
     except:
      pass
  if camtask is not None:
   try:
    ps = int(camtask.taskdevicepluginconfig[5])
   except:
    ps = 0
   if ps>0:
    self.set_mime('image/jpeg')
    try:
     image = Image.new("RGB", (8,8), "black")
     draw = ImageDraw.Draw(image)
     for ix in range(8):
      for iy in range(8):
        col = camtask.getcolor(camtask.heatdata[ix+(8*iy)])
        draw.point([(ix,(iy%8))], fill=col )
     if camtask.rotateangle!=0:
      image = image.rotate(camtask.rotateangle)
     image = image.resize( (ps,ps), Image.LANCZOS)
     img_io = BytesIO()
     image.save(img_io, 'JPEG')
     img_io.seek(0)
     return img_io.read()
    except Exception as e:
     print("e:",e)
