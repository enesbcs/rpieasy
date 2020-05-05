#!/usr/bin/env python3
#############################################################################
################ Helper Library for FTDI GPIO handling ######################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import Settings
import os
import time
try:
 from pyftdi.ftdi import Ftdi
 from pyftdi.usbtools import UsbTools
 from pyftdi.gpio import GpioAsyncController
 from pyftdi.gpio import GpioMpsseController
 from pyftdi.i2c import I2cController
 from pyftdi.spi import SpiController
except:
 print("pyFTDI not installed!")

import webserver
import threading
import misc
import rpieGlobals

PINOUT = [
{"ID":0,
"BCM":-1,
"realpin":-1,
"name":["None"],
"canchange":2,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,
"ftdevice":"",
"ftdevtype":""
}
]

BOTH    = 3
RISING  = 1
FALLING = 2
IN      = 0
OUT     = 1
SPI     = 3
I2C     = 4
UNKNOWN = 5
LOW     = 0
HIGH    = 1

def set_bit(v, index, x):
  """Set the index:th bit of v to 1 if x is truthy, else to 0, and return the new value."""
  if x<0:
   x=0
  mask = 1 << index   # Compute mask, an integer with just bit 'index' set.
  v &= ~mask          # Clear the bit indicated by the mask (if x is False)
  if x:
    v |= mask         # If x was True, set the bit indicated by the mask.
  return v

def is_serialnumber(devname):
    ser = False
    u1 = devname.split("/")
    for i in range(len(u1)):
        parts = u1[i].count(":")
        if parts>1:
         if parts == 2:
          ser = True
          break
    return ser

def get_ftdi_devices(rtype=0):
 try:
  devs = Ftdi.list_devices()
 except:
  devs = []
 if rtype==0:
  return len(devs)
 elif rtype==1:
  return devs
 elif rtype==2:
  try:
   res = UsbTools.build_dev_strings(Ftdi.SCHEME,Ftdi.VENDOR_IDS,Ftdi.PRODUCT_IDS,devs)
  except:
   res = []
#  res.append( ('ftdi://ftdi:232h:3:9/1', '(Single RS232-HS)') ) # debug
#  res.append( ('ftdi://ftdi:232h:3:9/2', '(Single RS232-HS)') ) # debug
  res = sorted(res)
  return res

def get_ftdi_configured_devices():
  devs = []
  for p in range(len(Settings.Pinout)):
   try:
    if not(Settings.Pinout[p]["ftdevice"] in devs):
     if Settings.Pinout[p]["ftdevice"].strip()!="":
      devs.append(Settings.Pinout[p]["ftdevice"])
   except:
    pass
  return devs

def get_ftdi_pinnames(pinnum,portindex=1,ismpsse=True):
   res = str(pinnum)
   if pinnum==0:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D0/UART-TX/SPI-CLK/I2C-SCL"
    else:
     res += "D0-TX/UART-TX"
   elif pinnum==1:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D1/UART-RX/SPI-MOSI/I2C-SDAo"
    else:
     res += "D1-RX/UART-RX"
   elif pinnum==2:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D2/UART-RTS/SPI-MISO/I2C-SDAi"
    else:
     res += "D2-RTS/UART-RTS"
   elif pinnum==3:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D3/UART-CTS/SPI-CE0"
    else:
     res += "D3-CTS/UART-CTS"
   elif pinnum==4:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D4/UART-DTR/SPI-CE1"
    else:
     res += "D4-DTR/UART-DTR"
   elif pinnum==5:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D5/UART-DSR/SPI-CE2"
    else:
     res += "D5-DSR/UART-DSR"
   elif pinnum==6:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D6/UART-DCD/SPI-CE3"
    else:
     res += "D6-DCD/UART-DCD"
   elif pinnum==7:
    res = chr(ord("A")+int(portindex-1))
    if ismpsse and portindex<3:
     res += "D7/UART-RI/SPI-CE4"
    else:
     res += "D7-RI/UART-RI"
   elif pinnum>7 and pinnum<16:
    res = chr(ord("A")+int(portindex-1))
    res += "C"+str(pinnum-8)
   bres = res.split("/")
   return bres

class FTDIGPIO:

 def __init__(self,GpioController,frequency=100000):
  self.gpioready = False
  try:
   self.GPIO = GpioController
   self._maxgpio = self.GPIO.width
   self.gpioready = True
  except:
   self.GPIO = None
   self.gpioready = False
  self._pinvalues      = []
  self._events         = []
  self._eventtypes     = []
  self._lastread       = 0
  self._available_pins = []
  self._pinmodes       = []
  self._readinprogress = False
  self._eventthread    = None
  self._firstin        = 0
  self._lastin         = 0
  self._writecache     = 0
  self.timeout = (1/frequency)
  for p in range(0,self._maxgpio):
   self._pinvalues.append(-1)
   self._events.append(None)
   self._eventtypes.append(-1)
  self._useable_gpio = 0
  if self.gpioready:
   allp  = self.GPIO.all_pins
   for p in range(0,self._maxgpio):
     if (allp & (1<<p))!=0:
      self._useable_gpio+=1
   self._detectpins()

 def _detectpins(self):
  self._available_pins = []
  self._pinmodes       = []
  if self.gpioready:
   allp  = self.GPIO.all_pins
#   print("det all pins:",allp)
   confp = self.GPIO.pins
#   print("det conf pins:",confp)
   dirp  = self.GPIO.direction
