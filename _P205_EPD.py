#!/usr/bin/env python3
#############################################################################
########################## EPD plugin for RPIEasy ###########################
#############################################################################
#
# Available commands:
#  EPDCMD,<value>          - value can be: on, off, clear, low, med, high
#  EPDCMD,clearline,<row>  - clears selected <row>
#  EPDTEXT,<row>,<col>,<text>  - write text message to OLED screen at the requested position
#
# Used library and supported models:
#  https://pypi.org/project/epd-library/
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import commands
from PIL import ImageFont, ImageDraw, Image
import threading

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 205
 PLUGIN_NAME = "Display - EPD E-paper (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "EPD"
 P205_Nlines = 8

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
  self.epdbase = None
  self.device = None
  self.width  = None
  self.height = None
  self.lines  = []
  self.ufont  = None
  self.lineheight = 11
  self.charwidth   = 8
  self.dispimage = None
  self.redframe  = None
  self.partialupdate = False
  self.setframe = False
  self.initprogress = False
  self.readinprogress = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.enabled or enableplugin:
    try:
     if self.initprogress==True:
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"EPD init already in progress!")
      return False
    except:
     pass
    self.initprogress = True
    self.initialized = False
#    self.device = None
#    self.epdbase = None
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Start EPD background init")
    bgt = threading.Thread(target=self.display_init)
    bgt.daemon = False
    bgt.start()
  else:
   self.initialized = False
   self.initprogress = False

 def display_init(self):
#    try:
#     if self.device is not None:
#      self.device.digital_read(self.device.busy_pin)
#      self.initialized = True
#      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EPD already initialized")
#    except:
#     self.initialized = False
    self.readinprogress = False
    if str(self.taskdevicepluginconfig[0]) != "0" and str(self.taskdevicepluginconfig[0]).strip() != "": # display type
     try:
      if str(self.taskdevicepluginconfig[0])=="154":
       import epd1in54
       self.epdbase = epd1in54
       self.redframe = None
      elif str(self.taskdevicepluginconfig[0])=="154b":
       import epd1in54b
       self.epdbase = epd1in54b
       self.redframe = True
      elif str(self.taskdevicepluginconfig[0])=="154c":
       import epd1in54c
       self.epdbase = epd1in54c
       self.redframe = True
      elif str(self.taskdevicepluginconfig[0])=="213":
       import epd2in13
       self.epdbase = epd2in13
       self.redframe = None
      elif str(self.taskdevicepluginconfig[0])=="213b":
       import epd2in13b
       self.epdbase = epd2in13b
       self.redframe = True
      elif str(self.taskdevicepluginconfig[0])=="270":
       import epd2in7
       self.epdbase = epd2in7
       self.redframe = None
      elif str(self.taskdevicepluginconfig[0])=="270b":
       import epd2in7b
       self.epdbase = epd2in7b
       self.redframe = True
      elif str(self.taskdevicepluginconfig[0])=="290":
       import epd2in9
       self.epdbase = epd2in9
       self.redframe = None
      elif str(self.taskdevicepluginconfig[0])=="290b":
       import epd2in9b
       self.epdbase = epd2in9b
       self.redframe = True
      elif str(self.taskdevicepluginconfig[0])=="420":
       import epd4in2
       self.epdbase = epd4in2
       self.redframe = None
      elif str(self.taskdevicepluginconfig[0])=="420b":
       import epd4in2b
       self.epdbase = epd4in2b
       self.redframe = True
      elif str(self.taskdevicepluginconfig[0])=="750":
       import epd7in5
       self.epdbase = epd7in5
       self.redframe = None
      elif str(self.taskdevicepluginconfig[0])=="750b":
       import epd7in5b
       self.epdbase = epd7in5b
       self.redframe = True
      else:
       self.epdbase = None
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EPD type unknown! "+str(e))
      self.enabled = False
      self.device = None
      self.initialized = False
      self.epdbase = None
      self.initprogress = False
      return False
    if self.epdbase is not None:
     try:
