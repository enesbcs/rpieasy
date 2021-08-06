#!/usr/bin/env python3
#############################################################################
############### Helper Library for OS specific functions LINUX ##############
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import misc
import time
import os
import re
import itertools
import Settings
import rpieGlobals
import subprocess

ASOUND_CONF = "/etc/asound.conf" #"/etc/asound.conf"

class autorun:
 autorun_file_name = "/etc/rc.local"  # /etc/rc.local
 runfilename = "run.sh"
 DISABLE_HDMI="/usr/bin/tvservice -o&"
 ENABLE_RPIAUTOSTART="/usr/bin/screen -d -m "+ os.path.dirname(os.path.realpath(__file__))+"/"+runfilename
 ENABLE_RPIAUTOSTART2= os.path.dirname(os.path.realpath(__file__))+"/"+runfilename+"&"
 SERVICE_FILE="/etc/systemd/system/rpieasy.service"
 RC_ENDMARKER="exit 0"

 def __init__(self): # general init
  self.rpiauto = False
  self.rpiauto2 = False
  self.hdmienabled = True

 def readconfig(self):
    try:
     with open(self.autorun_file_name) as f:
      for line in f:
       line = line.strip()
       if len(line)>0 and line[0] == "#":
        line = ""
       if self.DISABLE_HDMI in line.lower():
        self.hdmienabled = False
       if self.ENABLE_RPIAUTOSTART in line or self.ENABLE_RPIAUTOSTART2 in line:
        self.rpiauto = True
    except:
     pass
    self.rpiauto2 = False
    try:
     if self.checkservice():
      self.rpiauto2 = True
    except:
     pass

 def saveconfig(self):
    contents = []
    try:
     with open(self.autorun_file_name) as f:
      for line in f:
       line = line.strip()
       if len(line)>0 and line[0] == "#" and ("!" not in line):
        line = ""
       if self.DISABLE_HDMI in line.lower():
        line = ""
       if self.ENABLE_RPIAUTOSTART in line or self.ENABLE_RPIAUTOSTART2 in line:
        line = ""
       if self.RC_ENDMARKER in line.lower():
        line = ""
       if line != "":
        contents.append(line)
     with open(self.autorun_file_name,"w") as f:
      for c in range(len(contents)):
       f.write(contents[c]+"\n")
      if self.rpiauto:
       if is_package_installed("screen"):
        f.write(self.ENABLE_RPIAUTOSTART+"\n")
       else:
        f.write(self.ENABLE_RPIAUTOSTART2+"\n") 
      if self.hdmienabled == False and rpieGlobals.ossubtype==10:
       f.write(self.DISABLE_HDMI+"\n")
      f.write(self.RC_ENDMARKER+"\n")
    except:
     pass

    contents = []
    try:
     with open(self.runfilename) as f:
      for line in f:
       line = line.strip()
       if "DIR=" in line and "$" not in line:
        contents.append("DIR="+str(os.path.dirname(os.path.realpath(__file__))))
       else:
        contents.append(line)
     with open(self.runfilename,"w") as f:
      for c in range(len(contents)):
       f.write(contents[c]+"\n")
    except:
     pass
    if self.rpiauto==False and self.rpiauto2==True:
      self.enableservice()
    else:
      self.disableservice()

 def checkservice(self):
     try:
      output = os.popen('systemctl is-enabled rpieasy').read()
     except:
      output = ""
     if "enabled" in output:
      return True
     else:
      return False

 def enableservice(self):
     try:
      if not os.path.exists(self.SERVICE_FILE):
       with open(self.SERVICE_FILE,"w") as f:
         f.write("[Unit]\nDescription=rpieasy\nAfter=network.target\n\n[Service]\n")
         f.write("ExecStart="+os.path.dirname(os.path.realpath(__file__))+"/"+self.runfilename)
         f.write("\nWorkingDirectory="+os.path.dirname(os.path.realpath(__file__)))
         f.write("\nStandardOutput=syslog\nStandardError=syslog\nSyslogIdentifier=rpieasy\nRestart=always\nUser=root\n\n[Install]\nWantedBy=multi-user.target\n")
     except Exception as e:
      print(e)
     try:
      output = os.popen(cmdline_rootcorrect('sudo systemctl enable rpieasy.service')).read()
     except Exception as e:
      print(e)

 def disableservice(self):
     try:
      output = os.popen(cmdline_rootcorrect('sudo systemctl disable rpieasy.service')).read()
     except:
      pass

