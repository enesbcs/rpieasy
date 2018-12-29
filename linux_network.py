#!/usr/bin/env python3
#############################################################################
################### Helper Library for Networking LINUX #####################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# WIFI Regex based on:
#  https://github.com/iancoleman/python-iwlist

from collections import namedtuple
import re
import subprocess
import os
import Settings
import time
import misc
import rpieGlobals

cellNumberRe = re.compile(r"^Cell\s+(?P<cellnumber>.+)\s+-\s+Address:\s(?P<mac>.+)$")
regexps = [
    re.compile(r"^ESSID:\"(?P<essid>.*)\"$"),
    re.compile(r"^Protocol:(?P<protocol>.+)$"),
    re.compile(r"^Mode:(?P<mode>.+)$"),
    re.compile(r"^Frequency:(?P<frequency>[\d.]+) (?P<frequency_units>.+) \(Channel (?P<channel>\d+)\)$"),
    re.compile(r"^Encryption key:(?P<encryption>.+)$"),
    re.compile(r"^Quality=(?P<signal_quality>\d+)/(?P<signal_total>\d+)\s+Signal level=(?P<signal_level_dBm>.+) d.+$"),
    re.compile(r"^Signal level=(?P<signal_quality>\d+)/(?P<signal_total>\d+).*$"),
]

wpaRe = re.compile(r"IE:\ WPA\ Version\ 1$")
wpa2Re = re.compile(r"IE:\ IEEE\ 802\.11i/WPA2\ Version\ 1$")

def get_ssid(devicename):
     ssid = ""
     output = os.popen('iwconfig '+devicename+' | grep '+devicename+" 2>/dev/null")
#     output = os.popen('iwconfig | grep '+devicename+" >/dev/null 2>&1")
     for line in output:
      if line.startswith(devicename) and ("SSID:" in line):
       ssid = line[line.find("SSID:")+5:].strip().replace('"',"")
     return ssid

def scanwifi(devicename):
    result = os.popen("iwlist "+str(devicename)+" scan").read() # sudo!!!
    return result

def parsewifiscan(content):
    cells = []
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        cellNumber = cellNumberRe.search(line)
        if cellNumber is not None:
            cells.append(cellNumber.groupdict())
            continue
        wpa = wpaRe.search(line)
        if wpa is not None :
            cells[-1].update({'encryption':'wpa'})
        wpa2 = wpa2Re.search(line)
        if wpa2 is not None :
            cells[-1].update({'encryption':'wpa2'}) 
        for expression in regexps:
            result = expression.search(line)
            if result is not None:
                if 'encryption' in result.groupdict() :
                    if result.groupdict()['encryption'] == 'on' :
                        cells[-1].update({'encryption': 'wep'})
                    else :
                        cells[-1].update({'encryption': 'off'})
                else :
                    cells[-1].update(result.groupdict())
                continue
    return cells

def getipinfos():
    result = os.popen("ifconfig").read() # check that ifconfig exists?
    return result

def parseifconfig(content):
 lines = content.split("\n")
 #mac_pattern = ".*?HWaddr[ ]([0-9A-Fa-f:]{17})"
 #mac_pattern2 = ".*?ether[ ]([0-9A-Fa-f:]{17})"
 mac_pattern = r'([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})'
 ifaces = []
 ifacenum = 0
 tarr = {"active":0,"name":"","mac":"","ip":"","mask":"","broadcast":""}
 if len(lines)>0:
  for ll in range(len(lines)):
   l = lines[ll]
   if "running" in l.lower():
    tarr["active"] = 1
   if l.strip()=="" or l.strip()=="\n" or ll==(len(content)-1):
    ifaces.append(tarr)
    ifacenum += 1
    tarr = {"active":0,"name":"","mac":"","ip":"","mask":"","broadcast":""}
   else:
    if l[0]!=" ":
     if ": " in l:
      lstr = l.split(": ")
     elif l.find(" ")>-1:
      lstr = l.split(" ")
     if ("ether" in l) or ("HWaddr" in l):
      tarr["mac"] = re.search(mac_pattern,l).group(0)
     try:
      tarr["name"] = lstr[0]
     except:
      pass
    else:
     if "inet " in l:
      #grep inet
      if ":" in l:
       istr = l.split(":")
      else:
       istr = l.split(" ")
      for i in range(len(istr)):
       if "inet" in istr[i].strip():
        tarr2 = istr[i+1].strip().split()
        tarr["ip"] = tarr2[0]
       elif ("netmask" in istr[i].strip()) or ("mask" in istr[i].strip().lower()):
        tarr2 = istr[i+1].strip().split()
        tarr["mask"] = tarr2[0]