#   print("det direction state: ",dirp)
   for p in range(0,self._maxgpio):
    if (allp & (1<<p))==0:
     self._available_pins.append(0)
     rp = self._maxgpio-self._useable_gpio
     if rp in [2,3]:
      self._pinmodes.append(I2C) #i2c
     elif rp>3:
      self._pinmodes.append(SPI) #spi
    else:
     self._available_pins.append(1)
     if (confp & (1<<p))==0:
      self._pinmodes.append(UNKNOWN) # not configured
     else:
      if (dirp & (1<<p))==0:
       self._pinmodes.append(IN)
      else:
       self._pinmodes.append(OUT)
   for p in range(0,self._maxgpio):
    if self._pinmodes[p]==IN: # input
     self._firstin = p
     break
   for p in reversed(range(self._maxgpio)):
    if self._pinmodes[p]==IN: # input
     self._lastin = p+1
     break
#   print(self._pinmodes)#debug

 def setmode(self,mode): # no real function, BOARD is the only mode
    self._detectpins()

 def setwarnings(self,mode):  # no real function, BOARD is the only mode
    pass

 def setup(self,channel,mode,initial=None, pull_up_down=True): # every input is input pullup!
    dirb = self.GPIO.direction
    pinb = self.GPIO.pins
    if type(channel) is list: # multiple channels
     for c in channel:
      dirb = set_bit(dirb,int(c),mode)
      pinb |= (1 << int(c))
    else: # single channel
     dirb = set_bit(dirb,int(channel),mode)
     pinb |= (1 << int(channel))
    try:
     self.GPIO.set_direction(pinb,dirb)
     res = True
    except Exception as e:
     res = False
    self._detectpins()
    if res and (not (initial is None)) and mode==OUT:
     self.output(channel,initial)
    return res

 def _readallpins(self):
    if self._readinprogress == False:
     self._readinprogress = True
     if time.time()-self._lastread>self.timeout:
      try:
       pv = self.GPIO.read()
       if type(pv) is tuple:
        pv = pv[0]
       elif type(pv) is list:
        pv = pv[0]
       pv = int(pv)
#       print(pv,self._firstin,self._lastin)
       for p in range(self._firstin,self._lastin):
        if self._pinmodes[p]==IN: # input
         if ( (pv & (1<<p)) != 0):
          self._pinvalues[p] = HIGH
         else:
          self._pinvalues[p] = LOW
      except Exception as e:
       pass
      self._lastread = time.time()
     self._readinprogress = False

 def input(self, channel):
     res = -1
     self._readallpins()
     if type(channel) is list: # multiple channels
      res = []
      for c in channel:
       res.append(self._pinvalues[c])
     else:
      res = self._pinvalues[channel]
     return res

 def output(self, channel, state,doupdate=True):
    try:
     if type(channel) is list: # multiple channels
      for c in channel:
       self._writecache = set_bit(self._writecache,int(c),state)
     else:
      self._writecache = set_bit(self._writecache,int(channel),state)
#     print(self.GPIO.pins,self.GPIO.direction,self._writecache)#debug
    except:
     pass
    try:
      self.GPIO.write(int(self._writecache))
    except Exception as e:
      pass
    if doupdate:
     try:
      if type(channel) is list: # multiple channels
       for c in channel:
        self._pinvalues[c] = state
      else:
       self._pinvalues[channel] = state
     except:
      pass

 def add_event_detect(self, channel, mode=BOTH, callback=None, bouncetime=0):
  if self._pinmodes[channel]!=IN: # not input
   return False
  try:
   self._events[channel] = callback
   self._eventtypes[channel] = mode
   res=True
  except:
   res=False
#  print("register",self._events,self._eventtypes)#debug
  if self._eventthread is None:
   self._eventthread = threading.Thread(target=self.bgthread)
   self._eventthread.daemon = True
   self._eventthread.start()
#   print("started")
  return res

 def remove_event_detect(self,channel):
  try:
   self._events[channel] = None
   return True
  except:
   return False

 def bgthread(self):
   while self.gpioready:
    pp = self._pinvalues
    self._readallpins()
    for p in range(self._firstin,self._lastin):
     if not(self._events[p] is None):
       runit = False
       if self._eventtypes[p]==RISING:
         if pp[p] < self._pinvalues[p]:
          runit = True
       elif self._eventtypes[p]==FALLING:
         if pp[p] > self._pinvalues[p]:
          runit = True
       elif self._eventtypes[p]==BOTH:
          runit = True
#       if pp[p]!=self._pinvalues[p]:
#        print(pp,self._pinvalues)#debug
#        print(runit)
       if runit:
        try:
         self._events[p](p)
        except:
         pass
    time.sleep(self.timeout)

 def gpio_function(self,pin):
  try:
   return self._pinmodes[pin]
  except:
   return -1 #unknown?

 def cleanup(self):
   self.gpioready = False
   try:
    for p in range(self._firstin,self._lastin):
     self.remove_event_detect(p)
   except:
    pass
   try:
    self.GPIO.close()
   except:
    pass

