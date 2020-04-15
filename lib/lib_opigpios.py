#!/usr/bin/env python3
#############################################################################
################ Helper Library for OPI GPIO handling #######################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import Settings
import os
import time
try:
 import linux_os as OS
except:
 print("Linux OS functions can not be imported!")
try:
 import OPi.GPIO as GPIO
except:
 print("OPi.GPIO not installed!")
try:
 import smbus
except:
 print("I2C smbus not installed!")
import webserver
import threading
import misc
import rpieGlobals

PINOUT40 = [
{"ID":0,
"BCM":-1,
"name":["None"], # reserved
"canchange":2,
"altfunc": 0},
{"ID":1,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":2,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":3,
"BCM":3,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":4,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":5,
"BCM":5,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":6,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":7,
"BCM":7,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":8,
"BCM":8,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":9,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":10,
"BCM":10,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":11,
"BCM":11,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":12,
"BCM":12,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":13,
"BCM":13,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":14,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":15,
"BCM":15,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":16,
"BCM":16,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":17,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":18,
"BCM":18,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":19,
"BCM":19,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":20,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":21,
"BCM":21,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":22,
"BCM":22,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":23,
"BCM":23,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":24,
"BCM":24,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":25,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":26,
"BCM":26,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":27,
"BCM":27,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":28,
"BCM":28,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":29,
"BCM":29,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":30,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":31,
"BCM":31,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":32,
"BCM":32,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":33,
"BCM":33,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":34,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":35,
"BCM":35,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":36,
"BCM":36,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":37,
"BCM":37,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":38,
"BCM":38,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":39,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":40,
"BCM":40,
"name":[],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1}
]

try:
 BOTH=GPIO.BOTH
 RISING=GPIO.RISING
 FALLING=GPIO.FALLING
except:
 BOTH=3
 RISING=1
 FALLING=2

class OrangePwm(threading.Thread):
  #https://github.com/evergreen-it-dev/orangepwm
  def __init__(self, frequency, gpioPin):
     self.baseTime = 1.0 / frequency
     self.maxCycle = 100.0
     self.sliceTime = self.baseTime / self.maxCycle
     self.gpioPin = gpioPin
     self.terminated = False
     self.toTerminate = False
     self.thread = None

  def start(self, dutyCycle):
    """
    Start PWM output. Expected parameter is :
    - dutyCycle : percentage of a single pattern to set HIGH output on the GPIO pin
    
    Example : with a frequency of 1 Hz, and a duty cycle set to 25, GPIO pin will 
    stay HIGH for 1*(25/100) seconds on HIGH output, and 1*(75/100) seconds on LOW output.
    """
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
        GPIO.output(self.gpioPin, GPIO.HIGH)
        time.sleep(self.dutyCycle * self.sliceTime)
      if self.dutyCycle < self.maxCycle:
        GPIO.output(self.gpioPin, GPIO.LOW)
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
    GPIO.output(self.gpioPin, GPIO.LOW)

class hwports:
 config_file_name = "/boot/armbianEnv.txt"
 CONFIG_OVERLAYS =  "overlays="
 CONFIG_SPI      =  "param_spidev_spi_bus="
 COMMAND_DISABLE_BT="sudo systemctl disable hciuart"

 def __init__(self): # general init
  self.i2c_channels = [] # 0,1
  self.i2c_channels_init = [] # 0,1
  self.i2c_initialized = False
  self.i2cbus = None
  self.spi_channels = [] # 0,1
  self.spi_cs = [0,0]
  self.serial = []
  self.pwmo = []
  self.BOARD = []
  for p in range(22):
   self.pwmo.append({"pin":0,"o":False})
  opv = OS.getarmbianinfo()
  if opv:
   pinout = opv["pins"]
  try:
      if pinout=="26z+2":
       from orangepi.zeroplus2 import BOARD
      elif pinout=="26z+":
       from orangepi.zeroplus import BOARD
      elif pinout=="26pi3":
       from orangepi.pi3 import BOARD
      elif pinout=="26o+":
       from orangepi.oneplus import BOARD
      elif pinout=="40w+":
       from orangepi.winplus import BOARD
      elif pinout=="40pr":
       from orangepi.prime import BOARD
      elif pinout=="40pc2":
       from orangepi.pc2 import BOARD
      elif pinout=="40pc":
       from orangepi.pc import BOARD
      else:
       pinout = "0"
  except Exception as e:
      pinout = "0"
  if pinout != "" and pinout != "0":
      try:
#       GPIO.setmode(GPIO.BOARD)
       GPIO.setmode(BOARD)
       self.BOARD=BOARD
      except Exception as e:
       print("GPIO set:",e)
  try:
   GPIO.setwarnings(False)
   self.gpioinit = True
  except:
   print("GPIO init failed")
   self.gpioinit = False

 def __del__(self):
   try:
    self.cleanup()
   except:
    pass

 def cleanup(self):
   if self.gpioinit:
    GPIO.cleanup()

 def gpio_function_name(self,func):
  typestr = "Unknown"
  try:
    func = int(func)
    if GPIO.IN==func:
      typestr = "Input"
    elif GPIO.OUT==func:
      typestr = "Output"
  except Exception as e:
   typestr = "Unknown"
  return typestr

 def gpio_function_name_from_pin(self,gpio):
  typestr = "Unknown"
  try:
   pinnum = int(gpio)
   if pinnum>0:
    typeint = self.gpio_function(pinnum)
    typestr = self.gpio_function_name(typeint)
  except Exception as e:
   typestr = "Unknown"
  return typestr

 def gpio_function(self,bpin):
  func = -1
  try:
   if os.path.exists("/sys/class/gpio/gpio"+str(self.BOARD[bpin])+"/direction"):
    func = os.popen("/bin/cat /sys/class/gpio/gpio"+str(self.BOARD[bpin])+"/direction 2>/dev/null").read()
    if "in" in func:
     func = GPIO.IN
    elif "out" in func:
     func = GPIO.OUT
  except:
   func = -1
  return func

 def input(self,bcmpin):
  return GPIO.input(bcmpin)

 def output(self,pin,value,Force=False):
  if Force:
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(pin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      if Settings.Pinout[b]["startupstate"]<4:
       self.setpinstate(b,4)
     break
  return GPIO.output(pin,value)

 def add_event_detect(self,pin, detection, pcallback,pbouncetime=0):
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
  GPIO.remove_event_detect(pin)

 def get_first_i2c(self):
  if len(self.i2c_channels_init)>0:
   return self.i2c_channels_init[0]
  for i in range(0,3): # get first
     if self.is_i2c_usable(i):
      return i
  return -1

 def i2c_init(self,channel=-1):
  if channel==-1:
   channel = self.get_first_i2c()
  if not(channel in self.i2c_channels_init):
   if self.is_i2c_usable(channel)==False:
      channel = -1
   if channel ==-1:
    return False
   self.i2cbus = smbus.SMBus(channel)
   self.i2c_channels_init.append(channel)
  return True

 def i2c_read_block(self,address,cmd,channel=-1):
  retval = None
  if channel==-1:
   channel = self.get_first_i2c()
  if (channel in self.i2c_channels_init):
   try:
    retval = self.i2cbus.read_i2c_block_data(address,cmd)
   except:
    retval = None
  return retval

 def is_i2c_usable(self,channel):
   result = False
   for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "I2C"+str(channel) in n[tn]:
       return True
   return result

 def is_i2c_enabled(self,channel):
  res = False
  if channel in self.i2c_channels:
   res = True
  if res==False:
   try:
    for p in range(len(Settings.Pinout)):
     if "I2C"+str(channel) in Settings.Pinout[p]["name"][ Settings.Pinout[p]["altfunc"] ]:
      res = True
      break
   except:
    pass
  return res

 def enable_i2c(self,channel):
  if self.is_i2c_usable(channel) and (self.is_i2c_enabled(channel)==False):
   self.i2c_channels.append(channel)
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "I2C"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = tn
   except:
    pass

 def disable_i2c(self,channel):
  if self.is_i2c_enabled(channel):
   try:
    self.i2c_channels.remove(channel)
   except:
    pass
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "I2C"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = 0
   except:
    pass

 def is_spi_usable(self,channel):
   result = False
   for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "SPI"+str(channel) in n[tn]:
       return True
   return result

 def is_spi_enabled(self,channel):
  res = False
  if channel in self.spi_channels:
   res = True
  if res==False:
   try:
    for p in range(len(Settings.Pinout)):
     if "SPI"+str(channel) in Settings.Pinout[p]["name"][ Settings.Pinout[p]["altfunc"] ]:
      res = True
      break
   except:
    pass
  return res

 def enable_spi(self,channel,cs=-1):
  if self.is_spi_usable(channel) and (self.is_spi_enabled(channel)==False):
   self.spi_channels.append(channel)
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "SPI"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = tn
   except:
    pass

 def disable_spi(self,channel):
  if self.is_spi_enabled(channel):
   try:
    self.spi_channels.remove(channel)
   except:
    pass
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "SPI"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = 0
   except:
    pass

 def is_serial_usable(self,channel=0):
   result = False
   for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "UART"+str(channel) in n[tn]:
       return True
   return result

 def is_serial_enabled(self,channel=0):
  res = False
  if channel in self.serial:
   res = True
  if res==False:
   try:
    for p in range(len(Settings.Pinout)):
     if "UART"+str(channel) in Settings.Pinout[p]["name"][ Settings.Pinout[p]["altfunc"] ]:
      res = True
      break
   except:
    pass
  return res

 def enable_serial(self,channel=0):
  if self.is_serial_usable(channel) and (self.is_serial_enabled(channel)==False):
   self.serial.append(channel)
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "UART"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = tn
   except:
    pass

 def disable_serial(self,channel):
  if self.is_serial_enabled(channel):
   try:
    self.serial.remove(channel)
   except:
    pass
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "UART"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = 0
   except:
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
      if (int(Settings.Pinout[p]["startupstate"]) not in [4]):
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
    self.pwmo[p]["pin"] = pin
    self.pwmo[p]["o"] = OrangePwm(freq,pin)
    self.pwmo[p]["o"].start(prop)
  return True

 def is_i2s_usable(self):
   result = False
   if self.pinnum=="40":
     result = True
   return result

 def set_i2s(self,state):
  if self.is_i2s_usable():
   if state==1 or state==True:
    self.i2s=1
    if self.is_spi_enabled(1):
     self.disable_spi(1) # collision resolving
   else:
    self.i2s=0

 def set1wgpio(self,bcmpin,FirstRead=False):
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      Settings.Pinout[b]["startupstate"] = 5
      if FirstRead:
       Settings.Pinout[b]["actualstate"]=Settings.Pinout[b]["startupstate"]
     break

 def setpinstartstate(self,bcmpin,state):
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      self.setpinstate(b,state,True)
     break

 def setpinactualstate(self,pinid,state):
    if Settings.Pinout[pinid]["actualstate"]<5 and state<5:
     Settings.Pinout[pinid]["actualstate"]=state

 def setpinstate(self,PINID,state,force=False):
   if (force==False):
    if Settings.Pinout[PINID]["altfunc"]>0 or Settings.Pinout[PINID]["canchange"]!=1 or Settings.Pinout[PINID]["BCM"]<0:
     return False
#   if (int(state)<=0 and int(Settings.Pinout[PINID]["startupstate"])>0):
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
    if self.gpioinit:
     try:
      GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.IN)
     except:
      pass
    self.setpinactualstate(PINID,1)
    return True
   elif state==4: #output
    if self.gpioinit:
     try:
      GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.OUT)
     except:
      pass
    Settings.Pinout[PINID]["startupstate"] = state
    self.setpinactualstate(PINID,4)
    return True
   elif state==5: #1wire
    self.setpinactualstate(PINID,-1)
    self.set1wgpio(int(Settings.Pinout[PINID]["BCM"]))
    return True
   return False

 def initpinstates(self):
    if self.gpioinit:
     for b in range(len(Settings.Pinout)):
      if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
       if int(Settings.Pinout[b]["BCM"])>=0:
        if int(Settings.Pinout[b]["startupstate"])<6 and int(Settings.Pinout[b]["startupstate"])>=0:
         self.setpinstate(b,Settings.Pinout[b]["startupstate"],True)

 def readconfig(self):
    self.i2c_channels = [] # 0,1
    self.spi_channels = [] # 0,1
    self.serial = []
    self.spi_cs = [0,0]