thermalzone = -1

def read_cpu_temp():
 global thermalzone
 res = 0
 if thermalzone == -1:
  thermalzone = 0
  for i in range(20):
   try:
    if os.path.exists("/sys/class/thermal/thermal_zone"+str(i)+"/type"):
     with open('/sys/class/thermal/thermal_zone'+str(i)+'/type') as fp:
      tstr = fp.readline()
     if (tstr.find("cpu")>=0) or (tstr.find("x86")>=0) or (tstr.find("bcm") >= 0):
       thermalzone = i
       break
   except:
    pass
 elif thermalzone == -2:
  res = read_cpu_temp_sensor()
  return res
 try:
   with open('/sys/devices/virtual/thermal/thermal_zone'+str(thermalzone)+'/temp') as fp:
      res = fp.readline()
 except:
   res = 0
   thermalzone = -2
 therm2 = misc.str2num2(res)
# print("D:",therm2,thermalzone)
 if therm2 > 300:
  therm2 = misc.str2num2(therm2 /1000) 
 return therm2

def read_cpu_temp_sensor():
    t = []
    try:
     output = os.popen("sensors | grep Core")
     for line in output:
      if ":" in line:
       try:
        pline = line.split(":")
        pline2 = pline[1].split("C")
        t.append(float(re.sub("[^\d\.]", "", pline2[0].strip())))
       except Exception as e:
        pass
    except:
     pass 
    if len(t)<1:
     return 0
    else:
     return(sum(t)/len(t))

def read_cpu_usage():
  try:
   cpu_a_prev = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8)} END {print usage }' ''').readline()),2)
   cpu_t_prev = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8+$4+$5)} END {print usage }' ''').readline()),2)
  except:
   cpu_a_prev = 0
   cpu_t_prev = 0
  time.sleep(0.2)
  try:
   cpu_a_cur = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8)} END {print usage }' ''').readline()),2)
   cpu_t_cur = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8+$4+$5)} END {print usage }' ''').readline()),2)
  except:
   cpu_a_cur = 0
   cpu_t_cur = 1
  try:
   cpu_util = misc.str2num2(100*(cpu_a_cur-cpu_a_prev) / (cpu_t_cur-cpu_t_prev))
  except:
   cpu_util = 0
  return cpu_util

def get_memory():
    with open('/proc/meminfo', 'r') as mem:
        ret = {}
        tmp = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) == 'MemTotal:':
                ret['total'] = int(sline[1])
            elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                tmp += int(sline[1])
        ret['free'] = tmp
        ret['used'] = int(ret['total']) - int(ret['free'])
    return ret

def FreeMem():
 return get_memory()['free']

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
   f = os.popen('ifconfig')
   for iface in [' '.join(i) for i in iter(lambda: list(itertools.takewhile(lambda l: not l.isspace(),f)), [])]:
        if re.findall('^(eth|wlan|enp|ens|enx|wlp|wls|wlx)[0-9]',iface) and re.findall('RUNNING',iface):
            ip = re.findall('(?<=inet\saddr:)[0-9\.]+',iface)
            if ip:
                return ip[0]
            else:
                ip = re.findall('(?<=inet\s)[0-9\.]+',iface) # support Arch linux
                if ip:
                 return ip[0]
   return False

def get_rssi():
    resstr = ""
    try:
     resstr = os.popen("/bin/cat /proc/net/wireless | awk 'NR==3 {print $4}' | sed 's/\.//'").readline().strip()
     if resstr == "0" or resstr == "-256":
      resstr = os.popen("/bin/cat /proc/net/wireless | awk 'NR==4 {print $4}' | sed 's/\.//'").readline().strip() # try next line
    except:
     resstr = ""
    if resstr=="":
     resstr = "-49.20051" # no wireless interface?
    return resstr

def check_permission():
  euid = os.geteuid()
  if euid != 0:
      return False
  else:
      return True
  
def gethardware():
    vendor = os.popen('/bin/cat /sys/devices/virtual/dmi/id/board_vendor 2>/dev/null').read()
    name = os.popen('/bin/cat /sys/devices/virtual/dmi/id/board_name 2>/dev/null').read()
    rs = vendor + " " + name
    return rs.strip()

