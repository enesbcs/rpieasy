#!/usr/bin/env python3
#############################################################################
################## LORA Direct controller for RPIEasy #######################
#############################################################################
#
# This controller is able to harvest datas arriving from direct LORA sensors
# or to send LORA RAW data. This is NOT LoraWan, it is direct LORA connection
# between local nodes!
#
# Supported hardware is SX1278 through PyLora
# + added support to SX1262 based on ehong-tl sx126x library
#
# Copyright (C) 2018-2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import misc
import rpieGlobals
import time
from rpieTime import *
import webserver
import commands
import Settings
import gpios
from datetime import datetime
import lib.lib_p2pbuffer as p2pbuffer
try:
 from SX127x.LoRa import *
 from SX127x.board_config import BOARD
except:
 pass
try:
 from lib.sx126x.sx1262 import SX1262
except:
 pass

CAPABILITY_BYTE = (1+2) # send and receive
REPORTINTERVAL = 1800#sec
#REPORTINTERVAL = 60#debug

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 20
 CONTROLLER_NAME = "LORA Direct (EXPERIMENTAL)"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = True
  self.onmsgcallbacksupported = False # use direct set_value() instead of generic callback to make sure that values setted anyway
  self.controllerport = 1
  self.lora = None
  self.sysinfosent=0
  self.timer30s = True
  self.sf = 9
  self.freq = 869.5
  self.sync = 0x12
  self.duty = 10
  self.defaultunit = 0
  self.enablesend = True
  self.noirq = False
  try:
   self.bw = BW.BW250
   self.coding = CODING_RATE.CR4_5
   self.rtype = 1276
   self.spi = None
   self.spidnum = None
  except:
   self.bw = 250
   self.coding = 5
   self.rtype = 1262
   self.spi = 0
   self.spidnum = 0
  self.dio1 = -1
  self.rst = -1
  self.busy = -1

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.initialized = False
  try:
    if self.rtype:
     pass
  except:
    self.rtype = 1276
  if self.enabled:
   if int(Settings.Settings["Unit"])>0:
    self.controllerport = Settings.Settings["Unit"]
   try:
    if self.rtype==1276:
     BOARD.setup()
     gpios.HWPorts.remove_event_detect(BOARD.DIO0)
     gpios.HWPorts.remove_event_detect(BOARD.DIO1)
     gpios.HWPorts.remove_event_detect(BOARD.DIO2)
     gpios.HWPorts.remove_event_detect(BOARD.DIO3)
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LORA Direct preinit msg: "+str(e))
   try:
    if self.rtype==1276:
     self.lora = LoRaRcvCont(self.pkt_receiver)
    elif self.rtype==1262:
     self.lora = LoRaRcvCont1262(self.spi,self.spidnum,self.dio1,self.rst,self.busy,self.pkt_receiver)
    self.connect()
    self.initialized = True
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"LORA Direct initialized")
   except Exception as e:
    self.initialized = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LORA Direct init error: "+str(e))
    return False
  return True

 def connect(self):
  self.connected = False
  self.sysinfosent = 0
  try:
   if self.lora is not None:
    if self.rtype==1276:
     self.lora.set_mode(MODE.STDBY)
     self.lora.set_pa_config(pa_select=1, max_power=21, output_power=15)
     self.lora.set_spreading_factor(self.sf)
     self.lora.set_bw(self.bw)
     self.lora.set_coding_rate(self.coding)
     self.lora.set_rx_crc(True)
     self.lora.set_freq(self.freq)
     self.lora.set_sync_word(self.sync) # default setting of 0x12 and a LoRaWAN setting of 0x34
     assert(self.lora.get_agc_auto_on() == 1)
    elif self.rtype==1262:
     self.lora.begin(freq=self.freq, bw=self.bw, sf=self.sf, syncWord=self.sync,crcOn=True,blocking=False)
    self.lora.loraduty = self.duty
    self.lora.start()
    self.connected = True
  except Exception as e:
    self.initialized = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LORA Direct connect error: "+str(e))

 def disconnect(self):
  self.connected = False
  try:
   if self.lora is not None:
     self.lora.set_mode(MODE.SLEEP)
   BOARD.spi.close()
   gpios.HWPorts.remove_event_detect(BOARD.DIO0)
   gpios.HWPorts.remove_event_detect(BOARD.DIO1)
   gpios.HWPorts.remove_event_detect(BOARD.DIO2)
   gpios.HWPorts.remove_event_detect(BOARD.DIO3)
  except:
   pass

 def webform_load(self):
  webserver.addFormNote("IP and Port parameter is not used!")
  webserver.addFormNote("SX127x hardware supported by pyLoRa library")
  webserver.addHtml("<p>Example sender sketches could be find <a href='https://github.com/enesbcs/EasyLora'>here</a>.")
  try:
   webserver.addTableSeparator("Hardware settings",2,3)
   options = ["PyLora (SX127x)","Sx1262"]
   optionvalues = [1276,1262]
   webserver.addFormSelector("LoRa chip type","loratype",len(optionvalues),options,optionvalues,None,self.rtype)
   if self.rtype==1276:
    try:
     if BOARD.SPI_BUS:
      pass
    except:
     self.rtype = 1262
   if self.rtype==1276:
    if BOARD.SPI_BUS==0:
     webserver.addHtml("<tr><td>SPI0 selected<td><i>(MOSI=GPIO10, MISO=GPIO9, SCK=GPIO11, NSS=GPIO8)</i>")
     spiok = False
     import gpios
     if gpios.HWPorts.is_spi_usable(BOARD.SPI_BUS):
      if gpios.HWPorts.is_spi_enabled(BOARD.SPI_BUS):
       webserver.addHtml(" - <b>SPI0 enabled</b>")
       spiok = True
     if spiok==False:
      webserver.addHtml("<tr><td><td>Enable SPI0 first at hardware <a href='pinout'>pinout page</a>!")
    else:
      webserver.addHtml("<tr><td><td>You have modified BOARD constants, so you are an expert!")
    webserver.addHtml("<tr><td>DIO0 (IRQ)<td>GPIO"+str(BOARD.DIO0))
    webserver.addHtml("<tr><td>DIO1<td>GPIO"+str(BOARD.DIO1))
    webserver.addHtml("<tr><td>DIO2<td>GPIO"+str(BOARD.DIO2))
    webserver.addHtml("<tr><td>DIO3<td>GPIO"+str(BOARD.DIO3))
    webserver.addHtml("<tr><td>RST<td>GPIO"+str(BOARD.RST))
   elif self.rtype==1262:
          try:
           import gpios
           options1, options2 = gpios.HWPorts.getspilist()
          except Exception as e:
           options1 = []
           options2 = []
          webserver.addHtml("<tr><td>SPI line:<td>")
          webserver.addSelector_Head("spi",False)
          for d in range(len(options1)):
           try:
            webserver.addSelector_Item("SPI"+str(options1[d]),options1[d],(self.spi==options1[d]),False)
           except:
            pass
          webserver.addSelector_Foot()
          webserver.addHtml("<tr><td>SPI device num:<td>")
          webserver.addSelector_Head("spidnum",False)
          for d in range(len(options2)):
           try:
            webserver.addSelector_Item("CE"+str(options2[d]),options2[d],(self.spidnum==options2[d]),False)
           except:
            pass
          webserver.addSelector_Foot()
          webserver.addFormPinSelect("DIO1 pin","dio1",self.dio1)
          webserver.addFormPinSelect("RESET pin","rst",self.rst)
          webserver.addFormPinSelect("BUSY pin","busy",self.busy)

   webserver.addTableSeparator("LoRa settings",2,3)
   webserver.addFormFloatNumberBox("Frequency","freq",self.freq,433,928)
   webserver.addUnit("Mhz")
   if self.lora is not None:
     try:
      afreq = self.lora.get_freq()
     except:
      afreq = "UNINITIALIZED"
     webserver.addFormNote("Current frequency: "+str(afreq)+" Mhz")
   webserver.addFormNote("Please check local regulations for your selected frequency!")

   options = ["10%","1%","0.1%"]
   optionvalues = [10,100,1000]
   webserver.addFormSelector("Duty cycle","duty",len(optionvalues),options,optionvalues,None,self.duty)
   webserver.addFormNote("Please check your local Duty cycle regulations for your selected frequency!")

   webserver.addFormNumericBox("Spreading factor","spreading",self.sf,6,12)
   options = ["7.8","10.4","15.6","20.8","31.25","41.7","62.5","125","250","500"]
   if self.rtype==1276:
    optionvalues = [BW.BW7_8, BW.BW10_4, BW.BW15_6, BW.BW20_8, BW.BW31_25, BW.BW41_7, BW.BW62_5, BW.BW125, BW.BW250, BW.BW500]
   else:
    optionvalues = [7.8,10.4,15.6,20.8,31.25,41.7,62.5,125,250,500]
   webserver.addFormSelector("Bandwidth","bw",len(optionvalues),options,optionvalues,None,self.bw)
   webserver.addUnit("khz")

   options = ["CR4/5","CR4/6","CR4/7","CR4/8"]
   if self.rtype==1276:
    optionvalues = [CODING_RATE.CR4_5,CODING_RATE.CR4_6,CODING_RATE.CR4_7,CODING_RATE.CR4_8]
   else:
    optionvalues = [5,6,7,8]
   webserver.addFormSelector("Coding rate","coding",len(optionvalues),options,optionvalues,None,self.coding)

   webserver.addFormNumericBox("Sync Word","sync",self.sync,0,255)
   webserver.addHtml("( 0x"+format(self.sync, '02x')+" )")
   webserver.addFormNote("Default 0x12, LoRaWAN is 0x34. Nodes can only communicate each other if uses same sync word!")

   webserver.addFormCheckBox("Enable Sending","sender",self.enablesend)
   webserver.addFormNumericBox("Default destination node index","defaultnode",self.defaultunit,0,255)
   webserver.addFormNote("Default node index for data sending")
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
  return True

 def webform_save(self,params):
  try:
   self.rtype = int(webserver.arg("loratype",params))
  except:
   self.rtype = 1276
  try:
   self.freq = float(webserver.arg("freq",params))
   self.duty = int(webserver.arg("duty",params))
   self.sf = int(webserver.arg("spreading",params))
   self.bw = float(webserver.arg("bw",params))
   self.coding = int(webserver.arg("coding",params))
   self.sync = int(webserver.arg("sync",params))
   self.defaultunit = int(webserver.arg("defaultnode",params))
   self.enablesend = (webserver.arg("sender",params)=="on")
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LORA parameter save: "+str(e))
  try:
   self.spi = int(webserver.arg("spi",params))
   self.spidnum = int(webserver.arg("spidnum",params))
   self.dio1 = int(webserver.arg("dio1",params))
   self.rst = int(webserver.arg("rst",params))
   self.busy = int(webserver.arg("busy",params))
  except:
   pass
  return True

 def nodesort(self,item):
  v = 0
  try:
   v = int(item["unitno"])
  except:
   v = 0
  return v

 def pkt_receiver(self,payload,rssi):
  if self.enabled:
    dp = p2pbuffer.data_packet()
    dp.buffer = payload