#       elif ("broadcast" in istr[i].strip()) or ("bcast" in istr[i].strip().lower()):
#        tarr2 = istr[i+1].strip().split()
#        tarr["broadcast"] = tarr2[0]
     elif ("ether" in l) or ("HWaddr" in l):
      tarr["mac"] = re.search(mac_pattern,l).group(0)
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
  self.apmode = 0          # 0-no,1-on connection error,2-always
  self.enabled=True
  self.connectiontype=0    # 1-wired,2-wireless
  self.connected = False
  self.lastconnectiontest=0
  self.netdevorder=-1

 def isconnected(self):
  if time.time()-self.lastconnectiontest>5:
    conn = False
    try:
     with open('/sys/class/net/'+self.devicename.strip()+'/carrier') as f:
      for line in f:
       line = line.strip()
       if line.startswith('1'):
        conn = True
        break
    except:
     pass
    self.connected=conn
#    try:
#     output = os.popen("ethtool "+self.devicename+" 2>/dev/null | grep 'Link detected'") # check that ethtool exists?
#     for line in output:
#      if "Link detected:" in line:
#       if "yes" in line:
#        self.connected=True
#       else:
#        self.connected=False
#       break
#    except:
#     pass 
    self.lastconnectiontest=time.time()
  return self.connected

 def iswireless(self):
  if self.connectiontype==0:
    wless = False
    try:
     with open('/proc/net/wireless') as f:
      for line in f:
       line = line.strip()
       if line.startswith(self.devicename):
        wless = True
        break
    except:
     pass
    if wless:
     self.connectiontype=2
    else:
     self.connectiontype=1
#    try:
#     output = os.popen("iwconfig "+self.devicename+" 2>/dev/null")
#     for line in output:
#      if "no wireless extensions" in line:
#       self.connectiontype=1
#       break
#      else:
#       self.connectiontype=2
#    except:
#     pass 
  return (self.connectiontype==2)

#def getsortkey(item):
# v = 0
# try:
#  v = item["active"]
# except:
#  v = 0
# return v