class SoftPwm(threading.Thread):
  def __init__(self, gpio, frequency, gpioPin):
     self.baseTime = 1.0 / frequency
     self.maxCycle = 100.0
     self.sliceTime = self.baseTime / self.maxCycle
     self.gpioPin = gpioPin
     self.terminated = False
     self.toTerminate = False
     self.thread = None
     self.gpio = gpio

  def start(self, dutyCycle):
    """
    Start PWM output. Expected parameter is :
    - dutyCycle : percentage of a single pattern to set HIGH output on the GPIO pin
    
    Example : with a frequency of 1 Hz, and a duty cycle set to 25, GPIO pin will 
    stay HIGH for 1*(25/100) seconds on HIGH output, and 1*(75/100) seconds on LOW output.
    """
    if self.gpio is None:
     return False
    if self.thread is not None:
     self.stop()
     self.toTerminate = False
     self.terminated = False
    self.dutyCycle = dutyCycle
    self.thread = threading.Thread(None, self.run, None, (), {})
    self.thread.start()

  def run(self):
    """
    Run the PWM pattern into a background thread. This function should not be called outside of this class.
    """
    while self.toTerminate == False:
      if self.dutyCycle > 0:
        self.gpio.output(self.gpioPin, HIGH)
        time.sleep(self.dutyCycle * self.sliceTime)
      if self.dutyCycle < self.maxCycle:
        self.gpio.output(self.gpioPin, LOW)
        time.sleep((self.maxCycle - self.dutyCycle) * self.sliceTime)
    self.terminated = True

  def changeDutyCycle(self, dutyCycle):
    """
    Change the duration of HIGH output of the pattern. Expected parameter is :
    - dutyCycle : percentage of a single pattern to set HIGH output on the GPIO pin
    
    Example : with a frequency of 1 Hz, and a duty cycle set to 25, GPIO pin will 
    stay HIGH for 1*(25/100) seconds on HIGH output, and 1*(75/100) seconds on LOW output.
    """
    self.dutyCycle = dutyCycle

  def changeFrequency(self, frequency):
    """
    Change the frequency of the PWM pattern. Expected parameter is :
    - frequency : the frequency in Hz for the PWM pattern. A correct value may be 100.
    
    Example : with a frequency of 1 Hz, and a duty cycle set to 25, GPIO pin will 
    stay HIGH for 1*(25/100) seconds on HIGH output, and 1*(75/100) seconds on LOW output.
    """
    self.baseTime = 1.0 / frequency
    self.sliceTime = self.baseTime / self.maxCycle

  def stop(self):
    """
    Stops PWM output.
    """
    self.toTerminate = True
    while self.terminated == False:
      # Just wait
      time.sleep(0.01)
    self.gpio.output(self.gpioPin, LOW)

class hwports:
 gpioctrl = [] # ftdi gpio
 gpios    = [] # rpigpio compatible layer
 i2cctrl  = [] # ftdi i2c
 spictrl  = [] # ftdi spi
 pinhandlers = []
 pwmo = []

 def __init__(self): # general init
  self.i2c_initialized = False
  self.i2cbus = None
  self.gpioctrl = [] # ftdi gpio
  self.gpios    = [] # rpigpio compatible layer
  self.i2cctrl  = [] # ftdi i2c
  self.spictrl  = [] # ftdi spi
  self.pinhandlers = []
  for p in range(len(Settings.Pinout)):
   self.pinhandlers.append(None)
  self.pwmo = []
  for p in range(22):
   self.pwmo.append({"pin":0,"o":False})

 def get_gpiohandler(self,pinid):
   try:
    gh = self.pinhandlers[pinid]
    rp = Settings.Pinout[pinid]["realpin"]
   except:
    gh = None
    rp = 0
   return gh, rp

 def __del__(self):
   self.cleanup()

 def cleanup(self):
   try:
    for p in self.pwmo:
     try:
      if p["o"]:
       p["o"].stop()
     except:
      pass
    for d in self.gpios:
     try:
      d["o"].cleanup()
     except Exception as e:
      pass
    for d in self.i2cctrl:
     try:
      d["o"].terminate()
     except Exception as e:
      pass
    for d in self.spictrl:
     try:
      d["o"].terminate()
     except Exception as e:
      pass
   except:
     pass

 def gpio_function_name(self,func):
  typestr = "Unknown"
  try:
    typeint = int(func)
    if IN==typeint:
      typestr = "Input"
    elif OUT==typeint:
      typestr = "Output"
    elif SPI==typeint:
      typestr = "SPI"
    elif I2C==typeint:
      typestr = "I2C"
#    elif SERIAL==typeint:
#      typestr = "Serial"
  except:
   typestr = "Unknown"
  return typestr

 def gpio_function_name_from_pin(self,gpio):
  GPIO, gpio = self.get_gpiohandler(gpio)