#    self.set_serial(1)
#    self.audio = 1

    try:
     import plugindeps
     for i in range(len(plugindeps.modulelist)):
      if plugindeps.modulelist[i]['name']=="GPIO":
       plugindeps.modulelist[i]["pip"] = ["OPi.GPIO"]
       plugindeps.modulelist[i]["testcmd"] = "import OPi.GPIO as GPIO"
      elif plugindeps.modulelist[i]['name']=="Adafruit_DHT":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="ws2812":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="LCD":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
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
    Settings.PinStatesMax = 7
    Settings.PinStates = ["Default","Input","Reserved","Reserved","Output","1WIRE","Special","Reserved"]
    try:
     with open(self.config_file_name) as f:
      for line in f:
       line = line.strip().lower()
       if line.startswith(self.CONFIG_OVERLAYS):
        for i in range(0,3):
         dn = "i2c"+str(i)
         if dn in line:
          self.enable_i2c(i)
        for i in range(0,5):
         dn = "uart"+str(i)
         if dn in line:
          self.enable_serial(i)
       if line.startswith(self.CONFIG_SPI):
        for i in range(0,3):
         if str(i) in line:
          self.enable_spi(i)
    except Exception as e:
     print(e)

    for b in range(len(Settings.Pinout)):
     if Settings.Pinout[b]["altfunc"] != 0 and Settings.Pinout[b]["startupstate"]>0 and Settings.Pinout[b]["startupstate"]<7:
      Settings.Pinout[b]["startupstate"] = -1 # set to default

    return True

 def saveconfig(self):
  # save config.txt
    contents = []
    ostr = ""
    w1enabled = False
    for p in range(len(Settings.Pinout)):
     try:
      if w1enabled==False and (Settings.Pinout[p]['startupstate']==5 or Settings.Pinout[p]['actualstate']==5):
       w1enabled = True
     except:
      pass
    try:
     mstr = []
     spis = []
     for p in range(len(Settings.Pinout)):
      n = Settings.Pinout[p]["name"]
      sn = Settings.Pinout[p]["altfunc"]
      if "I2C" in n[sn] or "SPI" in n[sn] or "UART" in n[sn]:
       for i in range(0,5):
        if "I2C"+str(i) in n[sn]:
         if not "i2c"+str(i) in mstr:
          mstr.append("i2c"+str(i))
       for i in range(0,3):
        if "SPI"+str(i) in n[sn] and not (i in spis):
         spis.append(i)
       for i in range(0,7):
        if "UART"+str(i) in n[sn]:
         if not "uart"+str(i) in mstr:
          mstr.append("uart"+str(i))
    except Exception as e:
     pass
    try:
     with open(self.config_file_name) as f:
      for line in f:
       line = line.strip()
       if line.startswith(self.CONFIG_OVERLAYS):
        ostr = line
        line = ""
       elif line.startswith(self.CONFIG_SPI):
        line = ""
       if line != "":
        contents.append(line)
    except:
     pass
    tostr = ostr.split("=")
    tstr2 = tostr[1].split()
    if len(spis)>0:
     mstr.append("spi-spidev")
    else:
     try:
      tstr2.remove("spi-spidev")
     except:
      pass
    if w1enabled:
     mstr.append("w1-gpio")
    else:
     try:
      tstr2.remove("w1-gpio")
     except:
      pass

    for o in tstr2:
     if ("i2c" in o or "uart" in o):
      if not (o in mstr):
       tstr2.remove(o)
    for o in mstr:
     if not(o in tstr2):
       tstr2.append(o)
    newstr = " ".join(tstr2)
    if newstr.strip()!="":
     contents.append(self.CONFIG_OVERLAYS+newstr)
    if len(spis)>0:
     for i in range(len(spis)):
      contents.append("param_spidev_spi_bus="+str(spis[i]))
    with open(self.config_file_name,"w") as f:
     for c in range(len(contents)):
      f.write(contents[c]+"\n")

    return True


 def is_i2c_lib_available(self):
  res = False
  try:
   import smbus
   res = True
  except:
   res = False
  return res

 def i2cscan(self,bus_number):
    devices = []
    try:
     bus = smbus.SMBus(bus_number)
    except:
     devices = []
    for device in range(3, 125): 
        try:
            if (device>=0x30 and device<=0x37) or (device>=0x50 and device<=0x5f):
             bus.read_byte(device)
            else:
             bus.write_quick(device)
            devices.append(device)  # hex(number)?
        except:
            pass
    if (0x5c not in devices): # 0x5c has to be checked twice as Am2320 auto-shutdown itself?
     try: 
      bus.read_byte(0x5c)
      devices.append(0x5c)
     except:
      pass
    if (0x7f not in devices): # 0x7f is non-standard used by PME
     try: 
      bus.read_byte(0x7f)
      devices.append(0x7f)
     except:
      pass

    try:
     bus.close()
    except:
     pass
    bus = None
    return devices

 def createpinout(self,pinout):
  global PINOUT40
  if ("40" in pinout and len(Settings.Pinout)<41) or ("26" in pinout and len(Settings.Pinout)<27):
     if "26" in pinout:
      for p in range(27):
       Settings.Pinout.append(PINOUT40[p])
     else:
      Settings.Pinout=PINOUT40
     try:
      if pinout=="26z+2":
       from orangepi.zeroplus2 import BOARD
      elif pinout=="26z+":
       from orangepi.zeroplus import BOARD
      elif pinout=="26pi3":
       from orangepi.pi3 import BOARD
      elif pinout=="26o+":
       from orangepi.oneplus import BOARD
      elif pinout=="40w+":
       from orangepi.winplus import BOARD
      elif pinout=="40pr":
       from orangepi.prime import BOARD
      elif pinout=="40pc2":
       from orangepi.pc2 import BOARD
      elif pinout=="40pc":
       from orangepi.pc import BOARD
      else:
       Settings.Pinout = [] # unknown board
     except Exception as e:
       Settings.Pinout = [] # unknown board
     if len(Settings.Pinout)>0:
      try:
       GPIO.setmode(BOARD)
      except Exception as e:
       print("GPIO set:",e)
