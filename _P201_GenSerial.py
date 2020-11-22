#!/usr/bin/env python3
#############################################################################
################## Generic Serial Comm plugin for RPIEasy ###################
#############################################################################
#
# Serial plugin based on PySerial
#
# Available commands:
#  serialwrite,<value>       - <value> can be a simple string or multiple bytes represented in hexadecimal started by a single 0x
#
# Examples:
#  serialwrite,0xFF01            - sends two bytes (written in hexadecimal form): 255,1
#  serialwrite,0x1045AA          - sends three bytes (written in hexadecimal form): 16,69,170
#  serialwrite,this is a message - sends a simple string "this is a message"
#  serialwriteln,this is a message - sends a simple string "this is a message\n"
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
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

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 201
 PLUGIN_NAME = "Communication - Serial (TESTING)"
 PLUGIN_VALUENAME1 = "Data"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_SER
   self.vtype = rpieGlobals.SENSOR_TYPE_TEXT
   self.readinprogress = 0
   self.valuecount = 1
   self.senddataoption = True
   self.timeroption = False
   self.timeroptional = False
   self.formulaoption = False
   self.bsize = 8
   self.sbit  = 1
   self.baud  = 0
   self.bgproc = None
   self.serdev = None
   self.timeout = 0.001
   self.maxexpecteddata = 512

 def calctimeout(self):
  try:
   self.baud = int(self.taskdevicepluginconfig[1])
   if self.baud<50:
    self.baud = 50
  except:
   self.baud = 50
  if self.maxexpecteddata>4096:# Linux serial buffer is fixed max 4096 bytes
   self.maxexpecteddata=4096
  if self.maxexpecteddata<1:
   self.maxexpecteddata=1
  self.timeout = (self.bsize+self.sbit)*self.maxexpecteddata/self.baud

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  try:
   if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="" and self.baud != 0:
#    self.serdev = None
    self.initialized = False
    if self.enabled:
     self.calctimeout()
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Try to init serial "+str(self.taskdevicepluginconfig[0])+" speed "+str(self.baud))
     self.connect()
     if self.initialized:
      pn = self.taskdevicepluginconfig[0].split("/")
      self.ports = str(pn[-1])
      self.bgproc = threading.Thread(target=self.bgreceiver)
      self.bgproc.daemon = True
      self.bgproc.start()
    else:
     self.baud = 0
     self.ports = 0
     try:
      self.serdev.close() # close in case if already opened by ourself
     except:
      pass
  except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = rpiSerial.serial_portlist()
  if len(options)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p201_addr",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
   webserver.addFormNote("For RPI use 'raspi-config' tool: 5- Interfacing Options-P6 Serial- (Kernel logging disabled + serial port hardware enabled) before enable this plugin")
   webserver.addFormNumericBox("Baudrate","p201_spd",self.taskdevicepluginconfig[1],50,4000000)
   webserver.addFormNote("Generic values: 9600, 19200, 38400, 57600, 115200")
   choice2 = self.taskdevicepluginconfig[2]
   options = ["5","6","7","8"]
   optionvalues = [rpiSerial.FIVEBITS,rpiSerial.SIXBITS,rpiSerial.SEVENBITS,rpiSerial.EIGHTBITS]
   webserver.addFormSelector("Bytesize","p201_bsize",len(optionvalues),options,optionvalues,None,int(choice2))
   webserver.addFormNote("Most common setting is 8")
   choice3 = self.taskdevicepluginconfig[3]
   options = ["None","Even","Odd","Mark","Space"]
   optionvalues = [rpiSerial.PARITY_NONE,rpiSerial.PARITY_EVEN,rpiSerial.PARITY_ODD,rpiSerial.PARITY_MARK,rpiSerial.PARITY_SPACE]
   webserver.addHtml("<tr><td>Parity:<td>")
   webserver.addSelector_Head("p201_par",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],optionvalues[o],(str(optionvalues[o])==str(choice3)),False)
   webserver.addSelector_Foot()
   webserver.addFormNote("Most common setting is None")
   choice4 = self.taskdevicepluginconfig[4]
   options = ["1","2"]
   optionvalues = [rpiSerial.STOPBITS_ONE,rpiSerial.STOPBITS_TWO]
   webserver.addFormSelector("Stopbits","p201_sbit",len(optionvalues),options,optionvalues,None,float(choice4))
   webserver.addFormNote("Most common setting is 1")
   webserver.addFormNumericBox("Expected max packet size","p201_pkt",self.taskdevicepluginconfig[5],1,4096) # Linux serial buffer is fixed max 4096 bytes
   webserver.addUnit("byte")
   choice6 = self.taskdevicepluginconfig[6]
   options = ["Hex values","String"]
   optionvalues = [0,1]
   webserver.addFormSelector("Data format","p201_fmt",len(optionvalues),options,optionvalues,None,int(choice6))
  else:
   webserver.addFormNote("No serial ports found")
  return True

 def webform_save(self,params):
  par = webserver.arg("p201_addr",params)
  self.taskdevicepluginconfig[0] = str(par)
  try: 
   baud = webserver.arg("p201_spd",params)
   self.taskdevicepluginconfig[1] = int(baud)
  except:
   self.taskdevicepluginconfig[1] = 50
  try:
   par = webserver.arg("p201_bsize",params)
   self.bsize = int(par)
   self.taskdevicepluginconfig[2] = self.bsize
   par = webserver.arg("p201_par",params)
   self.taskdevicepluginconfig[3] = str(par)
   par = webserver.arg("p201_sbit",params)
   self.sbit = int(par)
   self.taskdevicepluginconfig[4] = self.sbit
   par = webserver.arg("p201_pkt",params)
   self.maxexpecteddata = int(par)
   self.taskdevicepluginconfig[5] = self.maxexpecteddata
   par = webserver.arg("p201_fmt",params)
   self.taskdevicepluginconfig[6] = int(par)
  except:
   self.bsize = 8
   self.sbit  = 1
   self.maxexpecteddata = 512
  self.calctimeout()
  self.plugin_init()
  return True
  
 def convert(self,inbuf):
  res = ""
  if len(inbuf)>0:
   ttipus = int(self.taskdevicepluginconfig[6])
   if ttipus==1: # string requested
    try:
     if len(inbuf)==1:
       if type(inbuf) is bytes:
        res += inbuf.decode("utf-8", errors="ignore")
       else:
        res += str(inbuf)
     else:
      for s in range(len(inbuf)):
       if type(inbuf[s]) is bytes:
        res += inbuf[s].decode("utf-8", errors="ignore")
       else:
        res += str(inbuf[s])
    except Exception as e:
     pass
    res = res.strip().replace("[b'","").replace("']","")