#  print("funcfrompin",gpio,GPIO)#debug
  typestr = "Unknown"
  try:
   pinnum = int(gpio)
   if pinnum>0:
    typeint = GPIO.gpio_function(pinnum)
    typestr = self.gpio_function_name(typeint)
  except Exception as e:
   typestr = "Unknown"
  return typestr

 def gpio_function(self,bcmpin):
  GPIO, bcmpin = self.get_gpiohandler(bcmpin)
  try:
   res = GPIO.gpio_function(bcmpin)
  except:
   res = -1
  return res

 def input(self,bcmpin):
  GPIO, bcmpin = self.get_gpiohandler(bcmpin)
  try:
   res = GPIO.input(bcmpin)
  except:
   res = -1
  return res

 def output(self,pin,value,Force=False):
  GPIO, pin = self.get_gpiohandler(pin)
  if Force:
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(pin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      if Settings.Pinout[b]["startupstate"]<4:
       self.setpinstate(b,4)
     break
  return GPIO.output(pin,value)

 def add_event_detect(self,pin, detection, pcallback,pbouncetime=0):
  GPIO, pin = self.get_gpiohandler(pin)
  for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(pin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      if Settings.Pinout[b]["startupstate"]<4:
       self.setpinstate(b,Settings.Pinout[b]["startupstate"])
      else:
       pass # i am lazy and not sure if is it can happen anyday...
     break
  if pbouncetime==0:
   GPIO.add_event_detect(pin,detection,callback=pcallback)
  else:
   GPIO.add_event_detect(pin,detection,callback=pcallback,bouncetime=pbouncetime)

 def remove_event_detect(self,pin):
  GPIO, pin = self.get_gpiohandler(pin)
  GPIO.remove_event_detect(pin)

 def get_first_i2c(self):
  res = -1
  for i in range(20):
   if self.is_i2c_usable(i):
    return i
  return res

 def i2c_init(self,channel=-1):
  if self.i2c_initialized == False:
   if channel==-1:
    channel = self.get_first_i2c()
   try:
    import smbus
    self.i2cbus = smbus.SMBus(channel)
    self.i2c_initialized = True
   except:
    self.i2c_initialized = False
  return self.i2c_initialized

 def i2c_read_block(self,address,cmd,channel=-1):
     channel = self.get_first_i2c()
     bus = self.get_i2c_ctrl(channel)
     try:
      i2c = bus.get_port(address)
      res = i2c.read_from(int(cmd),readlen=32)
     except:
      res = None
     return res

 def is_i2c_usable(self,channel):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      try:
       for i in range(0,len(n)):
        if "I2C"+str(channel)+"-" in n[i]:
         return True
      except:
       pass
     return False
#  devlist = get_ftdi_devices(2)
#  lismpsse = False
#  try:
#   fi = Ftdi()
#   fi = fi.create_from_url(devlist[channel][0])
#   lismpsse = fi.has_mpsse
#   fi.close()
#  except Exception as e:
#   pass
#  return lismpsse

 def is_i2c_enabled(self,channel):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      sn = Settings.Pinout[p]["altfunc"]
      try:
       if "I2C"+str(channel)+"-" in n[sn]:
        return True
      except:
       pass
     return False

 def enable_i2c(self,channel):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      if len(n)>2:
       try:
        if "I2C"+str(channel)+"-" in n[3]:
         Settings.Pinout[p]["altfunc"] = 3
#         print(p,"ok",Settings.Pinout[p])
       except Exception as e:
        pass

 def disable_i2c(self,channel):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      try:
       if "I2C"+str(channel)+"-" in n[3]:
        Settings.Pinout[p]["altfunc"] = 0
      except:
       pass

 def is_spi_usable(self,channel):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      try:
        for i in range(0,len(n)):
         if "SPI"+str(channel)+"-" in n[i]:
          return True
      except:
        pass
     return False

 def is_spi_enabled(self,channel):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      sn = Settings.Pinout[p]["altfunc"]
      try:
       if "SPI"+str(channel)+"-" in n[sn]:
        return True
      except:
       pass
     return False

 def enable_spi(self,channel,cs=1):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      if len(n)>1:
       try:
        if "SPI"+str(channel)+"-" in n[2]:
         rok = False
         if "-CE" in n[2]:
          try:
           cenum = int(n[2][-1])
          except:
           cenum = 5
          if cenum<int(cs):
           rok = True
          else:
           Settings.Pinout[p]["altfunc"] = 0
         else:
          rok = True
         if rok:
          Settings.Pinout[p]["altfunc"] = 2
       except:
        pass

 def disable_spi(self,channel):
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      try:
       if "SPI"+str(channel)+"-" in n[2]:
        Settings.Pinout[p]["altfunc"] = 0
      except:
       pass

 def get_spi_cs_count(self,channel):
     cenum = -1
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      sn = Settings.Pinout[p]["altfunc"]
      if sn==2:
       try:
        if "SPI"+str(channel)+"-" in n[sn]:
          if "-CE" in n[2]:
           try:
            cenum = int(n[2][-1])
           except:
            pass
       except:
        pass
     return (cenum+1)

 def is_serial_usable(self,channel=0):
  pass

 def is_serial_enabled(self,channel=0):
  pass

 def enable_serial(self,channel=0):
  pass

 def disable_serial(self,channel):
  pass

 def set_serial(self,status,channel=0):
  if (status==0) or (status==False):
   self.disable_serial(channel)
  else:
   self.enable_serial(channel)

 def output_pwm(self,bcmpin,pprop,pfreq=1000): # default 1000Hz
  pin = int(bcmpin)
  prop = int(pprop)
  freq = int(pfreq)

  for p in range(len(Settings.Pinout)):
     if int(Settings.Pinout[p]["BCM"])==pin :
      if (int(Settings.Pinout[p]["startupstate"]) not in [4,5,6]):
       return False # if not output skip

  pfound = False
  if len(self.pwmo)>0:
    for p in range(0,len(self.pwmo)):
     if int(self.pwmo[p]["pin"])==pin:
      if (self.pwmo[p]["o"]):
       if prop<=0:
        self.pwmo[p]["o"].stop()
       else:
        self.pwmo[p]["o"].start(prop)
        self.pwmo[p]["o"].changeFrequency(freq)
        self.pwmo[p]["o"].changeDutyCycle(prop)
      pfound = True
      break
  if pfound==False:
    GPIO, rpin = self.get_gpiohandler(pin)
    self.pwmo[p]["pin"] = pin
    self.pwmo[p]["o"] = SoftPwm(GPIO,freq,rpin)
    self.pwmo[p]["o"].start(prop)
  return True

 def setpinstartstate(self,bcmpin,state):
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      self.setpinstate(b,state,True)
     break

 def setpinactualstate(self,pinid,state):
    if Settings.Pinout[pinid]["actualstate"]<7 and state<7:
     Settings.Pinout[pinid]["actualstate"]=state

 def setpinstate(self,PINID,state,force=False):
   if (force==False):
    if Settings.Pinout[PINID]["altfunc"]>0 or Settings.Pinout[PINID]["canchange"]!=1 or Settings.Pinout[PINID]["BCM"]<0:
     return False
#   if (int(state)<=0 and int(Settings.Pinout[PINID]["startupstate"])>0):
   GPIO, rpin = self.get_gpiohandler(int(Settings.Pinout[PINID]["BCM"]))
   if int(state)<=0:
#    pass # revert to default input
    pass # do nothing
    Settings.Pinout[PINID]["startupstate"] = -1
#    if self.gpioinit:
#     try:
#      GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.IN)
#     except:
#      pass
#    self.setpinactualstate(PINID,99) # ugly hack
    return True
   elif state==1:
    pass # input
    Settings.Pinout[PINID]["startupstate"] = state
#    if self.gpioinit:
    try:
      GPIO.setup(rpin, IN)
    except:
      pass
    self.setpinactualstate(PINID,1)
    return True
   elif state in [4,5,6]: #output
#    if self.gpioinit:
    try:
      if state==5:
       GPIO.setup(rpin, OUT, initial=LOW)
      elif state==6:
       GPIO.setup(rpin, OUT, initial=HIGH)
      else:
       GPIO.setup(rpin, OUT)
    except:
      pass
    Settings.Pinout[PINID]["startupstate"] = state
    self.setpinactualstate(PINID,4)
    return True
   return False

 def initpinstates(self):
     for b in range(len(Settings.Pinout)):
      if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
       if int(Settings.Pinout[b]["BCM"])>=0:
        if int(Settings.Pinout[b]["startupstate"])<7 and int(Settings.Pinout[b]["startupstate"])>=0:
         self.setpinstate(b,Settings.Pinout[b]["startupstate"],True)

 def readconfig(self):
    Settings.PinStatesMax = 7
    Settings.PinStates = ["Default","Input","Reserved","Reserved","Output","Output-Low","Output-High","Special","Reserved"]
    for b in range(len(Settings.Pinout)):
     if Settings.Pinout[b]["altfunc"] != 0 and Settings.Pinout[b]["startupstate"]>0 and Settings.Pinout[b]["startupstate"]<7:
      Settings.Pinout[b]["startupstate"] = -1 # set to default
    try:
     import plugindeps
     for i in range(len(plugindeps.modulelist)):
      if plugindeps.modulelist[i]['name']=="GPIO":
       plugindeps.modulelist[i]["pip"] = ["pyftdi"]
       plugindeps.modulelist[i]["testcmd"] = "from pyftdi.ftdi import Ftdi"
      elif plugindeps.modulelist[i]['name']=="i2c":
       try:
        plugindeps.modulelist[i]["pip"] = ["pyftdi"]
        plugindeps.modulelist[i]["installcmd"] = "cp lib/ftdi/smbus.py smbus.py && cp lib/ftdi/smbus2.py smbus2.py"
        del plugindeps.modulelist[i]["apt"]
       except Exception as e:
        pass
      elif plugindeps.modulelist[i]['name']=="Adafruit_DHT":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="ws2812":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
#      elif plugindeps.modulelist[i]['name']=="OLED":
#       plugindeps.modulelist[i]["pip"] = [""] # only real i2c supported!
      elif plugindeps.modulelist[i]['name']=="tm1637":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="ina219":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="pylora":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="epd":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="amg":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="wpi":
       plugindeps.modulelist[i]["installcmd"] = [""] # only RPI supported!
    except:
     pass
    self.gpioctrl = [] # ftdi gpio
    self.gpios    = [] # rpigpio compatible layer
    self.i2cctrl  = [] # ftdi i2c
    self.spictrl  = [] # ftdi spi
    self.pinhandlers = []

    devlist = get_ftdi_devices(2)
    devs = get_ftdi_configured_devices()
    for cd in range(len(devs)):
     notfound = True
     for rd in range(len(devlist)):
      if devlist[rd][0] == devs[cd]:
       notfound = False
       break
     if notfound: # configured device missing?
      if is_serialnumber(devs[cd]): # delete if serial based
        self.removedevpinout(devs[cd])
        devs = get_ftdi_configured_devices()
      else:# replace if address based
       dt = ""
       rep = ""
       for p in range(len(Settings.Pinout)):
        if Settings.Pinout[p]["ftdevice"]==devs[cd]:
         dt = Settings.Pinout[p]["ftdevtype"]
         break
       if dt != "":
        for rd in range(len(devlist)):
          if not devlist[rd][0] in devs: # if not configured
           if (devlist[rd][1] == dt) and (is_serialnumber(devlist[rd][0])==False): # if found a similar, not configured one
            rep = devlist[rd][0]
            break
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Missing "+devs[cd]+" replaced with "+rep)
       if rep != "": # dynamic replacement
        for p in range(len(Settings.Pinout)):
         if Settings.Pinout[p]["ftdevice"]==devs[cd]:
          Settings.Pinout[p]["ftdevice"] = rep
        devs = get_ftdi_configured_devices()

    if len(devs)>0:
     for d in range(len(devs)):
       gtype = 0
       hconfpin = 0
       dirpin = 0
       cter = 0
       cpins = 0
       for p in range(len(Settings.Pinout)):
        if Settings.Pinout[p]["ftdevice"]==devs[d]:
         try:
          if Settings.Pinout[p]["startupstate"]>-1:
           hconfpin = Settings.Pinout[p]["realpin"]
           if Settings.Pinout[p]["startupstate"] in [4,5,6]:
            dirpin = set_bit(dirpin,hconfpin,1)
            cpins |= (1 << int(c))
           elif Settings.Pinout[p]["startupstate"] == 1:
            cpins |= (1 << int(c))
          if Settings.Pinout[p]["altfunc"]>0:
           gtype = Settings.Pinout[p]["altfunc"]
           cter += 1
         except:
          pass
#       print("readconfig ",gtype,hconfpin,dirpin)#debug
       self.gpioctrl.append({"ftdevice":devs[d],"o":None})
       try:
        if gtype==0:
         if hconfpin<8: # old style will be enough
          self.gpioctrl[d]["o"] = GpioAsyncController()
         else:          # wide style needed
          self.gpioctrl[d]["o"] = GpioMpsseController()
         try:
          reqfreq = 1.0E5
          self.gpioctrl[d]["o"].configure(devs[d],direction=dirpin,frequency=reqfreq)
         except:
          reqfreq = 0
         if reqfreq==0:
          self.gpioctrl[d]["o"].configure(devs[d],direction=dirpin)
        elif gtype==2:  # spi
         cter = cter - 3
         if cter<1:
          cter = 1
         elif cter>5:
          cter = 5
         self.spictrl.append({"ftdevice":devs[d],"o":None})
         self.spictrl[-1]["o"] = SpiController(cs_count=cter)
         self.spictrl[-1]["o"].configure(devs[d],direction=dirpin)
         self.gpioctrl[d]["o"] = self.spictrl[-1]["o"].get_gpio()
         self.gpioctrl[d]["o"].set_direction(cpins,dirpin)
        elif gtype==3:  # i2c
         self.i2cctrl.append({"ftdevice":devs[d],"o":None})
         self.i2cctrl[-1]["o"] = I2cController()
         self.i2cctrl[-1]["o"].configure(devs[d],direction=dirpin)
         self.gpioctrl[d]["o"] = self.i2cctrl[-1]["o"].get_gpio()
         self.gpioctrl[d]["o"].set_direction(cpins,dirpin)

        self.gpios.append({"ftdevice":devs[d],"o":None})
        if self.gpioctrl[d]["o"] is not None:
         try:
          freq = self.gpioctrl[d]["o"].frequency
         except:
          freq = 1.0E4
         self.gpios[d]["o"] = FTDIGPIO(self.gpioctrl[d]["o"],freq)
       except Exception as e:
        print("gpio init err",e)

     self.pinhandlers = []
     self.pinhandlers.append(None)
     for p in range(len(Settings.Pinout)):
      for d in range(len(devs)):
        if Settings.Pinout[p]["ftdevice"]==devs[d]:
#         if Settings.Pinout[p]["altfunc"]==2:#spi
#          self.pinhandlers.append(None)
#         elif Settings.Pinout[p]["altfunc"]==3:#i2c
#          self.pinhandlers.append(None)
#         else:
          self.pinhandlers.append(self.gpios[d]["o"])
#     print(self.pinhandlers,len(self.pinhandlers))
#     print(Settings.Pinout,len(Settings.Pinout))
     if self.get_first_i2c()>-1:
      rpieGlobals.extender = 256
     else:
      rpieGlobals.extender = 128
    return True

 def saveconfig(self):
  # save config.txt
    return True # debug

 def is_i2c_lib_available(self):
  return True

 def get_i2c_ctrl(self,bus_number=-1,devname=""):
   res = None
   if devname=="" and bus_number>-1:
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      sn = Settings.Pinout[p]["altfunc"]
      try:
       if "I2C"+str(bus_number)+"-" in n[sn]:
        devname = Settings.Pinout[p]["ftdevice"]
        break
      except:
       pass
   if devname!="":
    for i in range(0,len(self.i2cctrl)):
     try:
      if self.i2cctrl[i]["ftdevice"] == devname:
       res = self.i2cctrl[i]["o"]
       break
     except:
      pass
   return res

 def i2cscan(self,bus_number):
    devices = []
    try:
     bus = self.get_i2c_ctrl(bus_number)
     bus.set_retry_count(1)
    except:
     bus = None
     devices = []
    for device in range(3, 125): 
        try:
            port = bus.get_port(device)
            port.read(0)
            devices.append(device)  # hex(number)?
        except:
            pass
    if (0x5c not in devices): # 0x5c has to be checked twice as Am2320 auto-shutdown itself?
     try: 
      port = bus.get_port(0x5c)
      port.read(0)
      devices.append(0x5c)
     except:
      pass
    if (0x7f not in devices): # 0x7f is non-standard used by PME
     try: 
      port = bus.get_port(0x7f)
      port.read(0)
      devices.append(0x7f)
     except:
      pass

    return devices

 def removedevpinout(self,ftdidevicename,devtype=""):
  for p in reversed(range(len(Settings.Pinout))):
   try:
    if Settings.Pinout[p]["ftdevice"]==ftdidevicename:
     del Settings.Pinout[p]
   except:
    pass

 def createdevpinout(self,ftdidevicename,devtype="",devorder=-1):
  global PINOUT
  startpoint = len(Settings.Pinout)
  try:
   fi = Ftdi()
   fi = fi.create_from_url(ftdidevicename)
   gpionum = fi.port_width
   lismpsse = fi.has_mpsse
   lportindex = fi.port_index
   fi.close()
  except Exception as e:
   gpionum = 0
#  print(gpionum,lismpsse,lportindex)
#  rarr = []
#  for r in range(gpionum):
#   rarr.append(-1)
#  g = 0
#  for r in range(0,gpionum,2):
#   rarr[r] = g
#   g+=1
#  for r in range(1,gpionum,2):
#   rarr[r] = g
#   g+=1
  if gpionum>0:
   for g in range(0,gpionum):
    pname = get_ftdi_pinnames(g,lportindex,lismpsse)
    if devorder>-1:
     try:
      pname[2] = pname[2].replace("SPI-","SPI"+str(devorder)+"-")
      pname[3] = pname[3].replace("I2C-","I2C"+str(devorder)+"-")
     except:
      pass
    pindet = {"ID": int(startpoint+g),
"BCM":int(startpoint+g),
"realpin":int(g),
"name":pname,
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,
"ftdevice":ftdidevicename,
"ftdevtype":devtype
}
    Settings.Pinout.append(pindet)
    pindet = None

 def createpinout(self,pinout):
  global PINOUT
  if len(Settings.Pinout)<1:
   Settings.Pinout = PINOUT
  return True
#  print(Settings.Pinout)

 def webform_load(self):
  try:
   from pyftdi.ftdi import Ftdi
  except:
   webserver.TXBuffer +="<p>pyftdi not installed!"
   return False

  devlist = get_ftdi_devices(2)
  conflist = get_ftdi_configured_devices()
  webserver.TXBuffer += "<form name='frmselect' method='post'>"
  if len(devlist)>0:
#   webserver.addFormSubHeader("Add USB FTDI devices to pins")
   webserver.TXBuffer += "<fieldset style='padding:5px;margin:5px;border:2px solid green;-moz-border-radius:8px;-webkit-border-radius:8px;border-radius:8px;'><legend>Add USB FTDI devices to pins</legend>"
   for d in range(len(devlist)):
    if not(devlist[d][0] in conflist):
#     print(devlist[d][0],devlist[d][1])
     webserver.TXBuffer += "<input type='radio' name='newdev' value='"+str(d)+"' id='newdev"+str(d)+"'><label for='newdev"+str(d)+"'>"+str(devlist[d][0])+"/"+str(devlist[d][1])+"</label>  "
   webserver.TXBuffer += "</fieldset>"
   webserver.TXBuffer += "<BR>"
   webserver.addSubmitButton()

  webserver.TXBuffer += "<table class='normal'><tr><th colspan=10>GPIO pinout</th></tr>"
  webserver.addHtml("<tr><th>Detected function</th><th>Requested function</th><th>Pin name</th><th>#</th><th>Value</th><th>Value</th><th>#</th><th>Pin name</th><th>Requested function</th><th>Detected function</th></tr>")
  devs = get_ftdi_configured_devices()
#  print(devs)#debug
  if len(devs)>0:
    for d in range(len(devs)):
     webserver.TXBuffer += "<TR><th colspan=10><strong>FTDI"+str(d)+": "+str(devs[d])+"</strong></td></tr>"
     allpins = 0
     firstp = 0
     lastp = 0
     for p in range(len(Settings.Pinout)):
        if Settings.Pinout[p]["ftdevice"]==devs[d]:
         allpins += 1
         if allpins==1:
          firstp = p
         lastp = p
     halfpins = int(allpins/2)
#     print(devs[d],firstp,lastp,allpins)
#     for p in range(int(len(Settings.Pinout)/2)+1):
     for p in range(firstp,firstp+halfpins):
      if Settings.Pinout[p]["canchange"] != 2:
       idnum = int(Settings.Pinout[p]["ID"])

       webserver.TXBuffer += "<TR><td>"
#     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
       if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      # print pin setup infos
        astate = Settings.Pinout[p]["actualstate"]
        if astate<0:
         astate=0
        astate = Settings.PinStates[astate]
        pinfunc = -1
#      if self.gpioinit:
        pinfunc = self.gpio_function(int(Settings.Pinout[p]["BCM"]))
        astate = str(self.gpio_function_name(pinfunc))
        webserver.TXBuffer += astate
        webserver.TXBuffer += "</td>" # actual state 
       else:
        webserver.TXBuffer += "-</td>"
       if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
        webserver.addHtml("<td>") # startupstate
        webserver.addSelector("pinstate"+str(p),Settings.PinStatesMax,Settings.PinStates,False,None,Settings.Pinout[p]["startupstate"],False)
        webserver.addHtml("</td>")
       else:
        webserver.TXBuffer += "<td>-</td>"
       try:
        funcorder = int(Settings.Pinout[p]["altfunc"])
       except:
        funcorder = 0
       if funcorder>0 and len(Settings.Pinout[p]["name"])>funcorder:
        webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][funcorder] +"</td>"
       else:
        webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][0] +"</td>"
       webserver.TXBuffer += "<td>"+ str(Settings.Pinout[p]["ID"]) +"</td>"
       webserver.TXBuffer += "<td style='{border-right: solid 1px #000;}'>"
       if Settings.Pinout[p]["canchange"]==1 and pinfunc in [0,1] and (astate in ["Input","Output"]):
