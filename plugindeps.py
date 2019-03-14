#!/usr/bin/env python3
#############################################################################
############# Helper Library for Plugin dependency check&install ############
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import subprocess
import os
import rpieGlobals
import misc
try:
 import linux_os as OS
except:
 print("Linux OS import error!")

modulelist = [
{"name":"paho-mqtt",
 "apt": ["python3-pip"], # Arch Linux=python-pip!! Arch package names may differ, will need more work...
 "pip": ["paho-mqtt"],
 "testcmd": "import paho.mqtt.client as mqtt\ntestmqttc = mqtt.Client()",
 "installed":-1},
{"name": "Adafruit_ADS1x15",
 "apt": ["python3-pip"],
 "pip": ["adafruit-ads1x15"],
 "testcmd": "import Adafruit_ADS1x15",
 "installed":-1},
{"name": "GPIO",
 "apt": ["python3-dev","python3-rpi.gpio"],
 "testcmd":"import RPi.GPIO as GPIO\ntest = GPIO.getmode()",
 "installed":-1},
{ "name":"i2c",
 "apt": ["python3-smbus","i2c-tools"],
 "testcmd":"import smbus",
 "installed":-1},
{"name":"DHT",
 "apt": ["python3-pip"],
 "pip": ["Adafruit_DHT"],
 "testcmd": "import Adafruit_DHT\ntest=Adafruit_DHT.DHT22",
 "installed":-1},
{"name":"apds",
 "apt": ["python3-pip"],
 "pip": ["apds9960"],
 "testcmd": "from apds9960.const import *\ntest=APDS9960_I2C_ADDR",
 "installed":-1},
{"name":"pygame",
 "apt": ["python3-pip"],
 "pip": ["pygame"],
 "testcmd": "import pygame\ntest=pygame.mixer.get_init()",
 "installed":-1},
{"name":"vlc",
 "apt": ["vlc-nox"],
 "testcmd":"import subprocess\nsubprocess.Popen(['/usr/bin/cvlc', '--version'])",
 "installed":-1},
{"name":"wiegand_io",
 "apt": ["wiringpi","build-essential"],
 "pip": ["setuptools"],
 "testcmd": "import wiegand_io",
 "installcmd" : "cd lib/wiegand_io && sudo python3 wiegand_setup.py install && cd ../..",
 "installed":-1},
{"name":"bluepy",
 "apt": ["python3-pip","libglib2.0-dev"],
 "pip": ["bluepy"],
 "testcmd": "from bluepy import btle",
 "installed":-1},
{"name":"hidapi",
 "apt": ["python3-pip"],
 "pip": ["hidapi"],
 "testcmd": "import hid",
 "installed":-1},
{"name":"Adafruit_DHT",
 "apt": ["python3-pip"],
 "pip": ["Adafruit_DHT"],
 "testcmd": "import Adafruit_DHT",
 "installed":-1},
{"name":"linux-kernel",
"testcmd" : "if misc.getosname(0)!='linux':\n raise Exception('Linux kernel needed')",
"installed":-1},
{"name":"pyserial",
 "apt": ["python3-pip"],
 "pip": ["pyserial"],
 "testcmd": "import serial.tools.list_ports",
 "installed":-1},
{"name": "OLED",
 "apt": ["python3-pip", "libfreetype6-dev", "libjpeg-dev", "build-essential","python3-dev","libtiff5","libopenjp2-7"],
 "pip": ["luma.oled"],
 "testcmd": "from luma.core.render import canvas",
 "installed":-1},
{"name": "MCP",
 "apt": [],
 "pip": [],
 "testcmd": "import lib.MCP230XX.MCP230XX",
 "installed":-1},
{"name":"rcswitch",
 "apt": ["wiringpi","python3-pip","build-essential"],
 "pip": ["setuptools"],
 "testcmd": "import py_rcswitch",
 "installcmd" : "cd lib/py_rcswitch && sudo python3 py_rcswitch_setup.py install && cd ../..",
 "installed":-1},
{"name":"ws2812",
 "apt": ["python3-pip"],
 "pip": ["rpi_ws281x"],
 "testcmd": "from rpi_ws281x import *",
 "installed":-1},


]

controllerdependencies = [
{"controllerid":"2",       # Domoticz MQTT
"modules":["paho-mqtt"]},
{"controllerid":"13",      # ESPEasy P2P
"modules":["linux-kernel"]},
{"controllerid":"14",      # Generic MQTT
"modules":["paho-mqtt"]}
]