def is_package_installed(pkgname):
   if rpieGlobals.ossubtype in [1,3,10]:
    output = os.popen('dpkg -s {}'.format(pkgname) +' 2>/dev/null').read()
    match = re.search(r'Status: (\w+.)*', output)
    if match and 'installed' in match.group(0).lower():
        return True
    return False
   elif rpieGlobals.ossubtype==2:
    output = os.popen('pacman -Q {}'.format(pkgname) +' 2>/dev/null').read()
    if pkgname in output:
     return True
    else:
     return False

def is_command_found(pkgname):
    output = os.popen('command -v {}'.format(pkgname) +' 2>/dev/null').read()
    if pkgname in output:
     return True
    else:
     return False

def checkRPI():
    try:
     with open('/proc/cpuinfo') as f:
      for line in f:
       line = line.strip()
       if line.startswith('Hardware') and ( line.endswith('BCM2708') or line.endswith('BCM2709') or line.endswith('BCM2835') or line.endswith('BCM2711') or line.endswith('BCM2837') or line.endswith('BCM2836') ):
        return True
    except:
     pass
    return False

def getRPIVer():
    detarr = []
    try:
     with open('/proc/cpuinfo') as f:
      for line in f:
       line = line.strip()
       if line.startswith('Revision'):
        detarr = line.split(':')
        break
    except:
     pass
    hwarr = { 
      "name": "Unknown model",
      "pins": "",
      "ram":"0"
    }
    if len(detarr)>1:
     hwid = detarr[1].strip().lower()
     if hwid[:4] == "1000":
      hwid = hwid[-4:]
     if (hwid == "0002") or (hwid == "0003"):
      hwarr = { 
       "name": "Pi 1 Model B",
       "ram": "256MB",
       "pins": "26R1",
       "lan": "1"
      }
     elif (hwid == "0004") or (hwid == "0005") or (hwid == "0006"):
      hwarr = { 
       "name": "Pi 1 Model B",
       "ram": "256MB",
       "pins": "26R2",
       "lan": "1"
      }
     elif (hwid == "0007") or (hwid == "0008") or (hwid == "0009"):
      hwarr = { 
       "name": "Pi 1 Model A",
       "ram": "256MB",
       "pins": "26R1"
      }
     elif (hwid == "000d") or (hwid == "000e") or (hwid == "000f"):
      hwarr = { 
       "name": "Pi 1 Model B",
       "ram": "512MB",
       "pins": "26R2",
       "lan": "1"
      }
     elif (hwid == "0010") or (hwid == "0013") or (hwid == "900032"):
      hwarr = { 
       "name": "Pi 1 Model B+",
       "ram": "512MB",
       "pins": "40",
       "lan": "1"
      }
     elif (hwid == "0011") or (hwid == "0014"):
      hwarr = { 
       "name": "Pi Compute Module 1",
       "ram": "512MB",
       "pins": "200"
      }
     elif (hwid == "a020a0"):
      hwarr = { 
       "name": "Pi Compute Module 3",
       "ram": "1GB",
       "pins": "200"
      }
     elif (hwid == "0012"):
      hwarr = { 
       "name": "Pi 1 Model A+",
       "ram": "256MB",
       "pins": "40"
      }
     elif (hwid == "0015"):
      hwarr = { 
       "name": "Pi 1 Model A+",
       "ram": "256/512MB",
       "pins": "40"
      }
     elif (hwid == "900021"):
      hwarr = { 
       "name": "Pi 1 Model A+",
       "ram": "512MB",
       "pins": "40"
      }
     elif  (hwid == "a01040") or (hwid == "a01041") or (hwid == "a21041") or (hwid == "a22042"):
      hwarr = { 
       "name": "Pi 2 Model B",
       "ram": "1GB",
       "pins": "40",
       "lan": "1"
      }
     elif (hwid == "900092") or (hwid == "900093") or (hwid == "920092") or (hwid == "920093"):
      hwarr = { 
       "name": "Pi Zero",
       "ram": "512MB",
       "pins": "40"
      }
     elif (hwid == "9000c1"):
      hwarr = { 
       "name": "Pi Zero W",
       "ram": "512MB",
       "pins": "40",
       "wlan": "1",
       "bt":"1"
      }
     elif (hwid == "a02082") or (hwid == "a22082") or (hwid == "a32082") or (hwid == "a52082") or (hwid == "a22083"):
      hwarr = { 
       "name": "Pi 3 Model B",
       "ram": "1GB",
       "pins": "40",
       "wlan": "1",
       "lan":"1",
       "bt":"1"
      }
     elif (hwid == "a020d3"):
      hwarr = { 
       "name": "Pi 3 Model B+",
       "ram": "1GB",
       "pins": "40",
       "wlan": "1",
       "lan":"1",
       "bt":"1"
      }
     elif (hwid == "9020e0"):
      hwarr = { 
       "name": "Pi 3 Model A+",
       "ram": "512MB",
       "pins": "40",
       "wlan": "1",
       "bt":"1"
      }
     elif (hwid == "a03111"):
      hwarr = { 
       "name": "Pi 4 Model B",
       "ram": "1GB",
       "pins": "40",
       "wlan": "1",
       "lan":"1",
       "bt":"1"
      }
     elif (hwid == "b03111") or (hwid == "b03112") or (hwid == "b03114"):
      hwarr = { 
       "name": "Pi 4 Model B",
       "ram": "2GB",
       "pins": "40",
       "wlan": "1",
       "lan":"1",
       "bt":"1"
      }
     elif (hwid == "c03111") or (hwid == "c03112") or (hwid == "c03114"):
      hwarr = { 
       "name": "Pi 4 Model B",
       "ram": "4GB",
       "pins": "40",
       "wlan": "1",
       "lan":"1",
       "bt":"1"
      }
     elif (hwid == "c03130"):
      hwarr = { 
       "name": "Pi 400 Rev1",
       "ram": "4GB",
       "pins": "40",
       "wlan": "1",
       "lan":"1",
       "bt":"1"
      }
     elif (hwid == "d03114"):
      hwarr = { 
       "name": "Pi 4 Model B",
       "ram": "8GB",
       "pins": "40",
       "wlan": "1",
       "lan":"1",
       "bt":"1"
      }
    return hwarr