#      if self.gpioinit:
        self.setpinstate(p,int(Settings.Pinout[p]["startupstate"]))
        try:
          webserver.TXBuffer += "("+str(self.input(int(Settings.Pinout[p]["BCM"])))+")"
        except:
          webserver.TXBuffer += "E" 
#      else:
#       webserver.TXBuffer += "X" 
        webserver.TXBuffer += "</td>" # add pin value
       else:
        webserver.TXBuffer += "-</td>"
       #right
       q = p + halfpins
       if q<len(Settings.Pinout):
        pinfunc = -1
        if Settings.Pinout[q]["canchange"]==1 and Settings.Pinout[q]["BCM"]>0:
         webserver.TXBuffer += "<td>"
         pinfunc = self.gpio_function(int(Settings.Pinout[q]["BCM"]))
         if pinfunc in [0,1] and Settings.Pinout[q]["altfunc"]==0:
           self.setpinstate(q,int(Settings.Pinout[q]["startupstate"]))
           try:
            webserver.TXBuffer += "("+str(self.input(int(Settings.Pinout[q]["BCM"])))+")"
           except:
            webserver.TXBuffer += "E" 
         webserver.TXBuffer += "</td>" # add pin value
        else:
         webserver.TXBuffer += "<td>-</td>"
        webserver.TXBuffer += "<td>"+ str(Settings.Pinout[q]["ID"]) +"</td>"
        try:
         funcorder = int(Settings.Pinout[q]["altfunc"])
        except:
         funcorder = 0
        if funcorder>0 and len(Settings.Pinout[q]["name"])>funcorder:
         webserver.TXBuffer += "<td>"+ Settings.Pinout[q]["name"][funcorder] +"</td>"
        else:
         webserver.TXBuffer += "<td>"+ Settings.Pinout[q]["name"][0] +"</td>"
        webserver.TXBuffer += "<td>"
        if Settings.Pinout[q]["canchange"]==1 and Settings.Pinout[q]["altfunc"]==0:
       # print pin setup infos
         webserver.addSelector("pinstate"+str(q),Settings.PinStatesMax,Settings.PinStates,False,None,Settings.Pinout[q]["startupstate"],False)
         webserver.addHtml("</td>")
        else:
         webserver.TXBuffer += "-</td>"
        webserver.addHtml("<td>") # startupstate
        if Settings.Pinout[q]["canchange"]==1 and Settings.Pinout[q]["BCM"]>0:
         astate = Settings.Pinout[q]["actualstate"]
         if astate<0:
           astate=0
         astate = Settings.PinStates[astate]
 #      if self.gpioinit:
         astate = str(self.gpio_function_name(pinfunc))
         webserver.TXBuffer += str(astate)+"</td>" # actual state 
        else:
         webserver.TXBuffer += "<td>-</td>"
       webserver.TXBuffer += "</TR>"

  webserver.TXBuffer += "</table>"

  webserver.TXBuffer += "<table class='normal'><TR>"
  webserver.addFormHeader("Advanced features")
  devcount = len(get_ftdi_configured_devices())