#    print(payload,dp.buffer) # debug
    dp.decode()
    if dp.pkgtype!=0:
        if dp.pkgtype==1:
#         print(dp.infopacket) # debug
         if int(dp.infopacket["unitno"]) == int(Settings.Settings["Unit"]): # skip own messages
          return False
         un = getunitordfromnum(dp.infopacket["unitno"]) # process incoming alive reports
         if un==-1:
          # CAPABILITIES byte: first bit 1 if able to send, second bit 1 if able to receive
          Settings.p2plist.append({"protocol":"LORA","unitno":dp.infopacket["unitno"],"name":dp.infopacket["name"],"build":dp.infopacket["build"],"type":dp.infopacket["type"],"mac":dp.infopacket["mac"],"lastseen":datetime.now(),"lastrssi":rssi,"cap":dp.infopacket["cap"]})
          misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"New LORA unit discovered: "+str(dp.infopacket["unitno"])+" "+str(dp.infopacket["name"]))
          Settings.p2plist.sort(reverse=False,key=self.nodesort)
         else:
          misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Unit alive: "+str(dp.infopacket["unitno"]))
          if Settings.p2plist[un]["type"]==0:
           Settings.p2plist[un]["name"] = dp.infopacket["name"]
           Settings.p2plist[un]["build"] = dp.infopacket["build"]
           Settings.p2plist[un]["type"] = dp.infopacket["type"]
           Settings.p2plist[un]["mac"] = dp.infopacket["mac"]
          Settings.p2plist[un]["cap"] = dp.infopacket["cap"]
          Settings.p2plist[un]["lastseen"] = datetime.now()
          Settings.p2plist[un]["lastrssi"] = rssi

        elif dp.pkgtype==5:                          # process incoming data
          if int(dp.sensordata["sunit"])==int(Settings.Settings["Unit"]):
           return False
          un = getunitordfromnum(dp.sensordata["sunit"])
          if un>-1: # refresh lastseen data
           Settings.p2plist[un]["lastseen"] = datetime.now()
           Settings.p2plist[un]["lastrssi"] = rssi
          else:
           Settings.p2plist.append({"protocol":"LORA","unitno":dp.sensordata["sunit"],"name":"","build":0,"type":0,"mac":"","lastseen":datetime.now(),"lastrssi":rssi,"cap":1})

          if (int(Settings.Settings["Unit"])==int(dp.sensordata["dunit"])) or (0==int(dp.sensordata["dunit"])): # process only if we are the destination or broadcast
           ltaskindex = -1
           for x in range(0,len(Settings.Tasks)): # check if the sent IDX already exists?
             try:
              if (type(Settings.Tasks[x]) is not bool and Settings.Tasks[x]):
                if Settings.Tasks[x].controlleridx[self.controllerindex]==int(dp.sensordata["idx"]):
                 ltaskindex = x
                 break
             except Exception as e:
              print(e)
           dvaluecount = int(dp.sensordata["valuecount"])
           if rpieGlobals.VARS_PER_TASK<dvaluecount: # avoid possible buffer overflow
            dvaluecount = rpieGlobals.VARS_PER_TASK
           if ltaskindex < 0: # create new task if necessarry
            devtype = int(dp.sensordata["pluginid"])
            m = False
            try:
             for y in range(len(rpieGlobals.deviceselector)):
              if int(rpieGlobals.deviceselector[y][1]) == devtype:
               m = __import__(rpieGlobals.deviceselector[y][0])
               break
            except:
             m = False
            TempEvent = None
            if m:
             try: 
              TempEvent = m.Plugin(-1)
             except:
              TempEvent = None
            if True:
             ltaskindex = -1
             for x in range(0,len(Settings.Tasks)): # check if there are free TaskIndex slot exists
               try:
                if (type(Settings.Tasks[x]) is bool):
                 if Settings.Tasks[x]==False:
                  ltaskindex = x
                  break
               except:
                pass
             devtype = 33 # dummy device
             m = False
             try:
              for y in range(len(rpieGlobals.deviceselector)):
               if int(rpieGlobals.deviceselector[y][1]) == devtype:
                m = __import__(rpieGlobals.deviceselector[y][0])
                break
             except:
              m = False
             if m:
              if ltaskindex<0:
               ltaskindex = len(Settings.Tasks)
              try:
               Settings.Tasks[ltaskindex] = m.Plugin(ltaskindex)
              except:
               ltaskindex = len(Settings.Tasks)
               Settings.Tasks.append(m.Plugin(ltaskindex))  # add a new device
              Settings.Tasks[ltaskindex].plugin_init(True)
              Settings.Tasks[ltaskindex].remotefeed = True  # Mark that this task accepts incoming data updates!
              Settings.Tasks[ltaskindex].enabled  = True
              Settings.Tasks[ltaskindex].interval = 0
              Settings.Tasks[ltaskindex].senddataenabled[self.controllerindex]=True
              Settings.Tasks[ltaskindex].controlleridx[self.controllerindex]=int(dp.sensordata["idx"])
              if TempEvent is not None:
               Settings.Tasks[ltaskindex].taskname = TempEvent.PLUGIN_NAME.replace(" ","")
               for v in range(dvaluecount):
                Settings.Tasks[ltaskindex].valuenames[v] = TempEvent.valuenames[v]
               Settings.Tasks[ltaskindex].taskdevicepluginconfig[0] = TempEvent.vtype
               Settings.Tasks[ltaskindex].vtype = TempEvent.vtype
              else:
               Settings.Tasks[ltaskindex].taskname = Settings.Tasks[ltaskindex].PLUGIN_NAME.replace(" ","")
              Settings.Tasks[ltaskindex].valuecount = dvaluecount
              Settings.savetasks()
           if ltaskindex<0:
            return False
           misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sensordata update arrived from unit "+str(dp.sensordata["sunit"])) # save received values
           if Settings.Tasks[ltaskindex].remotefeed:
            for v in range(dvaluecount):
             Settings.Tasks[ltaskindex].set_value(v+1,dp.sensordata["values"][v],False)
            Settings.Tasks[ltaskindex].plugin_senddata()

        elif dp.pkgtype==7: # process incoming command
          if int(dp.cmdpacket["sunit"])==int(Settings.Settings["Unit"]):
           return False
          un = getunitordfromnum(dp.cmdpacket["sunit"])
          if un>-1: # refresh lastseen data
           Settings.p2plist[un]["lastseen"] = datetime.now()
           Settings.p2plist[un]["lastrssi"] = rssi
          else:
           Settings.p2plist.append({"protocol":"LORA","unitno":dp.cmdpacket["sunit"],"name":"","build":0,"type":0,"mac":"","lastseen":datetime.now(),"lastrssi":rssi,"cap":1})
          if (int(Settings.Settings["Unit"])==int(dp.cmdpacket["dunit"])) or (0==int(dp.cmdpacket["dunit"])): # process only if we are the destination or broadcast
           misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Command arrived from "+str(dp.cmdpacket["sunit"]))