#    if len(res.strip())<1: # change to hex if not string?
#     ttipus = 0
   if ttipus ==0: # hexstring requested
    for s in range(len(inbuf)):
     if type(inbuf[s]) is bytes:
       try:
        res += "0x"+str(inbuf[s].hex())
       except:
        res += str(inbuf[s])
     elif len(inbuf[s])>0:
      for t in range(len(inbuf[s])):
       try:
        res += "0x"+str(inbuf[s].hex())
       except:
        res += str(inbuf[s])
  return res 

 def connect(self):
    try:
     self.serdev.close() # close in case if already opened by ourself
    except:
     pass
    try:
     self.serdev = rpiSerial.SerialPort(self.taskdevicepluginconfig[0],self.baud,ptimeout=self.timeout,pbytesize=self.bsize,pstopbits=self.sbit)
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
   recdata = []
   while self.enabled:
    if self.serdev is not None:
#     tt = rpieTime.millis()
     try:
      while self.serdev.available()>0:
       reading = self.serdev.readline()
       recdata.append(reading)
      if len(recdata)>0:
       rstr = self.convert(recdata).strip()
       if len(rstr)>0 and rstr != "" and rstr != "0x":
#       print(rpieTime.millis()-tt)
        self.set_value(1,rstr,True)
       recdata = []
       reading = []
      else:
       time.sleep(0.001)
     except Exception as e:
      time.sleep(0.5)
#      self.connect()
   try:
     self.serdev.close()
   except:
     pass

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "serialwrite" or cmdarr[0] == "serialwriteln":
   res = True
   sepp = cmd.find(',')
   text = cmd[sepp+1:]
   sbuf = []
   if text[:2]=="0x":
    text = text[2:]
    try:
     text = ''.join( text.split(" ") )
     for i in range(0, len(text), 2):
       sbuf.append( int (text[i:i+2], 16 ) )
    except Exception as e:
#     print(i,e)
     sbuf = str(text)
   else:
    sbuf = str(text)
   if cmdarr[0] == "serialwriteln":
    sbuf += "\n"
   if self.serdev is not None:
    try:
     self.serdev.write(sbuf)
    except Exception as e:
     pass
  return res