#  devcount = get_ftdi_devices(0)
  for i in range(0,devcount):
   if self.is_i2c_usable(i):
    webserver.addFormCheckBox("Enable I2C-"+str(i),"i2c"+str(i),self.is_i2c_enabled(i))
    webserver.addFormCheckBox("Enable SPI-"+str(i),"spi"+str(i),self.is_spi_enabled(i))
    options = ["1","2","3","4","5"]
    optionvalues = [1,2,3,4,5]
    webserver.addFormSelector("SPI-"+str(i)+" CE count","i2c"+str(i)+"ce",len(optionvalues),options,optionvalues,None,self.get_spi_cs_count(i))

  webserver.addFormSeparator(2)
  webserver.TXBuffer += "<tr><td colspan=2>"
  webserver.addSubmitButton()
  webserver.addSubmitButton("Reread config","reread")
  webserver.TXBuffer += "</td></tr>"
  webserver.addFormNote("WARNING: Some changes needed to reboot after submitting changes! And some changes requires root permission.")
  webserver.addHtml("</table></form>")

  return True

 def webform_save(self,params):
   submit = webserver.arg("Submit",params)
   setbtn = webserver.arg("set",params)

   devlist = get_ftdi_devices(2)
#   print(devlist)
   if len(devlist)>0:
    try:
     d = int(webserver.arg("newdev",params))
    except:
     d = -1
    if d>-1 and d<len(devlist):
