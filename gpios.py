#!/usr/bin/env python3
#############################################################################
################## Helper Library for GPIO handling #########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import Settings
import os
import time

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
 {"name": "MPU6050 Triple axis gyroscope & accelerometer",
  "addr": [0x68,0x69]},
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

def GPIO_refresh_status(pin,pstate=-1,pluginid=0,pmode="unknown",logtext=""):
 global GPIOStatus, HWPorts
 pin = int(pin)
 if pin<0:
  return -1
 createnew = False
 gi = GPIO_get_statusid(pin)
# print(gi)
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
  GPIOStatus[gi]["log"]=logtext.strip()
 if pstate==-1:
   if ("input" in pmode) or ("output" in pmode):
    try:
     pstate = int(HWPorts.input(int(pin)))
    except:
     pstate = -1
 elif createnew==False:
   GPIOStatus[gi]["state"] = int(pstate)
 if createnew:
  tstruc = {"log": logtext,"plugin":pluginid,"pin":pin,"mode": pmode, "state": pstate}
  gi = len(GPIOStatus)
  GPIOStatus.append(tstruc)
 return gi

def GPIO_get_status(gpionum): # input: BCM GPIO num, output: GPIOStatus string
 global GPIOStatus
 gpionum=int(gpionum)
 result = "{}"
 if gpionum<len(GPIOStatus) and gpionum>-1:
  result = str(GPIOStatus[gpionum]).replace("'",'"').replace(', ',',\n')
  result = result.replace("{","{\n").replace("}","\n}")
 return result

def preinit(gpiotype):
 global HWPorts, BOTH, RISING, FALLING, IN, OUT, PUD_UP, PUD_DOWN
 #Init Hardware GLOBAL ports
 if gpiotype==10: # RPI
  import lib.lib_rpigpios as GPIOHW
  from lib.lib_rpigpios import hwports
  BOTH=GPIOHW.BOTH
  RISING=GPIOHW.RISING
  FALLING=GPIOHW.FALLING
  IN=GPIOHW.IN
  OUT=GPIOHW.OUT
  PUD_UP=GPIOHW.PUD_UP
  PUD_DOWN=GPIOHW.PUD_DOWN
  HWPorts = hwports()
  if os.path.exists("/DietPi/config.txt"): # DietPi FIX!
   HWPorts.config_file_name = "/DietPi/config.txt"
 elif gpiotype==3: # OPI
  import lib.lib_opigpios as GPIOHW
  from lib.lib_opigpios import hwports
  BOTH=GPIOHW.BOTH
  RISING=GPIOHW.RISING
  FALLING=GPIOHW.FALLING
  IN=GPIOHW.IN
  OUT=GPIOHW.OUT
  PUD_UP=GPIOHW.PUD_UP
  PUD_DOWN=GPIOHW.PUD_DOWN
  HWPorts = hwports()
 elif gpiotype==19: # FTDI
  import lib.lib_ftdigpios as GPIOHW
  from lib.lib_ftdigpios import hwports
  BOTH=GPIOHW.BOTH
  RISING=GPIOHW.RISING
  FALLING=GPIOHW.FALLING
  IN=GPIOHW.IN
  OUT=GPIOHW.OUT
  PUD_UP=GPIOHW.PUD_UP
  PUD_DOWN=GPIOHW.PUD_DOWN
  HWPorts = hwports()

#HWPorts = None
