#!/usr/bin/env python3
#############################################################################
################## Telegram notifier plugin for RPIEasy #####################
#############################################################################
#
# Copyright (C) 2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import nplugin
import webserver
import rpieGlobals
import misc
import commands
import urllib.request
import threading
import requests
import ssl
import json

class Plugin(nplugin.NPluginProto):
 NPLUGIN_ID = 8
 NPLUGIN_NAME = "MS Teams"

 def __init__(self,nindex): # general init
  nplugin.NPluginProto.__init__(self,nindex)
  self.server = "webhook.office.com"
  self.port = 443
  self.passw = ""
  self.fullurl = ""
  self.body=""     # template

 def getuniquename(self):
  fullurl = ""
  if self.fullurl !="":
   furl = self.fullurl.replace("//","/")
   try:
    fa = furl.split("/")
    fullurl = fullurl[1]
   except:
    pass
  else:
   fullurl = self.server
  return fullurl

 def plugin_init(self,enableplugin=None):
  nplugin.NPluginProto.plugin_init(self,enableplugin)
  if self.passw=="*****":
   self.passw=""
  self.initialized = False
  if self.fullurl != "" and self.enabled:
    self.initialized = True

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Teams channel Webhook URL","fullurl",self.fullurl,512)
  webserver.addHtml("<TR><TD>Body:<TD><textarea name='body' rows='5' cols='80' size=255 wrap='off'>")
  webserver.addHtml(str(self.body))
  webserver.addHtml("</textarea>")
  return True

 def webform_save(self,params): # process settings post reply
  self.fullurl = webserver.arg("fullurl",params)
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
  try:
   jdata = {'text': str(message) }
   urlstr = str(self.fullurl)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Teams notification: "+str(e))
   return False
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Sending Teams notification")
  httpproc = threading.Thread(target=self.urlpost, args=(urlstr,jdata,))  # use threading to avoid blocking
  httpproc.daemon = True
  httpproc.start()
  return True

 def urlpost(self,url,postdata):
  try:
   hdr = {'Content-Type': 'application/json'}
   response = requests.post(url, headers=hdr, data=json.dumps(postdata))
   # str(response.text.encode('utf8'))=='1'
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+ self.getuniquename() +" connection failed "+str(e))

 def msgparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(ostr)
      return resstr
