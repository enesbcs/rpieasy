#!/usr/bin/env python3
#############################################################################
#################### Dashboard plugin for RPIEasy ###########################
#############################################################################
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
import os_os as OS

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 212
 PLUGIN_NAME = "GUI - Dashboard"
 PLUGIN_VALUENAME1 = "State"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.readinprogress = 0
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = False
  self._nextdataservetime = 0
  self.celldata = []

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.initialized = False

 def webform_load(self): # create html page for settings
  webserver.addFormCheckBox("Use standard HTML head","p212_head",self.taskdevicepluginconfig[2])
  try:
   sp = Settings.AdvSettings["startpage"]
  except:
   sp = "/"
  webserver.addFormCheckBox("Set as startpage","p212_start",(sp=="/dash"))
  webserver.addHtml("<tr><td>Columns:<td>")
  webserver.addSelector_Head("p212_cols",False)
  for o in range(7):
   webserver.addSelector_Item(str(o),o,(str(o)==str(self.taskdevicepluginconfig[0])),False)
  webserver.addSelector_Foot()

  webserver.addHtml("<tr><td>Rows:<td>")
  webserver.addSelector_Head("p212_rows",False)
  for o in range(16):
   webserver.addSelector_Item(str(o),o,(str(o)==str(self.taskdevicepluginconfig[1])),False)
  webserver.addSelector_Foot()

  if int(self.taskdevicepluginconfig[0])>0 and int(self.taskdevicepluginconfig[1])>0:
   if self.enabled:
    webserver.addHtml("<tr><td>Dashboard address:</td><td><a href='dash'>/dash</a></td></tr>")
   options1 = ["None","Text","Binary input","Switch output","Meter","Gauge","Slider output","Select output"]
   optionvalues1 = [-1,0,1,2,3,4,5,6]
   options2 = ["None"]
   optionvalues2 = ["_"]
   for t in range(0,len(Settings.Tasks)):
     if (Settings.Tasks[t] and (type(Settings.Tasks[t]) is not bool)):
      for v in range(0,Settings.Tasks[t].valuecount):
       options2.append("T"+str(t+1)+"-"+str(v+1)+" / "+str(Settings.Tasks[t].taskname)+"-"+str(Settings.Tasks[t].valuenames[v]))
       optionvalues2.append(str(t)+"_"+str(v))

   for r in range(int(self.taskdevicepluginconfig[1])):
    for c in range(int(self.taskdevicepluginconfig[0])):
     offs = (r * int(self.taskdevicepluginconfig[0])) + c
     try:
      adata = self.celldata[offs]
     except:
      adata = {}
     dtype = -1
     if "type" in adata:
      dtype = int(adata["type"])
     webserver.addHtml("<tr><td><b>Cell"+str(offs)+" (y"+str(r)+"x"+str(c)+")</b><td>")

     dname = ""
     if "name" in adata:
      dname = str(adata["name"])
     webserver.addFormTextBox("Name overwrite","p212_names_"+str(offs),dname,64)

     webserver.addFormSelector("Type","p212_type_"+str(offs),len(options1),options1,optionvalues1,None,dtype)
     webserver.addHtml("<tr><td>Data source:<td>")
     ddata = "_"
     if "data" in adata:
      ddata = str(adata["data"])
     webserver.addSelector_Head("p212_data_"+str(offs),False)
     for o in range(len(options2)):
      webserver.addSelector_Item(options2[o],optionvalues2[o],(str(optionvalues2[o])==str(ddata)),False)
     webserver.addSelector_Foot()

     if dtype in (0,4):
      try:
       udata = str(adata["unit"])
      except:
       udata = ""
      webserver.addFormTextBox("Unit","p212_unit_"+str(offs),udata,16)
     if dtype in (3,4,5):
      try:
       umin = float(adata["min"])
      except:
       umin = 0
      try:
       umax = float(adata["max"])
      except:
       umax = 100
      webserver.addFormFloatNumberBox("Min value","p212_min_"+str(offs),umin,-65535.0,65535.0)
      webserver.addFormFloatNumberBox("Max value","p212_max_"+str(offs),umax,-65535.0,65535.0)
     elif dtype == 6:
      try:
       uon = str(adata["optionnames"])
      except:
       uon = ""
      try:
       uopt = str(adata["options"])
      except:
       uopt = ""
      webserver.addFormTextBox("Option name list","p212_optionnames_"+str(offs),uon,1024)
      webserver.addFormTextBox("Option value list","p212_options_"+str(offs),uopt,1024)
      webserver.addFormNote("Input comma separated values for selector boxes!")
  return True

 def webform_save(self,params): # process settings post reply
   try:
    sp = Settings.AdvSettings["startpage"]
   except:
    sp = "/"
   spold = sp
   if (webserver.arg("p212_start",params)=="on"):
    try:
     if sp != "/dash":
      Settings.AdvSettings["startpage"]  = "/dash"
    except:
     pass
   else:
    try:
     if sp == "/dash":
      Settings.AdvSettings["startpage"]  = "/"
    except:
     pass
   if spold != Settings.AdvSettings["startpage"]:
    Settings.saveadvsettings()
   if (webserver.arg("p212_head",params)=="on"):
    self.taskdevicepluginconfig[2] = True
   else:
    self.taskdevicepluginconfig[2] = False

   par = webserver.arg("p212_cols",params)
   try:
    self.taskdevicepluginconfig[0] = int(par)
   except:
    self.taskdevicepluginconfig[0] = 1
   par = webserver.arg("p212_rows",params)
   try:
    self.taskdevicepluginconfig[1] = int(par)
   except:
    self.taskdevicepluginconfig[1] = 1

   for c in range(int(self.taskdevicepluginconfig[0])):
    for r in range(int(self.taskdevicepluginconfig[1])):
     offs = (r * int(self.taskdevicepluginconfig[0])) + c
     mknew = True
     try:
      self.celldata[offs]["type"] = int(webserver.arg("p212_type_"+str(offs),params))
      self.celldata[offs]["data"] = str(webserver.arg("p212_data_"+str(offs),params))
      mknew = False
     except:
      pass
     if mknew:
      try:
       adata = {"type":int(webserver.arg("p212_type_"+str(offs),params)), "data":str(webserver.arg("p212_data_"+str(offs),params))}
      except:
       adata = {"type":-1, "data":"_"}
      self.celldata.append(adata)
     try:
      self.celldata[offs]["unit"] = str(webserver.arg("p212_unit_"+str(offs),params))
     except:
      pass
     try:
      self.celldata[offs]["min"] = float(webserver.arg("p212_min_"+str(offs),params))
      self.celldata[offs]["max"] = float(webserver.arg("p212_max_"+str(offs),params))
     except:
      pass
     try:
      self.celldata[offs]["optionnames"] = str(webserver.arg("p212_optionnames_"+str(offs),params))
      self.celldata[offs]["options"] = str(webserver.arg("p212_options_"+str(offs),params))
      self.celldata[offs]["name"] = str(webserver.arg("p212_names_"+str(offs),params))
     except:
      pass

   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled:
     self._lastdataservetime = rpieTime.millis()
  return result

@webserver.WebServer.route('/dash')
def handle_dash(self):
  try:
   if (not webserver.isLoggedIn(self.get,self.cookie)):
    return self.redirect('/login')
   webserver.navMenuIndex=7

   dashtask = None
   for t in range(0,len(Settings.Tasks)):
     if (Settings.Tasks[t] and (type(Settings.Tasks[t]) is not bool)):
      try:
       if Settings.Tasks[t].enabled:
        if Settings.Tasks[t].pluginid==212:
         dashtask = Settings.Tasks[t]
         break
      except:
       pass
   webserver.TXBuffer =""
   if (dashtask is not None) and (dashtask.taskdevicepluginconfig[2]):
    webserver.sendHeadandTail("TmplStd",webserver._HEAD)
    webserver.TXBuffer += "<link rel='stylesheet' href='/img/dash.css'>"
   else:
    webserver.TXBuffer += "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/><link rel='stylesheet' href='/img/dash.css'></head><body>"

   if (dashtask is not None) and (len(dashtask.celldata)>0):
    astr = ""
    estr = ""
    vstr = ""
    if int(dashtask.taskdevicepluginconfig[0])>1 and int(dashtask.taskdevicepluginconfig[0])<7:
     astr = " tab"+str(dashtask.taskdevicepluginconfig[0])
    webserver.addHtml("<table width='100%' class='tab "+astr+"'>")
    offs = 0
    for r in range(int(dashtask.taskdevicepluginconfig[1])):
     if offs>=len(dashtask.celldata):
      break
     webserver.addHtml("<tr>")
     for c in range(int(dashtask.taskdevicepluginconfig[0])):
      if offs>=len(dashtask.celldata):
       break
      webserver.addHtml("<td>")
      offs = (r * int(dashtask.taskdevicepluginconfig[0])) + c
      try:
       dtype = int(dashtask.celldata[offs]["type"])
       tid = str(dashtask.celldata[offs]["data"])
       estr += '"'+tid+'",'
       ti = tid.split("_")
       tasknum = int(ti[0])
       valnum  = int(ti[1])
       vstr += '"'+ str(Settings.Tasks[tasknum].uservar[valnum]) +'",'
       try:
        namestr = str(dashtask.celldata[offs]["name"])
       except:
         namestr = ""
       if namestr.strip() == "":
        namestr = str(Settings.Tasks[tasknum].gettaskname())+"#"+str(Settings.Tasks[tasknum].valuenames[valnum])
       webserver.addHtml("<div class='div_d' id='valuename_"+ str(tid) + "'>"+ namestr + "</div>")
      except:
       dtype = -1
      try:
        udata = str(dashtask.celldata[offs]["unit"])
      except:
        udata = ""
      if dtype == 0:
       webserver.addHtml("<div class='textval' id='value_"+str(tid)+ "'>"+ str(Settings.Tasks[tasknum].uservar[valnum]) +"</div>")
      elif dtype == 1:
       webserver.addHtml("<div class='centered'><input type='checkbox' id='value_"+str(tid)+ "' class='state' disabled='disabled'/><label for='value_"+str(tid)+ "' class='toggleWrapper'><div class='toggle'></div></label></div>")
      elif dtype == 2:
       webserver.addHtml("<div class='switch'><input id='value_"+str(tid)+ "' class='cmn-toggle cmn-toggle-round' type='checkbox' onchange='cboxchanged(this)'><label for='value_"+str(tid)+ "'></label></div>")
      elif dtype == 3:
       try:
         umin = float(dashtask.celldata[offs]["min"])
       except:
         umin = 0
       try:
         umax = float(dashtask.celldata[offs]["max"])
       except:
         umax = 100
       webserver.addHtml("<div style='width:100%'><meter id='value_"+str(tid)+ "' min='"+str(umin)+"' max='"+str(umax)+"' value='" + str(Settings.Tasks[tasknum].uservar[valnum]) + "' class='meter'></meter>")
       sval = umin
       stepval = (umax-umin)/5
       webserver.addHtml("<ul id='scale'><li style='width: 10%'><span></span></li>")
       while sval < (umax-stepval):
        sval = sval + stepval
        webserver.addHtml("<li><span id='scale'>"+str(sval)+"</span></li>")
       webserver.addHtml("<li style='width: 10%'><span id='scale'></span></li></ul></div>")
      elif dtype == 4:
       webserver.addHtml("<div class='gauge' id='value_"+str(tid)+ "'><div class='gauge__body'><div class='gauge__fill'></div><div class='gauge__cover'></div></div></div>")
      elif dtype == 5:
       try:
         umin = float(dashtask.celldata[offs]["min"])
       except:
         umin = 0
       try:
         umax = float(dashtask.celldata[offs]["max"])
       except:
         umax = 100
       webserver.addHtml("<input type='range' min='" +str(umin) +"' max='"+ str(umax) +"' value='" + str(Settings.Tasks[tasknum].uservar[valnum]) + "' class='slider' id='value_"+str(tid)+ "' onchange='sselchanged(this)' oninput='this.nextElementSibling.value = this.value'>")
       webserver.addHtml("<output>"+ str(Settings.Tasks[tasknum].uservar[valnum]) +"</output>")
      elif dtype == 6:
       webserver.addHtml("<div class='box'><select name='value_"+str(tid)+ "' id='value_"+str(tid)+ "' onchange='sselchanged(this)'>")
       optionnames = []
       if "," in dashtask.celldata[offs]["optionnames"]:
        optionnames = dashtask.celldata[offs]["optionnames"].split(",")
       elif ";" in dashtask.celldata[offs]["optionnames"]:
        optionnames = dashtask.celldata[offs]["optionnames"].split(",")
       options = []
       if "," in dashtask.celldata[offs]["options"]:
        options = dashtask.celldata[offs]["options"].split(",")
       elif ";" in dashtask.celldata[offs]["options"]:
        options = dashtask.celldata[offs]["options"].split(",")
       ol = len(optionnames)
       if ol> len(options):
        ol = len(options)
       for o in range(ol):
        webserver.addHtml("<option value='"+ str(options[o]) +"'>"+ str(optionnames[o])  +"</option>")
       webserver.addHtml("</select></div>")
      else:
        webserver.addHtml("&nbsp;")
      if udata.strip() != "":
        webserver.addHtml(textparse(udata))
      webserver.addHtml("</td>")
     webserver.addHtml("</tr>")
    webserver.addHtml("</table>")
    webserver.addHtml('<script type="text/javascript" src="/img/dash.js"></script>')
    webserver.addHtml("<script>var elements=["+estr+"]; var values=["+vstr+"];")
    offs = (dashtask.taskdevicepluginconfig[0] * dashtask.taskdevicepluginconfig[1])
    pstr = ""
    for o in range(offs):
     if "min" in dashtask.celldata[o]:
      pstr += "[" + str(dashtask.celldata[o]["min"]) + "," + str(dashtask.celldata[o]["max"]) + "],"
     else:
      pstr += '[0,100],'
    webserver.addHtml('var props=['+str(pstr)+'];')
    webserver.addHtml("var ownurl='http://" + str(OS.get_ip())+":"+str(Settings.WebUIPort)+"';")
    webserver.addHtml("refreshDatas();setInterval(function(){ getDatas(); }, "+ str(dashtask.interval*1000) +");</script>")
   else:
    webserver.TXBuffer += "<p>Setup dashboard first!"
   if dashtask.taskdevicepluginconfig[2]:
    webserver.sendHeadandTail("TmplStd",webserver._TAIL)
   else:
    webserver.TXBuffer += "</body></html>"
  except Exception as e:
   print("Config error, try to delete and recreate task!")
  return webserver.TXBuffer

def textparse(ostr):
      resstr=str(ostr)
      if "{" in resstr or "&" in resstr:
       resstr = resstr.replace("{D}","˚").replace("&deg;","˚")
       resstr = resstr.replace("{<<}","«").replace("&laquo;","«")
       resstr = resstr.replace("{>>} ","»").replace("&raquo;","»")
       resstr = resstr.replace("{u} ","µ").replace("&micro; ","µ")
       resstr = resstr.replace("{E}","€").replace("&euro;","€")
       resstr = resstr.replace("{Y}","¥").replace("&yen;","¥")
       resstr = resstr.replace("{P}","£").replace("&pound;","£")
       resstr = resstr.replace("{c}","¢").replace("&cent;","¢")
       resstr = resstr.replace("{^1}","¹").replace("&sup1;","¹")
       resstr = resstr.replace("{^2}","²").replace("&sup2;","²")
       resstr = resstr.replace("{^3}","³").replace("&sup3;","³")
       resstr = resstr.replace("{1_4}","¼").replace("&frac14;","¼")
       resstr = resstr.replace("{1_2}","½").replace("&frac24;","½")
       resstr = resstr.replace("{3_4}","¾").replace("&frac34;","¾")
       resstr = resstr.replace("{+-}","±").replace("&plusmn;","±")
       resstr = resstr.replace("{x}","×").replace("&times;","×")
       resstr = resstr.replace("{..}","÷").replace("&divide;","÷")
      return resstr