#       print(devlist[d][0],devlist[d][1])
       devcount = len(get_ftdi_configured_devices())
       self.createdevpinout(devlist[d][0],devlist[d][1],devcount)
#       try:
#        Settings.savepinout()
#       except Exception as e:
#        misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   if (submit=='Submit'):
#    devcount = get_ftdi_devices(0)
    devcount = len(get_ftdi_configured_devices())
    for i in range(0,devcount):
     wset = webserver.arg("i2c"+str(i),params)
     wset2 = webserver.arg("spi"+str(i),params)
     if wset=="on":
      self.disable_spi(i)
      self.enable_i2c(i)
     elif wset2=="on":
      cenum = webserver.arg("i2c"+str(i)+"ce",params)
      self.enable_spi(i,cenum)
     else:
      self.disable_i2c(i)
      self.disable_spi(i) # revert to gpio mode
    for p in range(len(Settings.Pinout)):
     pins = webserver.arg("pinstate"+str(p),params).strip()
#     print(p,pins)
     if pins and pins!="" and p!= "":
      try:
       self.setpinstate(p,int(pins))
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Pin "+str(p)+" "+str(e))
#    print("pins after save: ",Settings.Pinout)#debug
    try:
     Settings.savepinout()
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Pinout "+str(e))

   return True

#Init Hardware GLOBAL ports
#HWPorts = hwports()
#if os.path.exists("/DietPi/config.txt"): # DietPi FIX!
# HWPorts.config_file_name = "/DietPi/config.txt"