def getsounddevs(playbackdevs = True):
    devlist = []
    try:
     if playbackdevs:
      output = os.popen('aplay -l 2>/dev/null')
     else: 
      output = os.popen('arecord -l 2>/dev/null')
     for line in output:
      devname = ""
      if line and line[0] != ' ':
       tarr = line.split(':')
       devpos = tarr[0][len(tarr[0])-1].strip()
       if devpos and len(devpos) > 0:
        tarr2 = tarr[1].split(', ')
        devname = tarr2[0].strip()
      if devname!="":
       devlist.append([devpos,devname])
    except:
     pass 
    return devlist

def getsoundsel():
    cardnum = 0
    try:
     with open(ASOUND_CONF) as f:
      for line in f:
       if line.find('card ')>=0:
        tstr = line.strip()
        tstr2 = tstr.split(' ')
        if len(tstr2)>1:
         cardnum = tstr2[1]
    except:
     pass
    return cardnum

def updateaudiocard(number):
 settingstr = "pcm.!default {{\ntype hw\ncard {0}\n}}\nctl.!default {{\ntype hw\ncard {0}\n}}\n".format(str(number))
 with open(ASOUND_CONF,"w") as f:
   f.write(settingstr)

def getosfullname():
    try:
     with open('/etc/os-release') as f:
      for line in f:
       line = line.strip()
       if line.startswith('PRETTY_NAME'):
        pname = line.split('"')
        return pname[1]
    except:
     pass
    return ""

def get_cpu():
     cspd = {"speed":"Unknown","arch":"Unknown","core":1,"model":"Unknown"}
     output = os.popen('lscpu')
     for line in output:
      if ("max MHz" in line):
       spd = line.strip().split(":")
       cspd["speed"] = spd[len(spd)-1].strip()+" Mhz"
      if line.startswith("CPU(s)"):
       spd = line.strip().split(":")
       cspd["core"] = spd[len(spd)-1].strip()
      if ("Architecture" in line):
       spd = line.strip().split(":")
       cspd["arch"] = spd[len(spd)-1].strip()
      if ("Model name" in line):
       spd = line.strip().split(":")
       cspd["model"] = spd[len(spd)-1].strip()
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
      cmdline = "unzip -o -q '"+str(zipname)+"'"
      if destdir != "":
       cmdline += ' -d '+str(destdir)
      output = os.popen(cmdline)
      for l in output:
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(l)) #       pass
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,str(e)) #       pass