#      if self.initialized==False:
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Start EPD init")
      self.device = self.epdbase.EPD()
      self.width = self.epdbase.EPD_WIDTH
      self.height = self.epdbase.EPD_HEIGHT
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EPD device preinit")
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EPD can not be initialized! "+str(e))
      self.enabled = False
      self.device = None
      self.initialized = False
      self.initprogress = False
      return False
     try:
      if self.device.lut_partial_update:
       pass
      self.partialupdate = True
     except:
      self.partialupdate = False
     try:
      lc = int(self.taskdevicepluginconfig[4])
     except:
      lc = self.P205_Nlines
     if lc < 1:
      lc = self.P205_Nlines
     try:
      lineheight = int(self.height / lc) #  lineheight = int(self.device.height / lc)+1
     except:
      lineheight = 8
     self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', lineheight)
     try:
      #self.device.init(self.device.lut_full_update)
      if self.redframe is None:
       if self.partialupdate:
        self.device.init(self.device.lut_partial_update)
       else:
        self.device.init()
      self.dispimage = Image.new('1', (self.width,self.height), 255)
      try:
       self.device.set_frame_memory(self.dispimage,0,0)
       self.setframe = True
      except:
       self.setframe = False
      if self.redframe is not None:
       self.redframe = self.dispimage
      draw = ImageDraw.Draw(self.dispimage)
