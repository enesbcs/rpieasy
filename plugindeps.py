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
 "apt": ["python3-pip","python3-setuptools"], # Arch Linux=python-pip!! Arch package names may differ, will need more work...
 "pip": ["paho-mqtt"],
 "testcmd": "import paho.mqtt.client as mqtt\ntestmqttc = mqtt.Client()",
 "installed":-1},
{"name": "Adafruit_ADS1x15",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["adafruit-ads1x15"],
 "testcmd": "import Adafruit_ADS1x15",
 "installed":-1},
{"name": "GPIO",
 "apt": ["python3-dev","python3-pip","python3-setuptools"],
 "pip":["RPi.GPIO"],
 "testcmd":"import RPi.GPIO as GPIO\ntest = GPIO.getmode()",
"installed":-1},
{ "name":"i2c",
 "apt": ["python3-smbus","i2c-tools"],
 "testcmd":"import smbus",
 "installed":-1},
{"name":"DHT",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["Adafruit_DHT"],
 "testcmd": "import Adafruit_DHT\ntest=Adafruit_DHT.DHT22",
 "installed":-1},
{"name":"apds",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["apds9960"],
 "testcmd": "from apds9960.const import *\ntest=APDS9960_I2C_ADDR",
 "installed":-1},
{"name":"pygame",
 "apt": ["python3-pip","libsdl-image1.2-dev","libsdl-mixer1.2-dev","libsdl-ttf2.0-dev","libsdl1.2-dev","ffmpeg","libfreetype6-dev","python3-dev","libportmidi-dev","libportmidi0","python3-setuptools"],
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
{"name":"wiegand_io2",
 "apt": ["wiringpi","build-essential","python3-pip","python3-setuptools"],
 "testcmd": "import wiegand_io2",
 "installcmd" : "cd lib/wiegand_io2 && sudo python3 wiegand_setup.py install && cd ../..",
 "installed":-1},
{"name":"bluepy",
 "apt": ["python3-pip","libglib2.0-dev","python3-setuptools"],
 "pip": ["bluepy"],
 "testcmd": "from bluepy import btle",
 "installed":-1},
{"name":"hidapi",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["hidapi"],
 "testcmd": "import hid",
 "installed":-1},
{"name":"Adafruit_DHT",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["Adafruit_DHT"],
 "testcmd": "import Adafruit_DHT",
 "installed":-1},
{"name":"linux-kernel",
"testcmd" : "if misc.getosname(0)!='linux':\n raise Exception('Linux kernel needed')",
"installed":-1},
{"name":"pyserial",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["pyserial"],
 "testcmd": "import serial.tools.list_ports",
 "installed":-1},
{"name": "OLED",
 "apt": ["python3-pip", "libfreetype6-dev", "libjpeg-dev", "build-essential","python3-dev","libtiff5","libopenjp2-7","python3-setuptools"],
 "pip": ["luma.oled"],
 "testcmd": "from luma.core.render import canvas",
 "installed":-1},
{"name": "MCP",
 "apt": [],
 "pip": [],
 "testcmd": "import lib.MCP230XX.MCP230XX",
 "installed":-1},
{"name":"rcswitch",
 "apt": ["wiringpi","python3-pip","build-essential","python3-setuptools"],
 "pip": ["setuptools"],
 "testcmd": "import py_rcswitch",
 "installcmd" : "cd lib/py_rcswitch && sudo python3 py_rcswitch_setup.py install && cd ../..",
 "installed":-1},
{"name":"ws2812",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["rpi_ws281x"],
 "testcmd": "from rpi_ws281x import *",
 "installed":-1},
{"name": "LCD",
 "apt": ["python3-pip", "python3-dev","python3-setuptools"],
 "pip": ["RPLCD"],
 "testcmd": "from RPLCD.i2c import CharLCD",
 "installed":-1},
{"name": "pca9685",
 "apt": ["python3-pip", "python3-dev","python3-setuptools"],
 "pip": ["PCA9685-driver"],
 "testcmd": "from pca9685_driver import Device",
 "installed":-1},
{"name": "tm1637",
 "apt": ["python3-pip", "python3-dev", "wiringpi","python3-setuptools"],
 "pip": ["raspberrypi-python-tm1637","wiringpi"],
 "testcmd": "import tm1637",
 "installed":-1},
{"name":"ina219",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["pi-ina219"],
 "testcmd": "from ina219 import INA219",
 "installed":-1},
{"name":"suntime",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["suntime"],
 "testcmd": "from suntime import Sun",
 "installed":-1},
{"name":"pydigitemp",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["pydigitemp"],
 "testcmd": "from digitemp.device import AddressableDevice",
 "installed":-1},
{"name":"pysolar",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["pytz","pysolar"],
 "testcmd": "from pysolar import solar",
 "installed":-1},
{"name":"mysql",
 "apt": ["python3-pip","python3-setuptools"],
 "pip": ["PyMySQL"],
 "testcmd": "import pymysql",
 "installed":-1},
{"name":"sqlite",
 "testcmd": "import sqlite3",
 "installed":-1},
{"name":"pocketsphinx",
 "apt": ["python3-dev","python3-pip","build-essential","swig","libpulse-dev","libasound2-dev","python3-pyaudio"],
 "pip": ["pocketsphinx","SpeechRecognition"],
 "testcmd": "import speech_recognition as sr",
 "installed":-1},

]

