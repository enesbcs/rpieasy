#!/usr/bin/env python3
#############################################################################
###################### RPI Easy integrated webserver ########################
#############################################################################
#
# It's a PERVER based independent webserver in pure python used by RPIEasy
# do not call it directly.
#
# HTML source is based heavily on the ESPEasy project for which i am very grateful!
# ESPEasy licensed under GPL v3 - https://www.letscontrolit.com/
#
# Otherwise, LICENSE file must be found with the same directory with this file.
#
from perver import Perver
import os
import re
import rpieGlobals
import Settings
import time
from datetime import datetime, timedelta
import rpieTime
import os_os as OS
import misc
import commands
import os_network as Network
import urllib
import hashlib
import threading

HTML_SYMBOL_WARNING = "&#9888;"
TASKS_PER_PAGE = 16
TXBuffer = ""
navMenuIndex = 0
_HEAD = False
_TAIL = True
INT_MIN = -2147483648
INT_MAX = 2147483647

WebServer = Perver()
WebServer.timeout = 10
WebServer.get_max = 65535

def isLoggedIn(pget,pcookie):
#  if (not clientIPallowed()) return False
  rpieGlobals.WebLoggedIn = False
  if (Settings.Settings["Password"] == ""):
    rpieGlobals.WebLoggedIn = True
  else:
    spw = str(hashlib.sha1(bytes(Settings.Settings["Password"],'utf-8')).hexdigest())
    pws = str(arg("password",pget)).strip()
    if pws != "":
     if pws==Settings.Settings["Password"] or pws==spw:
      rpieGlobals.WebLoggedIn = True
    else:
     for c in pcookie:
      if 'password' in c:
       if spw==str(pcookie[c].strip()):
        rpieGlobals.WebLoggedIn = True
  return rpieGlobals.WebLoggedIn

def arg(argname,parent):
 return (argname in parent and parent[argname] or '')