def getfirstusername():
    cmdline = "awk -F: '{ print $3"
    cmdline += '","$1","'
    cmdline += "$7}' /etc/passwd"
    uptr = []
    unames = []
    try:
     output = os.popen(cmdline)
     for line in output:
      l = line.split(",")
      if len(l)>2:
       if (int(l[0]) in [100,101,500,501,1000,1001]) and ("nologin" not in l[2]) and ("false" not in l[2]):
        uptr.append(int(l[0]))
        unames.append(l[1])
    except:
     pass 
    if len(uptr)>0:
     return unames[0]
    else:
     return False

firstusername = ""
def runasfirstuser(subprocess_options): # some applications, such as VLC will not run as root, try to run as the first normal user
   global firstusername
   result = False
   if check_permission(): # only needed if we have root access
    if firstusername=="":
     firstusername = getfirstusername()
    if firstusername:
     params = ["su","-l",firstusername] + subprocess_options
     try:
      result = subprocess.Popen(params,shell=False)
     except:
      result = False
   if result==False:
     try:
      result = subprocess.Popen(subprocess_options,shell=False)
     except:
      result = False
   return result

def checkboot_ro():
     err = False
     try:
      output = os.popen('cat /proc/mounts | grep /boot')
      for l in output:
       if ("ro," in l) or ("tmpfs" in l):
        err = True
        break
     except:
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
     fname = "/boot/cmdline.txt"
     tstr = ""
     try:
      if os.path.exists(fname):
       tstr = os.popen('/bin/cat '+fname).read()
     except:
      tstr = ""
     return tstr

def get_i2c_state(m=0): # RPI only
    if m==0:
     tstr = "ERROR: I2C module not started"
     try:
      output = os.popen('lsmod | grep i2c')
      for l in output:
       if ("i2c_dev" in l):
        tstr = ""
        break
     except:
      pass
    else:
     fname = "/etc/modules"
     tstr = "ERROR: i2c-dev is not found in "+fname
     try:
      if os.path.exists(fname):
       with open(fname) as f:
        for line in f:
         if line.strip() == "i2c-dev":
          tstr = ""
     except:
      pass
     if tstr != "":
      try:
       if os.path.exists(fname):
        with open(fname,"a") as f:
         f.write("\ni2c-dev\n")
      except:
       pass
    return tstr

def disable_serialsyslog():
    fname = "/boot/cmdline.txt"
    content = get_bootparams().strip()
    if len(content)>0:
     pcontent = content.split(" ")
     content2 = ""
     sf = False
     for i in range(len(pcontent)):
      if ("ttyAMA" not in pcontent[i] and "ttyS" not in pcontent[i] and "serial" not in pcontent[i]):
       content2 += pcontent[i].strip() + " "
      else:
       sf = True
     if sf:
       os.popen('/bin/cp '+fname+" "+fname+".bak").read()
       with open(fname,"w") as f:
        f.write(content2.strip()+"\n")

def cmdline_rootcorrect(cmdline):
  res = cmdline
  if "sudo " in cmdline:
   if check_permission(): # only needed if we have root access
    res = cmdline.replace("sudo -H ","")
    res = res.replace("sudo ","")
  return res.strip()

def checkOPI():
  opv = getarmbianinfo()
  if len(opv)>0:
   try:
    return ("orange" in opv["name"].lower())
   except:
    return False
  else:
   return False