#      self.device.clear_frame_memory(0xFF) # float object error?
      if self.redframe is None and self.setframe:
       self.device.set_frame_memory(self.dispimage,0,0)
      if self.redframe is not None:
       self.device.display_frame(self.device.get_frame_buffer(self.dispimage),None)
      else:
       if self.setframe:
        self.device.display_frame()
       else:
        self.device.display_frame(self.device.get_frame_buffer(self.dispimage))
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EPD init error: "+str(e))
      self.initialized = False
      self.initprogress = False
      return False
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EPD background drawed")
     if draw:
      maxcols = int(self.taskdevicepluginconfig[5])
      if maxcols < 1:
       maxcols = 1
      tstr = "X"*maxcols
      try:
       if int(self.taskdevicepluginconfig[2]) in [1,3]: # width correction for initial char size detection
        tv = self.width
        self.width = self.height
        self.height = tv
        self.dispimage = Image.new('1', (self.width,self.height), 255)
        draw = ImageDraw.Draw(self.dispimage)
      except:
       pass
      try:
       sw = draw.textsize(tstr,self.ufont)[0]
      except:
       sw = self.width
      while (sw>self.width):
       lineheight-=1
       self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', lineheight)
       sw = draw.textsize(tstr,self.ufont)[0]
      self.charwidth, self.lineheight = draw.textsize("X",self.ufont)
      if lc in [2,4,6,8]:
       self.lineheight += 1
      try:
       if int(self.taskdevicepluginconfig[2]) in [1,3]: # reverse width correction for initial char size detection
        tv = self.width
        self.width = self.height
        self.height = tv
        self.dispimage = Image.new('1', (self.width,self.height), 255)
      except:
       pass
     if self.interval>2:
       nextr = self.interval-2
     else:
       nextr = 0
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
     self.initialized = True
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"EPD device ready")
     if self.interval != 0:
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Starting first EPD data display")
      self.plugin_read()
    else:
     self.initialized = False
    self.initprogress = False

 def webform_load(self): # create html page for settings
  choice1 = str(self.taskdevicepluginconfig[0]) # store display type
  options = ['1.54" (200x200)','1.54"B (200x200)','1.54"C (150x150)','2.13" (250x122)','2.13"B (212x104)','2.7" (264x176)','2.7"B (264x176)','2.9" (296x128)','2.9"B (296x128)','4.2" (400x300)','4.2"B (400x300)','7.5" (800x480)','7.5"B (800x480)']
  optionvalues = ["154","154b","154c","213","213b","270","270b","290","290b","420","420b","750","750b"]
  webserver.addHtml("<tr><td>Display type:<td>")
  webserver.addSelector_Head("p205_type",False)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],optionvalues[d],(str(choice1)==str(optionvalues[d])),False)
  webserver.addSelector_Foot()
  webserver.addFormNote("Enable <a href='pinout'>SPI-0</a> first!")
  webserver.addFormNote("Hardware connection (OLED => Raspberry Pi)<br>VCC->3.3V, GND->GND, SDI->MOSI, SCLK->SCLK, CS-> GPIO8/CE0, D/C->GPIO25 (out), RES->GPIO17 (out), BUSY->GPIO24 (in)")

  choice3 = int(float(self.taskdevicepluginconfig[2])) # store rotation state
  options =      ["Normal","Rotate by 90","Rotate by 180","Rotate by 270"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Mode","p205_rotate",len(optionvalues),options,optionvalues,None,choice3)

  choice5 = int(float(self.taskdevicepluginconfig[4])) # store line count
  webserver.addHtml("<tr><td>Number of lines:<td>")
  webserver.addSelector_Head("p205_linecount",False)
  for l in range(1,self.P205_Nlines+1):
   webserver.addSelector_Item(str(l),l,(l==choice5),False)
  webserver.addSelector_Foot()
  webserver.addFormNumericBox("Try to display # characters per row","p205_charperl",self.taskdevicepluginconfig[5],1,32)
  webserver.addFormNote("Leave it '1' if you do not care")
  webserver.addFormCheckBox("Clear only used lines","p205_partialclear",self.taskdevicepluginconfig[6])
  if choice5 > 0 and choice5<9:
   lc = choice5
  else:
   lc = self.P205_Nlines
  for l in range(lc):
   try:
    linestr = self.lines[l]
   except:
    linestr = ""
   webserver.addFormTextBox("Line"+str(l+1),"p205_template"+str(l),linestr,128)

  return True

 def plugin_exit(self):
   self.initialized = False
   self.initprogress = False

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p205_type",params)
   self.taskdevicepluginconfig[0] = str(par)

   par = webserver.arg("p205_rotate",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[2] = int(par)

   par = webserver.arg("p205_linecount",params)
   if par == "":
    par = 8
   self.taskdevicepluginconfig[4] = int(par)

   par = webserver.arg("p205_charperl",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[5] = int(par)

   if (webserver.arg("p205_partialclear",params)=="on"):
    self.taskdevicepluginconfig[6] = True
   else:
    self.taskdevicepluginconfig[6] = False

   for l in range(self.P205_Nlines):
    linestr = webserver.arg("p205_template"+str(l),params).strip()
#    if linestr!="" and linestr!="0":
    try:
      self.lines[l]=linestr
    except:
      self.lines.append(linestr)
   self.plugin_init()
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  if self.initialized and self.enabled and self.device is not None:
   if self.readinprogress == False:
     self.readinprogress = True
     try:
      if self.taskdevicepluginconfig[6] == False:
       self.dispimage = Image.new('1', (self.width,self.height), 255)
      if self.dispimage:
       draw = ImageDraw.Draw(self.dispimage)
       for l in range(int(self.taskdevicepluginconfig[4])):
        resstr = ""
        try:
         linestr=str(self.lines[l])
         resstr=self.epdparse(linestr)
        except:
         resstr=""
        if resstr != "":
         y = (l*self.lineheight)
         if self.taskdevicepluginconfig[6]:
          draw.rectangle( ((0,y+2), (self.device.width,y+self.lineheight)), fill=255)
         draw.text( (0,y), resstr, font=self.ufont, fill=0)
         self.dodisplay()
     except Exception as e:
      if self.initialized:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EPD write error! "+str(e))
     self._lastdataservetime = rpieTime.millis()
     self.readinprogress = False
  return True

 def dodisplay(self):
  if self.initialized and self.device is not None:
      try:
       if self.taskdevicepluginconfig[2] == 0:
        dimage = self.dispimage
       elif self.taskdevicepluginconfig[2] == 1:
        dimage = self.dispimage.rotate(90,expand=True, fillcolor=0)
       elif self.taskdevicepluginconfig[2] == 2:
        dimage = self.dispimage.rotate(180,expand=True, fillcolor=0)
       elif self.taskdevicepluginconfig[2] == 3:
        dimage = self.dispimage.rotate(270,expand=True, fillcolor=0)
       else:
        misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Invalid rotation!")
        return False
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PIL rotate error! "+str(e))
      try:
       if self.redframe is None and self.setframe:
        self.device.set_frame_memory(dimage,0,0)
       if self.redframe is not None:
        self.device.display_frame(self.device.get_frame_buffer(dimage),None)
       else:
        if self.setframe:
         self.device.display_frame()
        else:
         self.device.display_frame(self.device.get_frame_buffer(dimage))
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EPD display error! "+str(e))

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0][:3] != "epd" or self.initialized==False:
   return False
  if cmdarr[0] == "epdcmd":
   try:
    cmd = cmdarr[1].strip()
   except:
    cmd = ""
   try:
    if self.device is not None:
     if cmd == "clear":
      self.device.init(self.device.lut_full_update)
      self.dispimage = Image.new('1', (self.width,self.height), 255)
      if self.redframe is None and self.setframe:
       self.device.set_frame_memory(self.dispimage,0,0)
      if self.redframe is not None:
       self.device.display_frame(self.device.get_frame_buffer(self.dispimage),None)
      else:
       if self.setframe:
        self.device.display_frame()
       else:
        self.device.display_frame(self.device.get_frame_buffer(self.dispimage))
      if self.partialupdate:
        self.device.init(self.device.lut_partial_update)
      else:
        self.device.init()
      res = True
     elif cmd == "clearline":
      try:
       l = int(cmdarr[2].strip())
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
       return False
      if self.device is not None and self.dispimage is not None:
        if l>0:
         l-=1
        draw = ImageDraw.Draw(self.dispimage)
        y = (l*self.lineheight)
        draw.rectangle( ((0,y+2), (self.device.width,y+self.lineheight)), fill=255)
        self.dodisplay()
      res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EPD command error! "+str(e))
    res = False
  elif cmdarr[0] == "epdline":
      try:
       x1 = int(cmdarr[1].strip())
       y1 = int(cmdarr[2].strip())
       x2 = int(cmdarr[3].strip())
       y2 = int(cmdarr[4].strip())
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
       return False
      if self.device is not None and self.dispimage is not None:
        draw = ImageDraw.Draw(self.dispimage)
        draw.line( ((x1,y1), (x2,y2)), fill=0)
        self.dodisplay()
      res = True
  elif cmdarr[0] == "epdrect":
      try:
       x1 = int(cmdarr[1].strip())
       y1 = int(cmdarr[2].strip())
       x2 = int(cmdarr[3].strip())
       y2 = int(cmdarr[4].strip())
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
       return False
      fillcolor = 0
      try:
       fillcolor = int(cmdarr[5])
      except:
       pass
      if self.device is not None and self.dispimage is not None:
        draw = ImageDraw.Draw(self.dispimage)
        draw.rectangle( ((x1,y1), (x2,y2)), fill=fillcolor)
        self.dodisplay()
      res = True
  elif cmdarr[0] == "epdimg":
      try:
       x1 = int(cmdarr[1].strip())
       y1 = int(cmdarr[2].strip())
       fname = cmdarr[3].strip()
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
       return False
      if self.device is not None and self.dispimage is not None:
        try:
         img = Image.open(fname,'r') # no path check!
        except Exception as e:
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Filename error: "+str(e))
         return False
        self.dispimage.paste(img,(x1,y1))
        self.dodisplay()
      res = True
  elif cmdarr[0] == "epdtext":
   sepp = len(cmdarr[0])+len(cmdarr[1])+len(cmdarr[2])+1
   sepp = cmd.find(',',sepp)
   try:
    y = int(cmdarr[1].strip())
    x = int(cmdarr[2].strip())
    text = cmd[sepp+1:]
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
    return False
   if x>0:
    x -= 1
   if y>0:
    y -= 1
   try:
    if self.device is not None:
      draw = ImageDraw.Draw(self.dispimage)
      resstr = self.epdparse(text)
      draw.text( ((x*self.charwidth),(y*self.lineheight)), resstr, fill=0, font=self.ufont)
      self.dodisplay()
      res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"OLED command error! "+str(e))
    res = False
  return res

 def epdparse(self,ostr):
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