#           print(dp.cmdpacket["cmdline"]) # DEBUG
           commands.doExecuteCommand(dp.cmdpacket["cmdline"],True)


 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1): # called by plugin
  if self.enabled and self.initialized and self.enablesend:
   if tasknum is None:
    return False
   if int(idx)>0:
    if Settings.Tasks[tasknum].remotefeed == False:  # do not republish received values
     dp2 = p2pbuffer.data_packet()
     dp2.sensordata["sunit"] = Settings.Settings["Unit"]
     dp2.sensordata["dunit"] = self.defaultunit
     dp2.sensordata["idx"] = idx
     if tasknum>-1:
      dp2.sensordata["pluginid"] = Settings.Tasks[tasknum].pluginid
     else:
      dp2.sensordata["pluginid"] = 33
     dp2.sensordata["valuecount"] = Settings.Tasks[tasknum].valuecount
     for u in range(Settings.Tasks[tasknum].valuecount):
      dp2.sensordata["values"][u] = Settings.Tasks[tasknum].uservar[u]
     dp2.encode(5)
     return self.lora.lorasend(dp2.buffer)

 def sendcommand(self,unitno,commandstr):
  if self.enabled and self.initialized and self.enablesend:
     dpc = p2pbuffer.data_packet()
     dpc.cmdpacket["sunit"] = Settings.Settings["Unit"]
     dpc.cmdpacket["dunit"] = unitno
     dpc.cmdpacket["cmdline"] = commandstr
     dpc.encode(7)
     return self.lora.lorasend(dpc.buffer)

 def timer_thirty_second(self):
  try:
   if self.enabled and (time.time()>self.sysinfosent+REPORTINTERVAL) and self.initialized and self.connected:
    if self.sendsysinfo():
     self.sysinfosent = time.time()
  except Exception as e:
   self.sysinfosent = 0

 def sendsysinfo(self):
  if self.enabled and self.initialized and self.enablesend:
    dp = p2pbuffer.data_packet()
    try:
     defdev = Settings.NetMan.getprimarydevice()
    except:
     defdev = -1
    if defdev != -1:
     dp.infopacket["mac"] = Settings.NetworkDevices[defdev].mac
    else:
     dp.infopacket["mac"] = "00:00:00:00:00:00"
    dp.infopacket["unitno"] = int(Settings.Settings["Unit"])
    dp.infopacket["build"] = int(rpieGlobals.BUILD)
    dp.infopacket["name"] = Settings.Settings["Name"]
    dp.infopacket["type"] = int(rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD)
    # CAPABILITIES byte: first bit 1 if able to send, second bit 1 if able to receive
    dp.infopacket["cap"] = int(CAPABILITY_BYTE)
    dp.encode(1)
    return self.lora.lorasend(dp.buffer)
  return False