def getarmbianinfo():
    hwarr = { 
      "name": "Unknown model",
      "shortname":"unknown",
      "version":"0.0",
      "pinout":"",
      "pins": "0"
    }
    try:
     with open('/etc/armbian-release') as f:
      for line in f:
       line = line.strip()
       if line.startswith('BOARD_NAME'):
        pname = line.split('"')
        hwarr["name"] = pname[1]
       if line.startswith('BOARD='):
        pname = line.split('=')
        hwarr["shortname"] = pname[1]
       if line.startswith('VERSION='):
        pname = line.split('=')
        hwarr["version"] = pname[1]
    except:
     pass
    if "orangepi" in hwarr["shortname"]:
     if "zeroplus2" in hwarr["shortname"]:
      hwarr["pinout"] = "zeroplus2"
      hwarr["pins"] = "26z+2"
     elif ("zeroplus" in hwarr["shortname"]) or ("pizero" in hwarr["shortname"]) or ("r1" in hwarr["shortname"]):
      hwarr["pinout"] = "zeroplus"
      hwarr["pins"] = "26z+"
     elif "pi3" in hwarr["shortname"]:
      hwarr["pinout"] = "pi3"
      hwarr["pins"] = "26pi3"
     elif ("oneplus" in hwarr["shortname"]) or ("pilite2" in hwarr["shortname"]):
      hwarr["pinout"] = "oneplus"
      hwarr["pins"] = "26o+"
     elif "winplus" in hwarr["shortname"]:
      hwarr["pinout"] = "winplus"
      hwarr["pins"] = "40w+"
     elif "prime" in hwarr["shortname"]:
      hwarr["pinout"] = "prime"
      hwarr["pins"] = "40pr"
     elif "pc2" in hwarr["shortname"]:
      hwarr["pinout"] = "pc2"
      hwarr["pins"] = "40pc2"
     elif ("pipc" in hwarr["shortname"]) or ("pilite" in hwarr["shortname"]) or ("pione" in hwarr["shortname"]) or ("piplus2" in hwarr["shortname"]):
      hwarr["pinout"] = "pc"
      hwarr["pins"] = "40pc"
    return hwarr

soundmixer = ""

def getsoundmixer():
  global soundmixer
  if soundmixer == "":
   try:
    cc = 0
    output = os.popen('amixer scontrols')
    for line in output:
      if cc == 0 and soundmixer=="":
       lc = line.split("'")
       soundmixer = "'"+str(lc[1])+"'"
       cc = 1
       return soundmixer
   except Exception as e:
    print("Sound mixer error:",e)
  return soundmixer

def getvolume(): # volume in percentage
  vol = 0
  try:
   output = os.popen("amixer get "+getsoundmixer())
   for line in output:
     if '%' in line:
      line2 = line.replace("[","%").replace("]","%")
      lc = line2.split("%")
      vol = str(lc[1]).strip()
      return vol
  except Exception as e:
   print("GetVolume:",e)
  return vol

def setvolume(volume): # volume in percentage
  try:
   output = os.popen('amixer set '+getsoundmixer()+' '+str(volume)+'%')
   for l in output:
    pass
   output = os.popen(cmdline_rootcorrect('sudo alsactl store'))
   for l in output:
    pass
  except:
   pass

def detectNM():
   nm = False
   nmpath = "/etc/NetworkManager/NetworkManager.conf"
   if os.path.exists(nmpath):
    try:
     with open(nmpath) as f:
      for line in f:
       line = line.strip().lower()
       if line.startswith("managed"):
        if "true" in line:
         nm = True
    except:
     pass
   return nm

def checkRockPI():
  rpi = False
  try:
   output = os.popen('uname -a')
   for line in output:
     if '-rockchip-' in line:
      rpi = True
  except Exception as e:
   pass
  return rpi

def getRockPIVer():
    hwarr = {
      "name": "Unknown model",
      "pins": "0",
      "ver" : "0.0"}
    notrock = False
    try:
     import lib.lib_rockgpios as GPIO
     ta = GPIO.getmraa()
     if ta[0][0] != "U":
      hwarr["name"] = ta[0]
      hwarr["pins"] = ta[1]
      hwarr["ver"]  = ta[2]
      return hwarr
    except Exception as e:
     notrock = True
    try:
     output = os.popen('mraa-gpio version')
     for line in output:
      if 'rock' in line.lower():
       tf = line.find(" on")
       if tf>-1:
        hwarr["name"] = line[tf+3:].strip()
    except Exception as e:
     notrock = True
    if notrock or ("Unknown" in hwarr["name"]):
     if checkRockPI():
      hwarr["name"] = "Unknown Rockchip"
      hwarr["pins"] = "X"
    return hwarr

def isAlreadyRunning():
    output = os.popen('ps -aux | grep RPIEasy | grep python').read()
    try:
     occ = int(output.count("RPIEasy.py"))
    except:
     occ = 0
    return occ
