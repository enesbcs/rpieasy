#!/usr/bin/env python3
#############################################################################
################### Helper Library for Networking WINDOWS ###################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#

from collections import namedtuple
import re
import subprocess
import shlex
import os
import Settings
import time
import misc
import rpieGlobals
import win_os as OS

def get_ssid(devicename):
     ssid = ""
     return ssid

def scanwifi(devicename):
    return ""

def parsewifiscan(content):
    cells = []
    return cells

def getipinfos():
    ostr = subprocess.check_output("ipconfig /all")
    result = ostr.decode(encoding='UTF-8',errors='ignore')
    return result

def parseifconfig(content):
 lines = content.split("\n")
 ifaces = []
 ifacenum = 0
 mac_pattern = r'([0-9A-Fa-f]{2}-){5}([0-9A-Fa-f]{2})'
 tarr = {"active":0,"name":"","mac":"","ip":"","mask":"","broadcast":""}
 if len(lines)>0:
  for ll in range(len(lines)):
   if ":" in lines[ll]:
    l = lines[ll]
    if l[0] != " ":
     if "adapter" in l:
      tarr = {"active":0,"name":"","mac":"","ip":"","mask":"","broadcast":"","wireless":False,"dhcp":False}
      ifaces.append(tarr)
      ifacenum += 1
      n1 = l.find("adapter")
      n2 = l.find(":")
      if n1>-1 and n2>-1:
       n1 = n1 + 8
       ifaces[ifacenum-1]['name'] = l[n1:n2]
      else:
       ifaces[ifacenum-1]['name'] = l.strip()
      if "ireless" in l:
       ifaces[ifacenum-1]['wireless'] = True 
    else:
      l2 = l.lower()
      if ifacenum<=len(ifaces):
       if 'IPv4' in l:
        ipa = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',l)
        if ipa and len(ipa)>0:
         ifaces[ifacenum-1]['ip'] = str(ipa[0])
         ifaces[ifacenum-1]['active'] = True
       elif 'mask' in l2:
        n2 = l.find(":")
        ipa = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',l[n2:])
        if ipa and len(ipa)>0:
         ifaces[ifacenum-1]['mask'] = str(ipa[0])
       elif 'dhcp' in l2 and 'yes' in l2:
        ifaces[ifacenum-1]['dhcp'] = True
       elif 'address' in l2 and l.count('-')>4:
        ifaces[ifacenum-1]['mac'] = re.search(mac_pattern,l).group(0)
        ifaces[ifacenum-1]['mac'] = ifaces[ifacenum-1]['mac'].replace("-",":")
 return ifaces

class NetworkDevice:
 def __init__(self):
  self.devicename =""
  self.mac = ""
  self.dhcp = False
  self.ip = ""
  self.mask = ""
#  self.broadcast = ""
  self.gw = ""
  self.dns = ""            # /etc/resolv.conf
  self.dnsserver = False
  self.apmode = 0          # 0-no,1-yes
  self.enabled=True
  self.connectiontype=0    # 1-wired,2-wireless
  self.connected = False
  self.lastconnectiontest=0
  self.netdevorder=-1

 def isconnected(self):
  return self.connected

 def iswireless(self):
  return False

#def getsortkey(item):
# v = 0
# try:
#  v = item["active"]
# except:
#  v = 0
# return v

class NetworkManager:
 interfaces_file_name = "" # /etc/network/interfaces
 resolvconf_file_name = "" # "/etc/resolv.conf"
 dhcpcd_file_name = ""

 def __init__(self): # general init
  self.wpaconfig = ""
  self.WifiSSID  = ""
  self.WifiKey   = ""
  self.WifiSSID2 = ""
  self.WifiKey2  = ""
  self.APMode    = -1 # -1:never, 0: on primary device fail, 1: on secondary device fail, 99: if first wifi fail, 100: always
  self.APModeDev = 99 # 0: primary, 1: secondary, 99 first wifi
  self.APModeTime = 30 # in seconds
  self.APStopTime = -1 # in seconds
  self.WifiAPKey = "configrpi"
  self.WifiAPChannel = 1
  self.WifiDevWatch  = -1
  self.WifiDevNum    = -1
  self.dhcpcd_inuse  = False

 def networkinit(self):
  ipi = getipinfos()
  ni = parseifconfig(ipi)
  realdevs = 0
  if ni:
   if len(ni)>0:
    #ni.sort(reverse=True,key=getsortkey)
    realdevs = 0
    for i in range(len(ni)):
     if ni[i]["mac"]!="":
      if len(Settings.NetworkDevices)<=realdevs:
       tarr = NetworkDevice()
       Settings.NetworkDevices.append(tarr)
      Settings.NetworkDevices[realdevs].ip = ni[i]["ip"]
      Settings.NetworkDevices[realdevs].mask = ni[i]["mask"]
      Settings.NetworkDevices[realdevs].devicename = ni[i]["name"]
      Settings.NetworkDevices[realdevs].connected = (int(ni[i]["active"])!=0)
      Settings.NetworkDevices[realdevs].lastconnectiontest=time.time()
      Settings.NetworkDevices[realdevs].mac = ni[i]["mac"]
      if Settings.NetworkDevices[realdevs].connected:
       if ni[i]["wireless"]:
        Settings.NetworkDevices[realdevs].connectiontype = 2
       else:
        Settings.NetworkDevices[realdevs].connectiontype = 1
      else:
        Settings.NetworkDevices[realdevs].connectiontype = 0
      realdevs+=1
  for dc in range(len(Settings.NetworkDevices)):
     Settings.NetworkDevices[dc].dns = Settings.NetworkDevices[dc].dns.strip()
     if Settings.NetworkDevices[dc].gw == "" and Settings.NetworkDevices[dc].ip!="":
      Settings.NetworkDevices[dc].gw = getgw(Settings.NetworkDevices[dc].devicename)

 def setAPconf(self,startup=False):
  return False # not supported

 def getdevicenames(self):
  rs = []
  if len(Settings.NetworkDevices)>0:
   for n in range(len(Settings.NetworkDevices)):
    rs.append(Settings.NetworkDevices[n].devicename)
  return rs

 def getfirstwirelessdev(self):
  try:
   pd = self.getprimarydevice()
   if Settings.NetworkDevices[pd].iswireless():
    return Settings.NetworkDevices[pd].devicename
   pd = self.getsecondarydevice()
   if Settings.NetworkDevices[pd].iswireless():
    return Settings.NetworkDevices[pd].devicename
  except:
   return False
  return False

 def getfirstwirelessdevnum(self):
  try:
   pd = self.getprimarydevice()
   if Settings.NetworkDevices[pd].iswireless():
    return pd
   pd = self.getsecondarydevice()
   if Settings.NetworkDevices[pd].iswireless():
    return pd
  except:
   return -1
  return -1

 def getprimarydevice(self):
  rs = 0
  if len(Settings.NetworkDevices)>0:
   for n in range(len(Settings.NetworkDevices)):
    if Settings.NetworkDevices[n].netdevorder==0:
     rs = n
     break
  return rs

 def getsecondarydevice(self):
  rs = -1 #windows fix
  if len(Settings.NetworkDevices)>0:
   for n in range(len(Settings.NetworkDevices)):
    if Settings.NetworkDevices[n].netdevorder>0:
     rs = n
     break
  return rs

 def setdeviceorder(self,primary,secondary):
  if len(Settings.NetworkDevices)>0:
   for n in range(len(Settings.NetworkDevices)):
    if n==primary:
     Settings.NetworkDevices[n].netdevorder=0
    elif n==secondary:
     Settings.NetworkDevices[n].netdevorder=1
    else:
     Settings.NetworkDevices[n].netdevorder=-1

 def saveconfig(self):
     pass

def getcountry():
 result = "HU"
 return result

def getdefaultgw():
 result = getgw(0)
 return result

def getgw(iface):
 result = ""
 try:
  output = os.popen("route print")
  for line in output:
   l = line.split()
   if l[1].strip() == "0.0.0.0" and l[3].strip() != "0.0.0.0":
    result = l[3]
    break
 except:
  result = ""
 return result

def isdhclient():
 result = False
 return result

def cidr_to_netmask(cidr):
  cidr = int(cidr)
  mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
  return (str( (0xff000000 & mask) >> 24)   + '.' +
          str( (0x00ff0000 & mask) >> 16)   + '.' +
          str( (0x0000ff00 & mask) >> 8)    + '.' +
          str( (0x000000ff & mask)))

def netmask_to_cidr(netmask):
 return sum([bin(int(x)).count("1") for x in netmask.split(".")])

def AP_start(ndi,force=False): # index in NetworkDevices array
    return False

def AP_stop(ndi): # index in NetworkDevices array
    return False