#      print(BOARD)#debug
      for p in BOARD:
        pt = BOARD[p] # pin type id
        name = []
        name.append(str(pt))
        if pt == 0:
         name = ["PA0","UART2-TX"]
        elif pt == 1:
         name = ["PA1","UART2-RX"]
        elif pt == 2:
         name = ["PA2","UART2-RTS"]
        elif pt == 3:
         name = ["PA3","UART2-CTS"]
        elif pt == 6:
         name = ["PA6"]
        elif pt == 7:
         name = ["PA7"]
        elif pt == 8:
         name = ["PA8"]
        elif pt == 9:
         name = ["PA9"]
        elif pt == 10:
         name = ["PA10"]
        elif pt == 11:
         name = ["PA11","I2C0-SCL"]
        elif pt == 12:
         name = ["PA12","I2C0-SDA"]
        elif pt == 13:
         name = ["PA13","SPI1-CE0","UART3-TX"]
        elif pt == 14:
         name = ["PA14","SPI1-SCLK","UART3-RX"]
        elif pt == 15:
         name = ["PA15","SPI1-MOSI","UART3-RTS"]
        elif pt == 16:
         name = ["PA16","SPI1-MISO","UART3-CTS"]
        elif pt == 18:
         name = ["PA18","PCM0-SYN","I2C1-SCL"]
        elif pt == 19:
         name = ["PA19","PCM0-CLK","I2C1-SDA"]
        elif pt == 20:
         name = ["PA20","PCM0-DOUT"]
        elif pt == 21:
         name = ["PA21","PCM0-DIN"]
        elif pt == 32:
         name = ["PB0","UART2-TX"]
        elif pt == 33:
         name = ["PB1","UART2-RX"]
        elif pt == 34:
         name = ["PB2","UART2-RTS"]
        elif pt == 35:
         name = ["PB3","UART2-CTS","I2S0"]
        elif pt == 36:
         name = ["PB4","PCM0-SYNC"]
        elif pt == 37:
         name = ["PB5","PCM0-BCLK"]
        elif pt == 38:
         name = ["PB6","PCM0-DOUT"]
        elif pt == 39:
         name = ["PB7"]
        elif pt == 64:
         if pinout=="40pc":
          name = ["PC0","SPI0-MOSI"]
         else:
          name = ["PC0","NAND","SPI0-SCLK"]
        elif pt == 65:
         name = ["PC1","SPI0-MISO"]
        elif pt == 66:
         if pinout=="40pc":
          name = ["PC2","SPI0-SCLK"]
         else:
          name = ["PC2","NAND","SPI0-MOSI"]
        elif pt == 67:
         if pinout=="40pc":
          name = ["PC3","SPI0-CE0"]
         else:
          name = ["PC3","NAND","SPI0-MISO"]
        elif pt == 68:
         name = ["PC4","NAND"]
        elif pt == 69:
         name = ["PC5","NAND","SPI0-CE0"]
        elif pt == 70:
         name = ["PC6","NAND"]
        elif pt == 71:
         name = ["PC7","NAND"]
        elif pt == 72:
         name = ["PC8","NAND"]
        elif pt == 73:
         name = ["PC9","NAND"]
        elif pt == 74:
         name = ["PC10","NAND"]
        elif pt == 75:
         name = ["PC11","NAND"]
        elif pt == 76:
         name = ["PC12","NAND"]
        elif pt == 96:
         name = ["PD0","UART3-TX","SPI1-CE0","LCD-D2"]
        elif pt == 97:
         name = ["PD1","UART3-RX","SPI1-CLK","LCD-D3"]
        elif pt == 98:
         name = ["PD2","UART4-TX","SPI1-MOSI","LCD-D4"]
        elif pt == 99:
         name = ["PD3","UART4-RX","SPI1-MISO","LCD-D5"]
        elif pt == 100:
         name = ["PD4","UART4-RTS","LCD-D6"]
        elif pt == 101:
         name = ["PD5","UART4-CTS","LCD-D7"]
        elif pt == 102:
         name = ["PD6","LCD-D10"]
        elif pt == 107:
         name = ["PD11","MII"]
        elif pt == 110:
         name = ["PD14","MII"]
        elif pt == 111:
         name = ["PD15","LCD0-D21","TS1-DVLD"]
        elif pt == 112:
         name = ["PD16","LCD0-D22","TS1-D0"]
        elif pt == 113:
         name = ["PD18","LCD0-CLK","TS2-ERR"]
        elif pt == 117:
         name = ["PD21","LCD0-VSYNC","UART2-RTS","TS2-D0"]
        elif pt == 118:
         name = ["PD22","UART2-CTS","TS3-CLK"]
        elif pt == 119:
         name = ["PD23","I2C2-SCL","UART3-RX","TS3-ERR"]
        elif pt == 120:
         name = ["PD24","I2C2-SDA","UART3-RX","TS3-SYNC"]
        elif pt == 121:
         name = ["PD25","I2C0-SCL","UART3-RTS","TS3-DVLD"]
        elif pt == 122:
         name = ["PD26","I2C0-SDA","UART3-CTS","TS3-D0"]
        elif pt == 142:
         name = ["PE14","I2C2-SCL"]
        elif pt == 143:
         name = ["PE15","I2C2-SDA"]
        elif pt == 198:
         name = ["PG6","UART1-TX"]
        elif pt == 199:
         name = ["PG7","UART1-RX"]
        elif pt == 200:
         name = ["PG8","UART1-RTS"]
        elif pt == 201:
         name = ["PG9","UART1-CTS"]
        elif pt == 226:
         name = ["PH2","I2C1-SCL"]
        elif pt == 227:
         if "26" in pinout:
          name = ["PH3","SPI1-CS","PCM0-DIN"]
         else:
          name = ["PH3","I2C1-SDA"]
        elif pt == 228:
         if "26" in pinout:
          name = ["PH4","SPI1-SCLK","PCM0-MCLK"]
         else:
          name = ["PH4","UART3-TX"]
        elif pt == 229:
         if "26" in pinout:
          name = ["PH5","SPI1-MOSI","I2C1-SCL","SPDIF-MCLK"]
         else:
          name = ["PH5","UART3-RX"]
        elif pt == 230:
         if "26" in pinout:
          name = ["PH6","SPI1-MISO","I2C1-SDA","SPDIF-IN"]
         else:
          name = ["PH6","UART3-RTS"]
        elif pt == 231:
         name = ["PH7","UART3-CTS"]
        elif pt == 352:
         name = ["PL0","I2CS-SCL"]
        elif pt == 353:
         name = ["PL1","I2CS-SDA"]
        elif pt == 354:
         name = ["PL2","UARTS-TX"]
        elif pt == 355:
         name = ["PL3","UARTS-RX"]
        elif pt == 360:
         name = ["PL8"]
        elif pt == 361:
         name = ["PL9","I2CS-SDA"]
        elif pt == 362:
         name = ["PL10"]

        if pinout=="40pc":
         try:
          name.remove("NAND")
         except:
          pass
        Settings.Pinout[p]["name"] = name
#       print(p,BOARD[p])
  return True
#  print(Settings.Pinout)

 def webform_load(self):
  try:
   import OPi.GPIO as GPIO
  except:
   webserver.TXBuffer +="<p>OPi.GPIO not installed!"
   return False
  webserver.TXBuffer += "<form name='frmselect' method='post'><table class='normal'>"
  webserver.TXBuffer += "<tr><th colspan=10>GPIO pinout</th></tr>"
  webserver.addHtml("<tr><th>Detected function</th><th>Requested function</th><th>Pin name</th><th>#</th><th>Value</th><th>Value</th><th>#</th><th>Pin name</th><th>Requested function</th><th>Detected function</th></tr>")
  for p in range(len(Settings.Pinout)):
   if Settings.Pinout[p]["canchange"] != 2:
    idnum = int(Settings.Pinout[p]["ID"])
    if bool(idnum & 1): # left
     webserver.TXBuffer += "<TR><td>"
#     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      # print pin setup infos
      astate = Settings.Pinout[p]["actualstate"]
      if astate<0:
       astate=0
      astate = Settings.PinStates[astate]
      pinfunc = -1
      if self.gpioinit:
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
      if self.gpioinit:
       self.setpinstate(p,int(Settings.Pinout[p]["startupstate"]))
       try:
        webserver.TXBuffer += "("+str(self.input(int(Settings.Pinout[p]["BCM"])))+")"
       except:
        webserver.TXBuffer += "E" 
      else:
       webserver.TXBuffer += "X" 
      webserver.TXBuffer += "</td>" # add pin value
     else:
      webserver.TXBuffer += "-</td>"
    else:               # right
     pinfunc = -1
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      webserver.TXBuffer += "<td>"
      if self.gpioinit:
       pinfunc = self.gpio_function(int(Settings.Pinout[p]["BCM"]))
       if pinfunc in [0,1] and Settings.Pinout[p]["altfunc"]==0:
        self.setpinstate(p,int(Settings.Pinout[p]["startupstate"]))
        try:
         webserver.TXBuffer += "("+str(self.input(int(Settings.Pinout[p]["BCM"])))+")"
        except:
         webserver.TXBuffer += "E" 
      else:
       webserver.TXBuffer += "X" 
      webserver.TXBuffer += "</td>" # add pin value
     else:
      webserver.TXBuffer += "<td>-</td>"
     webserver.TXBuffer += "<td>"+ str(Settings.Pinout[p]["ID"]) +"</td>"
     try:
      funcorder = int(Settings.Pinout[p]["altfunc"])
     except:
      funcorder = 0
     if funcorder>0 and len(Settings.Pinout[p]["name"])>funcorder:
      webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][funcorder] +"</td>"
     else:
      webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][0] +"</td>"
     webserver.TXBuffer += "<td>"
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
      # print pin setup infos
      webserver.addSelector("pinstate"+str(p),Settings.PinStatesMax,Settings.PinStates,False,None,Settings.Pinout[p]["startupstate"],False)
      webserver.addHtml("</td>")
     else:
      webserver.TXBuffer += "-</td>"
     webserver.addHtml("<td>") # startupstate
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      astate = Settings.Pinout[p]["actualstate"]
      if astate<0:
        astate=0
      astate = Settings.PinStates[astate]
      if self.gpioinit:
        astate = str(self.gpio_function_name(pinfunc))
      webserver.TXBuffer += str(astate)+"</td>" # actual state 
     else:
      webserver.TXBuffer += "<td>-</td>"
     webserver.TXBuffer += "</TR>"
  webserver.TXBuffer += "</table>"

  webserver.TXBuffer += "<table class='normal'><TR>"
  webserver.addFormHeader("Advanced features")
  for i in range(0,5):
   if self.is_i2c_usable(i):
    webserver.addFormCheckBox("Enable I2C-"+str(i),"i2c"+str(i),self.is_i2c_enabled(i))
  for i in range(0,3):
   if self.is_spi_usable(i):
    webserver.addFormCheckBox("Enable SPI-"+str(i),"spi"+str(i),self.is_spi_enabled(i))
  for i in range(0,7):
   if self.is_serial_usable(i):
    webserver.addFormCheckBox("Enable UART-"+str(i),"uart"+str(i),self.is_serial_enabled(i))
  webserver.addFormSeparator(2)
  webserver.TXBuffer += "<tr><td colspan=2>"
  if OS.check_permission():
   webserver.addSubmitButton()
  webserver.addSubmitButton("Set without save","set")
  webserver.addSubmitButton("Reread config","reread")
  webserver.TXBuffer += "</td></tr>"
  if OS.check_permission():
   if OS.checkboot_ro():
     webserver.addFormNote("<font color='red'>WARNING: Your /boot partition is mounted READONLY! Changes could not be saved! Run 'sudo mount -o remount,rw /boot' or whatever necessary to solve it!")
  webserver.addFormNote("WARNING: Some changes needed to reboot after submitting changes! And most changes requires root permission.")
  webserver.addHtml("</table></form>")

  return True

 def webform_save(self,params):
   submit = webserver.arg("Submit",params)
   setbtn = webserver.arg("set",params)
   if (submit=='Submit') or (setbtn!=''):
    for i in range(0,5):
     wset = webserver.arg("i2c"+str(i),params)
     if wset=="on":
      self.enable_i2c(i)
     else:
      self.disable_i2c(i)
    for i in range(0,3):
     wset = webserver.arg("spi"+str(i),params)
     if wset=="on":
      self.enable_spi(i)
     else:
      self.disable_spi(i)
    for i in range(0,7):
     wset = webserver.arg("uart"+str(i),params)
     if wset=="on":
      self.enable_serial(i)
     else:
      self.disable_serial(i)
    for p in range(len(Settings.Pinout)):
     pins = webserver.arg("pinstate"+str(p),params).strip()
#     print(p,pins)
     if pins and pins!="" and p!= "":
      try:
       self.setpinstate(p,int(pins))
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Pin "+str(p)+" "+str(e))
    if OS.check_permission() and setbtn=='':
     try:
      self.saveconfig()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    try:
     Settings.savepinout()
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))


   return True

#Init Hardware GLOBAL ports
#HWPorts = hwports()
#if os.path.exists("/DietPi/config.txt"): # DietPi FIX!
# HWPorts.config_file_name = "/DietPi/config.txt"