class LoRaRcvCont(LoRa):
    def __init__(self, receiverfunc=None, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.receiverfunc=receiverfunc
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.tx_active = False
        self.tx_start  = 0
        self.tx_end    = 0
        self.nexttransmit = 0
        self.loraduty  = 100

    def on_rx_done(self):
#        print("\nRxDone")
        payload = self.read_payload(nocheck=True)
        rssi = self.get_pkt_rssi_value()
#        print(bytes(payload).decode("utf-8",'ignore'))
#        print(rssi)
#        print(payload,len(payload),type(payload))
#        for i in range(0,len(payload)):
#         print(payload[i])
        bpayload = bytes(payload)
#        print(bpayload)
        if self.receiverfunc:
          self.receiverfunc(bpayload,rssi)
        self.clear_irq_flags(RxDone=1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        self.tx_end = millis()
        self.nexttransmit = ((self.tx_end-self.tx_start)*self.loraduty)+self.tx_end
#        print("\nTxDone") # DEBUG
        self.set_mode(MODE.STDBY)
        self.clear_irq_flags(TxDone=1) # clear txdone IRQ flag
#        self.set_dio_mapping([0] * 6)
        self.start()

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError") # DEBUG
        print(self.get_irq_flags())

    def start(self):
        self.set_dio_mapping([0] * 6)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        self.tx_active = False
#        while True: # DEBUG
#            time.sleep(1)
#            rssi_value = self.get_rssi_value()
#            status = self.get_modem_status()
#            sys.stdout.flush()
#            sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))

    def lorasend(self,payload):
       if self.tx_active:
        return False
       self.tx_start = millis()
       if self.tx_start<self.nexttransmit:
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Next possible transmit "+str(self.nexttransmit))
        return False
       self.tx_active = True
       try:
        self.write_payload(list(payload))
        self.set_dio_mapping([1,0,0,0,0,0])
       except:
        self.tx_active = False
        return False
       self.tx_start = millis()
       self.set_mode(MODE.TX)
#       print("Sending ",payload) #DEBUG
       return True

try:
 class LoRaRcvCont1262(SX1262):
    def __init__(self, spi_bus, spi_ce, irq, rst, gpio, receiverfunc=None):
        super(LoRaRcvCont1262, self).__init__(spi_bus, spi_ce, irq, rst, gpio)
        self.receiverfunc=receiverfunc
        self.tx_active = False
        self.tx_start  = 0
        self.tx_end    = 0
        self.nexttransmit = 0
        self.loraduty  = 100

    def get_freq(self):
        return self.frequency

    def callbackfunc(self,events):
      if events & SX1262.RX_DONE:
        self.tx_active = False
        msg, err = self.recv()
        error = SX1262.STATUS[err]
        rssi = self.getRSSI()
        if self.receiverfunc:
          self.receiverfunc(msg,rssi)
      if events & SX1262.TX_DONE:
        self.tx_end = millis()
        self.nexttransmit = ((self.tx_end-self.tx_start)*self.loraduty)+self.tx_end
#        print("\nTxDone") # DEBUG
        self.tx_active = False

    def start(self):
        self.tx_active = False
        self.setBlockingCallback(False, self.callbackfunc)

    def lorasend(self,payload):
       if self.tx_active:
        return False
       self.tx_start = millis()
       if self.tx_start<self.nexttransmit:
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Next possible transmit "+str(self.nexttransmit))
        return False
       self.tx_active = True
       try:
        self.tx_start = millis()
        self.send(payload)
       except:
        self.tx_active = False
        return False
       print("Sending ",payload) #DEBUG
       return True
except:
 class LoRaRcvCont1262():
   def __init__():
    pass

# Helper functions

def getunitordfromnum(unitno):
  for n in range(len(Settings.p2plist)):
   if int(Settings.p2plist[n]["unitno"]) == int(unitno) and str(Settings.p2plist[n]["protocol"]) == "LORA":
    return n
  return -1
