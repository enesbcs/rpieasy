import lib.lib_mqttad as mqttad
import rpieGlobals as r
import webserver as w
import Settings
import os

def handle_adconfig(response):
    goon = False
    try:
     cid = int(w.arg("cid",response))
     sname = Settings.Settings["Name"]
     dtopic = Settings.Controllers[cid].discoverytopic
     fconf  = Settings.Controllers[cid].adconffile
     goon = True
    except Exception as e:
     w.TXBuffer += str(e)
    if goon:
     t = mqttad.ADHelper(dtopic,sname,cid)
     if w.arg('del',response).strip() != "":
        #print("delete")#debug
        try:
         os.remove(fconf)
        except:
         pass
     if w.arg('Submit',response).strip() != "":
        #print("save")#debug
        strs = []
        for c in range(r.TASKS_MAX*r.TASKS_MAX):
            if w.arg('dt_'+str(c)+'_0',response):
             if w.arg('da_'+str(c),response) == "":
              res = {}
              res['auto'] = 0
              res['id'] = w.arg('di_'+str(c),response)
              res['crc'] = w.arg('dc_'+str(c),response)
              res['config'] = []
              for d in range(r.TASKS_MAX):
                  if w.arg('dt_'+str(c)+'_'+str(d),response):
                    try:
                     res['config'].append([ w.arg('dt_'+str(c)+'_'+str(d),response), w.arg('dp_'+str(c)+'_'+str(d),response) ])
                    except:
                     pass
              strs.append(res)
            else:
             break
        if len(strs)>0:
             #print("websave",strs)#debug
             t.save_static_mstrs(fconf,strs)
     confs = t.get_MQTT_strs()
     confs = t.add_static_mstrs(fconf,confs)
     #print("auto",confs) #debug
     w.TXBuffer += "<p align=left><form name='adconf' method='post'><table align='left' width='100%' border=1px frame='box' rules='all'>"
     w.addFormHeader("MQTT Device configs")
     if len(confs)>0:
      for cd in range(len(confs)):
        try:
         w.addFormSubHeader("Device #"+str(cd))
         w.addFormCheckBox("Auto-creation","da_"+str(cd),(int(confs[cd]['auto'])>0))
         w.TXBuffer += "<input type='hidden' name='dc_" + str(cd)+ "' value='" + str(confs[cd]['crc']) +"'></td></tr>"
         w.TXBuffer += "<input type='hidden' name='di_" + str(cd)+ "' value='" + str(confs[cd]['id']) +"'></td></tr>"
         for cl in range(len(confs[cd]['config'])):
             w.addFormTextBox("Topic","dt_"+str(cd)+"_"+str(cl),confs[cd]['config'][cl][0],256)
             w.addRowLabel("Payload")
             w.TXBuffer += "<textarea name='dp_"+str(cd)+"_"+str(cl)+"' rows=4 wrap=on>"
             w.TXBuffer += confs[cd]['config'][cl][1]
             w.TXBuffer +=  "</textarea></td></tr>"
        except Exception as e:
         print(e)
     w.addFormSeparator(2)
     w.addFormNote("Only devices with unchecked Auto-creation will be saved!")
     w.addSubmitButton()
     w.addSubmitButton("Delete all","del")
     w.TXBuffer += "<input type='hidden' name='cid' value='" +str(cid) +"'>"
     w.TXBuffer += "</table></form>"
