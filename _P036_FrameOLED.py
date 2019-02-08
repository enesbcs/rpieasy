#!/usr/bin/env python3
#############################################################################
########################## OLED plugin for RPIEasy ##########################
#############################################################################
#
# Available commands:
#  OLEDFRAMEDCMD,<value>          - value can be: on, off, low, med, high
#  OLEDFRAMEDCMD,scroll           - scroll to next page
#
# Loosely based on marvellous ESPEasy Plugin 036.
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# Made with the support of Budman1758
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import commands
import math
import Settings
import linux_network as Network
import linux_os as OS
from datetime import datetime
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from PIL import ImageFont, ImageDraw, Image

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 36
 PLUGIN_NAME = "Display - Framed OLED (TESTING)"
 PLUGIN_VALUENAME1 = "OLED"
 P36_Nlines = 12
 P36_CONTRAST_LOW  = 64
 P36_CONTRAST_MED  = 0xCF
 P36_CONTRAST_HIGH = 0xFF

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.ports = 0
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = False
  self.device = None
  self.width  = None
  self.height = None
  self.lines  = []
  self.ufont  = None
  self.hfont  = None
  self.ypos   = []
  self.dispimage = None
  self.textbuffer = []
  self.lastlineindex = 0
  self.pages = 0
  self.actualpage = 0
  self.conty1 = 0
  self.conty2 = 0
  self.headline = 0
  self.lastwifistrength = -1
  self.writeinprogress = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
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
    if self.interval>2:
      nextr = self.interval-2
    else:
      nextr = self.interval

    self.initialized = False
    serialdev = None
    self.taskdevicepluginconfig[1] = int(float(self.taskdevicepluginconfig[1]))
    if self.taskdevicepluginconfig[1] != 0: # i2c address
     serialdev = i2c(port=i2cport, address=self.taskdevicepluginconfig[1])
    else:
     return self.initialized
    self.device = None
    try:
     if "x" in str(self.taskdevicepluginconfig[3]):
      resstr = str(self.taskdevicepluginconfig[3]).split()
      self.width = int(resstr[0])
      self.width = int(resstr[1])
     else:
      self.width  = None
      self.height = None
    except:
     self.width  = None
     self.height = None

    if str(self.taskdevicepluginconfig[0]) != "0" and str(self.taskdevicepluginconfig[0]).strip() != "": # display type
     try:
      if str(self.taskdevicepluginconfig[0])=="ssd1306":
       from luma.oled.device import ssd1306
       if self.height is None:
        self.device = ssd1306(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1306(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="sh1106":
       from luma.oled.device import sh1106
       if self.height is None:
        self.device = sh1106(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = sh1106(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1309":
       from luma.oled.device import ssd1309
       if self.height is None:
        self.device = ssd1309(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1309(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1331":
       from luma.oled.device import ssd1331
       if self.height is None:
        self.device = ssd1331(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1331(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1351":
       from luma.oled.device import ssd1351
       if self.height is None:
        self.device = ssd1351(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1351(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1322":
       from luma.oled.device import ssd1322
       if self.height is None:
        self.device = ssd1322(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1322(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1325":
       from luma.oled.device import ssd1325
       if self.height is None:
        self.device = ssd1325(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1325(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1327":
       from luma.oled.device import ssd1327
       if self.height is None:
        self.device = ssd1327(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1327(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"OLED can not be initialized! "+str(e))
      self.enabled = False
      self.device = None
      return False
    if self.device is not None:
     try:
      lc = int(self.taskdevicepluginconfig[4])
     except:
      lc = 1
     if lc < 1:
      lc = 1
     elif lc>4:
      lc = 4
     try:
      self.hfont=ImageFont.truetype('img/UbuntuMono-R.ttf', 10)
      lineheight=11
      if lc==1:
       lineheight = 24
       self.ypos = [20,0,0,0]
      elif lc==2:
       lineheight = 16
       self.ypos = [15,34,0,0]
      elif lc==3:
       lineheight = 12
       self.ypos = [13,25,37,0]
      elif lc==4:
       lineheight = 10
       self.ypos = [12,22,32,42]
      self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', lineheight)
     except Exception as e:
      print(e)
     try:
      self.device.show()
     except:
      pass
     if self.interval>2:
       nextr = self.interval-2
     else:
       nextr = 0
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
     try:
       self.dispimage = Image.new('1', (self.device.width,self.device.height), "black")
       self.conty1 = 12
       self.conty2 = self.device.height-12
       self.textbuffer = []
       self.actualpage = 0
       self.lastlineindex = self.P36_Nlines
       for l in reversed(range(self.P36_Nlines)):
        if (str(self.lines[l]).strip()!="") and (str(self.lines[l]).strip()!="0"):
         self.lastlineindex = l
         break
       try:
        self.pages = math.ceil((self.lastlineindex+1) / int(self.taskdevicepluginconfig[4]))
       except:
        self.pages = 0
     except Exception as e:
      self.initialized = False
     try:
      cont = int(self.taskdevicepluginconfig[6])
     except:
      cont = 0
     if cont>0:
      self.device.contrast(cont)

     draw = ImageDraw.Draw(self.dispimage)
     maxcols = int(self.taskdevicepluginconfig[7]) # auto decrease font size if needed
     if maxcols < 1:
       maxcols = 1
     tstr = "X"*maxcols
     try:
       sw = draw.textsize(tstr,self.ufont)[0]
     except:
       sw = self.device.width
     while (sw>self.device.width):
       lineheight-=1
       self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', lineheight)
       sw = draw.textsize(tstr,self.ufont)[0]
     self.writeinprogress = 0
    else:
     self.initialized = False
  else:
   self.__del__()

 def webform_load(self): # create html page for settings
  choice1 = str(self.taskdevicepluginconfig[0]) # store display type
  import luma.oled.device
  options = luma.oled.device.__all__
  webserver.addHtml("<tr><td>Display type:<td>")
  webserver.addSelector_Head("p036_type",True)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice1==options[d]),False)
  webserver.addSelector_Foot()
  choice2 = int(float(self.taskdevicepluginconfig[1])) # store i2c address
  options = ["0x3c","0x3d"]
  optionvalues = [0x3c,0x3d]
  webserver.addFormSelector("Address","p036_adr",len(options),options,optionvalues,None,choice2)
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  choice3 = int(float(self.taskdevicepluginconfig[2])) # store rotation state
  options =      ["Normal","Rotate by 180"]
  optionvalues = [0,2]
  webserver.addFormSelector("Mode","p036_rotate",len(optionvalues),options,optionvalues,None,choice3)
  options = ["Default","128x64","128x128","128x32","96x96","96x64","64x48","64x32"]
  choice4 = self.taskdevicepluginconfig[3] # store resolution
  webserver.addHtml("<tr><td>Resolution:<td>")
  webserver.addSelector_Head("p036_res",False)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice4==options[d]),False)
  webserver.addSelector_Foot()

  choice5 = int(float(self.taskdevicepluginconfig[4])) # store line count
  webserver.addHtml("<tr><td>Lines per Frame:<td>")
  webserver.addSelector_Head("p036_linecount",False)
  for l in range(1,5):
   webserver.addSelector_Item(str(l),l,(l==choice5),False)
  webserver.addSelector_Foot()

  choice6 = int(float(self.taskdevicepluginconfig[5])) # transition speed
  options =      ["Very Slow","Slow","Fast","Very Fast","Instant"]
  optionvalues = [1,2,4,8,32]
  webserver.addFormSelector("Scroll","p036_scroll",len(optionvalues),options,optionvalues,None,choice6)

  for l in range(self.P36_Nlines):
   try:
    linestr = self.lines[l]
   except:
    linestr = ""
   webserver.addFormTextBox("Line"+str(l+1),"p036_template"+str(l),linestr,128)

  choice7 = int(float(self.taskdevicepluginconfig[6])) # contrast
  options = ["Low","Medium","High"]
  optionvalues = [self.P36_CONTRAST_LOW, self.P36_CONTRAST_MED, self.P36_CONTRAST_HIGH]
  webserver.addFormSelector("Contrast","p036_contrast",len(optionvalues),options,optionvalues,None,choice7)
  webserver.addFormNumericBox("Try to display # characters per row","p036_charperl",self.taskdevicepluginconfig[7],1,32)
  webserver.addFormNote("Leave it '1' if you do not care")
  return True

 def __del__(self):
  self.initialized = False
  try:
   if self.device is not None:
    self.device.clear()
    self.device.hide()
  except:
   pass

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p036_type",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[0] = str(par)

   par = webserver.arg("p036_adr",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[1] = int(par)

   par = webserver.arg("p036_rotate",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[2] = int(par)

   par = webserver.arg("p036_res",params)
   self.taskdevicepluginconfig[3] = str(par)

   par = webserver.arg("p036_linecount",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[4] = int(par)

   for l in range(self.P36_Nlines):
    linestr = webserver.arg("p036_template"+str(l),params).strip()
#    if linestr!="" and linestr!="0":
    try:
      self.lines[l]=linestr
    except:
      self.lines.append(linestr)

   par = webserver.arg("p036_scroll",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[5] = int(par)
   par = webserver.arg("p036_contrast",params)
   if par == "":
    par = self.P36_CONTRAST_MED
   self.taskdevicepluginconfig[6] = int(par)

   par = webserver.arg("p036_charperl",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[7] = int(par)

   self.plugin_init()
   return True

 def showfirstpage(self):
  draw = ImageDraw.Draw(self.dispimage)
  draw.rectangle( ((0,self.conty1),(128,self.conty2)) ,fill="black")
  for l in range(int(self.taskdevicepluginconfig[4])):
   tpos = int((self.device.width-(draw.textsize(self.textbuffer[0][l],self.ufont)[0]))/2)-2
   if tpos<0:
    tpos = 0
   draw.text( (tpos,self.ypos[l]), self.textbuffer[0][l], fill="white", font=self.ufont)
  self.device.display(self.dispimage)
  self.actualpage = 1

 def scrollnextpage(self):
  draw = ImageDraw.Draw(self.dispimage)
  ax = 0
  step=int(self.taskdevicepluginconfig[5])
  for offset in range(0,128,step):
    draw.rectangle( ((0,self.conty1),(128,self.conty2)) ,fill="black")
    for l in range(int(self.taskdevicepluginconfig[4])):
     tpos = int((self.device.width-(draw.textsize(self.textbuffer[0][l],self.ufont)[0]))/2)-2
     if tpos<0:
      tpos = 0
     draw.text( (tpos+ax, self.ypos[l]), self.textbuffer[0][l], fill="white", font=self.ufont)
    for l in range(int(self.taskdevicepluginconfig[4])):
     tpos = int((self.device.width-(draw.textsize(self.textbuffer[1][l],self.ufont)[0]))/2)-2
     if tpos<0:
      tpos = 0
     draw.text( (tpos+ax+self.device.width, self.ypos[l]), self.textbuffer[1][l], fill="white", font=self.ufont)
    self.device.display(self.dispimage)
    ax -= step
    if self.initialized==False:
     break
  draw.rectangle( ((0,self.conty1),(128,self.conty2)) ,fill="black")
  for l in range(int(self.taskdevicepluginconfig[4])): # last position
     tpos = int((self.device.width-(draw.textsize(self.textbuffer[1][l],self.ufont)[0]))/2)-2
     if tpos<0:
      tpos = 0
     draw.text( (tpos, self.ypos[l]), self.textbuffer[1][l], fill="white", font=self.ufont)
  self.display_footer()

 def display_time(self):
  draw = ImageDraw.Draw(self.dispimage)
  draw.rectangle( ((0,0),(28,10)) ,fill="black")
  draw.text( (0,0), datetime.now().strftime('%H:%M'), fill="white", font=self.hfont)
  self.device.display(self.dispimage)

 def display_wifibars(self):
  connected = True
  try:
   rssi = int(OS.get_rssi())
  except:
   rssi = -100
   connected = False
  if rssi<-99:
   connected = False
  nbars_filled = (rssi+100)/8
  x = self.device.width - 23 # 105
  y = 0
  size_x = 15
  size_y = 10
  nbars = 5
  width = int(size_x / nbars)
  size_x = width * nbars -1
  if self.lastwifistrength != nbars_filled:
   self.lastwifistrength = nbars_filled
   draw = ImageDraw.Draw(self.dispimage)
   draw.rectangle( ((x,y),(x+size_x,y+size_y)) ,fill="black")
   if connected:
    for ibar in range(0,nbars):
     height = size_y * (ibar+1) / nbars
     xpos   = x + ibar * width
     ypos   = y + size_y - height
     if (ibar<=nbars_filled):
      draw.rectangle( ((xpos,ypos),(xpos+width-1,ypos+height)),fill="white")
     else:
      draw.rectangle( ((xpos,ypos),(xpos+width-1,ypos+1)),fill="white")
      draw.rectangle( ((xpos,y+size_y-1),(xpos+width-1,y+size_y)),fill="white")
  return True

 def display_footer(self):
  ft = ""
  for p in range(self.pages):
   if p==self.actualpage:
    ft += str(u"\u2022") # "•"
   else:
    ft += str(u"\u00B7") # "·"
  draw = ImageDraw.Draw(self.dispimage)
  tpos = int((self.device.width-(draw.textsize(ft,self.hfont)[0]))/2)-2
  if tpos<0:
   tpos = 0
  draw.rectangle( ((20,self.conty2),(108,self.device.height)) ,fill="black")
  draw.text( (tpos, self.conty2), ft, fill="white", font=self.hfont)
  self.device.display(self.dispimage)

 def display_name(self):
  draw = ImageDraw.Draw(self.dispimage)
  tstr = ""
  if self.headline == 0:
   tstr = str(Settings.Settings["Name"])
   self.headline = 1
  else:
   try:
    wdev = Settings.NetMan.getfirstwirelessdev()
   except:
    wdev = False
   if wdev:
    tstr = str(Network.get_ssid(wdev))
   self.headline = 0
  draw.rectangle( ((29,0),(106,12)) ,fill="black")
  tpos = int((self.device.width-(draw.textsize(tstr,self.hfont)[0]))/2)-2
  if tpos<0:
   tpos = 0
  draw.text( (tpos, 0), tstr, fill="white", font=self.hfont)

 def plugin_read(self): # deal with data processing at specified time interval
  if self.initialized and self.enabled and self.device and self.writeinprogress==0:
     try:
      if self.dispimage:
       self.writeinprogress = 1
       self.display_time()
       self.display_name()
       self.display_wifibars()
       if self.pages==1:
        spos = 0
       else:
        spos = (self.actualpage*int(self.taskdevicepluginconfig[4]))
       if len(self.textbuffer)>1: # previous value in pos 0, second in 1 normal loop
        for l in range(int(self.taskdevicepluginconfig[4])):
         self.textbuffer[1][l] = self.oledparse(str(self.lines[spos+l]))
       elif len(self.textbuffer)==1: # previous value in pos 0, no second
        tbuf = []
        for l in range(int(self.taskdevicepluginconfig[4])):
         tbuf.append(self.oledparse(str(self.lines[spos+l])))
        self.textbuffer.append(tbuf)
       else: # no values in buffer
        self.display_footer()
        tbuf = []
        for l in range(int(self.taskdevicepluginconfig[4])):
         tbuf.append(self.oledparse(str(self.lines[spos+l])))
        self.textbuffer.append(tbuf)
        self.showfirstpage()
        self._lastdataservetime = rpieTime.millis()
        self.writeinprogress = 0
        return True
       self.scrollnextpage()
       if self.pages>1:
        if self.actualpage<(self.pages-1):
         self.actualpage += 1
        else:
         self.actualpage = 0
       if len(self.textbuffer)>1: # skew things after scroll
        for l in range(int(self.taskdevicepluginconfig[4])):
         self.textbuffer[0][l] = self.textbuffer[1][l]
       self.writeinprogress = 0
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"OLED write error! "+str(e))
      self.writeinprogress = 0
     self._lastdataservetime = rpieTime.millis()
#     print(self.textbuffer,self.actualpage,self.pages)
  return True

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "oledframedcmd":
   try:
    cmd = cmdarr[1].strip()
   except:
    cmd = ""
   try:
    if self.device is not None:
     if cmd == "on":
      self.device.show()
      res = True
     elif cmd == "off":
      self.device.hide()
      res = True
     elif cmd == "low":
      self.device.contrast(self.P36_CONTRAST_LOW)
      res = True
     elif cmd == "med":
      self.device.contrast(self.P36_CONTRAST_MED)
      res = True
     elif cmd == "high":
      self.device.contrast(self.P36_CONTRAST_HIGH)
      res = True
     elif cmd == "scroll":
      self._lastdataservetime = rpieTime.millis()
      self.plugin_read()
      res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"OLED command error! "+str(e))
    res = False
  return res

 def oledparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(linestr)
      if "{" in resstr or "&" in resstr:
       resstr = resstr.replace("{D}","˚").replace("&deg;","˚")
       resstr = resstr.replace("{<<}","«").replace("&laquo;","«")
       resstr = resstr.replace("{>>} ","»").replace("&raquo;","»")
       resstr = resstr.replace("{u} ","µ").replace("&micro; ","µ")
       resstr = resstr.replace("{E}","€").replace("&euro;","€")
       resstr = resstr.replace("{Y}","¥").replace("&yen;","¥")
       resstr = resstr.replace("{P}","£").replace("&pound;","£")
       resstr = resstr.replace("{c}","¢").replace("&cent;","¢")
       resstr = resstr.replace("{^1}","¹").replace("&sup1;","¹")
       resstr = resstr.replace("{^2}","²").replace("&sup2;","²")
       resstr = resstr.replace("{^3}","³").replace("&sup3;","³")
       resstr = resstr.replace("{1_4}","¼").replace("&frac14;","¼")
       resstr = resstr.replace("{1_2}","½").replace("&frac24;","½")
       resstr = resstr.replace("{3_4}","¾").replace("&frac34;","¾")
       resstr = resstr.replace("{+-}","±").replace("&plusmn;","±")
       resstr = resstr.replace("{x}","×").replace("&times;","×")
       resstr = resstr.replace("{..}","÷").replace("&divide;","÷")
      return resstr
