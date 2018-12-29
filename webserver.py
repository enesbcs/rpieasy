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
from datetime import datetime
import rpieTime
import linux_os as OS
import misc
import commands
import linux_network as Network
import urllib

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

def isLoggedIn():
#  if (not clientIPallowed()) return False
  if (Settings.Settings["Password"] == ""):
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
 if (not isLoggedIn()):
  return self.redirect('/login')

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 cmdline = arg("cmd",responsearr).strip()

 sendHeadandTail("TmplStd",_HEAD)

 responsestr = ""
 if len(cmdline)>0:
  responsestr = str(commands.doExecuteCommand(cmdline))  # response ExecuteCommand(VALUE_SOURCE_HTTP, webrequest.c_str());
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
 TXBuffer += "<TR><TD>Wifi RSSI:<TD>" + str( OS.get_rssi() ) + " dB"
 TXBuffer += "<TR><TD><TD>"
 addButton("sysinfo", "More info");
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

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/config')
def handle_config(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=1
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
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
  if "**" not in tpw:
   Settings.Settings["Password"]  = tpw
# ...
  Settings.savesettings()
#  time.sleep(0.1)
  if Settings.NetMan:
   Settings.NetMan.APMode = arg("apmode",responsearr)
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
  Settings.savenetsettings()     # save to json
 else:
  Settings.loadsettings() 

 sendHeadandTail("TmplStd",_HEAD); 

 TXBuffer += "<form name='frmselect' method='post'><table class='normal'>"
 addFormHeader("Main Settings")

 addFormTextBox( "Unit Name", "name", Settings.Settings["Name"], 25)
 
 addFormNumericBox( "Unit Number", "unit", Settings.Settings["Unit"], 0, 9999)
# addFormPasswordBox( "Admin Password" , "password", Settings.Settings["Password"], 25)   # Not implemented MISSING!

# addFormCheckBox("AP Mode enable on connection failure","apmode",Settings.NetMan.APMode) # Not implemented MISSING!
# addFormPasswordBox("WPA AP Mode Key", "apkey", Settings.NetMan.WifiAPKey, 128)          # Not implemented MISSING!
 TXBuffer += "<TR><TD style='width:150px;' align='left'><TD>"
 addSubmitButton()

 oslvl = misc.getsupportlevel(1)
 if oslvl in [1,10]: # maintain supported system list!!!
  addFormSeparator(2)
  addFormCheckBox("I have root rights and i really want to manage network settings below","netman", netmanage)
  addFormNote("<font color=red><b>If not enabled, OS config files will not be overwritten!</b></font>")
 
  addFormSubHeader("Wifi Settings") #/etc/wpa_supplicant/wpa_supplicant.conf
  addFormTextBox( "SSID", "ssid", Settings.NetMan.WifiSSID, 64)
  addFormPasswordBox("WPA Key", "key", Settings.NetMan.WifiKey, 128)
  addFormTextBox( "Fallback SSID", "ssid2", Settings.NetMan.WifiSSID2, 64)
  addFormPasswordBox( "Fallback WPA Key", "key2", Settings.NetMan.WifiKey2, 128)
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
 addSubmitButton()
 TXBuffer += "</table></form>"
  
 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/controllers')
def handle_controllers(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=2
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 

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
 enabled = arg("controllerenabled",responsearr)

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
#      try:
      Settings.Controllers[controllerindex].webform_load()
#      except:
#       pass

    addFormSeparator(2)
    TXBuffer += "<tr><td><td>"
    TXBuffer += "<a class='button link' href=\"controllers\">Close</a>"
    addSubmitButton()
    if controllerindex != '':
     addSubmitButton("Delete", "del")
    TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/hardware')
def handle_hardware(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 suplvl = misc.getsupportlevel()
 if suplvl[0] != "N":
  ar = OS.autorun()
  ar.readconfig()

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 submit = arg("Submit",responsearr)

 if (submit=="Submit") and (suplvl[0] != "N"):
  stat = arg("rpiauto",responsearr)
  if stat=="on":
   ar.rpiauto=True
  else:
   ar.rpiauto=False
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

 TXBuffer += "<form name='frmselect' method='post'><table class='normal'><tr><TH style='width:150px;' align='left' colspan=2>System"
 TXBuffer += "<TR><TD>Type:<TD>"+suplvl
 if suplvl[0] != "N":
  TXBuffer += "<TR><TD>OS:<TD>"+str(rpieGlobals.osinuse)+" "+str(misc.getosname(1))
 if suplvl[0] == "L":
  TXBuffer += "<TR><TD>OS full name:<TD>"+str(OS.getosfullname())
  TXBuffer += "<TR><TD>Hardware:<TD>"+str(OS.gethardware())
 if suplvl[0] == "R":
  rpv = OS.getRPIVer()
  if len(rpv)>1:
   TXBuffer += "<TR><TD>Hardware:<TD>"+rpv["name"]+" "+rpv["ram"]
 if suplvl[0] != "N":
  addFormSeparator(2)
  racc = OS.check_permission()
  rstr = str(racc)
  if racc == False:
   rstr = "<font color=red>"+rstr+"</font> (system-wide settings are only for root)"
  TXBuffer += "<TR><TD>Root access:<TD>"+rstr
  TXBuffer += "<TR><TD>Sound playback device:<TD>"
  sounddevs = OS.getsounddevs()
  defaultdev = OS.getsoundsel()
  if len(sounddevs)>0: 
   addSelector_Head('snddev',False)
   for i in range(0,len(sounddevs)):    
    addSelector_Item(sounddevs[i][1],int(sounddevs[i][0]),(int(sounddevs[i][0])==int(defaultdev)),False)
   addSelector_Foot()
  else:
   TXBuffer += "No device"

  addFormCheckBox("RPIEasy autostart at boot","rpiauto",ar.rpiauto)
  if OS.checkRPI():
   addFormCheckBox("Enable HDMI at startup","hdmienabled",ar.hdmienabled)
  if OS.check_permission():
   TXBuffer += "<tr><td colspan=2>"
   addSubmitButton()

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
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 try:
  import gpios
 except:
  print("Unable to load GPIO support")

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 submit = arg("Submit",responsearr)
 setbtn = arg("set",responsearr).strip()

 if arg("reread",responsearr) != '':
  submit = ''
  gpios.HWPorts.readconfig()
 
 if (submit=="Submit") or (setbtn!=''):
  stat = arg("i2c0",responsearr)
  if stat=="on":
   gpios.HWPorts.enable_i2c(0)
  else:
   gpios.HWPorts.disable_i2c(0)
  stat = arg("i2c1",responsearr)
  if stat=="on":
   gpios.HWPorts.enable_i2c(1)
  else:
   gpios.HWPorts.disable_i2c(1)

  stat = arg("spi0",responsearr)
  if stat=="on":
   gpios.HWPorts.enable_spi(0,2)
  else:
   gpios.HWPorts.disable_spi(0)

  stat = int(arg("spi1",responsearr).strip())
  if stat == 0:
   gpios.HWPorts.disable_spi(1)
  else:
   gpios.HWPorts.enable_spi(1,stat)

  stat = arg("uart",responsearr)
  if stat=="on":
   gpios.HWPorts.set_serial(1)
  else:
   gpios.HWPorts.set_serial(0)
  stat = arg("audio",responsearr)
  if stat=="on":
   gpios.HWPorts.set_audio(1)
  else:
   gpios.HWPorts.set_audio(0)
  stat = arg("i2s",responsearr)
  if stat=="on":
   gpios.HWPorts.set_i2s(1)
  else:
   gpios.HWPorts.set_i2s(0)

  try:
   stat = int(arg("bluetooth",responsearr).strip())  
  except:
   stat=0
  gpios.HWPorts.set_internal_bt(stat)
  stat = arg("wifi",responsearr)
  if stat=="on":
   gpios.HWPorts.set_wifi(1)
  else:
   gpios.HWPorts.set_wifi(0)

  try:
   stat = int(arg("gpumem",responsearr).strip())
  except:
   stat=16
  gpios.HWPorts.gpumem = stat

  for p in range(len(Settings.Pinout)):
   pins = arg("pinstate"+str(p),responsearr)
   if pins:
    gpios.HWPorts.setpinstate(p,int(pins))

  if OS.check_permission() and setbtn=='':
   gpios.HWPorts.saveconfig()
  Settings.savepinout()

 if (len(Settings.Pinout)>1):
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
     if Settings.Pinout[p]["canchange"]==1 and pinfunc in [0,1]:
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
  addFormSeparator(2)
  TXBuffer += "<tr><td colspan=2>"
  if OS.check_permission():
   addSubmitButton()
  addSubmitButton("Set without save","set")
  addSubmitButton("Reread config","reread")
  TXBuffer += "</td></tr>"
  addFormNote("WARNING: Some changes needed to reboot after submitting changes! And most changes requires root permission.")
  addHtml("</table></form>")
 else:
  addHtml('This hardware is currently not supported!')

 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.route('/plugins')
def handle_plugins(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 

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
  plugindeps.installdeps(moduletoinstall)

 if OS.check_permission()==False:
   TXBuffer += "Installation WILL NOT WORK without root permission!<p>"

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
      TXBuffer += "NOT Supported"
      usable = False
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
 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/devices')
#@WebServer.get('/devices')
def handle_devices(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=4
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 

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
    pass
  if ttid != -1:
   Settings.Tasks[taskIndex].plugin_exit()
   taskIndexNotSet = True
   Settings.Tasks[taskIndex] = False
   Settings.savetasks() # savetasksettings!!!
 if taskIndexNotSet: # show all tasks as table
    if True:
     TXBuffer += "<script> (function(){ var max_tasknumber = "+ str(rpieGlobals.TASKS_MAX) +"; var max_taskvalues = "+ str(rpieGlobals.VARS_PER_TASK) +"; var timeForNext = 2000; var c; var k; var err = ''; var i = setInterval(function(){ var url = '/json?view=sensorupdate';"
     TXBuffer += "	fetch(url).then( function(response) {  if (response.status !== 200) { console.log('Looks like there was a problem. Status Code: ' +  response.status); return; } response.json().then(function(data) {"
     TXBuffer += "	timeForNext = data.TTL; for (c = 0; c < max_tasknumber; c++) { for (k = 0; k < max_taskvalues; k++) { try {	valueEntry = data.Sensors[c].TaskValues[k].Value; }	catch(err) { valueEntry = err.name;	}"
     TXBuffer += "	finally {if (valueEntry !== 'TypeError') {"
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
       TXBuffer += "<TD>"
       TXBuffer += str(x + 1)
       TXBuffer += "<TD>"
       
       if (len(Settings.Tasks)>x) and (Settings.Tasks[x]):
        addEnabled(Settings.Tasks[x].enabled)

        TXBuffer += "<TD>"
        TXBuffer += Settings.Tasks[x].getdevicename()
        TXBuffer += "<TD>"
        TXBuffer += Settings.Tasks[x].gettaskname()
        TXBuffer += "<TD>"

        customConfig = False;
        #customConfig = PluginCall(PLUGIN_WEBFORM_SHOW_CONFIG, &TempEvent,TXBuffer.buf);
        if not(customConfig):
          if (Settings.Tasks[x].ports != 0):
            TXBuffer += str(Settings.Tasks[x].taskdeviceport)

        TXBuffer += "<TD>"

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

        if (Settings.Tasks[x].dtype == rpieGlobals.DEVICE_TYPE_I2C):
            i2cpins = Settings.get_i2c_pins()
            TXBuffer += i2cpins[0]
            TXBuffer += "<BR>"+i2cpins[1]
        for tp in range(0,len(Settings.Tasks[x].taskdevicepin)):
          if int(Settings.Tasks[x].taskdevicepin[tp])>=0:
            TXBuffer += "<br>GPIO-"
            TXBuffer += str(Settings.Tasks[x].taskdevicepin[tp])
        TXBuffer += "<TD>"

        customValues = False
#        customValues = PluginCall(PLUGIN_WEBFORM_SHOW_VALUES, &TempEvent,TXBuffer.buf);
        if not(customValues):
          if (Settings.Tasks[x].vtype == rpieGlobals.SENSOR_TYPE_LONG):
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
            TXBuffer  += str(Settings.Tasks[x].uservar[0] + (Settings.Tasks[x].uservar[1] << 16))
            TXBuffer  += "</div>"
          else:
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
                if str(decimalv) == "" or int(decimalv)<0:
                 decimalv = "0"
                else:
                 decimalv = str(decimalv).strip()
                numformat = "{0:."+ decimalv + "f}"
                try:
                 TXBuffer += numformat.format(numtodisp)
                except:
                 TXBuffer += numtodisp 
                TXBuffer += "</div>"

       else:
        TXBuffer += "<TD><TD><TD><TD><TD><TD>"
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
       addSelector_Item(rpieGlobals.deviceselector[y][2],int(rpieGlobals.deviceselector[y][1]),(rpieGlobals.deviceselector[y][1]==tte),False,"")
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
       Settings.Tasks[taskIndex].taskname = tasknamestr.replace(" ","")
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
        for pins in range(0,3):
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
           tvdec = 1
          Settings.Tasks[taskIndex].decimals[varnr] = tvdec
         else:
          Settings.Tasks[taskIndex].valuenames[varnr] = ""
        Settings.Tasks[taskIndex].webform_save(responsearr) # call plugin read FORM
        Settings.Tasks[taskIndex].enabled = (arg("TDE",responsearr) == "on")
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
      if (Settings.Tasks[taskIndex].ports>0) or (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_SINGLE and Settings.Tasks[taskIndex].dtype<= rpieGlobals.DEVICE_TYPE_QUAD):
        addFormSubHeader( "Sensor" if Settings.Tasks[taskIndex].senddataoption else "Actuator" )

        if (Settings.Tasks[taskIndex].ports != 0):
          addFormNumericBox("Port", "TDP", Settings.Tasks[taskIndex].taskdeviceport)
#        if (Settings.Tasks[taskIndex].pullupoption):
#          addFormCheckBox("Internal PullUp", "TDPPU", Settings.Tasks[taskIndex].pullup)
        if (Settings.Tasks[taskIndex].inverselogicoption):
          addFormCheckBox("Inversed Logic", "TDPI", Settings.Tasks[taskIndex].pininversed)
        if (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_SINGLE and Settings.Tasks[taskIndex].dtype<=rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("1st GPIO", "taskdevicepin1", Settings.Tasks[taskIndex].taskdevicepin[0])
        if (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_DUAL and Settings.Tasks[taskIndex].dtype<=rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("2nd GPIO", "taskdevicepin2", Settings.Tasks[taskIndex].taskdevicepin[1])
        if (Settings.Tasks[taskIndex].dtype>=rpieGlobals.DEVICE_TYPE_TRIPLE and Settings.Tasks[taskIndex].dtype<=rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("3rd GPIO", "taskdevicepin3", Settings.Tasks[taskIndex].taskdevicepin[2])
        if (Settings.Tasks[taskIndex].dtype==rpieGlobals.DEVICE_TYPE_QUAD):
          addFormPinSelect("4th GPIO", "taskdevicepin4", Settings.Tasks[taskIndex].taskdevicepin[3])

      try:
       Settings.Tasks[taskIndex].webform_load() # call plugin function to fill TXBuffer
      except Exception as e:
       print(e)

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
        addFormNumericBox( "Interval", "TDT", Settings.Tasks[taskIndex].interval, 0, 65535)
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
            addTextBox(sid, Settings.Tasks[taskIndex].formula[varNr], 40)

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
    TXBuffer += "<input type='hidden' name='page' value='1'>"

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
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 

 addHtml('Notifications page')
 TXBuffer+="<p>Work in progress!"
 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/log')
def handle_log(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 

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

 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/tools')
def handle_tools(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post

 webrequest = arg("cmd",responsearr)

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
  responsestr = str(commands.doExecuteCommand(webrequest))  # response ExecuteCommand(VALUE_SOURCE_WEB_FRONTEND, webrequest.c_str());
 if len(responsestr)>0:
  TXBuffer += "<TR><TD colspan='2'>Command Output<BR><textarea readonly rows='10' wrap='on'>"
  TXBuffer += str(responsestr)
  TXBuffer += "</textarea>"

 addFormSubHeader("System")

 html_TR_TD_height(30)
 TXBuffer += "<a class='button link wide' onclick="
 TXBuffer += '"'
 TXBuffer += "return confirm('Do you really want to Reboot device?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=reboot'>Reboot</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Reboots Device"

 html_TR_TD_height(30)
 TXBuffer += "<a class='button link wide' onclick="
 TXBuffer += '"'
 TXBuffer += "return confirm('Do you really want to Shutdown machine?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=halt'>Halt</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Halts Device"

 html_TR_TD_height(30)
 TXBuffer += "<a class='button link wide' onclick="
 TXBuffer += '"'
 TXBuffer += "return confirm('Do you really want to exit RPIEasy application?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=exit'>Exit</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Exit from RPIEasy"

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
 
 html_TR_TD_height(30);
 addWideButton("sysvars", "System Variables", "")
 TXBuffer += "<TD>"
 TXBuffer += "Show all system variables"

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
 TXBuffer += "return confirm('Do you really want to Reset all settings?')"
 TXBuffer += '"'
 TXBuffer += " href='/?cmd=reset'>Reset device settings</a>"
 TXBuffer += "<TD>"
 TXBuffer += "Erase all JSON settings files"

 TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/i2cscanner')
def handle_i2cscanner(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)
 try:
  import gpios
 except Exception as e:
  TXBuffer += str(e)
  return TXBuffer

 TXBuffer += "<table class='multirow' border=1px frame='box' rules='all'><TH>I2C Addresses in use<TH>Supported devices</th></tr>"
 i2cenabled = 0
 i2cdevs = 0
 for i in range(0,2):
   if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
    i2cenabled += 1
    addFormSubHeader("I2C-"+str(i))
    TXBuffer += "</td></tr>"
    i2cl = gpios.is_i2c_lib_available()
    if i2cl:
     i2ca = gpios.i2cscan(i)
     for d in range(len(i2ca)):
      i2cdevs += 1
      TXBuffer += "<TR><TD>"+str(hex(i2ca[d]))+"</td><td>"
      TXBuffer += str(gpios.geti2cdevname(i2ca[d])).replace(";","<br>")
      TXBuffer += "</td></tr>"
    else:
     TXBuffer += "<tr><td colspan=2>I2C supporting SMBus library not found. Please install <a href='plugins?installmodule=i2c'>smbus</a>.</td></tr>"
 if i2cenabled==0:
  TXBuffer += "<tr><td colspan=2>Usable I2C bus not found</td></tr>"
 elif i2cdevs==0:
  TXBuffer += "<tr><td colspan=2>No device found on I2C bus</td></tr>"
 TXBuffer += "</table>"
 sendHeadandTail("TmplStd",_TAIL);
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
 if (not isLoggedIn()):
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
 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/blescanner') 
def handle_blescanner(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=3
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD)

 blesupported = True
 try: 
  from bluepy.btle import Scanner
 except:
  blesupported = False
 if blesupported:
    if OS.check_permission()==False:
     TXBuffer += "Scanning does not work properly without root permission!<p>"
    blesuccess = True
    try:
     scanner = Scanner()
     devices = scanner.scan(5.0)
    except Exception as e:
     TXBuffer += "BLE scanning failed "+str(e)+"<p>"
     blesuccess = False
    if blesuccess:
     TXBuffer += "<table class='multirow'><TR><TH>Interface<TH>Address<TH>Address type<TH>RSSI<TH>Connectable<TH>Name<TH>Appearance</TH></TR>"
     for dev in devices:
      TXBuffer += "<TR><TD>"+str(dev.iface)+"<TD>"+str(dev.addr)+"<TD>"+str(dev.addrType)+"<TD>"+str(dev.rssi)+" dBm<TD>"+str(dev.connectable)
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
      TXBuffer += "<TD>"+str(dname)+"<TD>"+str(appear)+"</TR>"
     TXBuffer += "</table>"
 else:
    TXBuffer += "BLE supporting library not found! Please install <a href='plugins?installmodule=bluepy'>bluepy</a>"

 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/login')
def handle_login(self):
 global TXBuffer
 TXBuffer=""
 addHtml('Login page')
 return TXBuffer

@WebServer.route('/control')
def handle_control(self):
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 webrequest = arg("cmd",responsearr)
 if len(webrequest)>0:
  responsestr = str(commands.doExecuteCommand(webrequest))
 return "OK"

@WebServer.route('/advanced')
def handle_advanced(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
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
   Settings.AdvSettings["battery"]["enabled"] = (arg("battery_mon",responsearr)=="on")
   Settings.AdvSettings["battery"]["tasknum"] = int(arg("battery_task",responsearr))
   Settings.AdvSettings["battery"]["taskvaluenum"] = int(arg("battery_valuenum",responsearr))
  except:
   Settings.AdvSettings["battery"] = {"enabled":False,"tasknum":0,"taskvaluenum":0}
  Settings.saveadvsettings()

 TXBuffer += "<form  method='post'><table class='normal'>"
 addFormHeader("Advanced Settings")
 addFormSubHeader("Log Settings")

 addFormLogLevelSelect("Console log Level","consoleloglevel", Settings.AdvSettings["consoleloglevel"]);
 addFormLogLevelSelect("Web log Level",    "webloglevel",     Settings.AdvSettings["webloglevel"]);

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
 sendHeadandTail("TmplStd",_TAIL);
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
 if (not isLoggedIn()):
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
   TXBuffer += '","Uptime":'+str(rpieTime.getuptime(0))
   TXBuffer += ',"Load":'+str(OS.read_cpu_usage())
   TXBuffer += ',"Free RAM":'+str(OS.FreeMem())
   TXBuffer += "},"
  if showwifi:
   TXBuffer += '"WiFi":{'
   defaultdev = -1
   try:
    defaultdev = Settings.NetMan.getprimarydevice()
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
  senstop = senstart
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
     try:
      ival = int(Settings.Tasks[sc].uservar[tv])
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

@WebServer.route('/rules')
def handle_rules(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=5
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 

 if self.type == "GET":
  responsearr = self.get
 else:
  responsearr = self.post
 rules = ""
 saved = arg("Submit",responsearr)
 if (saved):
  rules = arg("rules",responsearr)
  if rules!="":
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

 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/sysvars')
def handle_rules(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 
 TXBuffer += "<table class='normal'><TR><TH align='left'>System Variables<TH align='left'>Normal"
 for sv in commands.SysVars:
  TXBuffer += "<TR><TD>%" + sv + "%</TD><TD>"
  TXBuffer += str(commands.getglobalvar(sv)) + "</TD></TR>"
 TXBuffer += "</table></form>"

 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/sysinfo')
def handle_sysinfo(self):
 import platform, sys
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
  return self.redirect('/login')
 sendHeadandTail("TmplStd",_HEAD); 
 TXBuffer += "<table class='normal'><TR><TH style='width:150px;' align='left'>System Info<TH align='left'>"

 TXBuffer += "<TR><TD>Unit:<TD>"
 TXBuffer += str(Settings.Settings["Unit"])
 TXBuffer += "<TR><TD>Local Time:<TD>" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
 TXBuffer += "<TR><TD>Uptime:<TD>" + rpieTime.getuptime(1)
 TXBuffer += "<TR><TD>Load:<TD>" +str( OS.read_cpu_usage() ) + " %"
 TXBuffer += "<TR><TD>Free Mem:<TD>" + str( OS.FreeMem() ) + " kB"
 addTableSeparator("Network", 2, 3)
 TXBuffer += "<TR><TD>Wifi RSSI:<TD>" + str( OS.get_rssi() ) + " dB"
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

 if suplvl[0] == "R":
  rpv = OS.getRPIVer()
  if len(rpv)>1:
   TXBuffer += "<TR><TD>Hardware:<TD>"+rpv["name"]+" "+rpv["ram"]
 if suplvl[0] != "N":
  racc = OS.check_permission()
  rstr = str(racc)
  TXBuffer += "<TR><TD>Root access:<TD>"+rstr

 TXBuffer += "</table>"
 sendHeadandTail("TmplStd",_TAIL);
 return TXBuffer

@WebServer.route('/filelist')
def handle_filelist(self):
 global TXBuffer, navMenuIndex
 TXBuffer=""
 navMenuIndex=7
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
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
  sendHeadandTail("TmplDsh",_HEAD); 
  sfile="&o="+str(retobj)
  TXBuffer += "<script type='text/javascript'>function reportbackfilename(objname,fname){var retval = window.opener.document.getElementById(objname); retval.value = fname; window.close();}</script>"
 else:
  sendHeadandTail("TmplStd",_HEAD); 
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
     TXBuffer += "'>SEL</a>"
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
  sendHeadandTail("TmplDsh",_TAIL);
 else:
  addButton("upload?path="+str(current_dir), "Upload")
  sendHeadandTail("TmplStd",_TAIL); 
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

@WebServer.route('/download')
def handle_download(self):
 if (rpieGlobals.wifiSetup):
  return self.redirect('/setup')
 if (not isLoggedIn()):
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
    print(e)
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
 if (not isLoggedIn()):
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
 TXBuffer += "<p><form enctype='multipart/form-data' method='post'><p>Upload file:<br><input type='file' name='datafile' size='200'></p><div><input class='button link' type='submit' value='Upload'><input type='hidden' name='path' value='"
 TXBuffer += upath + "'></div></form>"
 sendHeadandTail("TmplStd",_TAIL)
 return TXBuffer

@WebServer.post('/upload')
def handle_upload_post(self):
 if self.post:
  current_dir = 'files/'
  upath = arg("path",self.post).strip()
  if upath:
   if upath == "data/":
    fname = ""
    try:
     if self.post['datafile']['filename']:
      fname = "data/" + self.post['datafile']['filename'].strip()
      fout = open(fname,"wb")
      fout.write(self.post['datafile']['file'])
      fout.close()
    except:
     fname = ""
    if fname.lower().endswith(".zip"):
     OS.extractzip(fname,"data/")
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
   if self.post['datafile']['filename']:
    fname = upath + self.post['datafile']['filename'].strip()
    fout = open(fname,"wb")
    fout.write(self.post['datafile']['file'])
    fout.close()
  except Exception as e:
   print(e)
 self.redirect("filelist?chgto="+str(upath))

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
  for x in range(len(Settings.Pinout)):
   if Settings.Pinout[x]["altfunc"]==0 and Settings.Pinout[x]["canchange"]>0:
    oname = Settings.Pinout[x]["name"][0]
    if Settings.Pinout[x]["canchange"]==1:
     onum=0
     try:
      onum = int(Settings.Pinout[x]["startupstate"])
      if onum<1:
       onum=0
     except:
      pass
     oname += " ("+Settings.PinStates[onum]+")"
    addSelector_Item(oname,Settings.Pinout[x]["BCM"],(str(choice)==str(Settings.Pinout[x]["BCM"])),False,"")
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


def addCopyButton(value, delimiter, name):
  global TXBuffer
  TXBuffer += "<script>function setClipboard() { var clipboard = ''; max_loop = 100; for (var i = 1; i < max_loop; i++){ var cur_id = '"
  TXBuffer += str(value)
  TXBuffer += "_' + i; var test = document.getElementById(cur_id); if (test == null){ i = max_loop + 1;  } else { clipboard += test.innerHTML.replace(/<[Bb][Rr]\\s*\\/?>/gim,'\\n') + '"
  TXBuffer += str(delimiter)
  TXBuffer += "'; } }"
  TXBuffer += "clipboard = clipboard.replace(/<\\/[Dd][Ii][Vv]\\s*\\/?>/gim,'\\n');"
  TXBuffer += "clipboard = clipboard.replace(/<[^>]*>/gim,'');"
  TXBuffer += "var tempInput = document.createElement('textarea'); tempInput.style = 'position: absolute; left: -1000px; top: -1000px'; tempInput.innerHTML = clipboard;"
  TXBuffer += "document.body.appendChild(tempInput); tempInput.select(); document.execCommand('copy'); document.body.removeChild(tempInput); alert('Copied: \"' + clipboard + '\" to clipboard!') }</script>"
  TXBuffer += "<button class='button link' onclick='setClipboard()'>"
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
  TXBuffer += "</H";
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
  addRowLabel(label);
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
  addRowLabel(label);
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
  #int indexStart, indexEnd;
  #String varName;  //, varValue;
  fileName = tmplName;
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
        varName.lower();

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