class NetworkManager:
 interfaces_file_name = "/etc/network/interfaces" # /etc/network/interfaces
 resolvconf_file_name = "/etc/resolv.conf" # "/etc/resolv.conf"
 dhcpcd_file_name = "/etc/dhcpcd.conf"

 def __init__(self): # general init
  self.wpaconfig = ""
  self.WifiSSID  = ""
  self.WifiKey   = ""
  self.WifiSSID2 = ""
  self.WifiKey2  = ""
  self.APMode    = 1 # 0-ap mode do not starts automatically, 1-ap mode starts automatically
  self.WifiAPKey = "rpieasy"
  self.dhcpcd_inuse = False

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
#      Settings.NetworkDevices[realdevs].broadcast = ni[i]["broadcast"]
      realdevs+=1
  if os.path.exists(self.dhcpcd_file_name):
   self.dhcpcd_inuse = True
  if self.dhcpcd_inuse:
   try:
     for i in range(len(Settings.NetworkDevices)):
      Settings.NetworkDevices[i].dhcp=True
     with open(self.dhcpcd_file_name) as f:
      detectedcard = -1
      for line in f:
       line = line.strip()
       if len(line)>0 and line[0] == "#":
        line = ""
       elif line.lower().startswith("interface"):
        detectedcard = -1
        for i in range(len(Settings.NetworkDevices)):
         if Settings.NetworkDevices[i].devicename in line:
          detectedcard = i
       elif ("static ip_address" in line) and (detectedcard>=0):
          Settings.NetworkDevices[detectedcard].dhcp=False
          l1 = line.split("=")
          if len(l1)>1:
           l = l1[1].split("/")
           if len(l)>0:
            Settings.NetworkDevices[detectedcard].ip=l[0]
            Settings.NetworkDevices[detectedcard].mask=cidr_to_netmask(l[1])
       elif ("static routers" in line.lower()) and (detectedcard>=0):
        if Settings.NetworkDevices[detectedcard].gw=="":
          l = line.split("=")
          if len(l)>0:
           Settings.NetworkDevices[detectedcard].gw=l[1]
       elif ("static domain_name_servers" in line.lower()) and (detectedcard>=0):
        if Settings.NetworkDevices[detectedcard].dns=="":
          l = line.split("=")
          if len(l)>0:
           Settings.NetworkDevices[detectedcard].dns=l[1]
   except:
    pass
  else:
   dhclient = isdhclient()
   if dhclient:
    for i in range(len(Settings.NetworkDevices)):
      Settings.NetworkDevices[i].dhcp = True
   try:
     with open(self.interfaces_file_name) as f:
      detectedcard = -1
      for line in f:
       line = line.strip()
       if len(line)>0 and line[0] == "#":
        line = ""
       elif "iface " in line.lower():
        detectedcard = -1
        for i in range(len(Settings.NetworkDevices)):
         if Settings.NetworkDevices[i].devicename in line:
          detectedcard = i
        if ("dhcp" in line) and (detectedcard>=0):
          Settings.NetworkDevices[detectedcard].dhcp=True
        if ("static" in line) and (detectedcard>=0):
          Settings.NetworkDevices[detectedcard].dhcp=False
       elif ("address " in line.lower()) and (detectedcard>=0):
        if Settings.NetworkDevices[detectedcard].ip=="":
          l = line.split(" ")
          if len(l)>0:
           Settings.NetworkDevices[detectedcard].ip=l[1]
       elif ("netmask " in line.lower()) and (detectedcard>=0):
        if Settings.NetworkDevices[detectedcard].mask=="":
          l = line.split(" ")
          if len(l)>0:
           Settings.NetworkDevices[detectedcard].mask=l[1]
       elif ("gateway " in line.lower()) and (detectedcard>=0):
        if Settings.NetworkDevices[detectedcard].gw=="":
          l = line.split(" ")
          if len(l)>0:
           Settings.NetworkDevices[detectedcard].gw=l[1]
       elif ("dns-nameservers " in line.lower()) and (detectedcard>=0):
        if Settings.NetworkDevices[detectedcard].dns=="":
          l = line.split(" ")
          if len(l)>0:
           for d in range(len(l)):
            Settings.NetworkDevices[detectedcard].dns+=l[d]+" "
       elif ("wpa-conf " in line.lower()):
          l = line.split(" ")
          if len(l)>0:
           self.wpaconfig = l[1]
   except:
     pass
  try:
     with open(self.resolvconf_file_name) as f:
      dnsservers = ""
      for line in f:
       line = line.strip().lower()
       if line.startswith("nameserver"):
        dl = line.split(" ")
        if len(dl)>1:
         fdns = dl[1].strip()
         for dc in range(len(Settings.NetworkDevices)):
          if fdns not in Settings.NetworkDevices[dc].dns:
           Settings.NetworkDevices[dc].dns += " "+fdns
  except:
     pass
  if self.wpaconfig=="":
     tv = "/etc/wpa_supplicant/wpa_supplicant.conf"
     if os.path.exists(tv):
      self.wpaconfig = tv
  if self.wpaconfig!="":
   try:
     netid = -1
     with open(self.wpaconfig) as f:
      for line in f:
       line=line.strip()
       if "network=" in line.lower():
        netid+=1
       if line.lower().strip().startswith("ssid="):
        tstrs = line.split("=")
        tstr = tstrs[1].replace('"',"").replace("'","")
        if netid == 0:
         self.WifiSSID=tstr
        elif netid == 1:
         self.WifiSSID2=tstr
       if "psk=" in line.lower():
        tstrs = line.split("=")
        tstr = tstrs[1].replace('"',"").replace("'","")
        if netid == 0:
         self.WifiKey=tstr
        elif netid == 1:
         self.WifiKey2=tstr
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
  for dc in range(len(Settings.NetworkDevices)):
     Settings.NetworkDevices[dc].dns = Settings.NetworkDevices[dc].dns.strip()
     if Settings.NetworkDevices[dc].gw == "" and Settings.NetworkDevices[dc].ip!="":
      Settings.NetworkDevices[dc].gw = getgw(Settings.NetworkDevices[dc].devicename)
     Settings.NetworkDevices[dc].connectiontype = 0 # reset iswireless value in case of device name change!

 def getdevicenames(self):
  rs = []
  if len(Settings.NetworkDevices)>0:
   for n in range(len(Settings.NetworkDevices)):
    rs.append(Settings.NetworkDevices[n].devicename)
  return rs

 def getfirstwirelessdev(self):
  pd = self.getprimarydevice()
  if Settings.NetworkDevices[pd].iswireless():
   return Settings.NetworkDevices[pd].devicename
  pd = self.getsecondarydevice()
  if Settings.NetworkDevices[pd].iswireless():
   return Settings.NetworkDevices[pd].devicename
  return False

 def getprimarydevice(self):
  rs = 0
  if len(Settings.NetworkDevices)>0:
   for n in range(len(Settings.NetworkDevices)):
    if Settings.NetworkDevices[n].netdevorder==0:
     rs = n
     break
  return rs

 def getsecondarydevice(self):
  rs = 1
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
  if len(Settings.NetworkDevices)>0:
   staticused = False
   wifiused   = False
   if self.dhcpcd_inuse:
    contents = []
    try:
      with open(self.dhcpcd_file_name) as f:
       for line in f:
        line = line.strip()
        if len(line)>0 and line[0] == "#":
         line = ""
        elif line.startswith("interface") or line.startswith("static "):
         line = ""
        if line != "":
         contents.append(line)
    except:
      pass
    try:
      with open(self.dhcpcd_file_name,"w") as f:
       for c in range(len(contents)):
        f.write(contents[c]+"\n")
       for n in range(len(Settings.NetworkDevices)):
        if Settings.NetworkDevices[n].dhcp==False and Settings.NetworkDevices[n].ip.strip()!="":
         staticused = True
         f.write("interface "+str(Settings.NetworkDevices[n].devicename)+"\n")
         f.write("static ip_address="+str(Settings.NetworkDevices[n].ip)+"/"+str(netmask_to_cidr(Settings.NetworkDevices[n].mask))+"\n")
         if Settings.NetworkDevices[n].gw.strip() != "":
          f.write("static routers="+str(Settings.NetworkDevices[n].gw)+"\n")
         if Settings.NetworkDevices[n].dns.strip() != "":
          f.write("static domain_name_servers="+str(Settings.NetworkDevices[n].dns)+"\n")
    except:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Can not write "+self.dhcpcd_file_name+" you may have no rights.")
   else:
    dhclient = isdhclient()
    for i in range(len(Settings.NetworkDevices)):
      if Settings.NetworkDevices[i].dhcp == False and Settings.NetworkDevices[i].ip.strip()!="":
       staticused = True
    if dhclient==False or staticused:
     try:
      with open(self.interfaces_file_name,"w") as f:
       f.write("auto lo\niface lo inet loopback\n\n") # always enable localhost
       for n in range(len(Settings.NetworkDevices)):
        f.write("allow-hotplug "+Settings.NetworkDevices[n].devicename+"\n")
        newentry = False
        if dhclient==False and (Settings.NetworkDevices[n].dhcp or Settings.NetworkDevices[n].ip.strip()==""):
         f.write("iface "+Settings.NetworkDevices[n].devicename+" inet dhcp\n")
         newentry = True
        elif dhclient==False or (Settings.NetworkDevices[n].dhcp==False and Settings.NetworkDevices[n].ip.strip()!=""):
         newentry = True
         f.write("iface "+Settings.NetworkDevices[n].devicename+" inet static\n")
         if len(Settings.NetworkDevices[n].ip)>0:
          f.write(" address "+Settings.NetworkDevices[n].ip+"\n")
         if len(Settings.NetworkDevices[n].mask)>0:
          f.write(" netmask "+Settings.NetworkDevices[n].mask+"\n")
         if len(Settings.NetworkDevices[n].gw)>0:
          f.write(" gateway "+Settings.NetworkDevices[n].gw+"\n")
         if len(Settings.NetworkDevices[n].dns)>0:
          f.write(" dns-nameservers "+Settings.NetworkDevices[n].dns+"\n")
        if newentry and Settings.NetworkDevices[n].iswireless():
         wifiused = True
         if len(self.wpaconfig)<1:
          self.wpaconfig="/etc/wpa_supplicant/wpa_supplicant.conf"
         f.write(" wpa-conf "+self.wpaconfig+"\n")
        f.write("\n")
     except:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Can not write "+self.interfaces_file_name+" you may have no rights.")
   if staticused:    # write resolv.conf!!
    dnslist = []
    for n in range(len(Settings.NetworkDevices)):
     dl = Settings.NetworkDevices[n].dns.split(" ")
     if len(dl)>0:
      for i in range(len(dl)):
       if dl[i].strip() not in dnslist:
        dnslist.append(dl[i].strip())
    try:
     with open(self.resolvconf_file_name,"w") as f:
      for i in range(len(dnslist)):
       f.write("nameserver "+dnslist[i]+"\n")
    except:
     pass
   if wifiused:      # write wpa conf!
    wpastart = ""
    headerended=False
    try:
     with open(self.wpaconfig) as f:
      for line in f:
       if "network=" in line:
        headerended=True
        break
       if headerended==False:
        wpastart += line.strip()+"\n"
    except:
     pass
    if wpastart=="":
     wpastart="ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry="+str(getcountry())+"\n"
    try:
     with open(self.wpaconfig,"w") as f:
      f.write(wpastart)
      if self.WifiSSID != "":
       f.write('network={\nssid="'+str(self.WifiSSID)+'"\nscan_ssid=1\npsk="'+str(self.WifiKey)+'"\nkey_mgmt=WPA-PSK\n}\n')
      if self.WifiSSID2 != "":
       f.write('network={\nssid="'+str(self.WifiSSID2)+'"\nscan_ssid=1\npsk="'+str(self.WifiKey2)+'"\nkey_mgmt=WPA-PSK\n}\n')
    except:
     pass

def getcountry():
 result = "GB"
 try:
  output = os.popen("locale | grep LANG=")
  for line in output:
   if "LANG=" in line:
    tarr = line.split(".")
    uarr = tarr[0].split("_")
    result = uarr[1].strip()
 except:
  result = "GB"
 return result

def getdefaultgw():
 result = ""
 try:
  output = os.popen("route -n | awk '$4 == " + '"UG" ' + "{print $2}'")
  for line in output:
   if line != "":
    return line
 except:
  result = ""
 return result

def getgw(iface):
 result = ""
 try:
  output = os.popen("route -n | grep "+str(iface))
  for line in output:
   l = line.split()
   if l[2].strip() == "0.0.0.0" and l[1].strip() != "0.0.0.0":
    result = l[1]
    break
 except:
  result = ""
 return result

def isdhclient():
 result = False
 try:
  output = os.popen("ps -aux | grep dhclient")
  for line in output:
   l = line.split()
   if "bin/dhclient" in line:
    result = True
    break
 except:
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

