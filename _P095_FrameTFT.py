#!/usr/bin/env python3
#############################################################################
##################### Framed TFT plugin for RPIEasy #########################
#############################################################################
#
# SPI displays framed plugin
#
#| command | details | description |
#|-----|-----|-----|
#| tft | `TFT,<tft_subcommand>,....` | Draw line, rect, circle, triangle and text |
#| tftcmd | `TFTCMD,<tftcmd_subcommand>` | Control the screen (on, off, clear,..) |
#
#TFT Subcommands:
#| TFT Subcommands | details | description |
#|-----|-----|-----|
#| txt | txt,<text> | Write simple text (use last position, color and size) |
#| txp | txp,<X>,<Y> | Set text position (move the cursor) |
#| txc | txc,<foreColor>,<backgroundColor> | Set text color (background is transparent if not provided |
#| txs | txs,<SIZE> | Set text size |
#| txtfull | txtfull,<row>,<col>,<size=1>,<foreColor=white>,<backColor=black>,<text> | Write text with all options |
#| l | l,<x1>,<y1>,<2>,<y2>,<color> | Draw a simple line |
#| r | r,<x>,<y>,<width>,<height>,<color> | Draw a rectangle |
#| rf | rf,<x>,<y>,<width>,<height>,<bordercolor>,<innercolor> | Draw a filled rectangle |
#| c | c,<x>,<y>,<radius>,<color> | Draw a circle |
#| cf | cf,<x>,<y>,<radius>,<bordercolor>,<innercolor> | Draw a filled circle |
#| t | t,<x1>,<y1>,<x2>,<y2>,<x3>,<y3>,<color>| Draw a triangle |
#| tf | tf,<x1>,<y1>,<x2>,<y2>,<x3>,<y3>,<bordercolor>,<innercolor> | Draw a filled triangle |
#| px | px,<x>,<y>,<color> | Print a single pixel |
#| img | img,<X>,<Y>,<filename> | Draw image file at position |
#
#TFTCMD Subcommands:
#| TFT Subcommands | details | description |
#|-----|-----|-----|
#| on | on | Display ON |
#| off | off | Display OFF |
#| clear | clear,<color> | Clear display |
#| rot | rot,<value> | Rotate display (value from 0 to 3 inclusive) |
#
# Copyright (C) 2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import commands
import math
import Settings
import linux_network as Network
import linux_os as OS
from datetime import datetime
from luma.core.interface.serial import spi
from luma.core.render import canvas
from PIL import ImageFont, ImageDraw, Image

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 95
 PLUGIN_NAME = "Display - Framed TFT SPI (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "OLED"
 P95_Nlines = 12

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SPI
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
  self.initval = -1
  self.btnval = -1
  self.btntime = 0
  self.displaystate = -1
  self.bitdepth = '1'
  self.lastx = 0
  self.lasty = 0
  self.bgcolor = "black"
  self.fgcolor = "white"
  self.tbgcolor = "black"
  self.tfgcolor = "white"
  self.bgimgname = None
  self.bgimg = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.enabled:
   if self.taskdevicepin[0]>=0:
    try:
     gpios.HWPorts.remove_event_detect(int(self.taskdevicepin[0]))
    except:
     pass
    try:
     self.btntime = 0
     self.btnval = -1
     self.initval = int(gpios.HWPorts.input(int(self.taskdevicepin[0])))
     gpios.HWPorts.add_event_detect(int(self.taskdevicepin[0]),gpios.BOTH,self.p095_handler)
    except:
     pass
   try:
      if self.spi<0 or self.spidnum<0:
        return
   except:
     self.spi = 0
     self.spidnum = 0
   self.ports = "SPI"+str(self.spi)+"/"+str(self.spidnum)
   if self.spi>-1 and self.spidnum>-1:
    if self.interval>2:
      nextr = self.interval-2
    else:
      nextr = self.interval
    try:
     if int(self.taskdevicepin[3])>-1:
        gpios.HWPorts.output(self.taskdevicepin[3],1)
    except:
     pass
    try:
     serialdev = spi(port=self.spi, device=self.spidnum, gpio_DC=self.taskdevicepin[1], gpio_RST=self.taskdevicepin[2])
    except:
     serialdev = None
     self.initialized = False
     return False
    try:
     if "x" in str(self.taskdevicepluginconfig[3]):
      resstr = str(self.taskdevicepluginconfig[3]).split('x')
      self.width = int(resstr[0])
      self.height = int(resstr[1])
     else:
      self.width  = None
      self.height = None
    except:
     self.width  = None
     self.height = None

    self.device = None
    self.initialized = False

    try:
     if str(self.taskdevicepluginconfig[0]) != "0" and str(self.taskdevicepluginconfig[0]).strip() != "": # display type
       if str(self.taskdevicepluginconfig[0])=="st7735": #24-bit RGB image
        from luma.lcd.device import st7735
        if self.width is not None:
         self.device = st7735(serialdev,width=self.width,height=self.height,rotate=int(float(self.taskdevicepluginconfig[2]))) #rgb
        else:
         self.device = st7735(serialdev,rotate=int(float(self.taskdevicepluginconfig[2])))
        self.initialized = True
        self.bitdepth = 'RGB'
       elif str(self.taskdevicepluginconfig[0])=="ili9341": #24-bit RGB image
        from luma.lcd.device import ili9341
        if self.width is not None:
         self.device = ili9341(serialdev,width=self.width,height=self.height,rotate=int(float(self.taskdevicepluginconfig[2])),h_offset=0,v_offset=0) #rgb
        else:
         self.device = ili9341(serialdev,rotate=int(float(self.taskdevicepluginconfig[2])))
        self.initialized = True
        self.bitdepth = 'RGB'
       elif str(self.taskdevicepluginconfig[0])=="ili9486": #24-bit RGB image
        from luma.lcd.device import ili9486
        if self.width is not None:
         self.device = ili9486(serialdev,width=self.width,height=self.height,rotate=int(float(self.taskdevicepluginconfig[2]))) #rgb
        else:
         self.device = ili9486(serialdev,rotate=int(float(self.taskdevicepluginconfig[2]))) #rgb
        self.initialized = True
        self.bitdepth = 'RGB'
       elif str(self.taskdevicepluginconfig[0])=="uc1701x": #1bit
        from luma.lcd.device import uc1701x
        self.device = uc1701x(serialdev,rotate=int(float(self.taskdevicepluginconfig[2]))) #only 128x64 mono
        self.initialized = True
        self.bitdepth = '1'
       elif str(self.taskdevicepluginconfig[0])=="st7567": #1bit
        from luma.lcd.device import st7567
        self.device = st7567(serialdev,rotate=int(float(self.taskdevicepluginconfig[2]))) #only 128x64 mono
        self.initialized = True
        self.bitdepth = '1'
    except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"TFT can not be initialized! "+str(e))
      self.device = None
      return False
    if self.device is not None:
     try:
      lc = int(self.taskdevicepluginconfig[4])
      self.width = self.device.width
      self.height = self.device.height
     except:
      lc = 1
     if lc < 1:
      lc = 1
     elif lc>4:
      lc = 4
     try:
      defh = 10
      if self.height!=64: # correct y coords
       defh = int(defh * (self.height/64))
      cx = 28
      if self.width!=128: # correct x coords
       cx = int(cx * (self.width/128))
      self.hfont=ImageFont.truetype('img/UbuntuMono-R.ttf', defh)

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

      if self.height!=64: # correct y coords
       for p in range(len(self.ypos)):
        self.ypos[p] = int(self.ypos[p] * (self.height/64))
       lineheight = int(lineheight * (self.height/64))

      self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', lineheight) # use size
     except Exception as e:
      print(e)
     try:
      self.device.show()
      self.displaystate = 1
     except:
      self.displaystate = 0
     if self.interval>2:
       nextr = self.interval-2
     else:
       nextr = 0
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
     try:
       self.dispimage = Image.new(self.bitdepth, (self.device.width,self.device.height), self.bgcolor)
       self.conty1 = 12
       if self.height!=64: # correct y coords
        self.conty1 = int(self.conty1 * (self.height/64))
       self.conty2 = self.device.height-self.conty1
       self.textbuffer = []
       self.actualpage = 0
       self.lastlineindex = self.P95_Nlines
       for l in reversed(range(self.P95_Nlines)):
        if (str(self.lines[l]).strip()!="") and (str(self.lines[l]).strip()!="0"):
         self.lastlineindex = l
         break
       try:
        self.pages = math.ceil((self.lastlineindex+1) / int(self.taskdevicepluginconfig[4]))
       except:
        self.pages = 0
     except Exception as e:
      self.initialized = False

     draw = ImageDraw.Draw(self.dispimage)
     maxcols = int(self.taskdevicepluginconfig[7]) # auto decrease font size if needed
     if maxcols < 1:
       maxcols = 1
     tstr = "X"*maxcols
     try:
       sw = draw.textsize(tstr,self.ufont)[0]
     except:
       sw = self.device.width
     try:
      while (sw>self.device.width):
       lineheight-=1
       self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', lineheight)
       sw = draw.textsize(tstr,self.ufont)[0]
     except:
      pass
     tstr = "22:22"
     try:
        sw = draw.textsize(tstr,self.hfont)[0]
     except:
        sw = cx
     try:
      while (sw>cx):
        defh-=1
        self.hfont=ImageFont.truetype('img/UbuntuMono-R.ttf', defh)
        sw = draw.textsize(tstr,self.hfont)[0]
     except:
      pass
     self.bgimg = None
     try:
      if self.bgimgname is not None and self.bgimgname != "":
        try:
         img = Image.open(self.bgimgname,'r') # no path check!
         self.bgimg = img.resize( (self.device.width,self.device.height), Image.LANCZOS)
        except Exception as e:
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Filename error: "+str(e))
     except:
      pass
     self.display_clear() #     self.device.clear()
     self.writeinprogress = 0
    else:
     self.initialized = False
  else:
   self.plugin_exit()

 def webform_load(self): # create html page for settings
  choice1 = str(self.taskdevicepluginconfig[0]) # store display type
  options = ["st7735","ili9341","ili9486","uc1701x","st7567"]
  webserver.addHtml("<tr><td>Display type:<td>")
  webserver.addSelector_Head("p095_type",False)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice1==options[d]),False)
  webserver.addSelector_Foot()

  webserver.addFormPinSelect("DC pin","p095_dc",self.taskdevicepin[1])
  webserver.addFormNote("Output pin")
  webserver.addFormPinSelect("RST pin","p095_rst",self.taskdevicepin[2])
  webserver.addFormNote("Output pin")
  webserver.addFormPinSelect("Enable pin","p095_en",self.taskdevicepin[3])
  webserver.addFormNote("Optional, output pin")

  choice3 = int(float(self.taskdevicepluginconfig[2])) # store rotation state
  options = ["Normal","Rotate by 90","Rotate by 180","Rotate by 270"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Mode","p095_rotate",len(optionvalues),options,optionvalues,None,choice3)
  options = ["Default","128x64","128x128","160x80","160x128","240x240","320x180","320x240","320x480"]
  choice4 = self.taskdevicepluginconfig[3] # store resolution
  webserver.addHtml("<tr><td>Resolution:<td>")
  webserver.addSelector_Head("p095_res",False)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice4==options[d]),False)
  webserver.addSelector_Foot()

  choice5 = int(float(self.taskdevicepluginconfig[4])) # store line count
  webserver.addHtml("<tr><td>Lines per Frame:<td>")
  webserver.addSelector_Head("p095_linecount",False)
  for l in range(1,5):
   webserver.addSelector_Item(str(l),l,(l==choice5),False)
  webserver.addSelector_Foot()

  choice6 = int(float(self.taskdevicepluginconfig[5])) # transition speed
  options =      ["Very Slow","Slow","Fast","Very Fast","Instant"]
  optionvalues = [1,2,4,8,32]
  webserver.addFormSelector("Scroll","p095_scroll",len(optionvalues),options,optionvalues,None,choice6)

  for l in range(self.P95_Nlines):
   try:
    linestr = self.lines[l]
   except:
    linestr = ""
   webserver.addFormTextBox("Line"+str(l+1),"p095_template"+str(l),linestr,128)

  webserver.addFormNumericBox("Try to display # characters per row","p095_charperl",self.taskdevicepluginconfig[7],1,32)
  webserver.addFormNote("Leave it '1' if you do not care")
  webserver.addFormPinSelect("Display button", "p095_button", self.taskdevicepin[0])
  webserver.addFormTextBox("Foreground color","p095_fgcol",self.tfgcolor,64)
  webserver.addFormTextBox("Background color","p095_bgcol",self.tbgcolor,64)
  webserver.addHtml("<p>Check <a href='https://i.stack.imgur.com/dKcr1.png'>PIL color name list</a> before filling out textboxes.")
  try:
   webserver.addFormTextBox("Background image pathname","p095_bgimgname",self.bgimgname,255)
   webserver.addBrowseButton("Browse","p095_bgimgname",startdir=self.bgimgname)
  except:
   self.bgimgname = ""
  return True

 def plugin_exit(self):
  self.initialized = False
  try:
   self.displaystate = 0
   if self.device is not None:
    self.device.clear()
    self.device.hide()
  except:
   pass
  try:
     if int(self.taskdevicepin[3])>-1:
        gpios.HWPorts.output(self.taskdevicepin[3],0)
  except:
     pass
  try:
   gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
  except:
   pass

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p095_type",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[0] = str(par)

   par = webserver.arg("p095_rotate",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[2] = int(par)

   par = webserver.arg("p095_res",params)
   self.taskdevicepluginconfig[3] = str(par)

   par = webserver.arg("p095_linecount",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[4] = int(par)

   for l in range(self.P95_Nlines):
    linestr = webserver.arg("p095_template"+str(l),params).strip()
#    if linestr!="" and linestr!="0":
    try:
      self.lines[l]=linestr
    except:
      self.lines.append(linestr)

   par = webserver.arg("p095_scroll",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[5] = int(par)

   par = webserver.arg("p095_charperl",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[7] = int(par)

   par = webserver.arg("p095_button",params)
   if par == "":
    par = -1
   self.taskdevicepin[0] = int(par)

   par = webserver.arg("p095_dc",params)
   if par == "":
    par = -1
   self.taskdevicepin[1] = int(par)
   par = webserver.arg("p095_rst",params)
   if par == "":
    par = -1
   self.taskdevicepin[2] = int(par)
   par = webserver.arg("p095_en",params)
   if par == "":
    par = -1
   self.taskdevicepin[3] = int(par)

   par = webserver.arg("p095_fgcol",params)
   if par == "":
    par = "white"
   self.fgcolor = str(par)
   self.tfgcolor = str(par)

   par = webserver.arg("p095_bgcol",params)
   if par == "":
    par = "black"
   self.bgcolor = str(par)
   self.tbgcolor = str(par)

   par = webserver.arg("p095_bgimgname",params)
   self.bgimgname = str(par)

   self.plugin_init()
   return True

 def showfirstpage(self):
  draw = ImageDraw.Draw(self.dispimage)
  self.clear_area((0,self.conty1),(self.width-1,self.conty2))  
  for l in range(int(self.taskdevicepluginconfig[4])):
   tpos = int((self.device.width-(draw.textsize(self.textbuffer[0][l],self.ufont)[0]))/2)-2
   if tpos<0:
    tpos = 0
   draw.text( (tpos,self.ypos[l]), self.textbuffer[0][l], fill=self.fgcolor, font=self.ufont)
  self.device.display(self.dispimage)
  self.actualpage = 1

 def scrollnextpage(self):
  draw = ImageDraw.Draw(self.dispimage)
  ax = 0
  step=int(self.taskdevicepluginconfig[5])
  for offset in range(0,self.width,step):
    self.clear_area((0,self.conty1),(self.width-1,self.conty2))
    for l in range(int(self.taskdevicepluginconfig[4])):
     tpos = int((self.device.width-(draw.textsize(self.textbuffer[0][l],self.ufont)[0]))/2)-2
     if tpos<0:
      tpos = 0
     draw.text( (tpos+ax, self.ypos[l]), self.textbuffer[0][l], fill=self.fgcolor, font=self.ufont)
    for l in range(int(self.taskdevicepluginconfig[4])):
     tpos = int((self.device.width-(draw.textsize(self.textbuffer[1][l],self.ufont)[0]))/2)-2
     if tpos<0:
      tpos = 0
     draw.text( (tpos+ax+self.device.width, self.ypos[l]), self.textbuffer[1][l], fill=self.fgcolor, font=self.ufont)
    self.device.display(self.dispimage)
    ax -= step
    if self.initialized==False:
     break
  self.clear_area((0,self.conty1),(self.width-1,self.conty2))
  for l in range(int(self.taskdevicepluginconfig[4])): # last position
     tpos = int((self.device.width-(draw.textsize(self.textbuffer[1][l],self.ufont)[0]))/2)-2
     if tpos<0:
      tpos = 0
     draw.text( (tpos, self.ypos[l]), self.textbuffer[1][l], fill=self.fgcolor, font=self.ufont)
  self.display_footer()

 def display_time(self):
  draw = ImageDraw.Draw(self.dispimage)
  cx = 28
  if self.width!=128: # correct x coords
    cx = int(cx * (self.width/128))
  cy = 10
  if self.height!=64: # correct y coords
    cy = int(cy * (self.height/64))
  self.clear_area((0,0),(cx,cy))
  draw.text( (0,0), datetime.now().strftime('%H:%M'), fill=self.fgcolor, font=self.hfont)
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
#  xw2 = 23
#  if self.width!=128: # correct x coords
#   xw2 = int(xw2 * (self.width/128))
  y = 0
  size_x = 15
  if self.width!=128: # correct x coords
    size_x = int(size_x * (self.width/128))
  x = self.device.width - size_x -1 # 105
  size_y = 10
  if self.height!=64: # correct y coords
    size_y = int(size_y * (self.height/64))
  nbars = 5
  width = int(size_x / nbars)
  size_x = width * nbars -1
  if self.lastwifistrength != nbars_filled:
   self.lastwifistrength = nbars_filled
   draw = ImageDraw.Draw(self.dispimage)
   self.clear_area((x,y),(x+size_x,y+size_y))
   if connected:
    for ibar in range(0,nbars):
     height = size_y * (ibar+1) / nbars
     xpos   = x + ibar * width
     ypos   = y + size_y - height
     if (ibar<=nbars_filled):
      draw.rectangle( ((xpos,ypos),(xpos+width-1,ypos+height)),fill=self.fgcolor)
     else:
      draw.rectangle( ((xpos,ypos),(xpos+width-1,ypos+1)),fill=self.fgcolor)
      draw.rectangle( ((xpos,y+size_y-1),(xpos+width-1,y+size_y)),fill=self.fgcolor)
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
  cx1 = 20
  cx2 = 108
  if self.width!=128: # correct x coords
    cx1 = int(cx1 * (self.width/128))
    cx2 = int(cx2 * (self.width/128))
  self.clear_area((cx1,self.conty2),(cx2,self.device.height))
  draw.text( (tpos, self.conty2), ft, fill=self.fgcolor, font=self.hfont)
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

  cx1 = 29
  cx2 = 106
  if self.width!=128: # correct x coords
    cx1 = int(cx1 * (self.width/128))
    cx2 = int(cx2 * (self.width/128))
  cy = 12
  if self.height!=64: # correct y coords
    cy = int(cy * (self.height/64))

  self.clear_area((cx1,0),(cx2,cy))
  tpos = int((self.device.width-(draw.textsize(tstr,self.hfont)[0]))/2)-2
  if tpos<0:
   tpos = 0
  draw.text( (tpos, 0), tstr, fill=self.fgcolor, font=self.hfont)

 def display_clear(self):
  draw = ImageDraw.Draw(self.dispimage)
  draw.rectangle( ((0,0),(self.device.width-1,self.device.height-1)),fill=self.fgcolor)
  self.device.display(self.dispimage)
  self.device.clear()
  if self.bgimg is not None:
   self.dispimage.paste(self.bgimg,(0,0))
  else:
   draw.rectangle( ((0,0),(self.device.width-1,self.device.height-1)),fill=self.bgcolor)
  self.device.display(self.dispimage)

 def clear_area(self, startpos, endpos, fill=None):
     if fill is None:
      fill = self.bgcolor
     if self.bgimg is None: #no background image, clear with single color
      draw = ImageDraw.Draw(self.dispimage)
      draw.rectangle( (startpos, endpos), fill=fill)
     else:
      try:
       region = self.bgimg.crop((startpos[0],startpos[1],endpos[0]+1,endpos[1]))
      except:
       region = self.bgimg.crop((startpos[0],startpos[1],endpos[0],endpos[1]))
      self.dispimage.paste(region,startpos)

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

 def p095_handler(self,channel=0):
   if self.taskdevicepin[0]>=0:
    try:
     btnval = int(gpios.HWPorts.input(int(self.taskdevicepin[0])))
     if btnval != self.btnval:
      self.btnval = btnval
      if btnval != self.initval: #btn pressed
       self.btntime = time.time()
      else: #returned to default state, measure time
       presstime = (time.time()-self.btntime)
       if presstime >= 1.5: #longpress
        if self.displaystate==1:
         self.displaystate = 0
         self.device.hide()
        else:
         self.displaystate = 1
         self.device.show()
       else: #shortpress
        self._lastdataservetime = rpieTime.millis()
        self.plugin_read()
    except:
     pass

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "tft":
   try:
    cmd = cmdarr[1].strip()
   except:
    cmd = ""
   try:
    if self.device is not None:
     if cmd == "txt":
      try:
       fc = self.oledparse(str(cmdarr[2]))
      except:
       fc = None
      if fc is not None:
       draw = ImageDraw.Draw(self.dispimage)
       sw = draw.textsize(fc,self.ufont)
       self.clear_area( (self.lastx, self.lasty), (self.lastx+sw[0], self.lasty+sw[1]), fill=self.tbgcolor )
       draw.text( (self.lastx,self.lasty), fc, fill=self.tfgcolor, font=self.ufont)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "txtfull":
      try:
       x = int(cmdarr[2])
       y = int(cmdarr[3])
      except:
       x = None
      bcol = self.tbgcolor
      col = self.tfgcolor
      fsize = -1
      text = ""
      if len(cmdarr)==5:
       text = str(cmdarr[4])
      if len(cmdarr)>5:
       try:
        fsize = int(cmdarr[4])
        self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', fsize)
       except:
        pass
      if len(cmdarr)>6:
       try:
        icol = str(cmdarr[5])
       except:
        icol = self.fgcolor
      if len(cmdarr)>7:
       try:
        bcol = str(cmdarr[6])
       except:
        bcol = self.fgcolor
      if len(cmdarr) in [5,6,7,8]:
       text = str(cmdarr[-1])
      if text != "":
       draw = ImageDraw.Draw(self.dispimage)
       sw = draw.textsize(text,self.ufont)
       self.clear_area( (x, y), (x+sw[0], y+sw[1]), fill=bcol )
       draw.text( (x,y), text, fill=icol, font=self.ufont)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "txp":
      try:
       px = int(cmdarr[2])
      except:
       px = 0
      try:
       py = int(cmdarr[3])
      except:
       py = 0
      self.lastx = px
      self.lasty = py
      res = True
     elif cmd == "txc":
      try:
       fc = str(cmdarr[2])
      except:
       fc = None
      try:
       bg = str(cmdarr[3])
      except:
       bg = self.bgcolor
      if fc is not None:
       self.tbgcolor = bg
       self.tfgcolor = fc
      res = True
     elif cmd == "txs":
      try:
       px = int(cmdarr[2])
      except:
       px = 8
      self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', px)
      res = True
     elif cmd == "l":
      try:
       x1 = int(cmdarr[2])
       y1 = int(cmdarr[3])
       x2 = int(cmdarr[4])
       y2 = int(cmdarr[5])
      except:
       x1 = None
      try:
       col = str(cmdarr[6])
      except:
       col = self.fgcolor
      if x1 is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.line( ((x1,y1),(x2,y2)), fill=col)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "r":
      try:
       x = int(cmdarr[2])
       y = int(cmdarr[3])
       w = int(cmdarr[4])
       h = int(cmdarr[5])
      except:
       x = None
      try:
       col = str(cmdarr[6])
      except:
       col = self.fgcolor
      if x is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.rectangle( ((x,y),(x+w,y+h)), outline= col)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "rf":
      try:
       x = int(cmdarr[2])
       y = int(cmdarr[3])
       w = int(cmdarr[4])
       h = int(cmdarr[5])
      except:
       x = None
      try:
       bcol = str(cmdarr[6])
      except:
       bcol = self.fgcolor
      try:
       icol = str(cmdarr[7])
      except:
       icol = self.fgcolor
      if x is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.rectangle( ((x,y),(x+w,y+h)), outline=bcol, fill= icol)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "c":
      try:
       x = int(cmdarr[2])
       y = int(cmdarr[3])
       r = int(cmdarr[4])
      except:
       x = None
      try:
       col = str(cmdarr[5])
      except:
       col = self.fgcolor
      if x is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.ellipse((x-r, y-r, x+r, y+r), outline= col)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "cf":
      try:
       x = int(cmdarr[2])
       y = int(cmdarr[3])
       r = int(cmdarr[4])
      except:
       x = None
      try:
       bcol = str(cmdarr[5])
      except:
       bcol = self.fgcolor
      try:
       icol = str(cmdarr[6])
      except:
       icol = self.fgcolor
      if x is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.ellipse((x-r, y-r, x+r, y+r), outline= bcol, fill= icol)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "t":
      try:
       x1 = int(cmdarr[2])
       y1 = int(cmdarr[3])
       x2 = int(cmdarr[4])
       y2 = int(cmdarr[5])
       x3 = int(cmdarr[6])
       y3 = int(cmdarr[7])
      except:
       x1 = None
      try:
       col = str(cmdarr[8])
      except:
       col = self.fgcolor
      if x1 is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.polygon( [(x1,y1), (x2,y2), (x3,y3)], outline=col)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "tf":
      try:
       x1 = int(cmdarr[2])
       y1 = int(cmdarr[3])
       x2 = int(cmdarr[4])
       y2 = int(cmdarr[5])
       x3 = int(cmdarr[6])
       y3 = int(cmdarr[7])
      except:
       x1 = None
      try:
       bcol = str(cmdarr[8])
      except:
       bcol = self.fgcolor
      try:
       icol = str(cmdarr[9])
      except:
       icol = self.fgcolor
      if x1 is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.polygon( [(x1,y1), (x2,y2), (x3,y3)], fill=icol, outline=bcol)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "px":
      try:
       x = int(cmdarr[2])
       y = int(cmdarr[3])
      except:
       x = None
      try:
       col = str(cmdarr[4])
      except:
       col = self.fgcolor
      if x is not None:
       draw = ImageDraw.Draw(self.dispimage)
       draw.point( (x,y), fill=col)
       self.device.display(self.dispimage)
      res = True
     elif cmd == "img":
      try:
       x = int(cmdarr[2])
       y = int(cmdarr[3])
      except:
       x = None
      try:
       fname = str(cmdarr[4])
      except:
       fname = ""
#      print(x,y,fname)#debug
      if x is not None:
        try:
         img = Image.open(fname,'r') # no path check!
        except Exception as e:
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Filename error: "+str(e))
         return False
        try:
         self.dispimage.paste(img,(x,y))
         self.device.display(self.dispimage)
         res = True
        except Exception as e:
         print(e)
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"TFT command error! "+str(e))
    res = False
  elif cmdarr[0] == "tftcmd":
   try:
    cmd = cmdarr[1].strip()
   except:
    cmd = ""
   try:
    if self.device is not None:
     if cmd == "on":
      try:
       if int(self.taskdevicepin[3])>-1:
        gpios.HWPorts.output(self.taskdevicepin[3],1)
      except:
        pass
      self.device.show()
      self.displaystate = 1
      res = True
     elif cmd == "off":
      self.device.hide()
      try:
       if int(self.taskdevicepin[3])>-1:
        gpios.HWPorts.output(self.taskdevicepin[3],0)
      except:
        pass
      self.displaystate = 0
      res = True
     elif cmd == "clear":
      try:
       scmd = cmdarr[2].strip()
      except:
       scmd = ""
      if scmd == "":
       self.display_clear()
      else:
        try:
         draw = ImageDraw.Draw(self.dispimage)
         draw.rectangle( ((0,0),(self.device.width-1,self.device.height-1)),fill=scmd)
         self.device.display(self.dispimage)
        except:
         pass
      res = True
     elif cmd == "rot":
      try:
       scmd = int(cmdarr[2])
      except:
       scmd = -1
      if scmd >= 0 and scmd < 4:
       self.taskdevicepluginconfig[2] = scmd
       self.plugin_init()
      res = True
     elif cmd == "scroll":
      self._lastdataservetime = rpieTime.millis()
      self.plugin_read()
      res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"TFT command error! "+str(e))
    res = False
  return res

 def oledparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(ostr)
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