controllerdependencies = [
{"controllerid":"2",       # Domoticz MQTT
"modules":["paho-mqtt"]},
{"controllerid":"13",      # ESPEasy P2P
"modules":["linux-kernel"]},
{"controllerid":"14",      # Generic MQTT
"modules":["paho-mqtt"]},
{"controllerid":"16",      # DBStore
"modules":["sqlite","mysql"]}

]

plugindependencies = [
{"pluginid": "26", #Sysinfo
 "supported_os_level": [1,2,10]},
{"pluginid": "1", #Switch
 "supported_os_level": [10],
 "modules":["GPIO"]},
{"pluginid": "3", #Pulse
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
 "modules":["GPIO","wiegand_io2"]},
{"pluginid": "7", # PCF8591
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "9", # MCP
 "supported_os_level": [10],
 "modules":["GPIO","i2c","MCP"]},
{"pluginid": "10", # BH1750
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "11", # PME
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "12", # LCD
 "supported_os_level": [10],
 "modules":["i2c","LCD"]},
{"pluginid": "13", #SR04
 "supported_os_level": [10],
 "modules":["GPIO"]},
{"pluginid": "14", # Si7021
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "15", # tsl2561
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "17", # PN532
 "supported_os_level": [10],
 "modules":["GPIO","i2c"]},
{"pluginid": "19", # PCF8574
 "supported_os_level": [10],
 "modules":["GPIO","i2c"]},
{"pluginid": "22", # PCA9685
 "supported_os_level": [10],
 "modules":["GPIO","i2c","pca9685"]},
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
{"pluginid": "27", # INA219
 "supported_os_level": [10],
 "modules":["i2c","ina219"]},
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
{"pluginid": "57", # HT16K33 LED
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "58", # HT16K33 Key
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "59", #Rotary
 "supported_os_level": [10],
 "modules":["GPIO"]},
{"pluginid": "62", # MPR121
 "supported_os_level": [10],
 "modules":["GPIO","i2c"]},
{"pluginid": "64", # APDS9960
 "supported_os_level": [10],
 "modules":["i2c","apds"]},
{"pluginid": "69", # LM75
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "73", # 7DGT
 "supported_os_level": [10],
 "modules":["tm1637"]},
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
{"pluginid": "202", # MCP9808
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "203", # MCP4725
 "supported_os_level": [10],
 "modules":["i2c"]},
{"pluginid": "204", #Stepper motor
 "supported_os_level": [10],
 "modules":["GPIO"]},
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
{"pluginid": "506", # pocketsphinx
 "supported_os_level": [1,2,10],
 "modules":["pocketsphinx"]},
{"pluginid": "508", #Temper
 "supported_os_level": [1,2,10],
 "modules":["pyserial","linux-kernel"]},
{"pluginid": "509", # EVDEV
 "modules":["linux-kernel"]},
{"pluginid": "510", # BLE iTag
 "modules":["bluepy"]},
{"pluginid": "512", # BLE Xiaomi Temp
 "modules":["bluepy"]},
{"pluginid": "513", # BLE Xiaomi Clock
 "modules":["bluepy"]},
{"pluginid": "514", # USB-Dallas
 "supported_os_level": [1,2,10],
 "modules":["pyserial","pydigitemp"]},
{"pluginid": "515", # BLE MiFlora
 "modules":["bluepy"]},

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
     installprog = "sudo -H pip3 install "+ installprog.strip()
     if OS.is_command_found("sudo")==False: # if sudo is installed use it because -H option is important
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
