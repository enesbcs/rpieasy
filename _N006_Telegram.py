#!/usr/bin/env python3
#############################################################################
################## Telegram notifier plugin for RPIEasy #####################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import nplugin
import webserver
import rpieGlobals
import misc
import commands
import urllib.request
import threading
from urllib import request, parse
import ssl
import json

class Plugin(nplugin.NPluginProto):
 NPLUGIN_ID = 6
 NPLUGIN_NAME = "Telegram"

 def __init__(self,nindex): # general init
  nplugin.NPluginProto.__init__(self,nindex)
  self.server = "api.telegram.org"
  self.port = 443
  self.passw = ""
  self.chatid = ""
  self.body=""     # template

 def getuniquename(self):
  return self.server

 def plugin_init(self,enableplugin=None):
  nplugin.NPluginProto.plugin_init(self,enableplugin)
  if self.passw=="*****":
   self.passw=""
  self.initialized = False
  if self.enabled:
   if self.chatid == "":
    urlstr = "https://"+str(self.server)+":"+str(self.port)+"/bot"+str(self.passw)+"/getUpdates"
    try:
     content = urllib.request.urlopen(urlstr,None,2)
     ret = content.read().decode('utf-8')
     if ("{" in ret):
      list = json.loads(ret)
      self.chatid = list["result"][0]["message"]["from"]["id"]
    except Exception as e:
     self.chatid = ""
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Telegram request failed: "+str(e))
   if self.chatid == "":
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Telegram ChatID not found!")
    self.initialized = False
   else:
    self.initialized = True

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Server","server",self.server,128)
  webserver.addFormNumericBox("Port","port",self.port,1,65535)
  webserver.addFormPasswordBox("Token","passw",self.passw,64)
  webserver.addFormTextBox("Chat-id","chatid",self.chatid,255)
  webserver.addHtml("<TR><TD>Body:<TD><textarea name='body' rows='5' cols='80' size=255 wrap='off'>")
  webserver.addHtml(str(self.body))
  webserver.addHtml("</textarea>")
  return True

 def webform_save(self,params): # process settings post reply
  self.server = webserver.arg("server",params)
  par1 = webserver.arg("port",params)
  try:
   par1=int(par1)
  except:
   par1=443
  if par1<1 or par1>65534:
   par1=443
  self.port=par1
  passw = webserver.arg("passw",params)
  if "**" not in passw:
   self.passw  = passw
   self.chatid = ""
  self.chatid    = str(webserver.arg("chatid",params))
  self.body    = webserver.arg("body",params)
  self.plugin_init()
  return True

 def notify(self,pmsg=""):
  if self.initialized==False or self.enabled==False:
   return False
  if pmsg=="":
   message = self.msgparse(self.body)
  else:
   message = self.msgparse(pmsg)
  if self.server=="0.0.0.0" or self.server=="":
   return False
  jdata = {}
  jdata['chat_id'] = self.chatid
  jdata['parse_mode'] = 'HTML'
  jdata['text'] = message
  jdata = urllib.parse.urlencode(jdata).encode("utf-8")
  urlstr = "https://"+str(self.server)+":"+str(self.port)+"/bot"+str(self.passw)+"/sendMessage"
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Sending telegram notification")
  httpproc = threading.Thread(target=self.urlpost, args=(urlstr,jdata,))  # use threading to avoid blocking
  httpproc.daemon = True
  httpproc.start()
  return True

 def urlpost(self,url,postdata):
  try:
   ctx = ssl.create_default_context()
   ctx.check_hostname=False
   ctx.verify_mode = ssl.CERT_NONE
   hdr = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
   req = request.Request(url, data=postdata, headers=hdr)
   response = request.urlopen(req,None,2,context=ctx)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+self.server+" connection failed "+str(e))

 def msgparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(ostr)
      return resstr
