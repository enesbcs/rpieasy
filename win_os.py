#!/usr/bin/env python3
#############################################################################
############## Helper Library for OS specific functions WINDOWS #############
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import misc
import time
import os
import re
import itertools
import Settings
import rpieGlobals
import subprocess
import wmi # pip install WMI
import pythoncom

class autorun:

 def __init__(self): # general init
  pass

 def readconfig(self):
    pass

 def saveconfig(self):
    pass

def read_cpu_temp(): 
 try:
  pythoncom.CoInitialize()
  w = wmi.WMI(namespace="root\wmi")
  temperature_info = w.MSAcpi_ThermalZoneTemperature()[0]
  temp = (temperature_info.CurrentTemperature/10.0)-273.15
 except Exception as e:
  temp = 0
 return temp

def read_cpu_usage():
 try:
  pythoncom.CoInitialize()
  c = wmi.WMI()
  noread = True
  cc = 5
  while noread and cc>0:
   x = [cpu.LoadPercentage for cpu in c.Win32_Processor()]
   cc = cc - 1
   if len(x)>0:
    cc=0
  u = sum(x)/len(x)
 except:
  u = 100
 return u

def get_memory():
  try:
   m = 0
   pythoncom.CoInitialize()
   comp = wmi.WMI()
   for i in comp.Win32_OperatingSystem():
    m = int(i.FreePhysicalMemory)
  except:
    m = 0
  return m

def FreeMem():
 return get_memory()

def get_ip(cardnum=0):
   ips=""
   if cardnum==0:
    try:
     cardnum=Settings.NetMan.getprimarydevice()
     if (Settings.NetworkDevices[cardnum].ip==""):
      cardnum=Settings.NetMan.getsecondarydevice()
    except:
     ips = ""
   if cardnum<len(Settings.NetworkDevices):
      ips = Settings.NetworkDevices[cardnum].ip
   if ips!="":
      return ips
   f = subprocess.getoutput("ipconfig")
   ipconfig = f.split('\n')
   for line in ipconfig:
        if 'IPv4' in line:
            ip = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',line)
            if ip:
                return ip[0]
   return False

def get_rssi():
    resstr = "-49.20051" # dummy, not implemented
    return resstr

def check_permission():
  try:
   euid = os.geteuid()
   if euid != 0:
      return False
   else:
      return True
  except:
   return False
  
def gethardware():
    return "Windows PC" # dummy, not implemented

def is_package_installed(pkgname):
   return False

def is_command_found(pkgname):
   return False

def checkRPI():
   return False

def getRPIVer():
    hwarr = { 
      "name": "Unknown model",
      "pins": ""
    }
    return hwarr

def getsounddevs(playbackdevs = True):
    devlist = []
    return devlist

def getsoundsel():
    cardnum = 0
    return cardnum

def updateaudiocard(number):
    pass

def getosfullname():
    return "Microsoft($) Windows($)"

def get_cpu():
     cspd = {"speed":"Unknown","arch":"Unknown","core":1,"model":"Unknown"}
     return cspd

def scan_dir(dir):
    dirs = []
    files = []
    try:
     for name in os.listdir(dir):
        path = os.path.join(dir, name)
        if os.path.isfile(path):
            files.append([path,os.path.getsize(path)])
        else:
            dirs.append([path,"DIR"])
    except:
     pass
    return dirs+files

def delete_dir(dir):
    if dir=="" or dir=="." or dir==".." or dir=="/":
     return False
    dirs = []
    files = []
    try:
     for name in os.listdir(dir):
        path = os.path.join(dir, name)
        if os.path.isfile(path):
            files.append(path)
        else:
            dirs.append(path)
    except:
     pass
    success = False
    try:
     for f in files:
      os.remove(f)
     for d in dirs:
      os.rmdir(d)
     os.rmdir(dir)
     success = True
    except:
     success = False
    return success

def delete_file(fname):
    success = False
    try:
     os.remove(fname)
     success = True
    except:
     success = False
    return success

def settingstozip():
     conf_zip = "data/data.zip"
     try:
      if os.path.exists(conf_zip):
       os.remove(conf_zip)
      output = os.popen('zip -j -9 -D '+str(conf_zip)+' data/*.json')
      for l in output:
       pass
     except:
      pass
     if os.path.exists(conf_zip):
      return conf_zip
     else:
      return ""

def extractzip(zipname,destdir=""):
     try:
      cmdline = 'unzip -o -q '+str(zipname)
      if destdir != "":
       cmdline += ' -d '+str(destdir)
      output = os.popen(cmdline)
      for l in output:
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(l)) #       pass
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(e)) #       pass

def getfirstusername():
     return False

def runasfirstuser(subprocess_options): # some applications, such as VLC will not run as root, try to run as the first normal user
   result = "user"
   return result

def checkboot_ro():
     err = False
     return err

def getfilecontent(fname):
     resbuf = []
     cfname = str(fname)
     if fname.startswith("files/") == False:
      cfname = "files/"+cfname
     try:
      if os.path.exists(cfname):
       with open(cfname) as f:
        for line in f:
         line = line.strip()
         resbuf.append(line)
     except:
      resbuf = []
     return resbuf

def get_bootparams(): # RPI only
     fname = ""
     return fname

def get_i2c_state(m=0): # RPI only
    if m==0:
     tstr = "ERROR: I2C module not started"
    else:
     fname = "/etc/modules"
     tstr = "ERROR: i2c-dev is not found in "+fname
    return tstr

def disable_serialsyslog():
   pass

def cmdline_rootcorrect(cmdline):
  res = cmdline
  if "sudo " in cmdline:
   if check_permission(): # only needed if we have root access
    res = cmdline.replace("sudo -H ","")
    res = res.replace("sudo ","")
  return res.strip()

def checkOPI():
   return False

def getarmbianinfo():
    hwarr = { 
      "name": "Unknown model",
      "shortname":"unknown",
      "version":"0.0",
      "pinout":"",
      "pins": "0"
    }
    return hwarr

def getsoundmixer():
  return ""

def getvolume(): # volume in percentage
  vol = 0
  return vol

def setvolume(volume): # volume in percentage
   pass

def detectNM():
   nm = False
   return nm
