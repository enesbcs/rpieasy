#!/usr/bin/env python3
#############################################################################
################## Serial Fingerprint plugin for RPIEasy ####################
#############################################################################
#
# Plugin for serial Fingerprint Module reading
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
from pyfingerprint.pyfingerprint import PyFingerprint
import lib.lib_serial as rpiSerial
import hashlib
import webserver
import Settings

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 208
 PLUGIN_NAME = "ID - Serial Fingerprint Module (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "ID"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SER
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self.fp = None
  self.readinprogress=0
  self.initialized=False

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = rpiSerial.serial_portlist()
  if len(options)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p208_addr",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
   webserver.addFormNote("Address of the FPM serial port")
  else:
   webserver.addFormNote("No serial ports found")
  options = ["None", "Valid", "Position","SHA2"]
  optionvalues = [0, 1, 2,3]
  webserver.addFormSelector("Indicator1","plugin_208_ind0",len(options),options,optionvalues,None,self.taskdevicepluginconfig[1])
  webserver.addFormSelector("Indicator2","plugin_208_ind1",len(options),options,optionvalues,None,self.taskdevicepluginconfig[2])
  webserver.addFormSelector("Indicator3","plugin_208_ind2",len(options),options,optionvalues,None,self.taskdevicepluginconfig[3])
  if self.enabled and self.initialized:
   try:
    webserver.addFormNote("Stored fingerprints: "+ str(self.fp.getTemplateCount())+"/"+str(self.fp.getStorageCapacity()))
   except:
    pass
  webserver.addHtml("<tr><td><a href='/finger'>Management page</a>")
  return True

 def webform_save(self,params): # process settings post reply
  try:
   self.taskdevicepluginconfig[0] = str(webserver.arg("p208_addr",params)).strip()
   for v in range(0,3):
    par = webserver.arg("plugin_208_ind"+str(v),params)
    if par == "":
     par = -1
    else:
     par=int(par)
    if str(self.taskdevicepluginconfig[v+1])!=str(par):
     self.uservar[v] = 0
    self.taskdevicepluginconfig[v+1] = par
    if int(par)>0 and self.valuecount!=v+1:
     self.valuecount = (v+1)
   if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
   elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
   elif self.valuecount == 3:
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.taskdevicepluginconfig[0] = str(self.taskdevicepluginconfig[0]).strip()
  self.readinprogress=0
  self.initialized=False
  if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  elif self.valuecount == 3:
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  if self.enabled and self.taskdevicepluginconfig[0]!="" and self.taskdevicepluginconfig[0]!="0":
   time.sleep(0.5)
   try:
    if self.fp is not None:
     self.fp.__del__()
   except:
    pass
   try:
    time.sleep(2)
    self.fp = PyFingerprint(self.taskdevicepluginconfig[0],57600,0xFFFFFFFF,0)
    time.sleep(0.5)
    if self.fp.verifyPassword()==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"FPM password wrong")
     self.fp = None
    self.initialized = True
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM initialized")
   except Exception as e:
    self.fp = None
    self.initialized = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"FPM init error: "+str(e))
   if self.initialized==False:
    time.sleep(3)
    self.plugin_init()

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
#  nochange = (self.interval>0)
  change = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"FPM scan")
   if self.interval>0 and self.interval<2:
    scantime = 0.8
   else:
    scantime = 2
   pos = -1
   try:
#    print("readimg") #debug
    st = time.time()
    readok = True
    while (self.fp.readImage() == False):
     if time.time()-st>=scantime:
      readok = False
      break
    self.fp.convertImage(0x01)
    result = self.fp.searchTemplate()
    pos = result[0]
    score = result[1]
   except Exception as e:
    pass
   value = "0"
   if readok:
    for v in range(0,3):
     vtype = int(self.taskdevicepluginconfig[v+1])
     if vtype == 1:
      if pos>-1:
       value = 1
      else:
       value = 0
     elif vtype == 2:
      value = pos
     elif vtype == 3:
      if pos>-1:
       value = "0"
       try:
        self.fp.loadTemplate(pos,0x01)
        chars = str(self.fp.downloadCharacteristics(0x01)).encode('utf-8')
        value = hashlib.sha256(chars).hexdigest()
       except:
        value = "0"
     if vtype in [1,2,3]:
      if str(self.uservar[v]) != str(value):
       self.set_value(v+1,value,False)
       change = True
   if change:
    self.plugin_senddata()
   if readok==False and self.interval==0:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"FPM read failed")
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

@webserver.WebServer.route('/finger')
def handle_fpm(self):
  webserver.navMenuIndex=4
  if (not webserver.isLoggedIn(self.get,self.cookie)):
    return self.redirect('/login')
  webserver.TXBuffer=""
  fpm = None
  options = []
  optionvalues = []
  for x in range(0,len(Settings.Tasks)):
    if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool:
     try:
      if Settings.Tasks[x].enabled:
       if Settings.Tasks[x].pluginid==208:
        optionvalues.append(x)
        options.append(str(x)+" / "+Settings.Tasks[x].gettaskname())
     except:
      pass
  if self.type == "GET":
    responsearr = self.get
  else:
    responsearr = self.post
#  print(optionvalues,options) # debug
  if len(optionvalues)>0:
   ftask = webserver.arg('fptask',responsearr)
   if str(ftask)!="":
    ftask = int(ftask)
    if ftask>-1:
     fpm = Settings.Tasks[ftask]
   else:
    ftask = optionvalues[0]
    fpm = Settings.Tasks[ftask]
  if (fpm is not None) and fpm.enabled and fpm.initialized:
   try:
    ffree = int(webserver.arg('ffree',responsearr))
   except:
    ffree = -1
   try:
    fpnum = int(webserver.arg('fpnum',responsearr))
   except:
    fpnum = ""
   try:
    add = webserver.arg('add',responsearr)
   except:
    add = ""
   try:
    fsearch = webserver.arg('search',responsearr)
   except:
    fsearch = ""
   try:
    fdel = webserver.arg('fdel',responsearr)
   except:
    fdel = ""
   try:
    fdelall = webserver.arg('fdelall',responsearr)
   except:
    fdelall = ""
   try:
    if add!="":
     readok = True
     st = time.time()
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM enroll, place your finger onto the scanner")
     time.sleep(0.5)
     while (fpm.fp.readImage() == False):
      if time.time()-st>=4:
       readok = False
       break
     if readok:
      fpm.fp.convertImage(0x01)
      result = fpm.fp.searchTemplate()
      posnum = result[0]
      if (posnum>=0):
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"FPM template already exists")
      else:
       fpm.fp.convertImage(0x02)
       fpm.fp.createTemplate()
       if ffree>-1:
        posnum = ffree
       else:
        posnum = fpm.fp.getTemplateCount()
       if (fpm.fp.storeTemplate(posnum) == True):
        misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM template "+str(posnum)+" added")
       else:
        misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"FPM template "+str(posnum)+" adding returned error")
     else:
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM read failed")
    elif fsearch!="":
     readok = True
     st = time.time()
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM search, place your finger onto the scanner")
     time.sleep(0.5)
     while (fpm.fp.readImage() == False):
      if time.time()-st>=4:
       readok = False
       break
     if readok:
      fpm.fp.convertImage(0x01)
      result = fpm.fp.searchTemplate()
      posnum = result[0]
      if (posnum>=0):
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM template found at #"+str(posnum))
      else:
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM template not found")
     else:
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM read failed")
    elif fdel!="":
     if fpnum!="":
      if (fpm.fp.deleteTemplate(int(fpnum)) == True):
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM template "+str(fpnum)+" deleted")
      else:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"FPM template "+str(fpnum)+" deletion failed")
    elif fdelall!="":
     if (fpm.fp.clearDatabase() == True):
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"FPM all templates deleted")
     else:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Template database deletion failed")
   except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"FPM error: "+str(e))

   webserver.sendHeadandTail("TmplStd",webserver._HEAD)
   webserver.TXBuffer += "<form name='frmtask' method='post'><table class='normal'>"
   webserver.addFormHeader("Fingerprint Module")
   webserver.addFormSelector("Fingerprint device task","fptask",len(options),options,optionvalues,None,ftask)
   webserver.addFormSubHeader("Stored fingerprints")
   if fpm is not None:
    webserver.TXBuffer += "<TR><TH>ID<TH>SHA2<TH></TR>"
    maxv = fpm.fp.getStorageCapacity()
    fc = fpm.fp.getTemplateCount()
    if fc > maxv:
     maxv = fc
    cter = 0
    ffree = -1
    for f in range(0,maxv):
       fid = f
       try:
        fpm.fp.loadTemplate(f,0x01)
        chars = str(fpm.fp.downloadCharacteristics(0x01)).encode('utf-8')
        value = hashlib.sha256(chars).hexdigest()
       except:
        fid = -1
       if fid>-1:
        cter = cter + 1
        webserver.TXBuffer += "<tr><td><input type='radio' name='fpnum' value='"+ str(fid)+"'>"+str(fid)
        webserver.TXBuffer += "<td>"+str(value)+"</tr>"
       elif ffree == -1:
        ffree = f
       if cter>fc:
        break
    if ffree==-1:
     ffree = maxv
    webserver.TXBuffer += "</table><p>"
    webserver.addSubmitButton("Enroll new fingerprint", "add")
    webserver.TXBuffer += "<BR>"
    webserver.addSubmitButton("Search for fingerprint", "search")
    webserver.TXBuffer += "<BR>"
    webserver.addSubmitButton("Delete selected fingerprint", "fdel")
    webserver.TXBuffer += "<BR>"
    webserver.addSubmitButton("Delete all fingerprints", "fdelall")
    webserver.TXBuffer += "<input type='hidden' name='ffree' value='" +str(ffree) + "'>"
   webserver.TXBuffer += "</form>"
   try:
    webserver.TXBuffer += "<p><table width='100%'><TR><TD colspan='2'>Results<BR><textarea readonly rows='10' wrap='on'>"
    lc = len(misc.SystemLog)
    if lc>5:
     ls = lc-5
    else:
     ls = 0
    for l in range(ls,lc):
     webserver.TXBuffer += '\r\n'+str(misc.SystemLog[l]["t"])+" : "+ str(misc.SystemLog[l]["l"])
    webserver.TXBuffer += "</textarea>"
   except Exception as e:
    print(e)
   webserver.TXBuffer += "</table>"
   webserver.sendHeadandTail("TmplStd",webserver._TAIL)
   return webserver.TXBuffer
  else:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"FPM module uninitialized!")
   time.sleep(1)
   return self.redirect('/log')
