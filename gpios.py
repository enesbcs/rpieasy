#!/usr/bin/env python3
#############################################################################
################## Helper Library for GPIO handling #########################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import Settings
import os
import time
import lib.lib_syspwm as syspwm
try:
 import linux_os as OS
except:
 print("Linux OS functions can not be imported!")
try:
 import RPi.GPIO as GPIO
except:
 print("RPi.GPIO not installed!")
try:
 import smbus
except:
 print("I2C smbus not installed!")
 
PINOUT40 = [
{"ID":0,
"BCM":-1,
"name":["None"],
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
"BCM":2,
"name":["GPIO2","I2C1-SDA"],
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
"BCM":3,
"name":["GPIO3","I2C1-SCL"],
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
"BCM":4,
"name":["GPIO4"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":8,
"BCM":14,
"name":["GPIO14","UART-TX","BT-TX"],
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
"BCM":15,
"name":["GPIO15","UART-RX","BT-RX"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":11,
"BCM":17,
"name":["GPIO17","SPI1-CE1"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":12,
"BCM":18,
"name":["GPIO18/PWM0","SPI1-CE0","PCM-CLK"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":13,
"BCM":27,
"name":["GPIO27"],
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
"BCM":22,
"name":["GPIO22"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":16,
"BCM":23,
"name":["GPIO23"],
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
"BCM":24,
"name":["GPIO24"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":19,
"BCM":10,
"name":["GPIO10","SPI0-MOSI"],
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
"BCM":9,
"name":["GPIO9","SPI0-MISO"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":22,
"BCM":25,
"name":["GPIO25"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":23,
"BCM":11,
"name":["GPIO11","SPI0-SCLK"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":24,
"BCM":8,
"name":["GPIO8","SPI0-CE0"],
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
"BCM":7,
"name":["GPIO7","SPI0-CE1"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":27,
"BCM":0,
"name":["ID_SD"],
"canchange":0,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":28,
"BCM":1,
"name":["ID_SC"],
"canchange":0,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":29,
"BCM":5,
"name":["GPIO5"],
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
"BCM":6,
"name":["GPIO6"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":32,
"BCM":12,
"name":["GPIO12/PWM0"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":33,
"BCM":13,
"name":["GPIO13/PWM1"],
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
"BCM":19,
"name":["GPIO19/PWM1","SPI1-MISO","PCM-FS"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":36,
"BCM":16,
"name":["GPIO16","SPI1-CE2"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":37,
"BCM":26,
"name":["GPIO26"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":38,
"BCM":20,
"name":["GPIO20","SPI1-MOSI","PCM-DIN"],
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
"BCM":21,
"name":["GPIO21","SPI1-SCLK","PCM-DOUT"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1}
]

PINOUT26R2_DELTA = [
{"ID":11,
"BCM":17,
"name":["GPIO17"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":12,
"BCM":18,
"name":["GPIO18/PWM0"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1}
]

PINOUT26R1_DELTA = [
{"ID":3,
"BCM":0,
"name":["GPIO0","I2C0-SDA"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":5,
"BCM":1,
"name":["GPIO1","I2C0-SCL"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":11,
"BCM":17,
"name":["GPIO17"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":12,
"BCM":18,
"name":["GPIO18/PWM0"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
{"ID":13,
"BCM":21,
"name":["GPIO21"],
"canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1},
]

I2CDevices = [
 {"name": "MCP9808 Temp sensor",
  "addr": [0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x1F]},
 {"name": "Chirp! Water sensor",
  "addr": [0x20]},
 {"name": "MCP23008/MCP23017 I2C GPIO expander; LCD1602; PCF8574",
  "addr": [0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27]},
 {"name": "PCF8574A",
  "addr": [0x38,0x39,0x3A,0x3B,0x3C,0x3D,0x3E,0x3F]},
 {"name": "PN532",
  "addr": [0x24]},
 {"name": "VL53L0x",
  "addr": [0x29]},
 {"name": "VL6180X ToF sensor",
  "addr": [0x29]},
 {"name": "TSL2561 light sensor",
  "addr": [0x29,0x39,0x49]},
 {"name": "APDS-9960 IR/Color/Proximity Sensor",
  "addr": [0x39]},
 {"name": "SSD1305/SSD1306 monochrome OLED",
  "addr": [0x3C,0x3D]},
 {"name": "HTU21D-F/Si7021 Humidity/Temp sensor",
  "addr": [0x40]},
 {"name": "INA219 Current sensor",
  "addr": [0x40,0x41,0x44,0x45]},
 {"name": "PCA9685 PWM extender",
  "addr": [0x40,0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F,0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5A,0x5B,0x5C,0x5D,0x5E,0x5F,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6A,0x6B,0x6C,0x6D,0x6E,0x6F,0x71,0x72,0x73,0x74,0x75,0x76,0x77]},
 {"name": "SHT30/31/35 Humidity/Temp sensor",
  "addr": [0x44,0x45]},
 {"name": "PN532 NFC/RFID reader",
  "addr": [0x48]},
 {"name": "ADS1115/ADS1015 4-channel ADC",
  "addr": [0x48,0x49,0x4A,0x4B]},
 {"name": "LM75A; PCF8591; MCP3221",
  "addr": [0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F]},
 {"name": "MAX44009 ambient light sensor",
  "addr": [0x4A]},
 {"name": "BH1750",
  "addr": [0x23,0x5C]},
 {"name": "MPR121 touch sensor",
  "addr": [0x5a,0x5b,0x5c,0x5d]},
 {"name": "DHT12/AM2320",
  "addr": [0x5C]},
 {"name": "MCP4725 DAC",
  "addr": [0x60,0x61]},
 {"name": "DS1307/DS3231/PCF8523 RTC",
  "addr": [0x68]},
 {"name": "PCA9685 'All Call'",
  "addr": [0x70]},
 {"name": "BMP085/BMP180 Temp/Barometric",
  "addr": [0x77]},
 {"name": "HT16K33",
  "addr": [0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77]},
 {"name": "BMP280 Temp/Barometric;BME180 Temp/Barometric/Humidity",
  "addr": [0x76,0x77]},
 {"name": "ProMini Extender (standard)",
  "addr": [0x3F,0x4F,0x5F,0x6F]},
 {"name": "ProMini Extender (non-standard)",
  "addr": [0x7F]}

]

GPIOStatus = []

try:
 BOTH=GPIO.BOTH
 RISING=GPIO.RISING
 FALLING=GPIO.FALLING
except:
 BOTH=3
 RISING=1
 FALLING=2

class hwports:
 config_file_name = "/boot/config.txt" # /boot/config.txt
 CONFIG_ENABLE_I2C="dtparam=i2c_arm=on"
 CONFIG_ENABLE_I2C0="dtparam=i2c0=on"
 CONFIG_ENABLE_I2C1="dtparam=i2c1=on" 
 CONFIG_ENABLE_SPI0="dtparam=spi=on"
 CONFIG_ENABLE_SPI1_1="dtoverlay=spi1-1cs"
 CONFIG_ENABLE_SPI1_2="dtoverlay=spi1-2cs"
 CONFIG_ENABLE_SPI1_3="dtoverlay=spi1-3cs"
 CONFIG_ENABLE_I2S="dtparams=i2s=on"
 CONFIG_DISABLE_UART="enable_uart=0" #0/1
 CONFIG_ENABLE_UART="enable_uart=1"
 CONFIG_DISABLE_UART2="dtparam=uart0=off"
 CONFIG_BT_SWUART="dtoverlay=pi3-miniuart-bt"
 CONFIG_DISABLE_BT="dtoverlay=pi3-disable-bt"
 CONFIG_DISABLE_WIFI="dtoverlay=pi3-disable-wifi"
 CONFIG_PWM0="dtoverlay=pwm"
 CONFIG_PWM0_1="dtoverlay=pwm-2chan"
 CONFIG_ENABLE_AUDIO="dtparam=audio=on" #on/off
 CONFIG_DISABLE_AUDIO="dtparam=audio=off" #on/off
 CONFIG_ONEWIRE="dtoverlay=w1-gpio"
 CONFIG_GPIO="gpio="
 CONFIG_GPUMEM="gpu_mem"
 COMMAND_DISABLE_BT="sudo systemctl disable hciuart"
 CONFIG_ENABLE_RTC="dtoverlay=i2c-rtc," # ds1307, pcf8523, ds3231

 def __init__(self): # general init
  self.i2c_channels = [] # 0,1
  self.i2c_initialized = False
  self.i2cbus = None
  self.spi_channels = [] # 0,1
  self.spi_cs = [0,0]
  self.serial = 0
  self.bluetooth = 0     # 0:disabled,1:enabled with SW miniUART,2:enabled with HW UART
  self.wifi = 0          # 0:disabled,1:enabled
  self.audio = 0
  self.i2s = 0
  self.pwm = [0,0]          # 0.byte:pwm0 pin, 1.byte:pwm1 pin, no more
  self.rtc = ""             # /lib/udev/hwclock-set
  self.pwmo = []
  for p in range(22):
   self.pwmo.append({"pin":0,"o":False})
  try:
   rpitype = OS.getRPIVer()
  except:
   rpitype=[]
  try:
   po = rpitype["pins"]
  except:
   po = "0"
  try:
   bta = int(rpitype["bt"])
  except:
   bta = 0
  try:
   wf = int(rpitype["wlan"])
  except:
   wf = 0
  try:
   iram = rpitype["ram"]
  except:
   iram = "0"
  try:
   GPIO.setwarnings(False)
   GPIO.setmode(GPIO.BCM)
   self.gpioinit = True
  except:
   print("GPIO init failed")
   self.gpioinit = False

  self.pinnum = po
  self.internalwlan = (wf==1)
  self.internalbt   = (bta==1)
  self.gpumin = 16
  self.gpumax = self.gpumin
  if "256m" in iram.lower():
   self.gpumax = 192
  elif "512m" in iram.lower():
   self.gpumax = 448
  elif "1m" in iram.lower():
   self.gpumax = 944
  self.gpumem = self.gpumin

 def __del__(self):
   try:
    self.cleanup()
   except:
    pass

 def cleanup(self):
   if self.gpioinit:
    for p in range(len(self.pwmo)):
     try:
      if (self.pwmo[p]["o"] != False) and not (self.pwmo[p]["o"] is None):
       self.pwmo[p]["o"].stop()
     except:
      pass
    GPIO.cleanup()

 def gpio_function_name(self,func):
  typestr = "Unknown"
  try:
    typeint = int(func)
    if GPIO.IN==typeint:
      typestr = "Input"
    elif GPIO.OUT==typeint:
      typestr = "Output"
    elif GPIO.SPI==typeint:
      typestr = "SPI"
    elif GPIO.I2C==typeint:
      typestr = "I2C"
    elif GPIO.HARD_PWM==typeint:
      typestr = "HardPWM"
    elif GPIO.SERIAL==typeint:
      typestr = "Serial"
  except:
   typestr = "Unknown"
  return typestr

 def gpio_function_name_from_pin(self,gpio):
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
  return GPIO.gpio_function(bcmpin)

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

 def i2c_init(self):
  if self.i2c_initialized == False:
   if self.is_i2c_usable(1):
    self.i2cbus = smbus.SMBus(1)
    self.i2c_initialized = True
   elif self.is_i2c_usable(0):
    self.i2cbus = smbus.SMBus(0)
    self.i2c_initialized = True
  return self.i2c_initialized

 def i2c_read_block(self,address,cmd):
  retval = None
  if self.i2c_initialized:
   try:
    retval = self.i2cbus.read_i2c_block_data(address,cmd)
   except:
    retval = None
  return retval

 def is_i2c_usable(self,channel):
   result = False
   if channel==0:
    if self.pinnum=="26R1":
     result = True
   else:
    if self.pinnum=="26R2" or self.pinnum=="40":
     result = True
   return result

 def is_i2c_enabled(self,channel):
  if channel in self.i2c_channels:
   return True
  else:
   return False

 def enable_i2c(self,channel):
  if self.is_i2c_usable(channel) and (self.is_i2c_enabled(channel)==False):
   self.i2c_channels.append(channel)
   Settings.Pinout[3]["altfunc"] = 1
   Settings.Pinout[5]["altfunc"] = 1

 def disable_i2c(self,channel):
  if self.is_i2c_enabled(channel):
   self.i2c_channels.remove(channel)
   Settings.Pinout[3]["altfunc"] = 0
   Settings.Pinout[5]["altfunc"] = 0

 def is_spi_usable(self,channel):
   result = False
   try:
    channel = int(channel)
   except:
    return False
   if channel==0:
    if str(self.pinnum)=="26R1" or str(self.pinnum)=="26R2" or str(self.pinnum)=="40":
     result = True
   else:
    if str(self.pinnum)=="40":
     result = True
   return result

 def is_spi_enabled(self,channel):
  if channel in self.spi_channels:
   return True
  else:
   return False

 def enable_spi(self,channel,cs=3): # cs can 1,2,3 for spi1, 2 for spi0
  try:
   channel=int(channel)
   cs=int(cs)
  except:
   return False
  if self.is_spi_usable(channel):
   if (self.is_spi_enabled(channel)==False):
    self.spi_channels.append(channel)
   if channel==0:
    self.spi_cs[0] = 2
    Settings.Pinout[19]["altfunc"] = 1
    Settings.Pinout[21]["altfunc"] = 1
    Settings.Pinout[23]["altfunc"] = 1
    Settings.Pinout[24]["altfunc"] = 1
    Settings.Pinout[26]["altfunc"] = 1
   else:
    self.spi_cs[1] = int(cs)
    Settings.Pinout[35]["altfunc"] = 1
    Settings.Pinout[38]["altfunc"] = 1
    Settings.Pinout[40]["altfunc"] = 1
    Settings.Pinout[12]["altfunc"] = 1
    Settings.Pinout[11]["altfunc"] = 0
    Settings.Pinout[36]["altfunc"] = 0
    if self.spi_cs[1]>1:
     Settings.Pinout[11]["altfunc"] = 1
     if self.spi_cs[1]>2:
      Settings.Pinout[36]["altfunc"] = 1

 def disable_spi(self,channel):
  try:
   channel=int(channel)
  except:
   return False
  if self.is_spi_enabled(channel):
   self.spi_channels.remove(channel)
   if channel==0:
    Settings.Pinout[19]["altfunc"] = 0
    Settings.Pinout[21]["altfunc"] = 0
    Settings.Pinout[23]["altfunc"] = 0
    Settings.Pinout[24]["altfunc"] = 0
    Settings.Pinout[26]["altfunc"] = 0
   else:
    if Settings.Pinout[12]["altfunc"] == 1:
     Settings.Pinout[35]["altfunc"] = 0
     Settings.Pinout[38]["altfunc"] = 0
     Settings.Pinout[40]["altfunc"] = 0
     Settings.Pinout[12]["altfunc"] = 0
     Settings.Pinout[11]["altfunc"] = 0
     Settings.Pinout[36]["altfunc"] = 0

 def is_serial_enabled(self):
  return (self.serial==1)

 def set_serial(self,status):
  if (status==0) or (status==False):
   self.serial = 0
   if Settings.Pinout[8]["altfunc"]==1 or self.bluetooth==0:
    Settings.Pinout[8]["altfunc"] = 0
    Settings.Pinout[10]["altfunc"] = 0
  else:
   self.serial = 1
   Settings.Pinout[8]["altfunc"] = 1
   Settings.Pinout[10]["altfunc"] = 1

 def is_internal_bt_usable(self):
  return self.internalbt

 def get_internal_bt_level(self):
  return self.bluetooth

 def set_internal_bt(self,uartlevel): #1=sw,2=hw
  if self.is_internal_bt_usable():
   self.bluetooth=uartlevel
   if uartlevel>1:
    Settings.Pinout[8]["altfunc"] = 2
    Settings.Pinout[10]["altfunc"] = 2
   else:
    if Settings.Pinout[8]["altfunc"]==2:
     if self.serial==1:
      Settings.Pinout[8]["altfunc"] = 1
      Settings.Pinout[10]["altfunc"] = 1
     else:
      Settings.Pinout[8]["altfunc"] = 0
      Settings.Pinout[10]["altfunc"] = 0
    elif self.serial ==0:
      Settings.Pinout[8]["altfunc"] = 0
      Settings.Pinout[10]["altfunc"] = 0
  else:
   self.bluetooth=0

 def is_audio_enabled(self):
  return (self.audio==1)

 def is_internal_wifi_usable(self):
  return self.internalwlan

 def set_wifi(self,status):
  self.wifi = 0
  if self.is_internal_wifi_usable():
   if (status==1) or (status==True):
    self.wifi = 1

 def is_wifi_enabled(self):
  return (self.wifi==1)

 def set_audio(self,status):
  if (status==0) or (status==False):
   self.audio = 0
  else:
   self.audio = 1

 def is_audio_enabled(self):
  return (self.audio==1)

 def enable_pwm_pin(self,channel,pin,FirstRead=False):
  if channel>=0 and channel<=1:
   pid = 0
   for p in range(len(Settings.Pinout)):
    if int(Settings.Pinout[p]["BCM"])==int(pin):
     pid = p
     break
   pch = "PWM"+str(channel)
   if (Settings.Pinout[pid]["altfunc"] == 0) and (pch in Settings.Pinout[pid]["name"][0]):
    if self.pwm[channel] > 0 and pin != self.pwm[channel]:
     for p in range(len(Settings.Pinout)):
      if int(Settings.Pinout[p]["BCM"])==int(self.pwm[channel]) and int(Settings.Pinout[p]["startupstate"])==7:
       Settings.Pinout[p]["startupstate"] = -1
       break
    self.pwm[channel]=pin
    Settings.Pinout[pid]["startupstate"] = 7 # set to H-PWM
    if FirstRead:
     Settings.Pinout[pid]["actualstate"]=Settings.Pinout[pid]["startupstate"]
    try:
     if channel==0:
      self.pwmo[0]["o"] = syspwm.HPWM(0)
      self.pwmo[0]["pin"] = pin
     else:
      self.pwmo[1]["o"] = syspwm.HPWM(1)
      self.pwmo[1]["pin"] = pin
    except Exception as e:
      print(e)

 def disable_pwm_pin(self,channel):
  if channel>=0 and channel<=1:
   if self.pwm[channel] > 0:
     for p in range(len(Settings.Pinout)):
      if int(Settings.Pinout[p]["BCM"])==int(self.pwm[channel]) and int(Settings.Pinout[p]["startupstate"])==7:
       Settings.Pinout[p]["startupstate"] = -1
       break
   self.pwm[channel]=0
   try:
    if channel==0:
     if self.pwmo[0]["o"]:
      self.pwmo[0]["o"].stop()
    else:
     if self.pwmo[1]["o"]:
      self.pwmo[1]["o"].stop()
   except:
    pass

 def output_pwm(self,bcmpin,pprop,pfreq=1000): # default 1000Hz
  pin = int(bcmpin)
  prop = int(pprop)
  freq = int(pfreq)
  if pin in self.pwm: # hardpwm
   pid = 0
   if self.pwm[0] == pin:
    pid = 0
   else:
    pid = 1
   if prop<=0:
    self.pwmo[pid]["o"].stop()
   else:
    self.pwmo[pid]["pin"]=pin
    self.pwmo[pid]["o"].set_frequency(freq)
    self.pwmo[pid]["o"].set_duty_prop(prop)
    self.pwmo[pid]["o"].enable()
   return True
  else: # softpwm
   pfound = False
   for p in range(len(Settings.Pinout)):
     if int(Settings.Pinout[p]["BCM"])==pin :
      if (int(Settings.Pinout[p]["startupstate"]) not in [4,5,6]):
       return False # if not output skip

   if len(self.pwmo)>2:
    for p in range(2,len(self.pwmo)):
     if int(self.pwmo[p]["pin"])==pin:
      if (self.pwmo[p]["o"]):
       if prop<=0:
        self.pwmo[p]["o"].stop()
       else:
        self.pwmo[p]["o"].start(prop)
        self.pwmo[p]["o"].ChangeFrequency(freq)
        self.pwmo[p]["o"].ChangeDutyCycle(prop)
      pfound = True
      break
   if pfound==False:
    self.pwmo[p]["pin"] = pin
    self.pwmo[p]["o"] = GPIO.PWM(pin,freq)
    self.pwmo[p]["o"].start(prop)
   return True

 def pwm_get_func(self,pin):
  func = 0
  if pin==12 or pin==13:
   func=4
  elif pin==18 or pin==19:
   func=2
  return str(func)

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
    Settings.Pinout[12]["altfunc"] = 2
    Settings.Pinout[35]["altfunc"] = 2
    Settings.Pinout[38]["altfunc"] = 2
    Settings.Pinout[40]["altfunc"] = 2
   else:
    self.i2s=0
    if Settings.Pinout[12]["altfunc"]==2:
     Settings.Pinout[12]["altfunc"] = 0
     Settings.Pinout[35]["altfunc"] = 0
     Settings.Pinout[38]["altfunc"] = 0
     Settings.Pinout[40]["altfunc"] = 0

 def set1wgpio(self,bcmpin,FirstRead=False):
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      Settings.Pinout[b]["startupstate"] = 8
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
    if Settings.Pinout[pinid]["actualstate"]==7:
     bcmpin = int(Settings.Pinout[pinid]["BCM"])
     if bcmpin == self.pwm[0]:
      self.disable_pwm_pin(0)
     elif bcmpin == self.pwm[1]:
      self.disable_pwm_pin(1)
    if Settings.Pinout[pinid]["actualstate"]<7 and state<7:
     Settings.Pinout[pinid]["actualstate"]=state

 def setpinstate(self,PINID,state,force=False):
   if (force==False):
    if Settings.Pinout[PINID]["altfunc"]>0 or Settings.Pinout[PINID]["canchange"]!=1 or Settings.Pinout[PINID]["BCM"]<0:
     return False
#   if (int(state)<=0 and int(Settings.Pinout[PINID]["startupstate"])>0):
   if int(state)<=0:
#    pass # revert to default input
    Settings.Pinout[PINID]["startupstate"] = -1
    if self.gpioinit:
     GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.IN)
    self.setpinactualstate(PINID,99) # ugly hack
    return True
   elif state==1:
    pass # input
    Settings.Pinout[PINID]["startupstate"] = state
    if self.gpioinit:
     GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.IN)
    self.setpinactualstate(PINID,1)
    return True
   elif state==2:
    pass # input pulldown
    Settings.Pinout[PINID]["startupstate"] = state
    if self.gpioinit:
     GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    self.setpinactualstate(PINID,state)
    return True
   elif state==3:
    pass # input pullup
    Settings.Pinout[PINID]["startupstate"] = state
    if self.gpioinit:
     GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    self.setpinactualstate(PINID,state)
    return True
   elif state==4 or state==5 or state==6:
    if state==5:
     if self.gpioinit:
      GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.OUT, initial=GPIO.LOW)
    elif state==6:
     if self.gpioinit:
      GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.OUT, initial=GPIO.HIGH)
    else:
     if self.gpioinit:
      GPIO.setup(int(Settings.Pinout[PINID]["BCM"]), GPIO.OUT)
    Settings.Pinout[PINID]["startupstate"] = state
    self.setpinactualstate(PINID,4)
    return True
   elif state==7:
    self.enable_pwm_pin(0,int(Settings.Pinout[PINID]["BCM"]))
    if Settings.Pinout[PINID]["startupstate"] != 7:
     self.enable_pwm_pin(1,int(Settings.Pinout[PINID]["BCM"]))
    return True
   elif state==8:
    self.setpinactualstate(PINID,-1)
    self.set1wgpio(int(Settings.Pinout[PINID]["BCM"]))
    return True
   return False

 def initpinstates(self):
    if self.gpioinit:
     for b in range(len(Settings.Pinout)):
      if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
       if int(Settings.Pinout[b]["BCM"])>=0:
        if int(Settings.Pinout[b]["startupstate"])<7 and int(Settings.Pinout[b]["startupstate"])>=0:
         self.setpinstate(b,Settings.Pinout[b]["startupstate"],True)

 def readconfig(self):
    self.i2c_channels = [] # 0,1
    self.spi_channels = [] # 0,1
    self.spi_cs = [0,0]
    self.set_serial(1)
    self.i2s = 0
    if self.internalbt:
     self.bluetooth = 2
    if self.internalwlan:
     self.wifi = 1
    self.audio = 1
    self.pwm = [0,0]          # 0.byte:pwm0 pin, 1.byte:pwm1 pin, no more
# read config.txt
    try:
     with open(self.config_file_name) as f:
      for line in f:
       line = line.strip()
       if len(line)>0 and line[0] == "#":
        line = ""
       if self.CONFIG_ENABLE_I2C in line.lower():
        if self.is_i2c_usable(1):
         self.enable_i2c(1)
        else:
         self.enable_i2c(0)
       elif self.CONFIG_ENABLE_I2C0 in line.lower():
        self.enable_i2c(0)
       elif self.CONFIG_ENABLE_I2C1 in line.lower():
        self.enable_i2c(1)
       elif self.CONFIG_ENABLE_SPI0 in line.lower():
        self.enable_spi(0,2)
       elif self.CONFIG_ENABLE_SPI1_1 in line.lower():
        self.enable_spi(1,1)
       elif self.CONFIG_ENABLE_SPI1_2 in line.lower():
        self.enable_spi(1,2)
       elif self.CONFIG_ENABLE_SPI1_3 in line.lower():
        self.enable_spi(1,3)
       elif self.CONFIG_ENABLE_I2S in line.lower():
        self.set_i2s(1)
       elif self.CONFIG_DISABLE_UART in line.lower():
        self.set_serial(0)
       elif self.CONFIG_DISABLE_UART2 in line.lower():
        self.set_serial(0)
       elif self.CONFIG_ENABLE_UART in line.lower():
        self.set_serial(1)
       elif self.CONFIG_BT_SWUART in line.lower():
        self.set_internal_bt(1)
       elif self.CONFIG_DISABLE_BT in line.lower():
        self.set_internal_bt(0)
       elif self.CONFIG_DISABLE_WIFI in line.lower():
        self.wifi=0
       elif self.CONFIG_DISABLE_AUDIO in line.lower():
        self.audio=0
       elif self.CONFIG_ENABLE_RTC in line.lower():
        params = line.split(",")
        if len(params)>1:
         self.rtc=params[1].strip()  
       elif line.lower().startswith(self.CONFIG_GPUMEM):
        params = line.split("=")
        try:
         self.gpumem=int(params[1].strip())
        except:
         self.gpumem=self.gpumin
       elif self.CONFIG_PWM0 in line.lower() or self.CONFIG_PWM0_1 in line.lower():
        params = line.split(",")
        if self.CONFIG_PWM0_1 in line.lower():
         self.pwm = [18,19]
        else:
         self.pwm = [18,0]
        try:
         pwmi = 0
         for p in range(len(params)):
          params2 = params[p].split("=")
          if "pin" in params2[0].lower():
           self.enable_pwm_pin(pwmi,int(params2[1].strip()),True)
           pwmi=pwmi+1
        except:
         pass
        self.enable_pwm_pin(0,self.pwm[0],True)
        self.enable_pwm_pin(1,self.pwm[1],True)
       elif self.CONFIG_ONEWIRE in line.lower():
        pinfound = False
        params = line.split(",")
        for p in range(len(params)):
         pin = 0
         if "gpiopin" in params[p]:
          params2 = params[p].split('=')
          try:
           pin = int(params2[1].strip())
           pinfound = True
          except:
           pin = 0
         if pin!= 0:
          self.set1wgpio(pin,True)
        if pinfound==False:
         self.set1wgpio(4,True)
       elif line.lower().startswith(self.CONFIG_GPIO):
        params = line.split("=")
        bcmpin = -1
        try:
         bcmpin = int(params[1].strip())
        except:
         bcmpin = -1
        if bcmpin != -1:
          pstate = -1
          if "ip" in params[2]:
            pstate = 1
          if "pd" in params[2]:
            pstate = 2
          if "pu" in params[2]:
            pstate = 3
          if "pn" in params[2] or "np" in params[2]:
            pstate = 1
          if "op" in params[2]:
            pstate = 4
          if "dl" in params[2]:
            pstate = 5
          if "dh" in params[2]:
            pstate = 6
          if pstate != -1:
            self.setpinstartstate(bcmpin,pstate)
    except:
     pass
    if self.get_internal_bt_level()>1:
      self.set_serial(0)
      self.set_internal_bt(2) # uart collision resolving
    if self.i2s==1:
     self.set_i2s(1)
    for b in range(len(Settings.Pinout)):
     if Settings.Pinout[b]["altfunc"] != 0 and Settings.Pinout[b]["startupstate"]>0 and Settings.Pinout[b]["startupstate"]<9:
      Settings.Pinout[b]["startupstate"] = -1 # set to default

 def saveconfig(self):
  # save config.txt
    contents = []
    try:
     with open(self.config_file_name) as f:
      for line in f:
       line = line.strip()
       if len(line)>0 and line[0] == "#":
        line = ""
       if self.CONFIG_ENABLE_I2C in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_I2C0 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_I2C1 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_SPI0 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_SPI1_1 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_SPI1_2 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_SPI1_3 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_I2S in line.lower():
        line = ""
       elif self.CONFIG_DISABLE_UART in line.lower():
        line = ""
       elif self.CONFIG_DISABLE_UART2 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_UART in line.lower():
        line = ""
       elif self.CONFIG_BT_SWUART in line.lower():
        line = ""
       elif self.CONFIG_DISABLE_BT in line.lower():
        line = ""
       elif self.CONFIG_DISABLE_WIFI in line.lower():
        line = ""
       elif self.CONFIG_DISABLE_AUDIO in line.lower() or self.CONFIG_ENABLE_AUDIO in line.lower():
        line = ""
       elif self.CONFIG_PWM0 in line.lower():
        line = ""
       elif self.CONFIG_ENABLE_RTC in line.lower():
        line = ""
       elif self.CONFIG_PWM0_1 in line.lower():
        line = ""
       elif self.CONFIG_ONEWIRE in line.lower():
        line = ""
       elif line.lower().startswith(self.CONFIG_GPIO):
        line = ""
       elif line.lower().startswith(self.CONFIG_GPUMEM):
        line = ""
       if line != "":
        contents.append(line)
    except:
     pass
    with open(self.config_file_name,"w") as f:
     for c in range(len(contents)):
      f.write(contents[c]+"\n")
     if len(self.i2c_channels)>0:
      f.write(self.CONFIG_ENABLE_I2C+"\n")
     if self.is_i2c_enabled(1):
      f.write(self.CONFIG_ENABLE_I2C1+"\n")
     if self.is_i2c_enabled(0):
      f.write(self.CONFIG_ENABLE_I2C0+"\n")
     if self.is_spi_enabled(0):
      f.write(self.CONFIG_ENABLE_SPI0+"\n")
     if self.i2s==1:
      f.write(self.CONFIG_ENABLE_I2S+"\n")
     if self.is_spi_enabled(1):
      if self.spi_cs[1] == 1:
       f.write(self.CONFIG_ENABLE_SPI1_1+"\n")
      elif self.spi_cs[1] == 2:
       f.write(self.CONFIG_ENABLE_SPI1_2+"\n")
      elif self.spi_cs[1] == 3:
       f.write(self.CONFIG_ENABLE_SPI1_3+"\n")
     if self.is_serial_enabled()==False:
      f.write(self.CONFIG_DISABLE_UART+"\n")
     else:
      f.write(self.CONFIG_ENABLE_UART+"\n")
     if self.is_internal_bt_usable():
       if self.get_internal_bt_level()==1:
        f.write(self.CONFIG_BT_SWUART+"\n")
       elif self.get_internal_bt_level()==0:
        f.write(self.CONFIG_DISABLE_BT+"\n")
     if self.is_internal_wifi_usable():
       if self.is_wifi_enabled()==False:
        f.write(self.CONFIG_DISABLE_WIFI+"\n")
     if self.rtc!="":
      f.write(self.CONFIG_ENABLE_RTC+self.rtc+"\n")
     if self.is_audio_enabled():
      f.write(self.CONFIG_ENABLE_AUDIO+"\n")
     else:
      f.write(self.CONFIG_DISABLE_AUDIO+"\n")
     f.write(self.CONFIG_GPUMEM+"="+str(self.gpumem)+"\n")
     line = ""
     if sum(self.pwm)>0:
      if self.pwm[0] != 0:
       ppin = self.pwm[0]
      else:
       ppin = self.pwm[1]
      if self.pwm[0] > 0 and self.pwm[1] > 0:
       line += self.CONFIG_PWM0_1+",pin="+str(self.pwm[0])+",func="+self.pwm_get_func(self.pwm[0])+",pin2="+str(self.pwm[1])+",func2="+self.pwm_get_func(self.pwm[1]) 
      else:
       line += self.CONFIG_PWM0+",pin="+str(ppin)+",func="+self.pwm_get_func(ppin)
     if line != "":
      f.write(line+"\n")
     for b in range(len(Settings.Pinout)):
      if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1 and Settings.Pinout[b]["startupstate"]>0 and Settings.Pinout[b]["startupstate"]<9:
       if Settings.Pinout[b]["startupstate"] == 1: # input
        f.write(self.CONFIG_GPIO+str(Settings.Pinout[b]["BCM"])+"=ip\n")
       elif Settings.Pinout[b]["startupstate"] == 2: # input pulldown
        f.write(self.CONFIG_GPIO+str(Settings.Pinout[b]["BCM"])+"=ip,pd\n")
       elif Settings.Pinout[b]["startupstate"] == 3: # input pullup
        f.write(self.CONFIG_GPIO+str(Settings.Pinout[b]["BCM"])+"=ip,pu\n")
       elif Settings.Pinout[b]["startupstate"] == 4: # out
        f.write(self.CONFIG_GPIO+str(Settings.Pinout[b]["BCM"])+"=op\n")
       elif Settings.Pinout[b]["startupstate"] == 5: # out lo
        f.write(self.CONFIG_GPIO+str(Settings.Pinout[b]["BCM"])+"=op,dl\n")
       elif Settings.Pinout[b]["startupstate"] == 6: # out hi
        f.write(self.CONFIG_GPIO+str(Settings.Pinout[b]["BCM"])+"=op,dh\n")
       elif Settings.Pinout[b]["startupstate"] == 8: # 1wire
        f.write(self.CONFIG_ONEWIRE+",gpiopin="+str(Settings.Pinout[b]["BCM"])+"\n")

def is_i2c_lib_available():
 res = False
 try:
  import smbus
  res = True
 except:
  res = False
 return res

def i2cscan(bus_number):
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

def geti2cdevname(devaddr):
 global I2CDevices
 name = ""
 for i in range(len(I2CDevices)):
  if int(devaddr) in I2CDevices[i]["addr"]:
   if name!="":
    name += "; "
   name += I2CDevices[i]["name"]
 if name == "":
  name = "Unknown"
 return name

def GPIO_get_statusid(gpionum): # input: BCM GPIO num, output: GPIOStatus entry number or -1
 global GPIOStatus
 res = -1
 for i in range(len(GPIOStatus)):
  try:
   if int(GPIOStatus[i]["pin"])==int(gpionum):
    res = i
    break
  except:
   pass
 return res

def GPIO_refresh_status(pin,pstate=-1,pluginid=0,pmode="unknown"):
 global GPIOStatus, HWPorts
 pin = int(pin)
 if pin<0:
  return -1
 createnew = False
 gi = GPIO_get_statusid(pin)
 print(gi)
 if gi==-1:
  createnew = True
  if pmode=="unknown":
   try:
    pmode = HWPorts.gpio_function_name_from_pin(pin).lower()
   except Exception as e:
    pass
  if pluginid==0:
   for tp in range(len(Settings.Tasks)):
    try:
     if pin in Settings.Tasks[tp].taskdevicepin:
      pluginid = Settings.Tasks[tp].pluginid
      break
    except:
     pass
 else:
  if pmode!="unknown":
   GPIOStatus[gi]["mode"]=pmode.strip().lower()
  else:
   try:
    pmode = HWPorts.gpio_function_name_from_pin(pin).lower()
    GPIOStatus[gi]["mode"]=pmode.strip().lower()
   except Exception as e:
    pass
 if pstate==-1:
   if ("input" in pmode) or ("output" in pmode):
    try:
     pstate = int(HWPorts.input(int(pin)))
    except:
     pstate = -1
 elif createnew==False:
   GPIOStatus[gi]["state"] = int(pstate)
 if createnew:
  tstruc = {"plugin":pluginid,"pin":pin,"mode": pmode, "state": pstate}
  gi = len(GPIOStatus)
  GPIOStatus.append(tstruc)
 return gi

#Init Hardware GLOBAL ports
HWPorts = hwports()
if os.path.exists("/DietPi/config.txt"): # DietPi FIX!
 HWPorts.config_file_name = "/DietPi/config.txt"
