#!/usr/bin/env python3
#############################################################################
################## RTSP to JPEG proxy plugin for RPIEasy ####################
#############################################################################
#
# Plugin which transforms a realtime stream or any OpenCV datasource into JPEG image
# for example Domoticz camera integration
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import webserver
import Settings
from PIL import Image, ImageDraw
from io import BytesIO
from threading import Thread
import cv2

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 522
 PLUGIN_NAME = "Image - OpenCV RTSP stream To JPEG"
 PLUGIN_VALUENAME1 = "jpeg"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.readinprogress = 0
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = False
  self.timeroptional = True
  self.formulaoption = False
  self._nextdataservetime = 0
  self.lastread = 0
  self.videostream = None
  self.lastinit = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  if enableplugin is None:
   try:
    if self.videostream:
     del self.videostream
   except:
    pass
  self.initialized = False
  self.readinprogress = 0
  if self.enabled:
#   rtsp_stream_link = 'rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov'
   rtsp_stream_link = str(self.taskdevicepluginconfig[0])
   try:
    self.videostream = VideoGrab(rtsp_stream_link)
    self.initialized = True
   except Exception as e:
    pass
   if self.videostream is None:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Videostream can not be initialized! ")
    return False
   else:
    if time.time()-self.lastinit>10:
     self.capture_start()
     self.lastinit = time.time()
  else:
   try:
    self.capture_stop()
    del self.videostream
   except:
    pass

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("RTSP stream","plugin_522_url",str(self.taskdevicepluginconfig[0]),255)
  webserver.addFormNote("Specify the full URL to access stream, with password if needed")
  webserver.addFormCheckBox("Enable resize","plugin_522_resize",self.taskdevicepluginconfig[1])
  webserver.addFormNumericBox("Width to resize","plugin_522_w",self.taskdevicepluginconfig[2],0,4096)
  webserver.addFormNumericBox("Height to resize","plugin_522_h",self.taskdevicepluginconfig[3],0,2160)
  webserver.addFormNote("Resize is a bit resource hungry, use only if really needed")
  try:
   if self.initialized and self.enabled:
    try:
     pname = self.gettaskname()
    except:
     pname = ""
    if pname=="":
     pname = "[NAME]"
    url = "image?name="+str(pname)
    webserver.addHtml("<tr><td>Output image url:</td>")
    if pname == "[NAME]":
     webserver.addHtml("<td>http://ipaddress:port/image?name="+pname)
    else:
     webserver.addHtml("<td><a href='"+url+"'>/"+url+"</a></td></tr>")
  except:
   pass
  return True

 def webform_save(self,params): # process settings post reply
   self.capture_stop()
   self.taskdevicepluginconfig[0] = webserver.arg("plugin_522_url",params)
   self.taskdevicepluginconfig[1] = (webserver.arg("plugin_522_resize",params)=="on")
   self.taskdevicepluginconfig[2] = int(webserver.arg("plugin_522_w",params))
   self.taskdevicepluginconfig[3] = int(webserver.arg("plugin_522_h",params))
   self.capture_start(self.taskdevicepluginconfig[0])
   return True

 def capture_start(self,src=None):
  try:
#   if self.videostream.initialized==False:
    self.videostream.start(src)
  except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Videostream can not be initialized! "+str(e))

 def capture_stop(self):
  try:
   self.videostream.stop()
  except:
   pass

 def plugin_exit(self):
  plugin.PluginProto.plugin_exit(self)
  try:
   if self.videostream is not None:
    self.videostream.__exit__()
    self.videostream = None
  except:
   pass

class VideoGrab(object):
    def __init__(self, src=0):
        # Create a VideoCapture object
        self.initialized = False
        self.status = False
        self.src = src
        self.delaytime = 1/20

    def start(self,src=None):
        if src is not None:
         self.src = src
        try:
         self.capture = cv2.VideoCapture(self.src)
         self.initialized = True
        except Exception as e:
         self.initialized = False
         self.capture = None
#         print(e)
        if self.initialized:
         starttime = time.time()
         try:
          if self.capture.isOpened():
            waittostart = True
            while waittostart: # wait until accessible
             (self.status, frame) = self.capture.read()
             if (self.status and frame is not None) or (time.time()-startime>10):
              waittostart = False
             time.sleep(0.1)
         except:
            pass
         # Start the thread to read frames from the video stream
         thread = Thread(target=self.update, args=())
         thread.daemon = True
         thread.start()

    def __exit__(self):
           self.stop()
           try:
             self.capture.release()
           except:
             pass
           self.capture = None

    def stop(self):
        if self.initialized:
           self.initialized = False
           time.sleep(0.5)

    def update(self):
        # Read the next frame from the stream in a different thread
        while self.initialized:
           try:
            if self.capture.isOpened():
                self.status = self.capture.grab()
            else:
                time.sleep(1)
            time.sleep(self.delaytime)
           except Exception as e:
            pass
        try:
         self.capture.release()
        except:
         pass

    def get_frame(self):
        if self.initialized==False:
         self.start()
        if self.initialized:
           try:
                (self.status, frame) = self.capture.retrieve()
           except Exception as e:
            pass
           return frame
        else:
           return None


@webserver.WebServer.route('/image')
def handle_videostream(self):
  tname = ""
  try:
   if (not webserver.isLoggedIn(self.get,self.cookie)):
    return self.redirect('/login')
   if self.type == "GET":
    responsearr = self.get
   else:
    responsearr = self.post
   if responsearr:
     tname = webserver.arg("name",responsearr)
  except Exception as e:
   print(e)

  vidtask = None
  for x in range(0,len(Settings.Tasks)):
    if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool:
     try:
      if Settings.Tasks[x].enabled:
       if Settings.Tasks[x].pluginid==522 and Settings.Tasks[x].gettaskname()==tname:
        vidtask = Settings.Tasks[x]
        break
     except:
      pass
  if vidtask is not None:
    succ = False
    self.set_mime('image/jpeg')
    try:
     cv2_im = vidtask.videostream.get_frame()
     if cv2_im is not None:
      cv2_im = cv2.cvtColor(cv2_im,cv2.COLOR_BGR2RGB)
      image = Image.fromarray(cv2_im)
      if vidtask.taskdevicepluginconfig[1]:
       image = image.resize( (int(vidtask.taskdevicepluginconfig[2]),int(vidtask.taskdevicepluginconfig[3])), Image.LANCZOS)
      img_io = BytesIO()
      image.save(img_io, 'JPEG')
      img_io.seek(0)
      succ = True
      return img_io.read()
     else:
      vidtask.capture_start()
      return None
    except Exception as e:
     print(e)
     succ = False
    if succ==False:
     vidtask.capture_start()