plugindependencies = [
{"pluginid": "26", #Sysinfo
 "supported_os_level": [1,2,10]},
{"pluginid": "1", #Switch
 "supported_os_level": [10],
 "modules":["GPIO"]},
{"pluginid": "4", #DS18b20
 "supported_os_level": [1,2,10],
 "modules":["linux-kernel"]},
{"pluginid": "5", # DHT
 "supported_os_level": [10],
 "modules":["Adafruit_DHT"]},
{"pluginid": "8", # Wiegand GPIO
 "supported_os_level": [10],
 "modules":["GPIO","wiegand_io"]},
{"pluginid": "9", # MCP
 "supported_os_level": [10],
 "modules":["GPIO","i2c","MCP"]},
{"pluginid": "10", # BH1750
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "11", # PME
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "14", # Si7021
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "15", # tsl2561
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "23", # OLED
 "supported_os_level": [10],
 "modules":["i2c","OLED"]},
{"pluginid": "24", # mlx90614
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "25", # ADS1x15
 "supported_os_level": [10],
 "modules":["i2c","Adafruit_ADS1x15"]},
{"pluginid": "26", #SysInfo
 "supported_os_level": [1,2,10],
 "modules":["linux-kernel"]},
{"pluginid": "28", # BMP280
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "29", # DomoOutput nem csak gpio??
 "supported_os_level": [10],
 "modules":["GPIO"]},
{"pluginid": "36", # FramedOLED
 "supported_os_level": [10],
 "modules":["i2c","OLED"]},
{"pluginid": "38", # Neopixel
 "supported_os_level": [10],
 "modules":["GPIO","ws2812"]},
{"pluginid": "49", #MH-Z19
 "supported_os_level": [1,2,10],
 "modules":["pyserial"]},
{"pluginid": "51", # AM2320
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "59", #Rotary
 "supported_os_level": [10],
 "modules":["GPIO"]},
{"pluginid": "64", # APDS9960
 "supported_os_level": [10],
 "modules":["i2c","apds"]},
{"pluginid": "111", #RF433 receiver
 "supported_os_level": [10],
 "modules":["GPIO","rcswitch"]},
{"pluginid": "112", #RF433 sender
 "supported_os_level": [10],
 "modules":["GPIO","rcswitch"]},
{"pluginid": "133", # VL53L0X
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "153", # MAX44009
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "200", #Dual Switch
 "supported_os_level": [10],
 "modules":["GPIO"]},
{"pluginid": "201", #Generic Serial
 "supported_os_level": [1,2,10],
 "modules":["pyserial"]},
{"pluginid": "501", # USB relay
 "modules":["hidapi"]},
{"pluginid": "502", # pygame play wav/mp3
 "supported_os_level": [1,2,10],
 "modules":["pygame"]},
{"pluginid": "503", # pygame play wav/mp3
 "supported_os_level": [1,2,10],
 "modules":["pygame"]},
{"pluginid": "505", # vlc radio play
 "supported_os_level": [1,2,10],
 "modules":["vlc"]},
{"pluginid": "508", #Temper
 "supported_os_level": [1,2,10],
 "modules":["pyserial","linux-kernel"]},
{"pluginid": "509", # EVDEV
 "modules":["linux-kernel"]},
{"pluginid": "510", # BLE iTag
 "modules":["bluepy"]}
]

def ismoduleusable(modulename):
 global modulelist
 usable = False
 for i in range(len(modulelist)):
  if modulelist[i]["name"]==modulename:
   if modulelist[i]["installed"]==0:
    return False
   elif modulelist[i]["installed"]==1:
    return True
   elif modulelist[i]["installed"]==-1:
    usable = True
    try:
     exec(modulelist[i]["testcmd"])
    except:
     usable = False
    if usable:
     modulelist[i]["installed"]=1
    else:
     modulelist[i]["installed"]=0
 return usable

def installdeps(modulename):
 global modulelist
 for i in range(len(modulelist)):
  if modulelist[i]["name"]==modulename and modulelist[i]["installed"]!=1:
   modulelist[i]["installed"] = -1
   try:
    if modulelist[i]["apt"]:
     installprog = " "
     for j in range(len(modulelist[i]["apt"])):
      if rpieGlobals.ossubtype==2: # arch exceptions
       if "python3-pip" in modulelist[i]["apt"][j]:
        modulelist[i]["apt"][j].replace("python3-pip","python-pip")
      installprog += modulelist[i]["apt"][j] + " "
     if rpieGlobals.ossubtype in [1,10]:
      installprog = OS.cmdline_rootcorrect("sudo apt-get update && sudo apt-get install -y "+ installprog.strip())
     elif rpieGlobals.ossubtype==2:
      installprog = OS.cmdline_rootcorrect("yes | sudo pacman -S "+ installprog.strip())
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,installprog)
     proc = subprocess.Popen(installprog, shell=True, stdin=None, stdout=open(os.devnull,"wb"), executable="/bin/bash")
     proc.wait()
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   try:
    if modulelist[i]["pip"]:
     installprog = " "
     for j in range(len(modulelist[i]["pip"])):
      installprog += modulelist[i]["pip"][j] + " "
     installprog = OS.cmdline_rootcorrect("sudo -H pip3 install "+ installprog.strip())
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,installprog)
     proc = subprocess.Popen(installprog, shell=True, stdin=None, stdout=open(os.devnull,"wb"), executable="/bin/bash")
     proc.wait()
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   try:
    if modulelist[i]["installcmd"]:
     installprog = OS.cmdline_rootcorrect(modulelist[i]["installcmd"].strip())
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,installprog)
     proc = subprocess.Popen(installprog, shell=True, stdin=None, stdout=open(os.devnull,"wb"), executable="/bin/bash")
     proc.wait()
   except Exception as e:
     if e!='installcmd':
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   break