@WebServer.route('/')
def handle_root(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=0
 if (rpieGlobals.wifiSetup):
   return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
   return self.redirect('/login')

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 
 cmdline = arg("cmd",responsearr).strip()
 responsestr = ""
 if len(cmdline)>0:
  responsestr = str(commands.doExecuteCommand(cmdline))

 try:
   startpage = Settings.AdvSettings["startpage"]
 except:
   startpage = "/"
 if len(startpage)>1:
   return self.redirect(startpage)

 sendHeadandTail("TmplStd",_HEAD)

 if len(responsestr)>0:
  TXBuffer += "<P>"
  TXBuffer += str(responsestr)
  TXBuffer += "<P>"

 TXBuffer += "<form>"
 TXBuffer += "<table class='normal'><tr><TH style='width:150px;' align='left'>System Info<TH align='left'>Value"
 TXBuffer += "<TR><TD>Unit:<TD>"
 TXBuffer += str(Settings.Settings["Unit"])
 TXBuffer += "<TR><TD>Local Time:<TD>" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
 TXBuffer += "<TR><TD>Uptime:<TD>" + rpieTime.getuptime(1)
 TXBuffer += "<TR><TD>Load:<TD>" +str( OS.read_cpu_usage() ) + " %"
 TXBuffer += "<TR><TD>Free Mem:<TD>" + str( OS.FreeMem() ) + " kB"
 TXBuffer += "<TR><TD>IP:<TD>" + str( OS.get_ip() )
 try:
  rssi = OS.get_rssi()
  if str(rssi)=="-49.20051":
   rssi = "Wired connection"
  else:
   rssi = str(rssi)+" dB"
 except:
   rssi = "?"
 TXBuffer += "<TR><TD>Wifi RSSI:<TD>" + str(rssi)
 TXBuffer += '<tr><td>Build<td>' + str(rpieGlobals.PROGNAME) + " " + str(rpieGlobals.PROGVER)
 TXBuffer += "<TR><TD><TD>"
 addButton("sysinfo", "More info")
 TXBuffer += "</table><BR>"
 if len(Settings.nodelist)>0:
   TXBuffer += "<BR><table class='multirow'><TR><TH>Node List<TH>Name<TH>Build<TH>Type<TH>IP<TH>Age"
   for n in Settings.nodelist:
    TXBuffer += "<TR><TD>Unit "+str(n["unitno"])+"<TD>"+str(n["name"])+"<TD>"+str(n["build"])+"<TD>"
    ntype = ""
    if int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASY_STD:
     ntype = "ESP Easy"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASYM_STD:
     ntype = "ESP Easy Mega"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASY32_STD:
     ntype = "ESP Easy32"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ARDUINO_EASY_STD:
     ntype = "Arduino Easy"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_NANO_EASY_STD:
     ntype = "Nano Easy"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD:
     ntype = "RPI Easy"
    TXBuffer += ntype+"<TD>"
    waddr = str(n["ip"])
    if str(n["port"]) != "" and str(n["port"]) != "0" and str(n["port"]) != "80":
     waddr += ":" + str(n["port"])
    addWideButton("http://"+waddr, waddr, "")
    TXBuffer += "<TD>"+str(n["age"])
   TXBuffer += "</table></form>"

 if len(Settings.p2plist)>0:
  try:
   TXBuffer += "<BR><table class='multirow'><TR><TH>Protocol<TH>P2P node number<TH>Name<TH>Build<TH>Type<TH>MAC<TH>RSSI<TH>Last seen<TH>Capabilities"
   for n in Settings.p2plist:
    hstr = str(n["protocol"])
    if hstr=="ESPNOW":
     hstr = "<a href='espnow'>"+hstr+"</a>"
    TXBuffer += "<TR><TD>"+hstr+"<TD>Unit "+str(n["unitno"])+"<TD>"+str(n["name"])+"<TD>"+str(n["build"])+"<TD>"
    ntype = "Unknown"
    if int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASY_STD:
     ntype = "ESP Easy"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASYM_STD:
     ntype = "ESP Easy Mega"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASY32_STD:
     ntype = "ESP Easy32"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ARDUINO_EASY_STD:
     ntype = "Arduino Easy"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_NANO_EASY_STD:
     ntype = "Nano Easy"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD:
     ntype = "RPI Easy"
    elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ATMEGA_EASY_LORA:
     ntype = "LoRa32u4"
    TXBuffer += ntype
    TXBuffer += "<TD>"+str(n["mac"])
    TXBuffer += "<TD>"+str(n["lastrssi"])
    ldt = n["lastseen"]
    lstr = ""
    try:
     lstr = ldt.strftime('%Y-%m-%d %H:%M:%S')
    except:
     lstr = str(ldt)
    TXBuffer += "<TD>"+lstr
    wm = int(n["cap"])
    wms = ""
    if (wm & 1)==1:
     wms = "SEND "
    if (wm & 2)==2:
     wms += "RECEIVE "
    TXBuffer += "<TD>"+wms
   TXBuffer += "</table></form>"
  except Exception as e:
   print(e)
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/config')
def handle_config(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=1
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 netdev0 = arg("netdev0",responsearr)
 netdev1 = arg("netdev1",responsearr)
 nd0_dhcp=""
 nd1_dhcp=""
 nd0_ip=""
 nd0_gw=""
 nd0_mask=""
 nd0_dns=""
 nd1_ip=""
 nd1_gw=""
 nd1_mask=""
 nd1_dns=""
 netmanage = (arg("netman",responsearr)=="on")

 saved = arg("Submit",responsearr)
 if (saved):
  Settings.Settings["Name"]  = arg("name",responsearr).replace(" ","")
  Settings.Settings["Unit"]  = arg("unit",responsearr)
  tpw = arg("password",responsearr)
  pwh = (arg("passwordhack",responsearr)=="on")
  try:
   Settings.Settings["PasswordHack"] = pwh
  except Exception as e:
   print(e)

  if "**" not in tpw:
   Settings.Settings["Password"]  = tpw
# ...
  Settings.savesettings()
#  time.sleep(0.1)
  if Settings.NetMan:
   Settings.NetMan.APMode = int(arg("apmode",responsearr))
   Settings.NetMan.APModeDev = int(arg("apmodedev",responsearr))
   Settings.NetMan.APModeTime = int(arg("apmodetime",responsearr))
   Settings.NetMan.APStopTime = int(arg("apstoptime",responsearr))
   Settings.NetMan.WifiAPChannel = int(arg("wifiapchannel",responsearr))
   tpw = arg("apkey",responsearr)
   if "**" not in tpw:
    Settings.NetMan.WifiAPKey = tpw
   Settings.NetMan.WifiSSID = arg("ssid",responsearr)
   Settings.NetMan.WifiSSID2 = arg("ssid2",responsearr)
   tpw = arg("key",responsearr)
   if "**" not in tpw:
    Settings.NetMan.WifiKey = tpw
   tpw = arg("key2",responsearr)
   if "**" not in tpw:
    Settings.NetMan.WifiKey2 = tpw
   Settings.NetMan.setAPconf()
  else:
   Settings.NetMan = Network.NetworkManager()
 
  try:
   netdev0=int(netdev0)
  except:
   netdev0=-1
  try:
   netdev1=int(netdev1)
  except:
   netdev1=-1
  nd0_dhcp= (arg("nd0_dhcp",responsearr)=="on")
  nd1_dhcp= (arg("nd1_dhcp",responsearr)=="on")
  nd0_ip= arg("nd0_ip",responsearr)
  nd0_gw= arg("nd0_gw",responsearr)
  nd0_mask= arg("nd0_mask",responsearr)
  nd0_dns= arg("nd0_dns",responsearr)
  nd1_ip= arg("nd1_ip",responsearr)
  nd1_gw= arg("nd1_gw",responsearr)
  nd1_mask= arg("nd1_mask",responsearr)
  nd1_dns= arg("nd1_dns",responsearr)

  if netdev0!=-1:
   Settings.NetMan.setdeviceorder(netdev0,netdev1)
   Settings.NetworkDevices[netdev0].dhcp=nd0_dhcp
   Settings.NetworkDevices[netdev0].ip=nd0_ip
   Settings.NetworkDevices[netdev0].gw=nd0_gw
   Settings.NetworkDevices[netdev0].mask=nd0_mask
   Settings.NetworkDevices[netdev0].dns=nd0_dns
  if netdev1!=-1:
   Settings.NetworkDevices[netdev1].dhcp=nd1_dhcp
   Settings.NetworkDevices[netdev1].ip=nd1_ip
   Settings.NetworkDevices[netdev1].gw=nd1_gw
   Settings.NetworkDevices[netdev1].mask=nd1_mask
   Settings.NetworkDevices[netdev1].dns=nd1_dns

  if netmanage:
   Settings.NetMan.saveconfig()  # save OS config files only if enabled and have root rights!!
  else:
   misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Settings saved without OS network settings modifications as you wish!")

  if netmanage and Settings.NetMan.WifiSSID != "" and Settings.NetMan.WifiKey != "":
   Network.AP_stop(Settings.NetMan.WifiDevNum)
   time.sleep(3)
  Settings.savenetsettings()     # save to json
 else:
  Settings.loadsettings()

 sendHeadandTail("TmplStd",_HEAD)

 TXBuffer += "<form name='frmselect' method='post'><table class='normal'>"
 addFormHeader("Main Settings")

 addFormTextBox( "Unit Name", "name", Settings.Settings["Name"], 25)

 addFormNumericBox( "Unit Number", "unit", Settings.Settings["Unit"], 0, 256)
 addFormPasswordBox( "Admin Password" , "password", Settings.Settings["Password"], 25)
 try:
  ph = Settings.Settings["PasswordHack"]
 except:
  ph = False
 addFormCheckBox("Disable password for safe commands","passwordhack", ph)
 addFormNote("NOT SAFE COMMANDS: Reboot,Reset,Halt,Update,Exit")

 addFormSeparator(2)
 try:
  choice = Settings.NetMan.APMode
 except:
  choice = -1
 options = ["Never","At startup without condition","Primary dev disconnected","Secondary dev disconnected","First WiFi dev disconnected"]
 optionvalues = [-1,100,0,1,99]
 addFormSelector("Start AP when","apmode",len(optionvalues),options,optionvalues,None,int(choice))
 try:
  choice = Settings.NetMan.APModeDev
 except:
  choice = 99
 options = ["Primary network device","Secondary network device","First wireless network device"]
 optionvalues = [0,1,99]
 addFormSelector("On this device","apmodedev",len(optionvalues),options,optionvalues,None,int(choice))
 try:
  dval = Settings.NetMan.APModeTime
 except:
  dval = 30
 addFormNumericBox( "After this time", "apmodetime", dval, 5, 600)
 addUnit("sec")
 try:
  dval = Settings.NetMan.WifiAPChannel
 except:
  dval = 1
 addFormNumericBox( "On this channel", "wifiapchannel", dval, 1, 13)
 try:
  dval = Settings.NetMan.APStopTime
 except:
  dval = -1
 options = ["Never","3","5","10","15"]
 optionvalues = [-1,180,300,600,900]
 addFormSelector("Stop AP after","apstoptime",len(optionvalues),options,optionvalues,None,int(dval))
 addUnit("min")

 addFormPasswordBox("WPA AP Mode Key", "apkey", Settings.NetMan.WifiAPKey, 128)
 addFormNote("Password has to be at least 8 character long!")

 try:
  if (plugindeps.modulelist):
   pass
 except:
  import plugindeps

 try:
  TXBuffer += "<TR><TD>HostAPD library status:<TD>"
  modname = "wifiap"
  puse = plugindeps.ismoduleusable(modname)
  addEnabled(puse)
  if puse==False:
   usable = False
   TXBuffer += "<a href='plugins?installmodule="+modname+"'>"
  TXBuffer += modname+" "
  if puse==False:
   TXBuffer += "</a> (Not installed, AP mode will not work!)"
  else:
   TXBuffer += "module installed"
 except Exception as e:
  print(e)

 TXBuffer += "<TR><TD style='width:150px;' align='left'><TD>"
 addSubmitButton()
 netmanager = OS.detectNM()
 oslvl = misc.getsupportlevel(1)
 if oslvl in [1,2,3,9,10]: # maintain supported system list!!!
  addFormSeparator(2)
  if oslvl != 2:
   if netmanager:
    addFormNote("<font color=red><b><a href='https://wiki.debian.org/NetworkManager'>NetworkManager</a> is currently not supported!</b></font>")
   else:
    addFormCheckBox("I have root rights and i really want to manage network settings below","netman", netmanage)
  addFormNote("<font color=red><b>If this checkbox not enabled, OS config files will not be overwritten!</b></font>")
 
  addFormSubHeader("Wifi Settings") #/etc/wpa_supplicant/wpa_supplicant.conf
  addFormTextBox( "SSID", "ssid", Settings.NetMan.WifiSSID, 32)
  addFormPasswordBox("WPA Key", "key", Settings.NetMan.WifiKey, 64)
  addFormTextBox( "Fallback SSID", "ssid2", Settings.NetMan.WifiSSID2, 32)
  addFormPasswordBox( "Fallback WPA Key", "key2", Settings.NetMan.WifiKey2, 64)
  addFormSeparator(2)

  addFormSubHeader("IP Settings")
  TXBuffer += "<TR><TD>Primary network device:<TD>"
  netdevs = Settings.NetMan.getdevicenames()
  if netdev0=="":
   defaultdev = Settings.NetMan.getprimarydevice()
  else:
   defaultdev = int(netdev0)
  if len(netdevs)>0: 
    addSelector_Head('netdev0',True)
    for i in range(0,len(netdevs)):
     addSelector_Item(netdevs[i],i,(int(i)==int(defaultdev)),False)
    addSelector_Foot()
    seld = defaultdev
    if defaultdev<0:
     seld = 0
    if nd0_dhcp=="":
     nd0_dhcp=Settings.NetworkDevices[seld].dhcp
    if nd0_dhcp!=True:
     nd0_dhcp=False
    if nd0_ip=="":
      nd0_ip=Settings.NetworkDevices[seld].ip
    if nd0_gw=="":
      nd0_gw=Settings.NetworkDevices[seld].gw
    if nd0_mask=="":
      nd0_mask=Settings.NetworkDevices[seld].mask
    if nd0_dns=="":
      nd0_dns=Settings.NetworkDevices[seld].dns
    addEnabled(Settings.NetworkDevices[seld].isconnected())
    addNetType(Settings.NetworkDevices[seld].iswireless())
    addFormCheckBox("DHCP","nd0_dhcp",nd0_dhcp)
    addFormTextBox("IP", "nd0_ip", nd0_ip,15)
    addFormTextBox("GW", "nd0_gw", nd0_gw,15)
    addFormTextBox("Mask", "nd0_mask",nd0_mask,15)
    addFormTextBox("DNS", "nd0_dns", nd0_dns,128)
    addFormNote("If DHCP enabled these fields will not be saved or used!")
  else:
    TXBuffer += "No device"
  if len(netdevs)>1:
   TXBuffer += "<TR><TD>Secondary network device:<TD>"
   if netdev1=="":
    defaultdev2 = Settings.NetMan.getsecondarydevice()
   else:
    defaultdev2=int(netdev1)
   seld2 = defaultdev2
   if defaultdev<0:
     seld2 = 0
   if seld2==seld:
    if seld==0:
     seld2=1
    else:
     seld2=0
   addSelector_Head('netdev1',True)
   for i in range(0,len(netdevs)):
     addSelector_Item(netdevs[i],i,(int(i)==int(seld2)),False)
   addSelector_Foot()
   if nd1_dhcp=="":
     nd1_dhcp=Settings.NetworkDevices[seld2].dhcp
   if nd1_dhcp!=True:
     nd1_dhcp=False
   if nd1_ip=="":
     nd1_ip=Settings.NetworkDevices[seld2].ip
   if nd1_gw=="":
     nd1_gw=Settings.NetworkDevices[seld2].gw
   if nd1_mask=="":
     nd1_mask=Settings.NetworkDevices[seld2].mask
   if nd1_dns=="":
     nd1_dns=Settings.NetworkDevices[seld2].dns
   addEnabled(Settings.NetworkDevices[seld2].isconnected())
   addNetType(Settings.NetworkDevices[seld2].iswireless())
   addFormCheckBox("DHCP","nd1_dhcp",nd1_dhcp)
   addFormTextBox("IP", "nd1_ip", nd1_ip,15)
   addFormTextBox("GW", "nd1_gw", nd1_gw,15)
   addFormTextBox("Mask", "nd1_mask",nd1_mask,15)
   addFormTextBox("DNS", "nd1_dns", nd1_dns,15)
   addFormNote("If DHCP enabled these fields will not be saved or used!")

  TXBuffer += "<TR><TD style='width:150px;' align='left'><TD>"
  if netmanager==False:
   addSubmitButton()
 TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/controllers')
def handle_controllers(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=2
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 edit = arg("edit",responsearr)

 controllerindex = arg("index",responsearr)
 controllerNotSet = (controllerindex == 0) or (controllerindex == '')
 if controllerindex!="":
  controllerindex = int(controllerindex) - 1
 controllerip = arg("controllerip",responsearr)
 controllerport = arg("controllerport",responsearr)
 protocol = arg("protocol",responsearr)
 if protocol!="":
  protocol=int(protocol)
 else:
  protocol=0
 controlleruser = arg("controlleruser",responsearr)
 controllerpassword = arg("controllerpassword",responsearr)
 enabled = (arg("controllerenabled",responsearr)=="on")

 if ((protocol == 0) and (edit=='') and (controllerindex!='')) or (arg('del',responsearr) != ''):
   try:
    Settings.Controllers[controllerindex].controller_exit()
   except:
    pass
   Settings.Controllers[controllerindex] = False
   controllerNotSet = True
   Settings.savecontrollers()

 if (controllerNotSet==False): # submitted
  if (protocol > 0): # submitted
   try:
    if (Settings.Controllers[controllerindex]):
     Settings.Controllers[controllerindex].controllerip = controllerip
     Settings.Controllers[controllerindex].controllerport = controllerport
     Settings.Controllers[controllerindex].controlleruser = controlleruser
     if "**" not in controllerpassword:
      Settings.Controllers[controllerindex].controllerpassword = controllerpassword
     Settings.Controllers[controllerindex].enabled = enabled
     Settings.Controllers[controllerindex].webform_save(responsearr)
     Settings.savecontrollers()
   except:
    pass
  else:
   try:
    if (Settings.Controllers[controllerindex]):
     protocol = Settings.Controllers[controllerindex].controllerid
   except:
    pass
 TXBuffer += "<form name='frmselect' method='post'>"
 if (controllerNotSet): # show all in table
    TXBuffer += "<table class='multirow' border=1px frame='box' rules='all'><TR><TH style='width:70px;'>"
    TXBuffer += "<TH style='width:50px;'>Nr<TH style='width:100px;'>Enabled<TH>Protocol<TH>Host<TH>Port"
    for x in range(rpieGlobals.CONTROLLER_MAX):
      TXBuffer += "<tr><td><a class='button link' href=\"controllers?index="
      TXBuffer += str(x + 1)
      TXBuffer += "&edit=1\">Edit</a><td>"
      TXBuffer += getControllerSymbol(x)
      TXBuffer += "</td><td>"
      try:
       if (Settings.Controllers[x]):
        addEnabled(Settings.Controllers[x].enabled)
        TXBuffer += "</td><td>"
        TXBuffer += str(Settings.Controllers[x].getcontrollername())
        TXBuffer += "</td><td>"
        TXBuffer += str(Settings.Controllers[x].controllerip)
        TXBuffer += "</td><td>"
        TXBuffer += str(Settings.Controllers[x].controllerport)
       else:
        TXBuffer += "<td><td><td>"
      except:
       TXBuffer += "<td><td><td>"
    TXBuffer += "</table></form>"
 else: # edit
    TXBuffer += "<table class='normal'><TR><TH style='width:150px;' align='left'>Controller Settings<TH>"
    TXBuffer += "<tr><td>Protocol:<td>"
    addSelector_Head("protocol", True)
    for x in range(len(rpieGlobals.controllerselector)):
      addSelector_Item(rpieGlobals.controllerselector[x][2],int(rpieGlobals.controllerselector[x][1]),(str(protocol) == str(rpieGlobals.controllerselector[x][1])),False,"")
    addSelector_Foot()
    if (int(protocol) > 0):
      createnewcontroller = True
      try:
       if (Settings.Controllers[controllerindex].getcontrollerid()==int(protocol)):
        createnewcontroller = False
      except:
       pass
      exceptstr = ""
      if createnewcontroller:
       for y in range(len(rpieGlobals.controllerselector)):
        if int(rpieGlobals.controllerselector[y][1]) == int(protocol):
         if len(Settings.Controllers)<=controllerindex:
          while len(Settings.Controllers)<=controllerindex:
           Settings.Controllers.append(False)
         try:
           m = __import__(rpieGlobals.controllerselector[y][0])
         except Exception as e:
          Settings.Controllers[controllerindex] = False
          exceptstr += str(e)
          m = False
         if m:
          try: 
           Settings.Controllers[controllerindex] = m.Controller(controllerindex)
          except Exception as e:
           Settings.Controllers.append(m.Controller(controllerindex))
           exceptstr += str(e)
         break
      if Settings.Controllers[controllerindex] == False:
       errormsg = "Importing failed, please double <a href='plugins'>check dependencies</a>! "+str(exceptstr)
       TXBuffer += errormsg+"</td></tr></table>"
       sendHeadandTail("TmplStd",_TAIL)
       return TXBuffer
      else:
       try:
        Settings.Controllers[controllerindex].controller_init() # call plugin init
        if (Settings.Controllers[controllerindex]):
          if (Settings.Controllers[controllerindex].enabled): 
           Settings.Controllers[controllerindex].setonmsgcallback(Settings.callback_from_controllers) 
        for x in range(0,len(Settings.Tasks)):
         if (Settings.Tasks[x] and type(Settings.Tasks[x]) is not bool): # device exists
          if (Settings.Tasks[x].enabled): # device enabled
            if (Settings.Tasks[x].senddataenabled[controllerindex]):
             if (Settings.Controllers[controllerindex]):
              if (Settings.Controllers[controllerindex].enabled):
               Settings.Tasks[x].controllercb[controllerindex] = Settings.Controllers[controllerindex].senddata
       except:
        pass
    if controllerindex != '':
     TXBuffer += "<input type='hidden' name='index' value='" + str(controllerindex+1) +"'>"
     if int(protocol)>0:
      addFormCheckBox("Enabled", "controllerenabled", Settings.Controllers[controllerindex].enabled)
      addFormTextBox("Controller Host Address", "controllerip", Settings.Controllers[controllerindex].controllerip, 96)
      addFormNumericBox("Controller Port", "controllerport", Settings.Controllers[controllerindex].controllerport, 1, 65535)
      if Settings.Controllers[controllerindex].usesAccount:
       addFormTextBox("Controller User", "controlleruser", Settings.Controllers[controllerindex].controlleruser,96)
      if Settings.Controllers[controllerindex].usesPassword:
       addFormPasswordBox("Controller Password", "controllerpassword", Settings.Controllers[controllerindex].controllerpassword,96)
      try:
       Settings.Controllers[controllerindex].webform_load()
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller"+str(controllerindex)+ " "+str(e))

    addFormSeparator(2)
    TXBuffer += "<tr><td><td>"
    TXBuffer += "<a class='button link' href=\"controllers\">Close</a>"
    addSubmitButton()
    if controllerindex != '':
     addSubmitButton("Delete", "del")
    TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/hardware')
def handle_hardware(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')

 sendHeadandTail("TmplStd",_HEAD)
 try:
  suplvl = misc.getsupportlevel()
  if suplvl[0] != "N":
   ar = OS.autorun()
   ar.readconfig()
 except:
  suplvl = 0

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 try:
  if (arg('nokernelserial',responsearr) != ""):
   OS.disable_serialsyslog()
 except:
  pass

 if (arg('volume',responsearr) != ""):
  try:
   OS.setvolume(str(arg('volume',responsearr)))
  except Exception as e:
   print(e)

 submit = arg("Submit",responsearr)

 if (submit=="Submit") and (suplvl[0] != "N"):
  try:
   stat = arg("rpiauto",responsearr)
   if stat=="on":
    ar.rpiauto=True
   else:
    ar.rpiauto=False
   stat = arg("rpiauto2",responsearr)
   if stat=="on":
    ar.rpiauto2=True
    ar.rpiauto=False #disable old method
   else:
    ar.rpiauto2=False
   stat = arg("hdmienabled",responsearr)
   if stat=="on":
    ar.hdmienabled=True
   else:
    ar.hdmienabled=False
   snddev = arg("snddev",responsearr)
   snddev = snddev.strip()
   if OS.check_permission():
    ar.saveconfig()
   try:
    if int(snddev)>=0:
     OS.updateaudiocard(snddev)
   except:
    pass
  except:
   pass

 try:
  TXBuffer += "<form name='frmselect' method='post'><table class='normal'><tr><TH style='width:150px;' align='left' colspan=2>System"
  TXBuffer += "<TR><TD>Type:<TD>"+suplvl

  if suplvl[0] != "N":
   TXBuffer += "<TR><TD>OS:<TD>"+str(rpieGlobals.osinuse)+" "+str(misc.getosname(1))
  if "Linux" in suplvl:
   TXBuffer += "<TR><TD>OS full name:<TD>"+str(OS.getosfullname())
  if suplvl[0] == "L":
   TXBuffer += "<TR><TD>Hardware:<TD>"+str(OS.gethardware())
  if "RPI" in suplvl:
   rpv = OS.getRPIVer()
   if len(rpv)>1:
    TXBuffer += "<TR><TD>Hardware:<TD>"+rpv["name"]+" "+rpv["ram"]
  elif "RockPI" in suplvl:
   ropv = OS.getRockPIVer()
   if len(ropv)>0:
    TXBuffer += "<TR><TD>Hardware:<TD>"+ropv["name"]
  elif "OPI" in suplvl:
   opv = OS.getarmbianinfo()
   if len(opv)>0:
    TXBuffer += "<TR><TD>Hardware:<TD>"+opv["name"]
  if suplvl[0] != "N":
   addFormSeparator(2)
   racc = OS.check_permission()
   rstr = str(racc)
   if racc == False:
    rstr = "<font color=red>"+rstr+"</font> (system-wide settings are only for root)"
   TXBuffer += "<TR><TD>Root access:<TD>"+rstr
   TXBuffer += "<TR><TD>Sound playback device:<TD>"
   try:
    sounddevs = OS.getsounddevs()
    defaultdev = OS.getsoundsel()
   except Exception as e:
    print("Sound device:",e)
   if len(sounddevs)>0: 
    addSelector_Head('snddev',False)
    for i in range(0,len(sounddevs)):
     addSelector_Item(sounddevs[i][1],int(sounddevs[i][0]),(int(sounddevs[i][0])==int(defaultdev)),False)
    addSelector_Foot()
    vol = 100
    try:
     vol = OS.getvolume()
    except Exception as e:
     print("GetVolume:",e)
    TXBuffer += '<TR><TD>Sound volume:<TD><input type="range" id="volume" name="volume" min="0" max="100" value="'+str(vol)+'">'
   else:
    TXBuffer += "No device"

   addFormCheckBox("RPIEasy autostart at boot with rc.local (recommended)","rpiauto",ar.rpiauto)
   addFormCheckBox("RPIEasy autostart at boot with systemctl/openrc (experimental)","rpiauto2",ar.rpiauto2)
   if OS.checkRPI():
    addFormCheckBox("Enable HDMI at startup","hdmienabled",ar.hdmienabled)
   if OS.check_permission():
    TXBuffer += "<tr><td colspan=2>"
    addSubmitButton() 
 except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HW page error "+str(e))

 addFormSeparator(2)
 TXBuffer += "<TR><TD HEIGHT=30>"
 addWideButton("plugins", "Plugin&controller dependencies", "")
 TXBuffer += "</TD><TD HEIGHT=30>"
 addWideButton("pinout", "Pinout&Ports", "")
 TXBuffer += "<TR><TD HEIGHT=30>"
 addWideButton("wifiscanner", "Scan Wifi networks", "")
 TXBuffer += "</TD><TD HEIGHT=30>"
 addWideButton("i2cscanner", "I2C Scan", "")
 TXBuffer += "<TR><TD HEIGHT=30>"
 addWideButton("blescanner", "Scan Bluetooth LE", "")

 try:
  bpcont = OS.get_bootparams()
  if ("ttyAMA" in bpcont) or ("ttyS" in bpcont) or ("serial" in bpcont):
   addFormSeparator(2)
   addSubmitButton("Disable Serial port usage by kernel","nokernelserial")
 except:
  pass

 TXBuffer += "</table></form>"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/pinout')
def handle_pinout(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 try:
  import gpios
  portok = True
 except:
  print("Unable to load GPIO support")
  portok = False
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 submit = arg("Submit",responsearr)
 setbtn = arg("set",responsearr).strip()

 if ((rpieGlobals.ossubtype not in [3,9,10]) and (submit=="Submit") or (setbtn!='')):
   try:
    gpios.HWPorts.webform_save(responsearr)
   except Exception as e:
    print(e)
    portok = False
   submit=""
   setbtn=""

 if arg("reread",responsearr) != '':
  submit = ''
  try:
   gpios.HWPorts.readconfig()
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Config read error="+str(e))
   portok = False

 if (submit=="Submit") or (setbtn!=''):
  try:
   stat = arg("i2c0",responsearr)
   if stat=="on":
    gpios.HWPorts.enable_i2c(0)
   else:
    gpios.HWPorts.disable_i2c(0)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C-0 error="+str(e))
  try:
   stat = arg("i2c1",responsearr)
   if stat=="on":
    gpios.HWPorts.enable_i2c(1)
   else:
    gpios.HWPorts.disable_i2c(1)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C-1 error="+str(e))
  try:
   stat = arg("spi0",responsearr)
   if stat=="on":
    gpios.HWPorts.enable_spi(0,2)
   else:
    gpios.HWPorts.disable_spi(0)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SPI-0 error="+str(e))

  try:
   stat = int(arg("spi1",responsearr).strip())
  except:
   stat = 0
  try:
   if stat == "":
    stat = 0
   if stat == 0:
     gpios.HWPorts.disable_spi(1)
   else:
     gpios.HWPorts.enable_spi(1,stat)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SPI-1 error="+str(e))

  try:
   stat = arg("uart",responsearr)
   if stat=="on":
    gpios.HWPorts.set_serial(1)
   else:
    gpios.HWPorts.set_serial(0)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"UART init error="+str(e))

  try:
   stat = arg("audio",responsearr)
   if stat=="on":
    gpios.HWPorts.set_audio(1)
   else:
    gpios.HWPorts.set_audio(0)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Audio init error="+str(e))
  try:
   stat = arg("i2s",responsearr)
   if stat=="on":
    gpios.HWPorts.set_i2s(1)
   else:
    gpios.HWPorts.set_i2s(0)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2S init error="+str(e))

  try:
   stat = int(arg("bluetooth",responsearr).strip())
  except:
   stat=0
  try:
   gpios.HWPorts.set_internal_bt(stat)
   stat = arg("wifi",responsearr)
   if stat=="on":
    gpios.HWPorts.set_wifi(1)
   else:
    gpios.HWPorts.set_wifi(0)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"WLAN init error="+str(e))

  try:
   stat = int(arg("gpumem",responsearr).strip())
  except:
   stat=16
  gpios.HWPorts.gpumem = stat

  si2carr = []
  for i in range(0,21):
   iarr = [-1,-1,-1]
   try:
    iarr[0] = int(arg("si2c"+str(i),responsearr))
    iarr[1] = int(arg("si2c"+str(i)+"_sda",responsearr))
    iarr[2] = int(arg("si2c"+str(i)+"_scl",responsearr))
    if -1 not in iarr:
     si2carr.append(iarr)
   except Exception as e:
    pass
  if (len(si2carr)>0) or (len(gpios.HWPorts.i2cgpio)>0): #deal with soft i2c
    pinold = []
    pinused = []
    for si in range(len(si2carr)):
      for i in range(1,3):
       pin = si2carr[si][i]
       if pin not in pinused and pin != -1:
        pinused.append(pin)
    for si in range(len(gpios.HWPorts.i2cgpio)):
      for i in range(1,3):
       pin = gpios.HWPorts.i2cgpio[si][i]
       if pin not in pinold:
        pinold.append(pin)
    for p in range(len(pinold)):
     if pinold[p] not in pinused:
      gpios.HWPorts.setpinspecial(pinold[p],0) #do not reserve pins that not used anymore
    for p in range(len(pinused)):
      gpios.HWPorts.setpinspecial(pinused[p],1) #set used pins as Special
    gpios.HWPorts.i2cgpio = si2carr # save new i2cpins

  for p in range(len(Settings.Pinout)):
   pins = arg("pinstate"+str(p),responsearr)
   if pins and pins!="" and p!= "":
    try:
     gpios.HWPorts.setpinstate(p,int(pins))
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Pin "+str(p)+" "+str(e))

  if OS.check_permission() and setbtn=='':
   try:
    gpios.HWPorts.saveconfig()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
  try:
   Settings.savepinout()
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))

 if ((rpieGlobals.ossubtype in [3,9,10]) and (len(Settings.Pinout)>1)): # RPI only
  TXBuffer += "<form name='frmselect' method='post'><table class='normal'>"
  TXBuffer += "<tr><th colspan=10>GPIO pinout</th></tr>"
  addHtml("<tr><th>Detected function</th><th>Requested function</th><th>Pin name</th><th>#</th><th>Value</th><th>Value</th><th>#</th><th>Pin name</th><th>Requested function</th><th>Detected function</th></tr>")
  for p in range(len(Settings.Pinout)):
   if Settings.Pinout[p]["canchange"] != 2:
    idnum = int(Settings.Pinout[p]["ID"])
    if bool(idnum & 1): # left
     TXBuffer += "<TR><td>"
#     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      # print pin setup infos
      astate = Settings.Pinout[p]["actualstate"]
      if astate<0:
       astate=0
      astate = Settings.PinStates[astate]
      pinfunc = -1
      if gpios.HWPorts.gpioinit:
       pinfunc = gpios.HWPorts.gpio_function(int(Settings.Pinout[p]["BCM"]))
       astate = str(gpios.HWPorts.gpio_function_name(pinfunc))
      TXBuffer += astate
      TXBuffer += "</td>" # actual state 
     else:
      TXBuffer += "-</td>"
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
      addHtml("<td>") # startupstate
      addSelector("pinstate"+str(p),Settings.PinStatesMax,Settings.PinStates,False,None,Settings.Pinout[p]["startupstate"],False)
      addHtml("</td>")
     else:
      TXBuffer += "<td>-</td>"
     try:
      funcorder = int(Settings.Pinout[p]["altfunc"])
     except:
      funcorder = 0
     if funcorder>0 and len(Settings.Pinout[p]["name"])>funcorder:
      TXBuffer += "<td>"+ Settings.Pinout[p]["name"][funcorder] +"</td>"
     else:
      TXBuffer += "<td>"+ Settings.Pinout[p]["name"][0] +"</td>"
     TXBuffer += "<td>"+ str(Settings.Pinout[p]["ID"]) +"</td>"
     TXBuffer += "<td style='{border-right: solid 1px #000;}'>"
     if Settings.Pinout[p]["canchange"]==1 and pinfunc in [0,1] and (astate in ["Input","Output"]):
      if gpios.HWPorts.gpioinit:
       gpios.HWPorts.setpinstate(p,int(Settings.Pinout[p]["startupstate"]))
       try:
        TXBuffer += "("+str(gpios.HWPorts.input(int(Settings.Pinout[p]["BCM"])))+")"
       except:
        TXBuffer += "E" 
      else:
       TXBuffer += "X" 
      TXBuffer += "</td>" # add pin value
     else:
      TXBuffer += "-</td>"
    else:               # right
     pinfunc = -1
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      TXBuffer += "<td>"
      if gpios.HWPorts.gpioinit:
       pinfunc = gpios.HWPorts.gpio_function(int(Settings.Pinout[p]["BCM"]))
       if pinfunc in [0,1] and Settings.Pinout[p]["altfunc"]==0:
        gpios.HWPorts.setpinstate(p,int(Settings.Pinout[p]["startupstate"]))
        try:
         TXBuffer += "("+str(gpios.HWPorts.input(int(Settings.Pinout[p]["BCM"])))+")"
        except:
         TXBuffer += "E" 
      else:
       TXBuffer += "X" 
      TXBuffer += "</td>" # add pin value
     else:
      TXBuffer += "<td>-</td>"
     TXBuffer += "<td>"+ str(Settings.Pinout[p]["ID"]) +"</td>"
     try:
      funcorder = int(Settings.Pinout[p]["altfunc"])
     except:
      funcorder = 0
     if funcorder>0 and len(Settings.Pinout[p]["name"])>funcorder:
      TXBuffer += "<td>"+ Settings.Pinout[p]["name"][funcorder] +"</td>"
     else:
      TXBuffer += "<td>"+ Settings.Pinout[p]["name"][0] +"</td>"
     TXBuffer += "<td>"
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
      # print pin setup infos
      addSelector("pinstate"+str(p),Settings.PinStatesMax,Settings.PinStates,False,None,Settings.Pinout[p]["startupstate"],False)
      addHtml("</td>")
     else:
      TXBuffer += "-</td>"
     addHtml("<td>") # startupstate
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      astate = Settings.Pinout[p]["actualstate"]
      if astate<0:
        astate=0
      astate = Settings.PinStates[astate]
      if gpios.HWPorts.gpioinit:
        astate = str(gpios.HWPorts.gpio_function_name(pinfunc))
      TXBuffer += str(astate)+"</td>" # actual state 
     else:
      TXBuffer += "<td>-</td>"
     TXBuffer += "</TR>"
  TXBuffer += "</table>"

  TXBuffer += "<table class='normal'><TR>"
  addFormHeader("Advanced features")
  for i in range(0,2):
   if gpios.HWPorts.is_i2c_usable(i):
    addFormCheckBox("Enable I2C-"+str(i),"i2c"+str(i),gpios.HWPorts.is_i2c_enabled(i))
  if gpios.HWPorts.is_spi_usable(0):
    addFormCheckBox("Enable SPI-0","spi0",gpios.HWPorts.is_spi_enabled(0))
  if gpios.HWPorts.is_spi_usable(1):
    selopt = 0
    if gpios.HWPorts.is_spi_enabled(1):
     selopt = gpios.HWPorts.spi_cs[1]
    soptions = ["Disabled","Enabled with 1xCS pins","Enabled with 2xCS pins","Enabled with 3xCS pins"]
    addFormSelector("SPI-1", "spi1", len(soptions), soptions, False, None, selopt, False)
  addFormCheckBox("Enable UART","uart",gpios.HWPorts.is_serial_enabled())
  addFormCheckBox("Enable internal Audio","audio",gpios.HWPorts.is_audio_enabled())
  addFormNote("Audio might interfere with PWM! Disable audio if PWM needed.")
  if gpios.HWPorts.is_i2s_usable():
   addFormCheckBox("Enable I2S","i2s",(gpios.HWPorts.i2s==1))
   addFormNote("I2S might interfere with PWM and SPI1")
  if gpios.HWPorts.is_internal_bt_usable():
    selopt = gpios.HWPorts.get_internal_bt_level()
    soptions = ["Disabled","Enabled with SW","Enabled with HW (default)"]
    addFormSelector("Internal Bluetooth", "bluetooth", len(soptions), soptions, False, None, selopt, False)
    addFormNote("BT might interfere with UART! Disable or use SW mode if real UART needed.")
  if gpios.HWPorts.is_internal_wifi_usable():
    addFormCheckBox("Internal WiFi","wifi",gpios.HWPorts.is_wifi_enabled())
  addFormNumericBox("GPU memory","gpumem", gpios.HWPorts.gpumem,gpios.HWPorts.gpumin,gpios.HWPorts.gpumax)
  addUnit("MB")
  addFormHeader("Software I2C")
  addFormNumericBox("New soft-I2C","si2c0", None, 3,20)
  addFormPinSelect("New SDA","si2c0_sda", None)
  addFormPinSelect("New SCL","si2c0_scl", None)
  if len(gpios.HWPorts.i2cgpio)>0:
   for i in range(len(gpios.HWPorts.i2cgpio)):
    b = gpios.HWPorts.i2cgpio[i][0]
    addFormNumericBox("Soft-I2C"+str(b),"si2c"+str(b), b, 3,20)
    addFormPinSelect("I2C"+str(b)+" SDA","si2c"+str(b)+"_sda", gpios.HWPorts.i2cgpio[i][1])
    addFormPinSelect("I2C"+str(b)+" SCL","si2c"+str(b)+"_scl", gpios.HWPorts.i2cgpio[i][2])
  addFormSeparator(2)
  TXBuffer += "<tr><td colspan=2>"
  if OS.check_permission():
   addSubmitButton()
  addSubmitButton("Set without save","set")
  addSubmitButton("Reread config","reread")
  TXBuffer += "</td></tr>"
  if OS.check_permission():
   if OS.checkboot_ro():
     addFormNote("<font color='red'>WARNING: Your /boot partition is mounted READONLY! Changes could not be saved! Run 'sudo mount -o remount,rw /boot' or whatever necessary to solve it!")
  addFormNote("WARNING: Some changes needed to reboot after submitting changes! And most changes requires root permission.")
  addHtml("</table></form>")
 else:
  try:
   gpios.HWPorts.webform_load()
   portok = True
  except Exception as e:
   addHtml("<p>This hardware has unknown GPIO.<p>")
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, str(e))
   portok = False
 if portok==False:
   output = os.popen('uname -a')
   for line in output:
            line = line.strip()
            addHtml("<br>"+str(line))
   if os.path.exists("/proc/cpuinfo"):
    with open("/proc/cpuinfo") as f:
        for line in f:
            line = line.strip()
            addHtml("<br>"+str(line))
   if os.path.exists("/etc/armbian-release"):
    with open("/etc/armbian-release") as f:
        for line in f:
            line = line.strip()
            addHtml("<br>"+str(line))

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/plugins')
def handle_plugins(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3

 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 try:
  if (plugindeps.modulelist):
   pass
 except:
  import plugindeps

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 moduletoinstall = arg('installmodule',responsearr).strip()

 if moduletoinstall:
  try:
   res = plugindeps.installdeps(moduletoinstall)
   if res==False:
    return self.redirect('/update')
  except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Module install: "+str(e))

 if OS.check_permission()==False:
   TXBuffer += "Installation WILL NOT WORK without root permission!<p>"

 TXBuffer += "<p><b>If you want to install a dependency, please click at the blue underlined text, where you see a red X!<b><p><br>"

 TXBuffer += "<table class='multirow' border=1px frame='box' rules='all'><TR><TH colspan=4>Controllers</TH></TR>"
 TXBuffer += "<TR><TH>#</TH><TH>Name</TH><TH>Dependencies</TH><TH>Usable</TH></TR>"

 for x in range(len(rpieGlobals.controllerselector)):
  if (rpieGlobals.controllerselector[x][1] != 0):
   TXBuffer += "<tr><td>" + str(rpieGlobals.controllerselector[x][1])+"</td><td align=left>"+rpieGlobals.controllerselector[x][2]+"</td>"
   depfound = -1
   for y in range(len(plugindeps.controllerdependencies)):
    if str(plugindeps.controllerdependencies[y]["controllerid"]) == str(rpieGlobals.controllerselector[x][1]):
     depfound = y
     break
   TXBuffer += "<td>"
   usable = True
   if depfound>-1:
    if (plugindeps.controllerdependencies[depfound]["modules"]):
     for z in range(len(plugindeps.controllerdependencies[depfound]["modules"])):
      puse = plugindeps.ismoduleusable(plugindeps.controllerdependencies[depfound]["modules"][z])
      addEnabled(puse)
      if puse==False:
       usable = False
       TXBuffer += "<a href='plugins?installmodule="+plugindeps.controllerdependencies[depfound]["modules"][z]+"'>"
      TXBuffer += plugindeps.controllerdependencies[depfound]["modules"][z]+" "
      if puse==False:
       TXBuffer += "</a>"
   else:
    TXBuffer += "No dependencies"
   TXBuffer += "</td><td>"
   addEnabled(usable)
   TXBuffer += "</td></tr>"

 TXBuffer += "</table><p><table class='multirow' border=1px frame='box' rules='all'><TR><TH colspan=4>Notifications</TH></TR>"
 TXBuffer += "<TR><TH>#</TH><TH>Name</TH><TH>Dependencies</TH><TH>Usable</TH></TR>"

 for x in range(len(rpieGlobals.notifierselector)):
  if (rpieGlobals.notifierselector[x][1] != 0):
   TXBuffer += "<tr><td>" + str(rpieGlobals.notifierselector[x][1])+"</td><td align=left>"+rpieGlobals.notifierselector[x][2]+"</td>"
   depfound = -1
   for y in range(len(plugindeps.notifierdependencies)):
    if str(plugindeps.notifierdependencies[y]["npluginid"]) == str(rpieGlobals.notifierselector[x][1]):
     depfound = y
     break
   TXBuffer += "<td>"
   usable = True
   if depfound>-1:
    if (plugindeps.notifierdependencies[depfound]["modules"]):
     for z in range(len(plugindeps.notifierdependencies[depfound]["modules"])):
      puse = plugindeps.ismoduleusable(plugindeps.notifierdependencies[depfound]["modules"][z])
      addEnabled(puse)
      if puse==False:
       usable = False
       TXBuffer += "<a href='plugins?installmodule="+plugindeps.notifierdependencies[depfound]["modules"][z]+"'>"
      TXBuffer += plugindeps.notifierdependencies[depfound]["modules"][z]+" "
      if puse==False:
       TXBuffer += "</a>"
   else:
    TXBuffer += "No dependencies"
   TXBuffer += "</td><td>"
   addEnabled(usable)
   TXBuffer += "</td></tr>"

 TXBuffer += "</table><p><table class='multirow' border=1px frame='box' rules='all'><TR><TH colspan=5>Plugins</TH></TR>"
 TXBuffer += "<TR><TH>#</TH><TH>Name</TH><TH>OS</TH><TH>Dependencies</TH><TH>Usable</TH></TR>"

 oslvl = misc.getsupportlevel(1)
 for x in range(len(rpieGlobals.deviceselector)):
  if (rpieGlobals.deviceselector[x][1] != 0):
   TXBuffer += "<tr><td>" + str(rpieGlobals.deviceselector[x][1])+"</td><td align=left>"+rpieGlobals.deviceselector[x][2]+"</td>"
   depfound = -1
   for y in range(len(plugindeps.plugindependencies)):
    if str(plugindeps.plugindependencies[y]["pluginid"]) == str(rpieGlobals.deviceselector[x][1]):
     depfound = y
     break
   TXBuffer += "<td>"
   usable = True
   if depfound>-1:
    try:
     if oslvl in plugindeps.plugindependencies[depfound]["supported_os_level"]:
      TXBuffer += "Supported"
     else:
      supstr = "NOT Supported"
      usable = False
      if "ext" in plugindeps.plugindependencies[depfound]:
       if rpieGlobals.extender >= plugindeps.plugindependencies[depfound]["ext"]:
        supstr = "Supported with extender"
        usable = True
      TXBuffer += supstr
    except:
      TXBuffer += "Supported"
    TXBuffer += "</td><td>"
    try:
     if (plugindeps.plugindependencies[depfound]["modules"]):
      for z in range(len(plugindeps.plugindependencies[depfound]["modules"])):
       puse = plugindeps.ismoduleusable(plugindeps.plugindependencies[depfound]["modules"][z])
       addEnabled(puse)
       if puse==False:
        usable = False
        TXBuffer += "<a href='plugins?installmodule="+plugindeps.plugindependencies[depfound]["modules"][z]+"'>"
       TXBuffer += plugindeps.plugindependencies[depfound]["modules"][z]+" "
       if puse==False:
        usable = False
        TXBuffer += "</a>"
    except:
     TXBuffer += "No dependencies"
   else:
    TXBuffer += "Supported</td><td>No dependencies"
   TXBuffer += "</td><td>"
   addEnabled(usable)
   TXBuffer += "</td></tr>"

 TXBuffer += "</table>"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/devices')
#@WebServer.get('/devices')
def handle_devices(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=4
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 taskdevicenumber = arg('TDNUM',responsearr)
 if taskdevicenumber=='':
  taskdevicenumber=0
 else:
  taskdevicenumber=int(float(taskdevicenumber))

 taskdevicetimer = arg('TDT',responsearr)
 if taskdevicetimer=='':
  taskdevicetimer=0
 else:
  taskdevicetimer=float(taskdevicetimer)

 edit = arg("edit",responsearr)
 page = arg("page",responsearr)
 setpage = arg("setpage",responsearr)
 taskIndex = arg("index",responsearr)
 runIndex = arg("run",responsearr)
 toggleIndex = arg("toggle",responsearr)

 if page=='':
  page=0
 else:
  page=int(float(page))
 if page==0:
  page = 1
 if setpage=='':
  setpage=0
 else:
  setpage=int(float(setpage))
 if (setpage>0):
  if setpage <= (rpieGlobals.TASKS_MAX / TASKS_PER_PAGE):
   page = setpage
  else:
   page = int(rpieGlobals.TASKS_MAX / TASKS_PER_PAGE)

 taskIndexNotSet = (taskIndex == 0) or (taskIndex == '')
 if taskIndex!="":
  taskIndex = int(taskIndex) - 1
 if arg('del',responsearr) != '':
  taskdevicenumber=0
  ttid = -1
  try:
    ttid = Settings.Tasks[taskIndex].pluginid
  except:
    ttid = -1
  if ttid != -1:
   try:
    Settings.Tasks[taskIndex].plugin_exit()
    taskIndexNotSet = True
    Settings.Tasks[taskIndex] = False
    Settings.savetasks() # savetasksettings!!!
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Deleting failed: "+str(e))

 if runIndex != "":
#  print(runIndex)
  if len(Settings.Tasks)<1:
   return False
  try:
   s = int(runIndex)
  except:
   s = -1
  try:
   if s >0 and (s<=len(Settings.Tasks)):
    s = s-1 # array is 0 based, tasks is 1 based
    if (type(Settings.Tasks[s])!=bool) and (Settings.Tasks[s]):
     if (Settings.Tasks[s].enabled):
      Settings.Tasks[s].plugin_read()
  except Exception as e:
    print(e)

 if toggleIndex != "":
  if len(Settings.Tasks)<1:
   return False
  try:
   s = int(toggleIndex)
  except:
   s = -1
  try:
   if s >0 and (s<=len(Settings.Tasks)):
    s = s-1 # array is 0 based, tasks is 1 based
    if (type(Settings.Tasks[s])!=bool) and (Settings.Tasks[s]):
     if (Settings.Tasks[s].enabled):
      Settings.Tasks[s].set_value(1,(1-int(float(Settings.Tasks[s].uservar[0]))),publish=True)
  except Exception as e:
    print(e)

 if taskIndexNotSet: # show all tasks as table
    if True:
     TXBuffer += "<script defer> (function(){ var max_tasknumber = "+ str(rpieGlobals.TASKS_MAX) +"; var max_taskvalues = "+ str(rpieGlobals.VARS_PER_TASK) +"; var timeForNext = 2000; var c; var k; var err = '';"
     TXBuffer += " var j = setInterval(function(){if (document.getElementById('clock') !== null) { var d = new Date();var s = d.getSeconds(); var m = d.getMinutes(); var h = d.getHours(); document.getElementById('clock').innerHTML = ('0'+h).slice(-2) + ':' + ('0'+m).slice(-2) + ':' + ('0'+s).slice(-2) ;}},timeForNext);"
     TXBuffer += " var i = setInterval(function(){ var url = '/json?view=sensorupdate';"
     TXBuffer += "	fetch(url).then( function(response) {  if (response.status !== 200) { console.log('Looks like there was a problem. Status Code: ' +  response.status); return; } response.json().then(function(data) {"
     TXBuffer += "	timeForNext = data.TTL; for (c = 0; c < max_tasknumber; c++) { for (k = 0; k < max_taskvalues; k++) { try {	valueEntry = data.Sensors[c].TaskValues[k].Value; }	catch(err) { valueEntry = err.name;	}"
     TXBuffer += "	finally {if ((valueEntry !== 'TypeError') && (document.getElementById('value_' + (data.Sensors[c].TaskNumber - 1) + '_' + (data.Sensors[c].TaskValues[k].ValueNumber -1)) !== null)) {"
     TXBuffer += "	document.getElementById('value_' + (data.Sensors[c].TaskNumber - 1) + '_' + (data.Sensors[c].TaskValues[k].ValueNumber -1)).innerHTML = data.Sensors[c].TaskValues[k].Value;"
     TXBuffer += "	document.getElementById('valuename_' + (data.Sensors[c].TaskNumber - 1) + '_' + (data.Sensors[c].TaskValues[k].ValueNumber -1) ).innerHTML = data.Sensors[c].TaskValues[k].Name + ':';"
     TXBuffer += "	}}}}});} ) .catch(function(err) {console.log(err.message); });}, timeForNext);})();"
     TXBuffer += "window.onblur = function() { window.blurred = true; }; window.onfocus = function() { window.blurred = false; }; </script>"

    TXBuffer += "<table class='multirow' border=1px frame='box' rules='all'><TR><TH style='width:70px;'>"
    if (rpieGlobals.TASKS_MAX != TASKS_PER_PAGE):
      TXBuffer += "<a class='button link' href='devices?setpage="
      if (page > 1):
        TXBuffer += str(page - 1)
      else:
        TXBuffer += str(page)
      TXBuffer += "'>&lt;</a>"
      TXBuffer += "<a class='button link' href='devices?setpage="
      if (page < (rpieGlobals.TASKS_MAX / TASKS_PER_PAGE)):
        TXBuffer += str(page + 1)
      else:
        TXBuffer += str(page)
      TXBuffer += "'>&gt;</a>"
      TXBuffer += "<TH style='width:50px;'>Task<TH style='width:100px;'>Enabled<TH>Device<TH>Name<TH>Port<TH style='width:100px;'>Ctr (IDX)<TH style='width:70px;'>GPIO<TH>Values"

      for x in range( ((page - 1) * TASKS_PER_PAGE), ((page) * TASKS_PER_PAGE) ):
       TXBuffer += "<TR><TD>"
       TXBuffer += "<a class='button link' href='devices?index="
       TXBuffer += str(x + 1)
       TXBuffer += "&page="
       TXBuffer += str(page)
       TXBuffer += "'>Edit</a>"
       try:
        if Settings.Tasks[x].enabled and Settings.Tasks[x].remotefeed<1:
         TXBuffer += "<a class='button link' href='devices?run="
         TXBuffer += str(x + 1)
         TXBuffer += "&page="
         TXBuffer += str(page)
         TXBuffer += "'>Run</a>"
         if Settings.Tasks[x].recdataoption and Settings.Tasks[x].vtype==rpieGlobals.SENSOR_TYPE_SWITCH:
          TXBuffer += "<a class='button link' href='devices?toggle="
          TXBuffer += str(x + 1)
          TXBuffer += "&page="
          TXBuffer += str(page)
          TXBuffer += "'>Toggle</a>"
       except:
        pass
       TXBuffer += "<TD>"
       TXBuffer += str(x + 1)
       TXBuffer += "<TD>"

       if (len(Settings.Tasks)>x) and (Settings.Tasks[x]):
        try:
         addEnabled(Settings.Tasks[x].enabled)
        except:
         break

        TXBuffer += "<TD>"
        TXBuffer += Settings.Tasks[x].getdevicename()
        TXBuffer += "<TD>"
        TXBuffer += Settings.Tasks[x].gettaskname()
        TXBuffer += "<TD>"

        try:
          if (str(Settings.Tasks[x].ports) != "0" and str(Settings.Tasks[x].ports) != ""):
            TXBuffer += str(Settings.Tasks[x].ports)
        except:
         pass
        if Settings.Tasks[x].remotefeed:
         TXBuffer += "<TD style='background-color:#00FF00'>"
        else:
         TXBuffer += "<TD>"

        try:
         if (Settings.Tasks[x].senddataoption):
          doBR = False
          maxcon = len(Settings.Controllers)
          if maxcon>rpieGlobals.CONTROLLER_MAX:
           maxcon = rpieGlobals.CONTROLLER_MAX
          try:
           for controllerNr in range(0,maxcon):
            if (Settings.Tasks[x]) and (Settings.Tasks[x].senddataenabled[controllerNr]) and (Settings.Controllers[controllerNr].enabled):
              if (doBR):
                TXBuffer += "<BR>"
              TXBuffer += getControllerSymbol(controllerNr)
              if (Settings.Controllers[controllerNr].usesID):
                TXBuffer += " ("
                TXBuffer += str(Settings.Tasks[x].controlleridx[controllerNr])
                TXBuffer += ")"
                if (int(Settings.Tasks[x].controlleridx[controllerNr]) <= 0):
                  TXBuffer += " " + HTML_SYMBOL_WARNING
              doBR = True
          except Exception as e:
            pass
         TXBuffer += "<TD>"
        except Exception as e:
         print(e)

        if (Settings.Tasks[x].dtype == rpieGlobals.DEVICE_TYPE_I2C):
            try:
             c = Settings.Tasks[x].i2c
            except:
             c = -1
             Settings.Tasks[x].i2c = -1
            try:
             i2cpins = Settings.get_i2c_pins(c)
             TXBuffer += i2cpins[0]
             TXBuffer += "<BR>"+str(i2cpins[1])
            except:
             TXBuffer += "NO-I2C"
        elif (Settings.Tasks[x].dtype == rpieGlobals.DEVICE_TYPE_SPI):
            try:
             c = Settings.Tasks[x].spi
            except:
             c = -1
             Settings.Tasks[x].spi = -1
            try:
             TXBuffer += "SPI"+str(c)
            except:
             TXBuffer += "NO-SPI"
        try:
         for tp in range(0,len(Settings.Tasks[x].taskdevicepin)):
          if int(Settings.Tasks[x].taskdevicepin[tp])>=0:
            TXBuffer += "<br>GPIO-"
            TXBuffer += str(Settings.Tasks[x].taskdevicepin[tp])
        except:
         pass
        TXBuffer += "<TD>"
        customValues = False

        if not(customValues):
          if (Settings.Tasks[x].vtype == rpieGlobals.SENSOR_TYPE_LONG):
           try:
            TXBuffer  += "<div class='div_l' "
            TXBuffer  += "id='valuename_"
            TXBuffer  += str(x)
            TXBuffer  += "_"
            TXBuffer  += '0'
            TXBuffer  += "'>"
            TXBuffer  += Settings.Tasks[x].getdevicevaluenames()[0]
            TXBuffer  += ":</div><div class='div_r' "
            TXBuffer  += "id='value_"
            TXBuffer  += str(x)
            TXBuffer  += "_"
            TXBuffer  += '0'
            TXBuffer  += "'>"
            numtodisp = str(float(Settings.Tasks[x].uservar[0]) + float(Settings.Tasks[x].uservar[1] << 16))
            TXBuffer += str(misc.formatnum(numtodisp,0))
            TXBuffer  += "</div>"
           except Exception as e:
            print(e)
          else:
            try:
             for varNr in range(0,rpieGlobals.VARS_PER_TASK):
              if ((Settings.Tasks[x].enabled) and (varNr < Settings.Tasks[x].valuecount)):
                if (varNr > 0):
                  TXBuffer += "<div class='div_br'></div>"
                TXBuffer += "<div class='div_l' "
                TXBuffer  += "id='valuename_"
                TXBuffer  += str(x)
                TXBuffer  += "_"
                TXBuffer  += str(varNr)
                TXBuffer  += "'>"
                TXBuffer += Settings.Tasks[x].getdevicevaluenames()[varNr]
                TXBuffer += ":</div><div class='div_r' "
                TXBuffer  += "id='value_"
                TXBuffer  += str(x)
                TXBuffer  += "_"
                TXBuffer  += str(varNr)
                TXBuffer  += "'>"
                numtodisp = Settings.Tasks[x].uservar[varNr]
                decimalv = Settings.Tasks[x].decimals[varNr]
                TXBuffer += str(misc.formatnum(numtodisp,decimalv))
#                if str(decimalv) == "-1":
#                 TXBuffer += str(numtodisp)
#                else:
#                 if str(decimalv) == "" or int(decimalv)<0:
#                  decimalv = "0"
#                 else:
#                  decimalv = str(decimalv).strip()
#                 numformat = "{0:."+ decimalv + "f}"
#                 try:
#                  TXBuffer += numformat.format(numtodisp)
#                 except:
#                  TXBuffer += numtodisp 
                TXBuffer += "</div>"
            except Exception as e:
             print(e)
          try:
           if int(Settings.AdvSettings["webloglevel"])>=rpieGlobals.LOG_LEVEL_DEBUG_MORE:
            if Settings.Tasks[x].enabled:
              if Settings.Tasks[x]._lastdataservetime != 0:
               lds = rpieTime.start_time + timedelta(seconds=(Settings.Tasks[x]._lastdataservetime / 1000))
               TXBuffer += "<div><p align=left><br><i>"+ lds.strftime('%Y-%m-%d %H:%M:%S')+"</i></div>"
          except Exception as e:
           print(e)
       else:
        TXBuffer += "<TD><TD><TD><TD><TD><TD>"
      TXBuffer += "<tr><TD colspan=2><div class='button' id='clock'>00:00:00</div><TD><TD><TD><TD><TD><TD><TD></tr>"
      TXBuffer += "</table></form>"
 
 else: #Show edit form if a specific entry is chosen with the edit button
    TXBuffer += "<form name='frmselect' method='post'><table class='normal'>"
    addFormHeader("Task Settings")
    TXBuffer += "<TR><TD style='width:150px;' align='left'>Device:<TD>"
    tte = taskdevicenumber
    try:
      tte = Settings.Tasks[taskIndex].pluginid
    except:
      pass
    if (tte<=0):
      addSelector_Head("TDNUM",True)
      for y in range(0,len(rpieGlobals.deviceselector)):
       pname = rpieGlobals.deviceselector[y][2]
       try:
        if int(rpieGlobals.deviceselector[y][1]) != 0:
         pname = "P"+str(int(rpieGlobals.deviceselector[y][1])).rjust(3,"0")+" - "+ rpieGlobals.deviceselector[y][2]
       except:
        pass
       addSelector_Item(pname,int(rpieGlobals.deviceselector[y][1]),(rpieGlobals.deviceselector[y][1]==tte),False,"")
      addSelector_Foot()
    else: # device selected
      createnewdevice = True
      try:
       if (Settings.Tasks[taskIndex].getpluginid()==int(tte)):
        createnewdevice = False
      except:
       pass
      exceptstr = ""
      if createnewdevice:
       for y in range(len(rpieGlobals.deviceselector)):
        if int(rpieGlobals.deviceselector[y][1]) == int(tte):
         if len(Settings.Tasks)<=taskIndex:
          while len(Settings.Tasks)<=taskIndex:
           Settings.Tasks.append(False)
         try:
           m = __import__(rpieGlobals.deviceselector[y][0])
         except Exception as e:
          Settings.Tasks[taskIndex] = False
          exceptstr += str(e)
          m = False
         if m:
          try: 
           Settings.Tasks[taskIndex] = m.Plugin(taskIndex)
          except Exception as e:
           Settings.Tasks.append(m.Plugin(taskIndex))
           exceptstr += str(e)
         break
      if Settings.Tasks[taskIndex] == False:
       errormsg = "Importing failed, please double <a href='plugins'>check dependencies</a>! "+exceptstr
       TXBuffer += errormsg+"</td></tr></table>"
       sendHeadandTail("TmplStd",_TAIL)
       return TXBuffer
      else:
       try:
        enableit = (arg("TDE",responsearr) == "on")
#        print("plugin init",enableit)
        if enableit:
         Settings.Tasks[taskIndex].plugin_init(True) # call plugin init / (arg("TDE",responsearr) == "on")
        else:
         Settings.Tasks[taskIndex].plugin_init() # call plugin init / (arg("TDE",responsearr) == "on")
       except:
        pass

      if edit != '' and not(taskIndexNotSet): # when form submitted
       if taskdevicenumber != 0: # save settings
        if taskdevicetimer > 0:
         Settings.Tasks[taskIndex].interval = taskdevicetimer
        else:
         if not(Settings.Tasks[taskIndex].timeroptional): # set default delay
          Settings.Tasks[taskIndex].interval = Settings.Settings["Delay"]
         else:
          Settings.Tasks[taskIndex].interval = 0
       tasknamestr = str(arg("TDN",responsearr)).strip()
       Settings.Tasks[taskIndex].taskname = tasknamestr.replace(" ","") #remove space from taskname

       try:
        import random
        tname = Settings.Tasks[taskIndex].taskname
        namecheck = True
        while namecheck:
         idvars = misc.get_taskname_taskids(tname)
         if (len(idvars)==1 and (taskIndex not in idvars)) or (len(idvars)>1): #duplicated tasknames denied
          tname = Settings.Tasks[taskIndex].taskname + str(int(random.random() * 100))
         else:
          namecheck = False
        Settings.Tasks[taskIndex].taskname = tname
       except Exception as e:
        print(e)

       if tasknamestr:
        Settings.Tasks[taskIndex].taskdeviceport = arg("TDP",responsearr)
        maxcon = len(Settings.Controllers)
        if maxcon>rpieGlobals.CONTROLLER_MAX:
         maxcon = rpieGlobals.CONTROLLER_MAX
        for controllerNr in range(0, maxcon):
          if ((Settings.Controllers[controllerNr]) and (Settings.Controllers[controllerNr].enabled)):
            sid = "TDSD"
            sid += str(controllerNr + 1)
            Settings.Tasks[taskIndex].senddataenabled[controllerNr] = (arg(sid,responsearr) == "on")
            if (Settings.Tasks[taskIndex].senddataenabled[controllerNr]):
              if (Settings.Controllers[controllerNr]):
               if (Settings.Controllers[controllerNr].enabled):
                Settings.Tasks[taskIndex].controllercb[controllerNr] = Settings.Controllers[controllerNr].senddata
            if (Settings.Tasks[taskIndex].senddataenabled[controllerNr]):
             sid = "TDID"
             sid += str(controllerNr + 1)
             ctrlidx = str(arg(sid,responsearr)).strip()
             if ctrlidx=="":
              ctrlidx = -1
             else:
              ctrlidx = int(ctrlidx)
             Settings.Tasks[taskIndex].controlleridx[controllerNr] = ctrlidx
        for pins in range(0,4):
         pinnum = arg("taskdevicepin"+str(pins+1),responsearr)
         if pinnum:
          Settings.Tasks[taskIndex].taskdevicepin[pins]=int(pinnum)
#        if Settings.Tasks[taskIndex].pullupoption:
#         Settings.Tasks[taskIndex].pullup = (arg("TDPPU",responsearr) == "on")
        if Settings.Tasks[taskIndex].inverselogicoption:
         Settings.Tasks[taskIndex].pininversed = (arg("TDPI",responsearr) == "on")
        for varnr in range(0,Settings.Tasks[taskIndex].valuecount):
         tvname = arg("TDVN"+str(varnr+1),responsearr)
         if tvname:
          Settings.Tasks[taskIndex].valuenames[varnr] = tvname.replace(" ","")
          Settings.Tasks[taskIndex].formula[varnr] = arg("TDF"+str(varnr+1),responsearr)
          tvdec = arg("TDVD"+str(varnr+1),responsearr)
          if tvdec == "" or tvdec == False or tvdec == None:
           tvdec = 0
          Settings.Tasks[taskIndex].decimals[varnr] = tvdec
         else:
          Settings.Tasks[taskIndex].valuenames[varnr] = ""
        Settings.Tasks[taskIndex].webform_save(responsearr) # call plugin read FORM
        Settings.Tasks[taskIndex].enabled = (arg("TDE",responsearr) == "on")
        if (Settings.Tasks[taskIndex].dtype==rpieGlobals.DEVICE_TYPE_I2C):
         try:
          if Settings.Tasks[taskIndex].i2c>-1:
           pass
         except:
          Settings.Tasks[taskIndex].i2c = -1 # set to default in case of error
         try:
          Settings.Tasks[taskIndex].i2c = int(arg("i2c",responsearr))
         except:
          pass
        elif (Settings.Tasks[taskIndex].dtype==rpieGlobals.DEVICE_TYPE_SPI):
         try:
          if Settings.Tasks[taskIndex].spi>-1:
           pass
         except:
          Settings.Tasks[taskIndex].spi = -1 # set to default in case of error
         try:
          Settings.Tasks[taskIndex].spi = int(arg("spi",responsearr))
         except:
          pass
         try:
          if Settings.Tasks[taskIndex].spidnum>-1:
           pass
         except:
          Settings.Tasks[taskIndex].spidnum = -1 # set to default in case of error
         try:
          Settings.Tasks[taskIndex].spidnum = int(arg("spidnum",responsearr))
         except:
          pass

        if Settings.Tasks[taskIndex].taskname=="":
         Settings.Tasks[taskIndex].enabled = False
        Settings.savetasks() # savetasksettings!!!

      TXBuffer += "<input type='hidden' name='TDNUM' value='"
      TXBuffer += str(Settings.Tasks[taskIndex].pluginid)
      TXBuffer += "'>"
      TXBuffer += str(Settings.Tasks[taskIndex].getdevicename()) #show selected device name and delete button

      addFormTextBox( "Name", "TDN", str(Settings.Tasks[taskIndex].gettaskname()), 40)
      addFormCheckBox("Enabled", "TDE", Settings.Tasks[taskIndex].enabled)
      # section: Sensor / Actuator
      if (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_SINGLE and Settings.Tasks[taskIndex].dtype<= rpieGlobals.DEVICE_TYPE_QUAD):
        addFormSubHeader( "Sensor" if Settings.Tasks[taskIndex].senddataoption else "Actuator" )

#        if (Settings.Tasks[taskIndex].ports != 0):
#          addFormNumericBox("Port", "TDP", Settings.Tasks[taskIndex].taskdeviceport)
#        if (Settings.Tasks[taskIndex].pullupoption):
#          addFormCheckBox("Internal PullUp", "TDPPU", Settings.Tasks[taskIndex].pullup)
        if (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_SINGLE and Settings.Tasks[taskIndex].dtype<=rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("1st GPIO", "taskdevicepin1", Settings.Tasks[taskIndex].taskdevicepin[0])
        if (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_DUAL and Settings.Tasks[taskIndex].dtype<=rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("2nd GPIO", "taskdevicepin2", Settings.Tasks[taskIndex].taskdevicepin[1])
        if (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_TRIPLE and Settings.Tasks[taskIndex].dtype<=rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("3rd GPIO", "taskdevicepin3", Settings.Tasks[taskIndex].taskdevicepin[2])
        if (Settings.Tasks[taskIndex].dtype==rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("4th GPIO", "taskdevicepin4", Settings.Tasks[taskIndex].taskdevicepin[3])
      if (Settings.Tasks[taskIndex].inverselogicoption):
          addFormCheckBox("Inversed Logic", "TDPI", Settings.Tasks[taskIndex].pininversed)
      if (Settings.Tasks[taskIndex].dtype==rpieGlobals.DEVICE_TYPE_I2C):
          try:
           import gpios
           options = gpios.HWPorts.geti2clist()
          except Exception as e:
           options = []
          addHtml("<tr><td>I2C line:<td>")
          addSelector_Head("i2c",False)
          for d in range(len(options)):
           try:
            addSelector_Item("I2C"+str(options[d]),options[d],(Settings.Tasks[taskIndex].i2c==options[d]),False)
           except:
            pass
          addSelector_Foot()
      elif (Settings.Tasks[taskIndex].dtype==rpieGlobals.DEVICE_TYPE_SPI):
          try:
           import gpios
           options1, options2 = gpios.HWPorts.getspilist()
          except Exception as e:
           options1 = []
           options2 = []
          addHtml("<tr><td>SPI line:<td>")
          addSelector_Head("spi",False)
          for d in range(len(options1)):
           try:
            addSelector_Item("SPI"+str(options1[d]),options1[d],(Settings.Tasks[taskIndex].spi==options1[d]),False)
           except:
            pass
          addSelector_Foot()
          addHtml("<tr><td>SPI device num:<td>")
          addSelector_Head("spidnum",False)
          for d in range(len(options2)):
           try:
            addSelector_Item("CE"+str(options2[d]),options2[d],(Settings.Tasks[taskIndex].spidnum==options2[d]),False)
           except:
            pass
          addSelector_Foot()

      try:
       Settings.Tasks[taskIndex].webform_load() # call plugin function to fill TXBuffer
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Task"+str(taskIndex+1)+ " "+str(e))

      if (Settings.Tasks[taskIndex].senddataoption): # section: Data Acquisition
        addFormSubHeader("Data Acquisition")
        maxcon = len(Settings.Controllers)
        if maxcon>rpieGlobals.CONTROLLER_MAX:
         maxcon = rpieGlobals.CONTROLLER_MAX
        for controllerNr in range(0, maxcon):
          if ((Settings.Controllers[controllerNr]) and (Settings.Controllers[controllerNr].enabled)):
            sid = "TDSD"
            sid += str(controllerNr + 1)

            TXBuffer += "<TR><TD>Send to Controller "
            TXBuffer += getControllerSymbol(controllerNr)
            TXBuffer += "<TD>"
            addCheckBox(sid, Settings.Tasks[taskIndex].senddataenabled[controllerNr])

            sid = "TDID"
            sid += str(controllerNr + 1)

            if (Settings.Controllers[controllerNr].enabled) and Settings.Tasks[taskIndex].senddataenabled[controllerNr]:
             if (Settings.Controllers[controllerNr].usesID):
              TXBuffer += "<TR><TD>IDX:<TD>"
              addNumericBox(sid, Settings.Tasks[taskIndex].controlleridx[controllerNr], 0, 9999)
             else:
              TXBuffer += "<input type='hidden' name='"+sid+ "' value='0'>" # no id, set to 0
            else:
             TXBuffer += "<input type='hidden' name='"+sid+ "' value='-1'>" # disabled set to -1
      addFormSeparator(2)

      if (Settings.Tasks[taskIndex].timeroption):
        addFormNumericBox( "Interval", "TDT", Settings.Tasks[taskIndex].interval, 0, INT_MAX)
        addUnit("sec")
        if (Settings.Tasks[taskIndex].timeroptional):
          TXBuffer += " (Optional for this Device)"

      if (Settings.Tasks[taskIndex].valuecount>0): # //section: Values
        addFormSubHeader("Values")
        TXBuffer += "</table><table class='normal'>"
        TXBuffer += "<TR><TH style='width:30px;' align='center'>#"
        TXBuffer += "<TH align='left'>Name"
        if (Settings.Tasks[taskIndex].formulaoption):
          TXBuffer += "<TH align='left'>Formula"

        if (Settings.Tasks[taskIndex].formulaoption or Settings.Tasks[taskIndex].decimalsonly):
          TXBuffer += "<TH style='width:30px;' align='left'>Decimals"

        for varNr in range(0, Settings.Tasks[taskIndex].valuecount):
          TXBuffer += "<TR><TD>"
          TXBuffer += str(varNr + 1)
          TXBuffer += "<TD>"
          sid = "TDVN"
          sid += str(varNr + 1)
          addTextBox(sid, Settings.Tasks[taskIndex].getdevicevaluenames()[varNr], 40)

          if (Settings.Tasks[taskIndex].formulaoption):
            TXBuffer += "<TD>"
            sid = "TDF"
            sid += str(varNr + 1)
            addTextBox(sid, Settings.Tasks[taskIndex].formula[varNr], 140)

          if (Settings.Tasks[taskIndex].formulaoption or Settings.Tasks[taskIndex].decimalsonly):
            TXBuffer += "<TD>"
            sid = "TDVD"
            sid += str(varNr + 1)
            addNumericBox(sid, Settings.Tasks[taskIndex].decimals[varNr], 0, 6)

    addFormSeparator(4)
    
    TXBuffer += "<TR><TD><TD colspan='3'><a class='button link' href='devices?setpage="
    TXBuffer += str(page)
    TXBuffer += "'>Close</a>"
    addSubmitButton()
    TXBuffer += "<input type='hidden' name='edit' value='1'>"
    if taskIndex != '':
     TXBuffer += "<input type='hidden' name='index' value='" + str(taskIndex+1) +"'>"
    TXBuffer += "<input type='hidden' name='page' value='"+ str(page) +"'>"

    if (tte>0): # if user selected a device, add the delete button
      addSubmitButton("Delete", "del")

    TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/notifications')
def handle_notifications(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=6
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 edit = arg("edit",responsearr)

 nindex = arg("index",responsearr)
 nNotSet = (nindex == 0) or (nindex == '')
 if nindex!="":
  nindex = int(nindex) - 1
 enabled = (arg("nenabled",responsearr)=="on")
 protocol = arg("protocol",responsearr)
 if protocol!="":
  protocol=int(protocol)
 else:
  protocol=0

 if ((protocol == 0) and (edit=='') and (nindex!='')) or (arg('del',responsearr) != ''):
   try:
    Settings.Notifiers[nindex].plugin_exit()
   except:
    pass
   Settings.Notifiers[nindex] = False
   nNotSet = True
   Settings.savenotifiers()

 if (nNotSet==False): # submitted
  if (protocol > 0): # submitted
   try:
    if (Settings.Notifiers[nindex]):
     Settings.Notifiers[nindex].enabled = enabled
     Settings.Notifiers[nindex].webform_save(responsearr)
     Settings.savenotifiers()
   except:
    pass
  else:
   try:
    if (Settings.Notifiers[nindex]):
     protocol = Settings.Notifiers[nindex].number
   except:
    pass
 TXBuffer += "<form name='frmselect' method='post'>"
 if (nNotSet): # show all in table
    TXBuffer += "<table class='multirow' border=1px frame='box' rules='all'><TR><TH style='width:70px;'>"
    TXBuffer += "<TH style='width:50px;'>Nr<TH style='width:100px;'>Enabled<TH>Service<TH>ID"
    for x in range(rpieGlobals.NOTIFICATION_MAX):
      TXBuffer += "<tr><td><a class='button link' href=\"notifications?index="
      TXBuffer += str(x + 1)
      TXBuffer += "&edit=1\">Edit</a><td>"
      TXBuffer += str(x + 1)
      TXBuffer += "</td><td>"
      try:
       if (Settings.Notifiers[x]):
        addEnabled(Settings.Notifiers[x].enabled)
        TXBuffer += "</td><td>"
        TXBuffer += str(Settings.Notifiers[x].getdevicename())
        TXBuffer += "</td><td>"
        TXBuffer += str(Settings.Notifiers[x].getuniquename())
       else:
        TXBuffer += "<td><td>"
      except:
       TXBuffer += "<td><td>"
    TXBuffer += "</table></form>"
 else: # edit
    TXBuffer += "<table class='normal'><TR><TH style='width:150px;' align='left'>Notification Settings<TH>"
    TXBuffer += "<tr><td>Notification:<td>"
    addSelector_Head("protocol", True)
    for x in range(len(rpieGlobals.notifierselector)):
      addSelector_Item(rpieGlobals.notifierselector[x][2],int(rpieGlobals.notifierselector[x][1]),(str(protocol) == str(rpieGlobals.notifierselector[x][1])),False,"")
    addSelector_Foot()
    if (int(protocol) > 0):
      createnewn = True
      try:
       if (Settings.Notifiers[nindex].getnpluginid()==int(protocol)):
        createnewn = False
      except:
       pass
      exceptstr = ""
      if createnewn:
       for y in range(len(rpieGlobals.notifierselector)):
        if int(rpieGlobals.notifierselector[y][1]) == int(protocol):
         if len(Settings.Notifiers)<=nindex:
          while len(Settings.Notifiers)<=nindex:
           Settings.Notifiers.append(False)
         try:
           m = __import__(rpieGlobals.notifierselector[y][0])
         except Exception as e:
          Settings.Notifiers[nindex] = False
          exceptstr += str(e)
          m = False
         if m:
          try: 
           Settings.Notifiers[nindex] = m.Plugin(nindex)
          except Exception as e:
           Settings.Notifiers.append(m.Plugin(nindex))
           exceptstr += str(e)
         break
      if Settings.Notifiers[nindex] == False:
       errormsg = "Importing failed, please double <a href='plugins'>check dependencies</a>! "+str(exceptstr)
       TXBuffer += errormsg+"</td></tr></table>"
       sendHeadandTail("TmplStd",_TAIL)
       return TXBuffer
      else:
       try:
        Settings.Notifiers[nindex].plugin_init() # call plugin init
       except:
        pass 
    if nindex != '':
     TXBuffer += "<input type='hidden' name='index' value='" + str(nindex+1) +"'>"
     if int(protocol)>0:
      addFormCheckBox("Enabled", "nenabled", Settings.Notifiers[nindex].enabled)
      try:
       Settings.Notifiers[nindex].webform_load()
      except Exception as e:
       print(e)
      if (arg('test',responsearr) != ''):
       Settings.Notifiers[nindex].notify("Test message")
    addFormSeparator(2)
    TXBuffer += "<tr><td><td>"
    TXBuffer += "<a class='button link' href=\"notifications\">Close</a>"
    addSubmitButton()
    if nindex != '':
     addSubmitButton("Delete", "del")
     addSubmitButton("Test", "test")
    TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/log')
def handle_log(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 TXBuffer += "<table class=\"normal\"><TR><TH id=\"headline\" align=\"left\">Log"
 addCopyButton("copyText", "", "Copy log to clipboard")
 TXBuffer += "</TR></table><div id='current_loglevel' style='font-weight: bold;'>Logging: </div><div class='logviewer' id='copyText_1'>"
 for l in misc.SystemLog:
  TXBuffer += '<div class="level_'
  TXBuffer += str(l["lvl"])
  TXBuffer += '"><font color="gray">'+str(l["t"])+"</font> "+ str(l["l"]) +"</div>"

 TXBuffer += "</div>"
 TXBuffer += "<BR>"
 TXBuffer += '<script type="text/javascript">var rtimer; function refreshpage() {window.location.reload(true);}'
 TXBuffer += "function checkit(){ if (document.getElementById('autoscroll').checked) {rtimer = setInterval(refreshpage,5000);} else {clearInterval(rtimer);}}</script>"
 TXBuffer += "Autoscroll: <label class='container'>&nbsp;<input type='checkbox' id='autoscroll' name='autoscroll' checked onclick='checkit();'><span class='checkmark'></span></label>"
 TXBuffer += "<script defer>checkit();copyText_1.scrollTop = 99999;</script>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/tools')
def handle_tools(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 try:
  if self.type == "GET":
   responsearr = self.get
  else:
   responsearr = self.post

  webrequest = arg("cmd",responsearr)
 except:
  webrequest = ""

 TXBuffer += "<form><table class='normal'>"
 addFormHeader("Tools")

 addFormSubHeader("Command")
 TXBuffer += "<TR><TD style='width: 280px'>"
 TXBuffer += "<input class='wide' type='text' name='cmd' value='"
 TXBuffer += str(webrequest)
 TXBuffer += "'>"
 TXBuffer += "<TD>"
 addSubmitButton()

 responsestr = ""
 if len(webrequest)>0:
  responsestr = str(commands.doExecuteCommand(webrequest))

 if len(responsestr)>0:
  try:
   TXBuffer += "<TR><TD colspan='2'>Command Output<BR><textarea readonly rows='10' wrap='on'>"
   TXBuffer += str(responsestr)
   lc = len(misc.SystemLog)
   if lc>5:
    ls = lc-5
   else:
    ls = 0
   for l in range(ls,lc):
    TXBuffer += '\r\n'+str(misc.SystemLog[l]["t"])+" : "+ str(misc.SystemLog[l]["l"])
   TXBuffer += "</textarea>"
  except Exception as e:
   print(str(e))

 addFormSubHeader("System")

 html_TR_TD_height(30)
 TXBuffer += "<a class='button link wide' onclick="
 TXBuffer += '"'
 TXBuffer += "return confirm('Do you really want to Reboot device?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=reboot'>Reboot</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Reboot System"

 html_TR_TD_height(30)
 TXBuffer += "<a class='button link wide' onclick="
 TXBuffer += '"'
 TXBuffer += "return confirm('Do you really want to Shutdown machine?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=halt'>Halt</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Halt/Shutdown System"

 html_TR_TD_height(30)
 TXBuffer += "<a class='button link wide' onclick="
 TXBuffer += '"'
 TXBuffer += "return confirm('Do you really want to exit RPIEasy application?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=exit'>Exit</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Exit from RPIEasy (or Restart if autostart script used)"

 html_TR_TD_height(30)
 addWideButton("log", "Log", "")
 TXBuffer += "<TD>"
 TXBuffer += "Open log output"

 html_TR_TD_height(30)
 addWideButton("sysinfo", "Info", "")
 TXBuffer += "<TD>"
 TXBuffer += "Open system info page"

 html_TR_TD_height(30)
 addWideButton("advanced", "Advanced", "")
 TXBuffer += "<TD>"
 TXBuffer += "Open advanced settings"

 html_TR_TD_height(30)
 addWideButton("json", "Show JSON", "")
 TXBuffer += "<TD>"
 TXBuffer += "Open JSON output"

 html_TR_TD_height(30)
 addWideButton("sysvars", "System Variables", "")
 TXBuffer += "<TD>"
 TXBuffer += "Show all system variables"

 html_TR_TD_height(30)
 addWideButton("update", "System Updates", "")
 TXBuffer += "<TD>"
 TXBuffer += "RPIEasy/OS/PIP updates"

 addFormSubHeader("Settings")
 html_TR_TD_height(30)
 addWideButton("upload?type=settings", "Load", "")
 TXBuffer += "<TD>"
 TXBuffer += "Uploads a JSON settings file"
# addFormNote("(File MUST be renamed to \"config.dat\" before upload!)")

 html_TR_TD_height(30)
 addWideButton("download?type=settings", "Save", "")
 TXBuffer += "<TD>"
 TXBuffer += "Downloads all JSON settings files"

 addFormSubHeader("Filesystem")
 html_TR_TD_height(30)
 addWideButton("filelist", "Files", "")
 TXBuffer += "<TD>"
 TXBuffer += "Show files on data directory"

 html_TR_TD_height(30)
 TXBuffer += "<a class='button link wide red' onclick="
 TXBuffer += '"'
 TXBuffer += "return confirm('Do you really want to Reset/Erase all settings?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=reset'>Reset device settings</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Erase all JSON settings files"

 TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/i2cscanner')
def handle_i2cscanner(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 try:
  import gpios
 except Exception as e:
  TXBuffer += str(e)
  return TXBuffer

 suplvl = misc.getsupportlevel()
 if "RPI" in suplvl:
  try:
   estr = OS.get_i2c_state(0)
   if estr != "":
    TXBuffer += "<p>"+estr
    TXBuffer += "<p>"+OS.get_i2c_state(1)
  except:
   pass

 TXBuffer += "<table class='multirow' border=1px frame='box' rules='all'><TH>I2C Addresses in use<TH>Supported devices</th></tr>"
 i2cenabled = 0
 i2cdevs = 0
 try:
  i2cbuses = gpios.HWPorts.geti2clist()
 except:
  i2cbuses = []
 if len(i2cbuses)<1:
  for i in range(0,6):
   if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
    i2cbuses.append(i)
 i2cl = gpios.HWPorts.is_i2c_lib_available()

 for i in i2cbuses:
  try:
    i2cenabled += 1
    addFormSubHeader("I2C-"+str(i))
    TXBuffer += "</td></tr>"
    if i2cl:
     i2ca = gpios.HWPorts.i2cscan(i)
     for d in range(len(i2ca)):
      i2cdevs += 1
      TXBuffer += "<TR><TD>"+str(hex(i2ca[d]))+"</td><td>"
      TXBuffer += str(gpios.geti2cdevname(i2ca[d])).replace(";","<br>")
      TXBuffer += "</td></tr>"
    else:
     TXBuffer += "<tr><td colspan=2>I2C supporting SMBus library not found. Please install <a href='plugins?installmodule=i2c'>smbus</a>.</td></tr>"
  except Exception as e:
   print(e) # debug
 if i2cenabled==0:
  TXBuffer += "<tr><td colspan=2>Usable I2C bus not found</td></tr>"
 elif i2cdevs==0:
  TXBuffer += "<tr><td colspan=2>No device found on I2C bus</td></tr>"
 TXBuffer += "</table>"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

def getsortkey(item): # DEBUG
 val = 0
 try:
  val = item["signal_level_dBm"]
 except:
  val = 0
 return val
 
def getelement(arr,prop):
 retval = ""
 try:
  retval=str(arr[prop])
 except:
  retval=""
 return retval

@WebServer.route('/wifiscanner')
def handle_wifiscanner(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 wifidev = Settings.NetMan.getfirstwirelessdev()
 if wifidev:
  sw = Network.scanwifi(wifidev)
  sw2 = Network.parsewifiscan(sw)
  if sw2:
   if len(sw2)>0:
    if OS.check_permission()==False:
     TXBuffer += "Scanning does not work properly without root permission!<p>"
    TXBuffer += "<table class='multirow'><TR><TH>SSID<TH>BSSID<TH>Security<TH>Frequency<TH>Channel<TH>Signal<TH>Strength</TH></TR>"
    sw2.sort(reverse=False,key=getsortkey)
    for w in range(len(sw2)):
     TXBuffer += "<TR><TD>"+getelement(sw2[w],"essid")+"<td>"+getelement(sw2[w],"mac")+"<td>"+getelement(sw2[w],"encryption")+"<td>"+getelement(sw2[w],"frequency")
     TXBuffer += " "+getelement(sw2[w],"frequency_units")
     TXBuffer += "<td>"+getelement(sw2[w],"channel")+"<td>"+getelement(sw2[w],"signal_quality")+"/"+getelement(sw2[w],"signal_total")
     TXBuffer += "<td>"+getelement(sw2[w],"signal_level_dBm")+"</tr>"
   TXBuffer += "</table>"
  else:
   TXBuffer += "<p>No Access Points found"
 else:
  TXBuffer += "<p>No usable wireless device found"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/blescanner')
def handle_blescanner(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 blesupported = True
 try:
  from bluepy.btle import Scanner
  import lib.lib_blehelper as BLEHelper
 except:
  blesupported = False
 if blesupported:
    if OS.check_permission()==False:
     TXBuffer += "Scanning does not work properly without root permission!<p>"
    blesuccess = True
    _blestatus = BLEHelper.BLEStatus[0]
    while _blestatus.isscaninprogress():
      _blestatus.requeststopscan()
      time.sleep(0.5)
    _blestatus.reportscan(1)
    try:
     scanner = Scanner()
     devices = scanner.scan(5.0)
    except Exception as e:
     TXBuffer += "BLE scanning failed "+str(e)+"<p>"
     TXBuffer += "Try to run:<br>sudo systemctl stop bluetooth<br>sudo hciconfig hci0 up<p>"
     blesuccess = False
    _blestatus.reportscan(0)
    if blesuccess:
     TXBuffer += "<table class='multirow'><TR><TH>Interface<TH>Address<TH>Address type<TH>RSSI<TH>Connectable<TH>Name<TH>Appearance</TH><TH>Actions</TH></TR>"
     cc = 0
     for dev in devices:
      cc += 1
      TXBuffer += "<TR><TD>"+str(dev.iface)+"<TD><div id='mac"+str(cc)+"_1' name='mac"+str(cc)+"_1'>"+str(dev.addr)+"</div><TD>"+str(dev.addrType)+"<TD>"+str(dev.rssi)+" dBm<TD>"+str(dev.connectable)
      dname = ""
      shortdname = ""
      appear = ""
      for (adtype, desc, value) in dev.getScanData():
        if desc.lower() == "complete local name":
         dname = str(value)
        if desc.lower() == "shortened local name":
         shortdname = str(value)
        if desc.lower() == "appearance":
         appear = str(value)
      if dname.strip()=="":
        dname = shortdname
      TXBuffer += "<TD>"+str(dname)+"<TD>"+str(appear)+"<TD>"
      addCopyButton("mac"+str(cc),"","Copy MAC to clipboard",str(cc))
      TXBuffer += "</TR>"
     TXBuffer += "</table>"
 else:
    TXBuffer += "BLE supporting library not found! Please install <a href='plugins?installmodule=bluepy'>bluepy</a>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/login')
def handle_login(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=0
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 webrequest = str(arg("password",responsearr)).strip()
 self.set_cookie("password","")
 pwok = isLoggedIn(responsearr,[])
 if webrequest != "":
  if pwok:
   self.set_cookie("password",hashlib.sha1(bytes(webrequest,'utf-8')).hexdigest())
  else:
   commands.rulesProcessing("Login#Failed",rpieGlobals.RULE_SYSTEM)
 sendHeadandTail("TmplStd",_HEAD)

 if pwok:
  TXBuffer += "<p>Password accepted!"
 else:
  TXBuffer += "<form method='post'>"
  TXBuffer += "<TR><TD>Password<TD>"
  TXBuffer += "<input class='wide' type='password' name='password' value='"
  TXBuffer += webrequest
  TXBuffer += "'><TR><TD><TD>"
  addSubmitButton()
  TXBuffer += "<TR><TD></TABLE></FORM>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/control')
def handle_control(self):
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 webrequest = arg("cmd",responsearr)
 try:
  ph = Settings.Settings["PasswordHack"]
 except:
  ph = False
 if ph:
  wrs = str(webrequest).strip()[:4]
  if wrs in ["rebo","rese","halt","upda","exit"]: #Reboot,Reset,Halt,Update,Exit
   ph = False
 if ph==False:
  if (not isLoggedIn(self.get,self.cookie)):
   return self.redirect('/login')
 responsestr = False
 if len(webrequest)>0:
  responsestr = str(commands.doExecuteCommand(webrequest))
 if responsestr == False:
  return "FAILED"
 return responsestr

@WebServer.route('/advanced')
def handle_advanced(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 saved = arg("Submit",responsearr)
 if (saved):
  try:
   Settings.AdvSettings["webloglevel"]  = int(arg("webloglevel",responsearr))
  except:
   Settings.AdvSettings["webloglevel"]  = 0
  try:
   Settings.AdvSettings["consoleloglevel"]  = int(arg("consoleloglevel",responsearr))
  except:
   Settings.AdvSettings["consoleloglevel"]  = 0
  try:
   Settings.AdvSettings["sysloglevel"]  = int(arg("sysloglevel",responsearr))
   Settings.AdvSettings["syslogip"]  = str(arg("syslogip",responsearr))
  except Exception as e:
   print(e,arg("sysloglevel",responsearr))
   Settings.AdvSettings["sysloglevel"]  = 0
   Settings.AdvSettings["syslogip"]  = ""
  try:
   Settings.AdvSettings["battery"]["enabled"] = (arg("battery_mon",responsearr)=="on")
   Settings.AdvSettings["battery"]["tasknum"] = int(arg("battery_task",responsearr))
   Settings.AdvSettings["battery"]["taskvaluenum"] = int(arg("battery_valuenum",responsearr))
  except:
   Settings.AdvSettings["battery"] = {"enabled":False,"tasknum":0,"taskvaluenum":0}

  try:
   Settings.AdvSettings["Latitude"]  = float(arg("latitude",responsearr))
   Settings.AdvSettings["Longitude"] = float(arg("longitude",responsearr))
  except:
   Settings.AdvSettings["Latitude"]  = 0
   Settings.AdvSettings["Longitude"] = 0
  portlist = []
  for p in range(0,9):
   try:
    d = int(arg("_p"+str(p),responsearr))
   except:
    d = 0
   if d > 0:
    portlist.append(d)
  if len(portlist)<1:
   portlist = [80,8080,8008,591]
  Settings.AdvSettings["portlist"] = portlist
  try:
   Settings.AdvSettings["startpage"]  = str(arg("startpage",responsearr))
  except:
   Settings.AdvSettings["startpage"]  = "/"
  Settings.saveadvsettings()

 TXBuffer += "<form  method='post'><table class='normal'>"
 addFormHeader("Advanced Settings")
 addFormSubHeader("Log Settings")

 addFormLogLevelSelect("Console log Level","consoleloglevel", Settings.AdvSettings["consoleloglevel"])
 addFormLogLevelSelect("Web log Level",    "webloglevel",     Settings.AdvSettings["webloglevel"])
 addFormLogLevelSelect("Syslog Level",    "sysloglevel",     Settings.AdvSettings["sysloglevel"])
 try:
  val = Settings.AdvSettings["syslogip"]
 except:
  val = ""
  Settings.AdvSettings["syslogip"] = val
 addFormTextBox("Syslog IP", "syslogip", val,64)

 addFormSubHeader("WebGUI Settings")
 defports = [80,8080,8008,591]
 try:
  ports = Settings.AdvSettings["portlist"]
 except:
  ports = defports
 TXBuffer += "<tr><td>Enabled GUI ports:<td><fieldset>"
 for p in range(len(defports)):
   try:
    cn = "_p"+str(p)
    TXBuffer += "<input type='checkbox' name='"+cn+"' id='"+cn+"' value='"+str(defports[p])+"' "
    if defports[p] in ports:
     TXBuffer += "checked"
    TXBuffer += "><label for='"+cn+"'>"+str(defports[p])+"</label> "
   except:
    pass
 TXBuffer += "</fieldset>"

 try:
  sp = Settings.AdvSettings["startpage"]
 except:
  sp = "/"
 addFormTextBox("Start page", "startpage", sp,64)

 addFormSubHeader("Location Settings")
 try:
   lat = Settings.AdvSettings["Latitude"]
   lon = Settings.AdvSettings["Longitude"]
 except:
   lat = 0
   lon = 0
 addFormFloatNumberBox("Latitude", "latitude", lat , -90.0, 90.0)
 addUnit("&deg;")
 addFormFloatNumberBox("Longitude", "longitude", lon, -180.0, 180.0)
 addUnit("&deg;")

 try:
  if (plugindeps.modulelist):
   pass
 except:
  import plugindeps

 try:
  TXBuffer += "<TR><TD>Suntime library status: (needed for sunset/sunrise)<TD>"
  modname = "suntime"
  puse = plugindeps.ismoduleusable(modname)
  addEnabled(puse)
  if puse==False:
   usable = False
   TXBuffer += "<a href='plugins?installmodule="+modname+"'>"
  TXBuffer += modname+" "
  if puse==False:
   TXBuffer += "</a> (Not installed)"
  else:
   TXBuffer += "Installed"
 except Exception as e:
  print(e)

 try:
  TXBuffer += "<TR><TD>PySolar library status: (needed for Sun azimuth)<TD>"
  modname = "pysolar"
  puse = plugindeps.ismoduleusable(modname)
  addEnabled(puse)
  if puse==False:
   usable = False
   TXBuffer += "<a href='plugins?installmodule="+modname+"'>"
  TXBuffer += modname+" "
  if puse==False:
   TXBuffer += "</a> (Not installed)"
  else:
   TXBuffer += "Installed"
 except Exception as e:
  print(e)

 addFormSubHeader("Battery reporting source")
 try:
  bmon = Settings.AdvSettings["battery"]["enabled"]
  btask = Settings.AdvSettings["battery"]["tasknum"]
  btval = Settings.AdvSettings["battery"]["taskvaluenum"]
 except:
  bmon = False
  btask = 0
  btval = 0
 addFormCheckBox("Enable watching battery monitoring task","battery_mon",bmon)
 addFormNumericBox("Task Number", "battery_task", btask, 0, rpieGlobals.TASKS_MAX)
 addFormNumericBox("Task Value Number", "battery_valuenum", btval, 0, rpieGlobals.VARS_PER_TASK)
 addFormNote("These values are currently zero based! (WIP)")
 if bmon:
  bval = 0
  try:
   bval = Settings.Tasks[int(btask)].uservar[int(btval)]
  except:
   bval = 0
  TXBuffer += "<TR><TD>Battery percentage:<TD>"+str(bval)+" %"

 addFormSeparator(2)
 TXBuffer += "<TR><TD style='width:150px;' align='left'><TD>"
 addSubmitButton()
 TXBuffer += "<input type='hidden' name='edit' value='1'>"
 TXBuffer += "</table></form>"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/setup')
def handle_setup(self):
 global TXBuffer
 TXBuffer=""
 addHtml('Setup page')
 return TXBuffer

@WebServer.route('/json')
def handle_json(self):
 import platform, sys
 global TXBuffer, navMenuIndex
 self.set_mime("application/json")
 TXBuffer=""
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 tasknrstr = arg("tasknr",responsearr).strip()
 showspectask = -1
 if (len(tasknrstr)>0):
  try:
   showspectask = int(tasknrstr)-1
  except:
   showspectask = -1
 showsystem = True
 showwifi = True
 showdataacq = True
 showtaskdetail = True
 view = arg("view",responsearr)
 if (len(view)>0):
  if view=="sensorupdate":
   showsystem = False
   showwifi = False
   showdataacq = False
   showtaskdetail = False
 TXBuffer += "{"
 if showspectask==-1:
  if showsystem:
   TXBuffer += '"System":{"Build":"'
   TXBuffer += rpieGlobals.PROGNAME + " " + rpieGlobals.PROGVER
   TXBuffer += '","System libraries":"Python '
   TXBuffer += sys.version.replace('\n','')+" "+platform.platform()
   TXBuffer += '","Plugins":'+str(len(rpieGlobals.deviceselector)-1)
   TXBuffer += ',"Local time":"'+ datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   TXBuffer += '","Unit":'+str(Settings.Settings["Unit"])
   TXBuffer += ',"Name":"'+str(Settings.Settings["Name"])
   try:
    TXBuffer += '","Uptime":'+str(float(rpieTime.getuptime(2)))
   except:
    TXBuffer += '","Uptime":0'
   TXBuffer += ',"Load":'+str(OS.read_cpu_usage())
   try:
    TXBuffer += ',"Free RAM":'+str(float(OS.FreeMem())*1024)
   except:
    TXBuffer += ',"Free RAM":0'
   TXBuffer += "},"
  if showwifi:
   TXBuffer += '"WiFi":{'
   defaultdev = -1
   try:
    defaultdev = Settings.NetMan.getprimarydevice()
    if Settings.NetworkDevices[defaultdev].ip=="":
     defaultdev = -1
   except: 
    defaultdev = -1
   if defaultdev==-1:
    try:
     defaultdev = Settings.NetMan.getsecondarydevice()
    except: 
     defaultdev = -1
   if defaultdev != -1:
    if Settings.NetworkDevices[defaultdev].dhcp:
     nam = "DHCP"
    else:
     nam = "Static"
   TXBuffer += '"IP config":"'+nam
   TXBuffer += '","IP":"'+Settings.NetworkDevices[defaultdev].ip
   TXBuffer += '","Subnet Mask":"'+Settings.NetworkDevices[defaultdev].mask
   TXBuffer += '","Gateway IP":"'+Settings.NetworkDevices[defaultdev].gw
   TXBuffer += '","MAC address":"'+Settings.NetworkDevices[defaultdev].mac+'"'
   dnss = Settings.NetworkDevices[defaultdev].dns.strip().split(" ")
   for d in range(len(dnss)):
    TXBuffer += ',"DNS '+str(d+1)+'":"'+dnss[d]+'"'
   wdev = False
   try:
    wdev = Settings.NetMan.getfirstwirelessdev()
   except:
    wdev = False
   if wdev:
    TXBuffer += ',"SSID":"'+str(Network.get_ssid(wdev))+'"'
   TXBuffer += ',"RSSI":'+str(OS.get_rssi())
   TXBuffer += "},"
  senstart = 0
  senstop  = len(Settings.Tasks)
 else:
  senstart = showspectask
  senstop = senstart+1
 TXBuffer += '"Sensors":['
 ttl = 120
 for sc in range(senstart,senstop):
  if Settings.Tasks[sc] != False:
   TXBuffer += '{"TaskValues": ['
   for tv in range(0,Settings.Tasks[sc].valuecount):
    TXBuffer += '{"ValueNumber":' + str(tv+1)+',"Name":"' + str(Settings.Tasks[sc].valuenames[tv])+'",'
    TXBuffer += '"NrDecimals":'+str(Settings.Tasks[sc].decimals[tv])+','
    TXBuffer += '"Value":'
    if str(Settings.Tasks[sc].uservar[tv])=="":
     TXBuffer += '""'
    else:
     if str(Settings.Tasks[sc].decimals[tv]) == "-1":
      ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
     else:
      try:
       ival = float(Settings.Tasks[sc].uservar[tv])
      except:
       ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
     TXBuffer += str(ival)
    TXBuffer += '},'
   if TXBuffer[len(TXBuffer)-1]==",":
    TXBuffer = TXBuffer[:-1]
   TXBuffer += '],'
   TXBuffer += '"DataAcquisition": ['
   for ca in range(rpieGlobals.CONTROLLER_MAX):
    TXBuffer += '{"Controller":'+str(ca+1)+',"IDX":'+str(Settings.Tasks[sc].controlleridx[ca])+',"Enabled":"'+str(Settings.Tasks[sc].senddataenabled[ca])+'"},'
   if TXBuffer[len(TXBuffer)-1]==",":
    TXBuffer = TXBuffer[:-1]
   TXBuffer += '],'
   TXBuffer += '"TaskInterval":'+str(Settings.Tasks[sc].interval)+','
   TXBuffer += '"Type":"'+str(Settings.Tasks[sc].getdevicename())+'",'
   TXBuffer += '"TaskName":"'+str(Settings.Tasks[sc].gettaskname())+'",'
   TXBuffer += '"TaskEnabled":"'+str(Settings.Tasks[sc].enabled)+'",'
   TXBuffer += '"TaskNumber":'+str(sc+1)+'},'
   if (Settings.Tasks[sc].interval<ttl) and (Settings.Tasks[sc].interval>0):
    ttl = Settings.Tasks[sc].interval
 if TXBuffer[len(TXBuffer)-1]==",":
  TXBuffer = TXBuffer[:-1]
 TXBuffer += '],'
 TXBuffer += '"TTL":'+str(ttl*1000)+'}'

 return TXBuffer

@WebServer.route('/csv')
def handle_csv(self):
 global TXBuffer, navMenuIndex
 self.set_mime("text/csv")
 TXBuffer=""
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 tasknrstr = arg("tasknr",responsearr).strip()
 sc = -1
 if (len(tasknrstr)>0):
  try:
   sc = int(tasknrstr)
  except:
   sc = -1
 tasknrstr = arg("tasks",responsearr).strip()
 valnr = arg("valnr",responsearr)
 try:
  tv = int(valnr)
 except:
  tv = -1
 rheader = (arg("header",responsearr)!="0")

 if sc>=0:
  if sc<len(Settings.Tasks) and Settings.Tasks[sc] != False and Settings.Tasks[sc].enabled:
   if tv>-1:
    if tv>=Settings.Tasks[sc].valuecount:#nono
     return TXBuffer
    if rheader:
     TXBuffer += str(Settings.Tasks[sc].valuenames[tv])+';\n'
    if str(Settings.Tasks[sc].uservar[tv])=="":
      TXBuffer += '""'
    else:
      if str(Settings.Tasks[sc].decimals[tv]) == "-1":
       ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
      else:
       try:
        ival = float(Settings.Tasks[sc].uservar[tv])
       except:
        ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
      TXBuffer += str(ival)
    TXBuffer += ";\n"
   else:
    if rheader:
     for tv in range(0,Settings.Tasks[sc].valuecount):
      TXBuffer += str(Settings.Tasks[sc].valuenames[tv])+';'
     TXBuffer += "\n"
    for tv in range(0,Settings.Tasks[sc].valuecount):
     if str(Settings.Tasks[sc].uservar[tv])=="":
      TXBuffer += '""'
     else:
      if str(Settings.Tasks[sc].decimals[tv]) == "-1":
       ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
      else:
       try:
        ival = float(Settings.Tasks[sc].uservar[tv])
       except:
        ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
      TXBuffer += str(ival)
     TXBuffer += ";"
    TXBuffer += "\n"
 elif "_" in tasknrstr:
  tia = tasknrstr.split(",")
  for ti in tia:
   try:
    t = ti.split("_")
    sc = int(t[0])
    tv = int(t[1])
    if sc<len(Settings.Tasks) and Settings.Tasks[sc] != False and Settings.Tasks[sc].enabled:
     if tv>-1:
      if tv>=Settings.Tasks[sc].valuecount:#nono
        TXBuffer += '"";'
        continue
      if str(Settings.Tasks[sc].uservar[tv])=="":
        TXBuffer += '""'
      else:
        if str(Settings.Tasks[sc].decimals[tv]) == "-1":
         ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
        else:
         try:
          ival = float(Settings.Tasks[sc].uservar[tv])
         except:
          ival = '"'+ str(Settings.Tasks[sc].uservar[tv]) + '"'
        TXBuffer += str(ival)
      TXBuffer += ";"
     else:
      TXBuffer += '"";'
    else:
      TXBuffer += '"";'
   except Exception as e:
    pass
 return TXBuffer

@WebServer.route('/rules')
def handle_rules(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=5
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 rules = ""
 saved = arg("Submit",responsearr)
 if (saved):
  rules = arg("rules",responsearr)
  try:
     with open(rpieGlobals.FILE_RULES,'w') as f:
      f.write(rules)
  except:
     pass
  if len(rules)>0:
    commands.splitruletoevents(rules)
 if rules=="":
    try:
     with open(rpieGlobals.FILE_RULES,'r') as f:
      rules = f.read()
    except:
     pass
 TXBuffer += "<form name = 'frmselect' method = 'post'><table class='normal'><TR><TH align='left'>Rules"
 TXBuffer += "<tr><td><textarea name='rules' rows='30' wrap='off'>"
 TXBuffer += rules+"</textarea>"
 addFormSeparator(2)
 addSubmitButton()
 TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/sysvars')
def handle_sysvars(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 TXBuffer += "<table class='normal'><TR><TH align='left'>System Variables<TH align='left'>Normal"
 for sv in commands.SysVars:
  TXBuffer += "<TR><TD>%" + sv + "%</TD><TD>"
  TXBuffer += str(commands.getglobalvar(sv)) + "</TD></TR>"
 conversions = [ "%c_m2day%(%uptime%)", "%c_m2dh%(%uptime%)", "%c_m2dhm%(%uptime%)" ]
 for sv in conversions:
  try:
   TXBuffer += "<TR><TD>" + sv + "</TD><TD>"
   TXBuffer += str(commands.parseruleline(sv)[0]) + "</TD></TR>"
  except:
   pass
 TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/timers')
def handle_timers(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 TXBuffer += "<table class='normal'><TR><TH align='left'>Timer #<TH align='left'>State<TH align='left'>Looping/Loopcount/Maxloops<TH align='left'>Timeout<TH align='left'>Last start<TH align='left'>Last error"
 try:
  for t in range(len(rpieTime.Timers)):
   TXBuffer += "<TR><TD>" + str(t+1) + "</TD><TD>"
   if rpieTime.Timers[t].state==0:
    TXBuffer += "off"
   elif rpieTime.Timers[t].state==1:
    TXBuffer += "running"
   elif rpieTime.Timers[t].state==2:
    TXBuffer += "paused"
   TXBuffer += "<TD>"
   if rpieTime.Timers[t].looping==False:
    TXBuffer += "no"
   else:
    TXBuffer += "yes/"+str(rpieTime.Timers[t].loopcount)+"/"+str(rpieTime.Timers[t].maxloops)
   TXBuffer += "<TD>"+str(rpieTime.Timers[t].timeout)
   if rpieTime.Timers[t].laststart == 0:
    TXBuffer += "<TD>never"
   else:
    TXBuffer += "<TD>"+ misc.formatnum((time.time() - rpieTime.Timers[t].laststart),2) +"s ago"
   TXBuffer += "<TD>"+str(rpieTime.Timers[t].lasterr)
 except Exception as e:
  print(e)
 TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/sysinfo')
def handle_sysinfo(self):
 import platform, sys
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 TXBuffer += "<table class='normal'><TR><TH style='width:150px;' align='left'>System Info<TH align='left'>"

 TXBuffer += "<TR><TD>Unit:<TD>"
 TXBuffer += str(Settings.Settings["Unit"])
 TXBuffer += "<TR><TD>Local Time:<TD>" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
 TXBuffer += "<TR><TD>Uptime:<TD>" + rpieTime.getuptime(1)
 TXBuffer += "<TR><TD>Load:<TD>" +str( OS.read_cpu_usage() ) + " %"
 TXBuffer += "<TR><TD>Free Mem:<TD>" + str( OS.FreeMem() ) + " kB"
 addTableSeparator("Network", 2, 3)
 try:
  rssi = OS.get_rssi()
  if str(rssi)=="-49.20051":
   rssi = "Wired connection"
  else:
   rssi = str(rssi)+" dB"
 except:
   rssi = "?"
 TXBuffer += "<TR><TD>Wifi RSSI:<TD>" + str(rssi)
 wdev = False
 try:
    wdev = Settings.NetMan.getfirstwirelessdev()
 except:
    wdev = False
 if wdev:
    TXBuffer += '<tr><td>SSID<td>'+str(Network.get_ssid(wdev))
 defaultdev = -1

 try:
    defaultdev = Settings.NetMan.getprimarydevice()
    if Settings.NetworkDevices[defaultdev].ip=="":
     defaultdev = -1
 except: 
    defaultdev = -1
 if defaultdev==-1:
    try:
     defaultdev = Settings.NetMan.getsecondarydevice()
    except: 
     defaultdev = -1

 if defaultdev != -1:
  if Settings.NetworkDevices[defaultdev].dhcp:
     nam = "DHCP"
  else:
     nam = "Static"
  TXBuffer += '<tr><td>IP config<td>'+nam
  TXBuffer += '<tr><td>IP / subnet<td>'+Settings.NetworkDevices[defaultdev].ip+" / "+Settings.NetworkDevices[defaultdev].mask
  TXBuffer += '<tr><td>GW<td>'+Settings.NetworkDevices[defaultdev].gw
  TXBuffer += '<tr><td>MAC<td>'+Settings.NetworkDevices[defaultdev].mac
  TXBuffer += "<tr><td>DNS<td>"
  dnss = Settings.NetworkDevices[defaultdev].dns.strip().split(" ")
  for d in range(len(dnss)):
    TXBuffer += dnss[d]+" "

 addTableSeparator("Software", 2, 3)
 TXBuffer += '<tr><td>Build<td>' + str(rpieGlobals.PROGNAME) + " " + str(rpieGlobals.PROGVER)
 TXBuffer += '<tr><td>Libraries<td>Python ' + sys.version.replace('\n','<br>') +" " +platform.platform()
 TXBuffer += '<tr><td>Plugins<td>'+str(len(rpieGlobals.deviceselector)-1)

 suplvl = misc.getsupportlevel()

 addTableSeparator("Hardware", 2, 3)
 TXBuffer += "<TR><TD>Type:<TD>"+suplvl
 if suplvl[0] != "N":
  TXBuffer += "<TR><TD>OS:<TD>"+str(rpieGlobals.osinuse)+" "+str(misc.getosname(1))
  TXBuffer += "<TR><TD>OS full name:<TD>"+str(OS.getosfullname())
  cpui = OS.get_cpu()
  TXBuffer += "<tr><td>CPU model:<td>"+str(cpui["model"])
  TXBuffer += "<tr><td>CPU speed:<td>"+str(cpui["speed"])
  TXBuffer += "<tr><td>CPU count:<td>"+str(cpui["core"])
  TXBuffer += "<tr><td>CPU architecture:<td>"+str(cpui["arch"])
  thw = str(OS.gethardware()).strip()
  if thw != "":
   TXBuffer += "<TR><TD>Hardware:<TD>"+thw

 try:
  if suplvl[0] == "R":
   rpv = OS.getRPIVer()
   if len(rpv)>1:
    TXBuffer += "<TR><TD>Hardware:<TD>"+rpv["name"]+" "+rpv["ram"]
 except:
  pass
 try:
  if suplvl[0] != "N":
   racc = OS.check_permission()
   rstr = str(racc)
   TXBuffer += "<TR><TD>Root access:<TD>"+rstr
 except:
  pass
 try:
  info = os.statvfs(os.path.realpath(__file__))
 except:
  info = None
 if info is not None:
  addTableSeparator("Storage", 2, 3)
  TXBuffer += "<TR><TD>Free size:<TD>"+ str(int(info.f_frsize * info.f_bavail / 1024)) +" kB"
  TXBuffer += "<TR><TD>Full size:<TD>"+ str(int(info.f_frsize * info.f_blocks / 1024)) +" kB"
 TXBuffer += "<tr></tr></table>"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/filelist')
def handle_filelist(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

#  TXBuffer += "window.open('filelist?o="+str(returnobjname)+"&chgto="+str(startdir)+"','Browse files','width=200,height=200')"
 retobj=arg("o",responsearr).strip() # browse panel requested

# sfile =arg("sel",responsearr).strip()
# if sfile:
#  sfile="&sel="+sfile

 if retobj:
  sendHeadandTail("TmplDsh",_HEAD)
  sfile="&o="+str(retobj)
  TXBuffer += "<script type='text/javascript'>function reportbackfilename(objname,fname){var retval = window.opener.document.getElementById(objname); retval.value = fname; window.close(); return fname;}</script>"
 else:
  sendHeadandTail("TmplStd",_HEAD)
  sfile=""
 current_dir = "files/"

 dfile =arg("delete",responsearr)
 if dfile:
  if dfile.startswith(current_dir)==False:
   dfile = current_dir+dfile
  OS.delete_file(dfile)
 ddir = arg("deletedir",responsearr)
 if ddir:
  if ddir.startswith(current_dir)==False:
   ddir = current_dir+ddir
  OS.delete_dir(ddir)

 dirasked = arg("chgto",responsearr).replace("..","")
 if dirasked:
  if dirasked[len(dirasked)-1]!="/":
   dirasked += "/"
  if dirasked.startswith(current_dir):
   current_dir = dirasked
  else:
   current_dir += dirasked
 if current_dir[len(current_dir)-1]=='/':
  tdir = current_dir[len(current_dir)-1:]
 else:
  tdir = current_dir
 lastc = tdir.rfind('/')
 if lastc > 0:
   tdir = tdir[:lastc+1]
 if tdir == "/":
  tdir = ""
 addFormSubHeader(str(current_dir))
 TXBuffer += "<br><table class='multirow' border=1px frame='box' rules='all'><TR><TH style='width:50px;'><TH align='left'>Name<TH align='left'>Size"
 TXBuffer += "<tr><td><td><a href='filelist?chgto="+urllib.parse.quote_plus(str(tdir))+str(sfile)+"'>..</a><td>" # parentdir?
 flist = OS.scan_dir(current_dir)
 if len(flist)>0:
  for f in flist:
   TXBuffer += "<tr>"
   TXBuffer += "<td>"
   if retobj:
     TXBuffer += "<a class='button link' onclick="
     TXBuffer += '"'
     TXBuffer += "reportbackfilename('"+str(retobj)+"','"+str(f[0])+"');"
     TXBuffer += '"'
     TXBuffer += ">SEL</a>"
   else:
    if f[1]=="DIR":
     TXBuffer += "<a class='button link' onclick="
     TXBuffer += '"'
     TXBuffer += "return confirm('Delete this directory?')"
     TXBuffer += '"'
     TXBuffer += " href='filelist?deletedir="+urllib.parse.quote_plus(f[0])+"'>DEL</a>"
    else:
     TXBuffer += "<a class='button link' onclick="
     TXBuffer += '"'
     TXBuffer += "return confirm('Delete this file?')"
     TXBuffer += '"'
     TXBuffer += " href='filelist?delete="+urllib.parse.quote_plus(f[0])+"'>DEL</a>"
   TXBuffer += "<td>"
   tagstarted = False
   if f[1]=="DIR":
    TXBuffer += "<a href='filelist?chgto="+urllib.parse.quote_plus(f[0])+str(sfile)+"'>"
    tagstarted = True
   elif retobj=="":
    TXBuffer += "<a href='download?file="+urllib.parse.quote_plus(f[0])+"'>"
    tagstarted = True
   if f[0].startswith(current_dir):
    f[0] = f[0][len(current_dir):].replace("/","")
   TXBuffer += str(f[0])
   if tagstarted:
    TXBuffer += "</a>"
   TXBuffer += "<td>"+str(f[1])

 TXBuffer += "</table>"
 TXBuffer += "<p><br>"
 if retobj:
  TXBuffer += "<a class='button link' onclick="
  TXBuffer += '"'
  TXBuffer += "window.close();"
  TXBuffer += '"'
  TXBuffer += "'>Close</a>"
  sendHeadandTail("TmplDsh",_TAIL)
 else:
  addButton("upload?path="+str(current_dir), "Upload")
  sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer


@WebServer.route('/favicon.ico')
def handle_favicon(self):
 return self.file('favicon.ico')

@WebServer.route('/default.css')
def handle_css(self):
 return self.file('default.css')

@WebServer.route('/img/{imagename}')
def handle_favicon(self,imagename):
 fname = "img/"+re.sub(r'[^a-zA-Z0-9. ]',r'',imagename)
 if os.path.isfile(fname):
  return self.file(fname)
 else:
  return ""

@WebServer.route('/config.dat')
def handle_configdat(self):
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 try:
    fname = OS.settingstozip()
 except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Download error: "+str(e))
 if fname!="":
    self.set_header("Content-Disposition", 'filename="config.dat"')
    return self.file(fname)
 else:
    return ""

@WebServer.route('/rules1.txt')
def handle_rules1(self):
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 fname = "files/rules1.txt"
 if os.path.isfile(fname):
  fpath = fname.split("/")
  self.set_header("Content-Disposition", 'filename="'+str(fpath[len(fpath)-1])+'"')
  return self.file(fname)
 else:
  return ""

@WebServer.route('/download')
def handle_download(self):
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 stype = arg("type",responsearr)
 if stype=="settings": # DEBUG
   try:
    fname = OS.settingstozip()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Download error: "+str(e))
   if fname!="":
    self.set_header("Content-Disposition", 'filename="data.zip"')
    return self.file(fname)
   else:
    return self.redirect("/tools")

 fname = arg("file",responsearr)
 if fname.startswith("files/")==False:
  fname = "files/" + fname
 fname = fname.replace("..","")
 if os.path.isfile(fname):
  fpath = fname.split("/")
  self.set_header("Content-Disposition", 'filename="'+str(fpath[len(fpath)-1])+'"')
  return self.file(fname)
 else:
  return ""

@WebServer.get('/upload')
def handle_upload(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 current_dir = "files/"
 upath = arg("path",self.get)
 if upath:
  if upath.startswith(current_dir)==False:
   upath = current_dir+upath
 else:
  upath = current_dir
 stype = arg("type",self.get)
 if stype=="settings":
  upath = "data/"
  current_dir = "data/"
  TXBuffer += "<p>You can upload JSON settings files one by one or in a single .ZIP archive.<p>"
 else:
  TXBuffer += "<p>Upload selected files into remote directory: <b>"+str(upath)+"</b><p>"
 TXBuffer += "<p>Please avoid using space in filenames, and restart RPIEasy to commit changes. Otherwise you will see empty structures..."
 TXBuffer += "<p><form enctype='multipart/form-data' method='post'><p>Upload file:<br><input type='file' name='datafile' id='datafile'></p><div><input class='button link' type='submit' value='Upload'><input type='hidden' name='path' value='"
 TXBuffer += upath + "'></div></form>"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.post('/upload')
def handle_upload_post(self):
 if self.post:
  misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "File upload started...")
  current_dir = 'files/'
  upath = arg("path",self.post).strip()
  if upath:
   if upath == "data/":
    fname = ""
    try:
     if ' ' in self.post['datafile']['filename']:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Please do not use space in filenames...")
      return self.redirect("/tools")
     if self.post['datafile']['filename']:
      fname = "data/" + self.post['datafile']['filename'].strip()
      fout = open(fname,"wb")
      fout.write(self.post['datafile']['file'])
      fout.close()
    except:
     fname = ""
    if fname.lower().endswith(".zip"):
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Unzipping...")
     OS.extractzip(fname,"data/")
    try:
     Settings.loadnetsettings()
     Settings.loadpinout()
     Settings.loadtasks()
     Settings.loadcontrollers()
     Settings.loadnotifiers()
    except Exception as e:
     print(e)
    return self.redirect("/tools")
  if upath:
   if upath.startswith(current_dir)==False:
    upath = current_dir+upath
  else:
   upath = current_dir
  if upath[len(upath)-1] != '/':
   upath += '/'
  fname = ""
  try:
   logstr = "Upload destination path:"+str(fname)+" Filename:"+str(self.post['datafile']['filename'])+" Filesize:"+str(len(self.post['datafile']['file']))
  except Exception as e:
   logstr = str(e)
  misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, logstr)
  try:
   if 'datafile' not in self.post:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Browser did not send any data "+str(self.post))
    return self.redirect("filelist?chgto="+str(upath))
   if self.post['datafile']['filename']:
    fname = upath + self.post['datafile']['filename'].strip()
    fout = open(fname,"wb")
    fout.write(self.post['datafile']['file'])
    fout.close()
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Exception while uploading "+str(e))
 return self.redirect("filelist?chgto="+str(upath))

@WebServer.route('/dashboard.esp') # still experimental!
def handle_custom(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=0
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 webrequest = arg("cmd",responsearr)
 if len(webrequest)>0:
  responsestr = str(commands.doExecuteCommand(webrequest))
 
 unit = arg("unit",responsearr).strip()
 btnunit = arg("btnunit",responsearr).strip()
 if unit == "":
  unit = btnunit

 if str(unit) != "":
   if str(unit) != str(Settings.Settings["Unit"]):
    ipa = ""
    if len(Settings.nodelist)>0:
     for n in Settings.nodelist:
      if str(n["unitno"]) == str(unit):
       ipa = str(n["ip"])
       break
    if ipa != "":
     if str(n["port"]) != "" and str(n["port"]) != "0" and str(n["port"]) != "80":
      ipa += ":" + str(n["port"])
     return self.redirect("http://"+str(ipa)+"/dashboard.esp")
#    sendHeadandTail("TmplDsh",_HEAD)
#    TXBuffer += "<meta http-equiv=\"refresh\" content=\"0; URL=http://"
#    TXBuffer += ipa
#    TXBuffer += "/dashboard.esp\">"
#    sendHeadandTail("TmplDsh",_TAIL)
#    return TXBuffer

 if len(Settings.nodelist)>0:
  prevn = 0
  nextn = 0
  nlen = len(Settings.nodelist)
  for n in range(0,nlen):
      if str(Settings.nodelist[n]["unitno"]) == str(Settings.Settings["Unit"]):
       if n>0:
        prevn=n-1
       else:
        prevn=n
       if n<(nlen-1):
        nextn=n+1
       else:
        nextn=n
       break

  sendHeadandTail("TmplDsh",_HEAD)
  TXBuffer += "<script><!--\nfunction dept_onchange(frmselect) {frmselect.submit();}\n//--></script>"
  TXBuffer += "<form name='frmselect' method='post'>"
  addSelector_Head("unit",True)
  choice = int(Settings.Settings["Unit"])
  for n in range(nlen):
    addSelector_Item((str(Settings.nodelist[n]["unitno"])+" - "+ str(Settings.nodelist[n]["name"])),int(Settings.nodelist[n]["unitno"]),(int(Settings.nodelist[n]["unitno"])==int(choice)),False)
  addSelector_Foot()
  TXBuffer += "<a class='button link' href='http://"
  ipa = str(Settings.nodelist[prevn]["ip"])
  iport = str(Settings.nodelist[prevn]["port"])
  if str(iport) != "" and str(iport) != "0" and str(iport) != "80":
    ipa += ":" + str(iport)
  TXBuffer += ipa + "/dashboard.esp"
  TXBuffer += "?btnunit="+str(Settings.nodelist[prevn]["unitno"])
  TXBuffer += "'>&lt;</a>"

  TXBuffer += "<a class='button link' href='http://"
  ipa = str(Settings.nodelist[nextn]["ip"])
  iport = str(Settings.nodelist[nextn]["port"])
  if str(iport) != "" and str(iport) != "0" and str(iport) != "80":
    ipa += ":" + str(iport)
  TXBuffer += ipa + "/dashboard.esp"
  TXBuffer += "?btnunit="+str(Settings.nodelist[nextn]["unitno"])
  TXBuffer += "'>&gt;</a>"

 try:
  customcont = OS.getfilecontent("dashboard.esp")
 except Exception as e:
  print(e)
 if len(customcont)>0:
  for l in customcont:
   try:
    cl, st = commands.parseruleline(str(l))
    if st=="CMD":
     TXBuffer += str(cl)
    else:
     TXBuffer += str(l)
   except Exception as e:
    print(e)
 else: # if template not found
  sendHeadandTail("TmplDsh",_HEAD)
  TXBuffer += "<table class='normal'>"
  try:
   for sc in range(0,len(Settings.Tasks)):
    if Settings.Tasks[sc] != False:
     TXBuffer += "<TR><TD>"+Settings.Tasks[sc].gettaskname()
     fl = False
     for tv in range(0,Settings.Tasks[sc].valuecount):
      if str(Settings.Tasks[sc].valuenames[tv])!="":
       if fl:
        TXBuffer += "<TR><TD>"
       TXBuffer += '<TD>' + str(Settings.Tasks[sc].valuenames[tv]) + "<td>" + str(Settings.Tasks[sc].uservar[tv]) + "</TR>"
       fl = True
  except Exception as e:
   print(e)
  TXBuffer += "</table><BR>"
  sendHeadandTail("TmplDsh",_TAIL)
 return TXBuffer

@WebServer.route('/adconfig')
def handle_adconfig(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=2
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 try:
  import lib.web_adconfig as ADConfig
  ADConfig.handle_adconfig(responsearr)
 except Exception as e:
  print("Adconfig error",e)
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

# -----------------------------

def addHtmlError(error):
 global TXBuffer
 if error.len()>0:
  TXBuffer += "<div class=\"alert\"><span class=\"closebtn\" onclick=\"this.parentElement.style.display='none';\">&times;</span>"
  TXBuffer += error
  TXBuffer += "</div>"

def addHtml(html):
 global TXBuffer
 TXBuffer += html

def addFormSelector(label, fid, optionCount, options, indices, attr, selectedIndex, reloadonchange = False):
  addRowLabel(label)
  addSelector(fid, optionCount, options, indices, attr, selectedIndex, reloadonchange)

def addFormPinSelect(label,fid,choice):
  addRowLabel(label)
  addPinSelect(False,fid,choice)

def addPinSelect(fori2c,name,choice):
  global TXBuffer
  addSelector_Head(name,False)
  addSelector_Item("None",-1,(str(choice)==str(-1)),False,"")
  for x in range(len(Settings.Pinout)):
   try:
    if int(Settings.Pinout[x]["altfunc"]==0) and int(Settings.Pinout[x]["canchange"])>0 and int(Settings.Pinout[x]["BCM"]>-1):
     oname = Settings.Pinout[x]["name"][0]
     if Settings.Pinout[x]["canchange"]==1:
      onum=0
      try:
       onum = int(Settings.Pinout[x]["startupstate"])
       if onum<1 or onum>len(Settings.PinStates):
        onum=0
      except:
       pass
      oname += " ("+Settings.PinStates[onum]+")"
     if Settings.Pinout[x]["BCM"] == Settings.Pinout[x]["ID"]:
      oname = str(Settings.Pinout[x]["BCM"]) + "-" + oname
     addSelector_Item(oname,Settings.Pinout[x]["BCM"],(str(choice)==str(Settings.Pinout[x]["BCM"])),False,"")
   except:
    pass
  addSelector_Foot()

def addSelector(fid, optionCount, options, indices, attr, selectedIndex, reloadonchange):
  global TXBuffer
  sindex = 0
  TXBuffer += "<select id='selectwidth' name='"
  TXBuffer += str(fid)
  TXBuffer += "'"
  if (reloadonchange):
    TXBuffer += " onchange='return dept_onchange(frmselect)'>"
  TXBuffer += ">"
  for x in range(optionCount):
    if (indices):
      sindex = indices[x]
    else:
      sindex = x
    TXBuffer += "<option value="
    TXBuffer += str(sindex)
    if (int(selectedIndex) == int(sindex)):
      TXBuffer += " selected"
    if (attr):
      TXBuffer += " "
      TXBuffer += str(attr[x])
    TXBuffer += ">"
    TXBuffer += str(options[x])
    TXBuffer += "</option>"
  TXBuffer += "</select>"

def addSelector_Head(fid, reloadonchange):
  global TXBuffer
  TXBuffer += "<select id='selectwidth' name='"
  TXBuffer += fid;
  TXBuffer += "'"
  if (reloadonchange):
    TXBuffer += " onchange='return dept_onchange(frmselect)'>"
  TXBuffer += ">"

def addSelector_Item(option, sindex, selected, disabled, attr=""):
  global TXBuffer
  TXBuffer += "<option value="
  TXBuffer += str(sindex)
  if (selected):
    TXBuffer += " selected"
  if (disabled):
    TXBuffer += " disabled"
  if (attr and attr.length() > 0):
    TXBuffer += " "
    TXBuffer += str(attr)
  TXBuffer += ">"
  TXBuffer += str(option)
  TXBuffer += "</option>"

def addSelector_Foot():
  global TXBuffer
  TXBuffer += "</select>"

def addUnit(unit):
  global TXBuffer
  TXBuffer += " ["
  TXBuffer += str(unit)
  TXBuffer += "]"

def addRowLabel(label):
  global TXBuffer
  TXBuffer += "<TR><TD>"
  TXBuffer += str(label)
  TXBuffer += ":<TD>"

def addButton(url, label):
 global TXBuffer
 TXBuffer += "<a class='button link' href='"
 TXBuffer += url
 TXBuffer += "'>"
 TXBuffer += label
 TXBuffer += "</a>"

def addWideButton(url, label, color):
 global TXBuffer
 TXBuffer += "<a class='button link wide"
 TXBuffer += color
 TXBuffer += "' href='"
 TXBuffer += url
 TXBuffer += "'>"
 TXBuffer += label
 TXBuffer += "</a>"

def addSubmitButton(value = "Submit", name="Submit"):
  global TXBuffer
  TXBuffer += "<input class='button link' type='submit' value='"
  TXBuffer += str(value)
  TXBuffer += "' name='"
  TXBuffer += name
  TXBuffer += "'><div id='toastmessage'></div><script type='text/javascript'>toasting();</script>"


def addCopyButton(value, delimiter, name,dist=""):
  global TXBuffer
  TXBuffer += "<script>function setClipboard"+str(dist)+"() { var clipboard = ''; max_loop = 100; for (var i = 1; i < max_loop; i++){ var cur_id = '"
  TXBuffer += str(value)
  TXBuffer += "_' + i; var test = document.getElementById(cur_id); if (test == null){ i = max_loop + 1;  } else { clipboard += test.innerHTML.replace(/<[Bb][Rr]\\s*\\/?>/gim,'\\n') + '"
  TXBuffer += str(delimiter)
  TXBuffer += "'; } }"
  TXBuffer += "clipboard = clipboard.replace(/<\\/[Dd][Ii][Vv]\\s*\\/?>/gim,'\\n');"
  TXBuffer += "clipboard = clipboard.replace(/<[^>]*>/gim,'');"
  TXBuffer += "var tempInput = document.createElement('textarea'); tempInput.style = 'position: absolute; left: -1000px; top: -1000px'; tempInput.innerHTML = clipboard;"
  TXBuffer += "document.body.appendChild(tempInput); tempInput.select(); document.execCommand('copy'); document.body.removeChild(tempInput); alert('Copied: \"' + clipboard + '\" to clipboard!') }</script>"
  TXBuffer += "<button class='button link' onclick='setClipboard"+str(dist)+"()'>"
  TXBuffer += str(name)
  TXBuffer += "</button>"

def addBrowseButton(label,returnobjname,startdir=""):
  global TXBuffer
  st = startdir
  if startdir:
   lastper = startdir.rfind('/')
   if len(startdir)-1!=lastper:
    st = startdir[:lastper]
  TXBuffer += "<a class='button link' onclick="
  TXBuffer += '"'
  TXBuffer += "window.open('filelist?o="+str(returnobjname)+"&chgto="+str(st)+"','Browse files','width=400,height=300')"
  TXBuffer += '"'
  TXBuffer += ">"+str(label)+"</a>"

def addTableSeparator(label, colspan, h_size):
  global TXBuffer
  TXBuffer += "<TR><TD colspan="
  TXBuffer += str(colspan)
  TXBuffer += "><H"
  TXBuffer += str(h_size)
  TXBuffer += '>'
  TXBuffer += str(label)
  TXBuffer += "</H"
  TXBuffer += str(h_size)
  TXBuffer += "></TD></TR>"

def addFormHeader(header1, header2=""):
  global TXBuffer
  if header2 == "":
   TXBuffer += "<TR><TD colspan='2'><h2>"
   TXBuffer += str(header1)
   TXBuffer += "</h2>"
  else:
   TXBuffer += "<TR><TH>"
   TXBuffer += str(header1)
   TXBuffer += "<TH>"
   TXBuffer += str(header2)
   TXBuffer += ""

def addFormSubHeader(header):
  global TXBuffer
  TXBuffer += "<TR><TD colspan='2'><h3>"
  TXBuffer += str(header)
  TXBuffer += "</h3>"

def addFormNote(text):
  global TXBuffer
  TXBuffer += "<TR><TD><TD><div class='note'>Note: "
  TXBuffer += str(text)
  TXBuffer += "</div>"

def addFormSeparator(clspan):
 global TXBuffer
 TXBuffer += "<TR><TD colspan='"
 TXBuffer += str(clspan)
 TXBuffer += "'><hr>"

def addCheckBox(fid, checked):
  global TXBuffer
  TXBuffer += "<label class='container'>&nbsp;"
  TXBuffer += "<input type='checkbox' id='"
  TXBuffer += str(fid)
  TXBuffer += "' name='"
  TXBuffer += str(fid)
  TXBuffer += "'"
  if (checked):
    TXBuffer += " checked"
  TXBuffer += "><span class='checkmark'></span></label>"

def addFormCheckBox(label, fid, checked):
  addRowLabel(label)
  addCheckBox(fid, checked)

def addNumericBox(fid, value, minv=INT_MIN, maxv=INT_MAX):
  global TXBuffer
  TXBuffer += "<input class='widenumber' type='number' name='"
  TXBuffer += str(fid)
  TXBuffer += "'"
  if (minv != INT_MIN):
    TXBuffer += " min="
    TXBuffer += str(minv)
  if (maxv != INT_MAX):
    TXBuffer += " max="
    TXBuffer += str(maxv)
  TXBuffer += " value="
  TXBuffer += str(value)
  TXBuffer += ">"

def addFormNumericBox(label, fid, value, minv=INT_MIN, maxv=INT_MAX):
  addRowLabel(label)
  addNumericBox(fid, value, minv, maxv)

def addTextBox(fid, value, maxlength):
  global TXBuffer
  TXBuffer += "<input class='wide' type='text' name='"
  TXBuffer += str(fid)
  TXBuffer += "' id='"
  TXBuffer += str(fid)
  TXBuffer += "' maxlength="
  TXBuffer += str(maxlength)
  TXBuffer += " value='"
  TXBuffer += str(value)
  TXBuffer += "'>"

def addFormTextBox(label, fid, value, maxlength):
  addRowLabel(label)
  addTextBox(fid, value, maxlength)

def addFormPasswordBox(label, fid, password, maxlength):
  global TXBuffer
  addRowLabel(label)
  TXBuffer += "<input class='wide' type='password' name='"
  TXBuffer += str(fid)
  TXBuffer += "' maxlength="
  TXBuffer += str(maxlength)
  TXBuffer += " value='"
  if (password != ""):
    TXBuffer += "*****"
  TXBuffer += "'>"


def addFormLogLevelSelect(label, sid, choice):
  addRowLabel(label)
  addLogLevelSelect(sid,choice)

def getLogLevelDisplayString(lvl):
 res = ""
 if lvl == 0:
  res = "None"
 elif lvl == rpieGlobals.LOG_LEVEL_ERROR:
  res ="Error"
 elif lvl == rpieGlobals.LOG_LEVEL_INFO:
  res ="Info"
 elif lvl == rpieGlobals.LOG_LEVEL_DEBUG:
  res ="Debug"
 elif lvl == rpieGlobals.LOG_LEVEL_DEBUG_MORE:
  res ="Debug More"
 elif lvl == rpieGlobals.LOG_LEVEL_DEBUG_DEV:
  res ="Debug Developer"
 return res

def addLogLevelSelect(name,choice):
  options=[]
  optionvalues=[]
  for l in range(0,10):
   lvlname = getLogLevelDisplayString(l)
   if lvlname!="":
    options.append(lvlname)
    optionvalues.append(l)
  addSelector(name, len(options), options, optionvalues, None, choice, False)

def html_TR_TD_highlight():
 global TXBuffer
 TXBuffer += "<TR class=\"highlight\"><TD>"

def html_TR_TD_height(height):
 global TXBuffer
 TXBuffer += "<TR><TD HEIGHT=\""+str(height)+"\">"

def addFormIPBox(label, fid, ip):
  global TXBuffer
  sstrip = ""
  if (ip[0] == 0 and ip[1] == 0 and ip[2] == 0 and ip[3] == 0):
    sstrip = ""
  else:
    formatIP(ip, sstrip) # MISSING - not sure it will be needed anymore

  addRowLabel(label)
  TXBuffer += "<input class='wide' type='text' name='"
  TXBuffer += str(fid)
  TXBuffer += "' value='"
  TXBuffer += str(sstrip)
  TXBuffer += "'>"

def addEnabled(enabled):
  global TXBuffer
  if (enabled):
    TXBuffer += "<span class='enabled on'>&#10004;</span>"
  else:
    TXBuffer += "<span class='enabled off'>&#10060;</span>"

def addFloatNumberBox(fid, value, fmin, fmax):
  global TXBuffer
  TXBuffer += "<input type='number' name='"
  TXBuffer += str(fid)
  TXBuffer += '\''
  TXBuffer += " min="
  TXBuffer += str(fmin)
  TXBuffer += " max="
  TXBuffer += str(fmax)
  TXBuffer += " step=0.01"
  TXBuffer += " style='width:5em;' value="
  TXBuffer += str(value)
  TXBuffer += '>'

def addFormFloatNumberBox(label, fid, value, fmin, fmax):
  addRowLabel(label)
  addFloatNumberBox(fid, value, fmin, fmax)

def addFormNumericBox(label, fid, value, minv=INT_MIN, maxv=INT_MAX):
  addRowLabel(label)
  addNumericBox(fid, value, minv, maxv)

def addNetType(wless):
  global TXBuffer
  if (wless):
    TXBuffer += "<img src='img/wlan.gif' width='22' alt='Wireless'>"
  else:
    TXBuffer += "<img src='img/lan.gif' width='22' alt='Wired'>"

def getControllerSymbol(indexs):
  ret = "<p style='font-size:20px'>&#"
  ret += str(10102+int(indexs))
  ret += ";</p>"
  return ret

def getValueSymbol(indexs):
  ret += "&#"
  ret += str(10112+int(indexs))
  ret += ";"
  return ret

def getWebPageTemplateDefault(tmplName):
  tmpl = ""
  if (tmplName == "TmplAP"):
    tmpl = (
              "<!DOCTYPE html><html lang='en'>"
              "<head>"
              "<meta charset='utf-8'/>"
              "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
              "<title>{{name}}</title>"
              "{{css}}"
              "</head>"
              "<body>"
              "<header class='apheader'>"
              "<h1>Welcome to RPI Easy AP</h1>"
              "</header>"
              "<section>"
              "<span class='message error'>"
              "{{error}}"
              "</span>"
              "{{content}}"
              "</section>"
              "<footer>"
                "<br>"
                "<h6>Made by <a href='http://bitekmindenhol.blog.hu' style='font-size: 15px; text-decoration: none'>NS Tech</a>. - Designed by <a href='http://www.letscontrolit.com' style='font-size: 15px; text-decoration: none'>www.letscontrolit.com</a></h6>"
              "</footer>"
              "</body>")
  elif (tmplName == "TmplMsg"):
    tmpl = (
              "<!DOCTYPE html><html lang='en'>"
              "<head>"
              "<meta charset='utf-8'/>"
              "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
              "<title>{{name}}</title>"
              "{{css}}"
              "</head>"
              "<body>"
              "<header class='headermenu'>"
              "<h1>RPI Easy: {{name}}</h1><div class='menu_button'>&#9776;</div><BR>"
              "</header>"
              "<section>"
              "<span class='message error'>"
              "{{error}}"
              "</span>"
              "{{content}}"
              "</section>"
              "<footer>"
                "<br>"
                "<h6>Made by <a href='http://bitekmindenhol.blog.hu' style='font-size: 15px; text-decoration: none'>NS Tech</a>. - Designed by <a href='http://www.letscontrolit.com' style='font-size: 15px; text-decoration: none'>www.letscontrolit.com</a></h6>"
              "</footer>"
              "</body>")
  elif (tmplName == "TmplDsh"):
    tmpl = (
      "<!DOCTYPE html><html lang='en'>"
      "<head>"
        "<meta charset='utf-8'/>"
        "<title>{{name}}</title>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "{{js}}"
        "{{css}}"
        "</head>"
        "<body>"
        "{{content}}"
        "</body></html>"
            )
  else:   #//all other template names e.g. TmplStd
#    print("tmplstd")
    tmpl = ( "<!DOCTYPE html><html lang='en'>"
	"<head>"
        "<meta charset='utf-8'/>"
        "<title>{{name}}</title>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "{{js}}"
        "{{css}}"
      "</head>"
      "<body class='bodymenu'>"
        "<span class='message' id='rbtmsg'></span>"
        "<header class='headermenu'>"
          "<h1>RPI Easy: {{name}} {{logo}}</h1><div class='menu_button'>&#9776;</div><BR>"
          "{{menu}}"
        "</header>"
        "<section>"
        "<span class='message error'>"
        "{{error}}"
        "</span>"
        "{{content}}"
        "</section>"
        "<footer>"
          "<br>"
          "<h6>Made by <a href='http://bitekmindenhol.blog.hu' style='font-size: 15px; text-decoration: none'>NS Tech</a>. - Designed by <a href='http://www.letscontrolit.com' style='font-size: 15px; text-decoration: none'>www.letscontrolit.com</a></h6>"
        "</footer>"
      "</body></html>"
            )
  return tmpl

def getWebPageTemplateVar( varName ):
  global TXBuffer, navMenuIndex
  if (varName == "name"):
    TXBuffer += Settings.Settings["Name"]
  elif (varName == "unit"):
    TXBuffer += str(Settings.Settings["Unit"])
  elif (varName == "menu"):
    TXBuffer += "<div class='menubar'>"
    for i in range(len(rpieGlobals.gpMenu)):
      TXBuffer += "<a class='menu"
      if (i == navMenuIndex):
        TXBuffer += " active"
      TXBuffer += "' href='"
      TXBuffer += rpieGlobals.gpMenu[i][1]
      TXBuffer += "'>"
      TXBuffer += rpieGlobals.gpMenu[i][0]
      TXBuffer += "</a>"
    TXBuffer += "</div>"

  elif (varName == "logo"):
    pass
#    if (os.path.isfile("./rpi.png")):
#      TXBuffer += "<img src=\"rpi.png\" width=48 height=48 align=right>"

  elif (varName == "css"):
    if (os.path.isfile("./default.css")):
      TXBuffer += "<link rel=\"stylesheet\" type=\"text/css\" href=\"default.css\">"

  elif (varName == "js"):
    TXBuffer += (
                  "<script><!--\n"
                  "function dept_onchange(frmselect) {frmselect.submit();}"
                  "\n//--></script>")
  else:
    log = "Templ: Unknown Var : "
    log += varName
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, log)

def sendHeadandTail(tmplName, Tail = False):
  global TXBuffer
  pageTemplate = ""
  fileName = tmplName
  fileName += ".html"

  if (os.path.isfile(fileName)):
   with open(fileName) as content_file:
    pageTemplate = content_file.read()
  else:
    pageTemplate = getWebPageTemplateDefault(tmplName)

  if (Tail):
    contentpos = pageTemplate.find("{{content}}")
    TXBuffer += pageTemplate[11+contentpos:]
  else:
    indexStart = pageTemplate.find("{{")
    while (indexStart >= 0):
      TXBuffer += pageTemplate[0:indexStart]
      pageTemplate = pageTemplate[indexStart:]
      indexEnd = pageTemplate.find("}}")
      if (indexEnd > 0):
        varName = pageTemplate[2:indexEnd]
        pageTemplate = pageTemplate[(indexEnd + 2):]
        varName = varName.lower()

        if (varName == "content"): # is var == page content?
          break #;  // send first part of result only
        elif (varName == "error"):
          getErrorNotifications()
        else:
          getWebPageTemplateVar(varName)
      else:
        pageTemplate = pageTemplate[2:]
      indexStart = pageTemplate.find("{{")

def getErrorNotifications():
 return False

@WebServer.route('/update')
def handle_update(self):
 global TXBuffer, navMenuIndex
 try:
  import lib.lib_update as Updater
 except Exception as e:
  print(e)
  return False

 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn(self.get,self.cookie)):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 if Settings.UpdateString != "": # custom string provided
  if Settings.UpdateString[0] == "!": #update in progress
   TXBuffer += "<center><img src='img/loading.gif'></center>"
   TXBuffer += "<p style='font-size:24px;font-weight:bold;text-align:center'>"+Settings.UpdateString[1:]+"</p>"

   TXBuffer += '<script type="text/javascript">var rtimer; function refreshpage() {window.location.reload(true);}</script>'
   TXBuffer += "<script defer>rtimer = setInterval(refreshpage,10000);</script>"
  elif Settings.UpdateString[0] == "=": #update ended
   TXBuffer += "<form>"
   TXBuffer += "<br><p style='font-size:24px;font-weight:bold;text-align:center'>"+Settings.UpdateString[1:]+"</p>"
   if ("dependency" in Settings.UpdateString):
    addWideButton("plugins", "Back to dependency page", "")
   else:
    addWideButton("update", "Back to update page", "")
   Settings.UpdateString = ""
  else:
   TXBuffer += Settings.UpdateString
   Settings.UpdateString = ""
 else:
  if self.type == "GET":
   responsearr = self.get
  else:
   responsearr = self.post
  updmode = arg("mode",responsearr)

  if updmode == "":
   TXBuffer += "<form><table class='normal'>"
   addFormHeader("Update")

   html_TR_TD_height(30)
   addWideButton("update?mode=rpi", "RPIEasy git update", "")
   TXBuffer += "<TD>"
   TXBuffer += "Update RPIEasy from GIT (restart will not work, unless autostart enabled at Hardware menu!)"

   html_TR_TD_height(30)
   addWideButton("update?mode=apt", "APT update", "")
   TXBuffer += "<TD>"
   TXBuffer += "Update and upgrade OS"

   html_TR_TD_height(30)
   addWideButton("update?mode=pip", "PIP update", "")
   TXBuffer += "<TD>"
   TXBuffer += "Update and upgrade Python libraries"

   TXBuffer += "</table></form>"
  else:
   if updmode == "rpi":
    t = threading.Thread(target=Updater.upgrade_rpi)
    t.daemon = True
    t.start()
   elif updmode == "pip":
    t = threading.Thread(target=Updater.update_pip)
    t.daemon = True
    t.start()
   elif updmode == "pipupgrade":
    packages = []
    for r in responsearr:
     if r[:2] == "p_":
      packages.append(arg(r,responsearr))
    t = threading.Thread(target=Updater.upgrade_pip, args=(packages,))
    t.daemon = True
    t.start()
   elif updmode == "apt":
    t = threading.Thread(target=Updater.update_apt)
    t.daemon = True
    t.start()
   elif updmode == "aptupgrade":
#    print("apt upgrade")#debug
    t = threading.Thread(target=Updater.upgrade_apt)
    t.daemon = True
    t.start()
   time.sleep(0.5)
   return self.redirect('/update')
#   TXBuffer += '<script type="text/javascript">var rtimer; function refreshpage() {window.location.reload(true);}</script>'
#   TXBuffer += "<script defer>rtimer = setInterval(refreshpage,1000);</script>"
 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer
