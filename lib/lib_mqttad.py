import rpieGlobals as r
import binascii
import Settings
import json

class ADHelper:

 def __init__(self,discovery_prefix,unitname,controllerid=0,basepath=""):
     self.discovery_prefix = discovery_prefix
     if self.discovery_prefix[-1] != "/":
         self.discovery_prefix += "/"
     self.unitname = unitname
     self.controllerid = controllerid
     if self.controllerid>0:
        self.controllerid -= 1
     if basepath == "":
        self.basepath = unitname
     else:
        self.basepath = basepath

 def getADstrPCrc(self,plugin):
     res = 0
     try:
      if plugin:
         if plugin.pluginid > 0:
            res = self.getADstrCrc(plugin.vtype, plugin.taskname, plugin.valuenames, plugin.recdataoption)
     except:
      pass
     return res

 def getADstrP(self,plugin):
     res = []
     try:
      if plugin:
         if plugin.pluginid > 0:
            res = self.getADstr(plugin.vtype, plugin.taskname, plugin.valuenames, plugin.valuecount, plugin.recdataoption)
     except Exception as e:
      print("adstrp",e)
     return res

 def getADstrCrc(self,stype,devname,valuenames,recdataoption=False):
     rv = 0
     try:
       buf = stype.to_bytes(2,'big') + bytes(devname,'utf-8') + recdataoption.to_bytes(1,'big')
       for v in valuenames:
         buf += bytes(v,'utf-8')
       rv = binascii.crc32(buf)
     except Exception as e:
      print(e)
     return rv

 def getADstr(self,stype,devname,valuenames,valucount,recdataoption=False,pluginid=-1):
    results = []
    adtype = ""
    mtopic = ""
    if devname != "":
     mpath = self.basepath + "/" + devname + "/"
    else:
     mpath = self.basepath + "/"
    if stype == r.SENSOR_TYPE_SWITCH:
       if recdataoption:
        adtype = "switch"
       else:
        adtype = "binary_sensor"
    elif stype == r.SENSOR_TYPE_DIMMER:
       if recdataoption:
        adtype = "light" #dimmer
        if pluginid in [502,505]: #P502, P505 is special selector!
         adtype = "select"
       else:
        adtype = "sensor"
    elif stype in [r.SENSOR_TYPE_SINGLE, r.SENSOR_TYPE_DUAL, r.SENSOR_TYPE_TRIPLE, r.SENSOR_TYPE_QUAD, r.SENSOR_TYPE_LONG, r.SENSOR_TYPE_TEXT]:
        adtype = "sensor"
    elif stype in [r.SENSOR_TYPE_TEMP_HUM, r.SENSOR_TYPE_TEMP_HUM_BARO, r.SENSOR_TYPE_TEMP_EMPTY_BARO, r.SENSOR_TYPE_TEMP_BARO]:
        adtype = "sensor" #temp
    if adtype != "":
     vc = valucount
     for v in range(vc):
       if v==0:
          addev = False
       if devname != "":
        mtopic = self.discovery_prefix + adtype + "/" + self.unitname + "-" + devname
       else:
        mtopic = self.discovery_prefix + adtype + "/" + self.unitname + "-" + valuenames[v]
       mpayload = {}
       if devname != "":
        mpayload["name"] = self.unitname + " " + devname
        if vc>1:
         mpayload["name"] += " " +valuenames[v]
        mpayload["uniq_id"] = self.unitname + "-" + devname + "-" + valuenames[v]
       else:
        mpayload["name"] = self.unitname + " " + valuenames[v]
        mpayload["uniq_id"] = self.unitname + "-" + valuenames[v]
       mpayload["~"] = mpath
       mpayload["stat_t"] = "~"+valuenames[v]
       if adtype == "switch":
          if v==0:
           mpayload["cmd_t"] = mpayload["stat_t"] + "/set"
           mpayload["pl_off"] = "0"
           mpayload["pl_on"] = "1"
       elif adtype == "binary_sensor":
          if v==0:
           mpayload["pl_off"] = "0"
           mpayload["pl_on"] = "1"
       elif adtype == "light":
          if stype == r.SENSOR_TYPE_DIMMER:
             mpayload["cmd_t"] = mpayload["stat_t"] + "/set"
             mpayload["brightness_command_topic"] = mpayload["stat_t"] + "/set"
             mpayload["brightness_state_topic"] = mpayload["stat_t"]
             mpayload["brightness"] = True
             mpayload["brightness_scale"] = 100 #limits: P213, P519 0..100
             mpayload["color_mode"] = True
             mpayload["supported_color_modes"] = []
             mpayload["supported_color_modes"].append("brightness")
       elif adtype == "select":
          pass #MISSING!
       elif adtype == "sensor":
          subt = ""
          if stype==r.SENSOR_TYPE_TEMP_HUM:
             if v==0:
                subt = "temperature"
             elif v==1:
                subt = "humidity"
             addev = True
          elif stype==r.SENSOR_TYPE_TEMP_HUM_BARO:
             if v==0:
                subt = "temperature"
             elif v==1:
                subt = "humidity"
             elif v==2:
                subt = "pressure"
             addev = True
          elif stype==r.SENSOR_TYPE_TEMP_BARO:
             if v==0:
                subt = "temperature"
             elif v==1:
                subt = "pressure"
             addev = True
          elif stype==r.SENSOR_TYPE_TEMP_EMPTY_BARO:
             if v==0:
                subt = "temperature"
             elif v==2:
                subt = "pressure"
             addev = True
          else: # generic
             if "temperature" in valuenames[v].lower():
                subt = "temperature"
                for j in range(0,len(valuenames)):
                 if "humidity" in valuenames[j].lower():
                   addev = True
             elif "cpu temp" in valuenames[v].lower():
                subt = "temperature" #C
             elif "humidity" in valuenames[v].lower():
                subt = "humidity" #%
                if v > 0 and "temp" in valuenames[0].lower():
                   addev = True
             elif "pressure" in valuenames[v].lower():
                subt = "pressure" #hPa
                if v > 0 and "temp" in valuenames[0].lower():
                   addev = True
             elif valuenames[v].lower().startswith("lux"):
                subt = "lux"
             elif "light" in valuenames[v].lower():
                subt = "lux"
             elif "brightness" in valuenames[v].lower():
                subt = "lux"
             elif valuenames[v].lower().startswith("mm"):
                subt = "distance"
             elif "proximity" in valuenames[v].lower():
                subt = "distance"
             elif valuenames[v].lower().startswith("volt"):
                subt = "voltage"
             elif "current" in valuenames[v].lower():
                subt = "current"
             elif "amper" in valuenames[v].lower():
                subt = "current"
             elif "power" in valuenames[v].lower():
                subt = "power"
             elif "watt" == valuenames[v].lower().strip():
                subt = "power"
             elif "energy" in valuenames[v].lower():
                subt = "energy"
             elif "wh" == valuenames[v].lower().strip():
                subt = "energy"
             elif "ppm" in valuenames[v].lower():
                subt = "gas_ppm"
             elif "battery" in valuenames[v].lower():
                subt = "battery"
                if v > 0 and "temp" in valuenames[v].lower():
                   addev = True
             else:
                subt = valuenames[v]
                addev = False
          if subt != "":
             mtopic += "/" + subt
             if addev:
                mpayload["device"] = {}
                mpayload["device"]["name"] = self.unitname + "-" + devname
                mpayload["device"]["identifiers"] = []
                mpayload["device"]["identifiers"].append(mpayload["device"]["name"])
             mpayload["stat_cla"] = "measurement"
             if subt=="temperature":
                mpayload["dev_cla"] = "temperature"
                mpayload["unit_of_meas"] = "C"
             elif subt=="humidity":
                mpayload["dev_cla"] = "humidity"
                mpayload["unit_of_meas"] = "%"
             elif subt=="battery":
                mpayload["dev_cla"] = "battery"
                mpayload["unit_of_meas"] = "%"
             elif subt=="lux":
                mpayload["dev_cla"] = "illuminance"
                mpayload["unit_of_meas"] = "lx"
             elif subt=="pressure":
                mpayload["dev_cla"] = "atmospheric_pressure"
                mpayload["unit_of_meas"] = "hPa"
             elif subt=="distance":
                mpayload["dev_cla"] = "distance"
                mpayload["unit_of_meas"] = "mm"
             elif subt=="current":
                mpayload["dev_cla"] = "current"
                mpayload["unit_of_meas"] = "A"
             elif subt=="power":
                mpayload["dev_cla"] = "power"
                mpayload["unit_of_meas"] = "W"
             elif subt=="energy":
                mpayload["dev_cla"] = "energy"
                mpayload["unit_of_meas"] = "Wh"
             elif subt=="gas_ppm":
                mpayload["dev_cla"] = "carbon_dioxide"
                mpayload["unit_of_meas"] = "ppm"
       mtopic += "/config"
       res = [mtopic,json.dumps(mpayload)]
       results.append(res)
       #print(mtopic,mpayload)#debug
    return results

 def get_MQTT_strs(self):
    strs = []
    res = {}
    res['config'] = self.getADstr(r.SENSOR_TYPE_SWITCH,"",["online"],1,False)
    res['id'] = -1
    res['crc'] = self.getADstrCrc(r.SENSOR_TYPE_SWITCH,"",["online"],False)
    res['auto'] = 1
    strs.append(res)
    for x in range(0,len(Settings.Tasks)):
        try:
          if (Settings.Tasks[x]):
           if (Settings.Tasks[x].enabled):
             if self.controllerid in Settings.Tasks[x].controlleridx:
                mqtts = self.getADstrP(Settings.Tasks[x])
                if len(mqtts)>0:
                 res = {}
                 res['config'] = mqtts
                 res['id'] = x
                 res['crc'] = self.getADstrPCrc(Settings.Tasks[x])
                 res['auto'] = 1
                 strs.append(res)
        except Exception as e:
         print(e)
    return strs

 def save_static_mstrs(self,filename,statconfig):
     try:
      with open(filename,"w") as outfile:
       json.dump(statconfig,outfile)
     except:
      pass

 def add_static_mstrs(self,filename,autoconfig):
     res = autoconfig
     try:
      with open(filename,'r') as openfile:
       confstat = json.load(openfile)
     except:
       confstat = []
     if len(confstat)>0:
        for s in range(len(confstat)):
            found = -1
            for t in range(len(res)):
               try:
                if int(res[t]['id']) == int(confstat[s]['id']):
                   found = t
                   res[t] = confstat[s]
                   break
               except:
                pass
            if found<0:
               res.append(confstat[s])
     return res
