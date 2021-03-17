#!/usr/bin/env python3
#############################################################################
###################### Serial GPS plugin for RPIEasy ########################
#############################################################################
#
# Serial GPS plugin
#
# Copyright (C) 2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
# Updated by bsimmo - https://github.com/bsimmo
#
import datetime
import json
import re
import threading
import time
import commands
import lib.lib_serial as rpiSerial
import misc
import plugin
import rpieGlobals
import rpieTime
import webserver

class Plugin(plugin.PluginProto):
    PLUGIN_ID = 82
    PLUGIN_NAME = "Position - GNSS/GPS (TESTING)"
    PLUGIN_VALUENAME1 = "Latitude"
    PLUGIN_VALUENAME2 = "Longitude"
    PLUGIN_VALUENAME3 = "Altitude"
    PLUGIN_VALUENAME4 = "Speed"

    GPSDAT = {
        'strType': None,
        'fixTime': "000000",
        'lat': None,
        'latDir': None,
        'lon': None,
        'lonDir': None,
        'fixQual': None,
        'numSat': "0",
        'horDil': "0",
        'alt': "0",
        'altUnit': None,
        'galt': None,
        'galtUnit': None,
        'DPGS_updt': None,
        'DPGS_ID': None
    }
    GPSTRACK = {
        'strType': None,
        'trueTrack': None,
        'trueTrackRel': None,
        'magnetTrack': None,
        'magnetTrackRel': None,
        'speedKnot': None,
        'speedKnotUnit': None,
        'speedKm': "0.0",
        'speedKmUnit': None,
    }
    GPSDATE = {
        'strType': None,
        'fixTime': "000000",
        'day': "0",
        'mon': "0",
        'year': "0",
        'lzoneh': None,
        'lzonem': None
    }
    GNSSRMC = {'strType' : None,
              'fixTime' : "000000",
              'status' : None,
              'lat' : None,
              'latdir' : None,
              'lon' : None,
              'londir' : None,
              'speed_over_ground_knots' : None,
              'track_made_good' : None,
              'fixDate' : "000000",
              'mag_variation' : None,
              'mag_variation_dir' : None,
              'faa_mode' : None,
              'checksum' : None
              }


    def __init__(self, taskindex):  # general init
        plugin.PluginProto.__init__(self, taskindex)
        self.dtype = rpieGlobals.DEVICE_TYPE_SER
        self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
        self.readinprogress = 0
        self.valuecount = 4
        self.senddataoption = True
        self.timeroption = True
        self.timeroptional = False
        self.formulaoption = True
        self.initialized = False
        self.validloc = -1
        self.bgproc = None
        self.serdev = None
        self.baud = 9600
        self.decimals = [6, 6, 1, 1]
        self.lat = 0
        self.lon = 0
        self.devfound = False
        self.gnssdate = 0
        self.gnsstime = 0

    def plugin_exit(self):
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "Exiting Plugin")
        self.initialized = False
        self.validloc = -1
        try:
            self.serdev.close()
            self.serdev = None
        except:
            pass

        try:
            self.bgproc.join()
            self.bgproc = None
        except:
            pass

    def plugin_init(self, enableplugin=None):
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "Plugin Init")
        plugin.PluginProto.plugin_init(self, enableplugin)
        self.readinprogress = 0
        self.initialized = False
        self.devfound = False

        try:
            if str(self.taskdevicepluginconfig[0]) != "0" and str(
                    self.taskdevicepluginconfig[0]).strip(
                    ) != "" and self.baud != 0 and self.enabled:
                if self.enabled:
                    misc.addLog(
                        rpieGlobals.LOG_LEVEL_INFO, "Try to init serial " +
                        str(self.taskdevicepluginconfig[0]) + " speed " +
                        str(self.baud))
                    self.connect()

                    if self.initialized:
                        pn = self.taskdevicepluginconfig[0].split("/")
                        misc.addLog(rpieGlobals.LOG_LEVEL_INFO,
                                    "Search for GNSS/GPS...")
                        self.ports = str(pn[-1])
                        self.bgproc = threading.Thread(target=self.bgreceiver)
                        self.bgproc.daemon = True
                        self.bgproc.start()
                else:
                    self.ports = 0
                    try:
                        self.serdev.close()  # close in case if already opened by ourself
                    except:
                        pass

        except Exception as e:
            misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "GNSS/GPS init error " + str(e))

    def webform_load(self):
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "Webform Loading")
        choice1 = self.taskdevicepluginconfig[0]
        try:
         options = rpiSerial.serial_portlist()
        except:
         options = []
        if len(options) > 0:
            webserver.addHtml("<tr><td>Serial Device:<td>")
            webserver.addSelector_Head("p082_addr", False)
            for o in range(len(options)):
                webserver.addSelector_Item(options[o], options[o],
                                           (str(options[o]) == str(choice1)),
                                           False)
            webserver.addSelector_Foot()
            webserver.addFormNote(
                "If using GPIO UART on the RaspberryPi, use 'sudo raspi-config' at the terminal: Select P3- Interface Options, then P6- Serial Port. /n Say NO to Login Shell, then YES to Serial Port, then reboot."
            )
        else:
            webserver.addFormNote("No serial or USB ports found")
        webserver.addFormCheckBox("Enable time decoding","p082_time",self.taskdevicepluginconfig[1])

        webserver.addHtml("<tr><td>Fix:<td>")
        time.sleep(2)  # wait to get reply
        webserver.addHtml(str(self.validloc))

        if self.initialized and self.validloc != 0:
            try:
                webserver.addHtml("<tr><td>Satellites in use:<td>")
                webserver.addHtml(self.GPSDAT["numSat"])
                webserver.addHtml("<tr><td>HDOP:<td>")
                webserver.addHtml(self.GPSDAT["horDil"])
            except:
                misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, f"webserver GNSS info failed, initialized {self.initialized}, validloc {self.validloc}")
                pass
            webserver.addHtml("<tr><td>UTC Time:<td>")
            notime = True
            try:
                webserver.addHtml(f"{str(self.gnssdate)} {str(self.gnsstime)}")
                notime = False
            except:
                pass
            if notime: #fallback
             try:
              gpstime = self.GPSDAT["fixTime"][0:2]+":"+ self.GPSDAT["fixTime"][2:4]+":"+self.GPSDAT["fixTime"][4:6]
              webserver.addHtml(self.GPSDATE["year"]+"-"+self.GPSDATE["mon"]+"-"+self.GPSDATE["day"]+" "+gpstime)
             except:
              pass

        return True

    def webform_save(self, params):
        par = webserver.arg("p082_addr", params)
        self.taskdevicepluginconfig[0] = str(par)
        if (str(webserver.arg("p082_time",params))=="on"):
         self.taskdevicepluginconfig[1] = 1
        else:
         self.taskdevicepluginconfig[1] = 0
        return True

    def plugin_read(self):
        result = False

        if self.initialized and self.readinprogress == 0 and self.enabled:
            self.readinprogress = 1
            if self.validloc == 1:
                try:
                    self.set_value(1, self.lat, False)
                    self.set_value(2, self.lon, False)
                    self.set_value(3, self.GPSDAT['alt'], False)
                    self.set_value(4, self.GPSTRACK['speedKm'], False)
                except:
                    pass

                self.plugin_senddata()
            self._lastdataservetime = rpieTime.millis()
            result = True
            self.readinprogress = 0
        return result

    def connect(self):
        try:
            if self.serdev.isopened():
                self.initialized = True
                return True
        except:
            pass

        try:
            self.serdev.close()  # close in case if already opened by ourself
            self.serdev = None
        except:
            pass

        try:
            self.serdev = rpiSerial.SerialPort(
                self.taskdevicepluginconfig[0],
                self.baud,
                ptimeout=1,
                pbytesize=rpiSerial.EIGHTBITS,
                pstopbits=rpiSerial.STOPBITS_ONE)
            misc.addLog(
                rpieGlobals.LOG_LEVEL_INFO,
                f"Serial connected {str(self.taskdevicepluginconfig[0])}")
        except Exception as e:
            misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Serial failed " + str(e))

        try:
            self.initialized = self.serdev.isopened()
        except Exception as e:
            self.initialized = False
            misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Open failed " + str(e))

    def bgreceiver(self):
        if self.initialized:
            self.validloc = -1
            while self.enabled and self.initialized:
                if self.serdev is not None:
                    try:
                        reading = self.serdev.readline()
                        if reading:
                            recdata = reading.decode("utf-8")
                            self.parseResponse(recdata)
                            try:
                             if self.taskdevicepluginconfig[1]==1:
                              self.create_datetime()  # this may be placed under parseResponse() proper when a proper package arrives
                            except:
                             pass
                        else:
                            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "bgreceiver reading failed")
                            time.sleep(0.001)
                    except:
                        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "bgreceiver serial readline failed")
                        time.sleep(0.5)

            try:
                self.serdev.close()
            except:
                misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "bgreceiver serial close failed")
                pass

    def parseResponse(self, gpsChars):
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "We have a response")
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE, f"gpsChars = {gpsChars}")
        try:
            if '*' in gpsChars:
                gpsStr, chkSum = gpsChars.split('*')
            elif '_' in gpsChars:
                gpsStr, chkSum = gpsChars.split('_')
            else:
                chkSum = gpsChars[-2:]
                gpsStr = gpsChars[:-2]
        except:
            chkSum = gpsChars[-2:]
            gpsStr = gpsChars[:-2]

        gpsComponents = gpsStr.split(',')
        gpsStart = gpsComponents[0]

        if ("GGA" in gpsStart):
            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Valid GGA from GNSS/GPS")
            if self.devfound == False:
                misc.addLog(rpieGlobals.LOG_LEVEL_INFO, "GNSS/GPS found")
                self.devfound = True

            prevval = self.validloc
            self.validloc = 0
            chkVal = 0

            for ch in gpsStr[1:]:  # Remove the $
                chkVal ^= ord(ch)

            if (chkVal == int(chkSum, 16)):
                misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE, f"chkVal = {chkVal}")
                for i, k in enumerate([
                        'strType', 'fixTime', 'lat', 'latDir', 'lon', 'lonDir',
                        'fixQual', 'numSat', 'horDil', 'alt', 'altUnit',
                        'galt', 'galtUnit', 'DPGS_updt', 'DPGS_ID'
                ]):
                    self.GPSDAT[k] = gpsComponents[i]

                try:
                    if int(self.GPSDAT['fixQual']) > 0:
                        self.validloc = 1
                except:
                    self.validloc = 0

                if self.validloc == 1:  # refresh values
                    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "GPS fix OK")

                    self.lat = dm_to_sd(self.GPSDAT['lat'])
                    if self.GPSDAT['latDir'] == 'S':
                        self.lat = self.lat * -1

                    self.lon = dm_to_sd(self.GPSDAT['lon'])
                    if str(self.GPSDAT['lonDir']) == 'W':
                        self.lon = self.lon * -1

                    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, f"latitude(dm) = {self.GPSDAT['lat']} : longitude(dm) = {self.GPSDAT['lon']}")
                    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, f"latitude(sd) = {self.lat} : longitude(sd) = {self.lon}")

            if self.validloc != prevval:  # status changed
                if self.validloc == 1:
                    commands.rulesProcessing("GPS#GotFix",
                                             rpieGlobals.RULE_SYSTEM)
                else:
                    commands.rulesProcessing("GPS#LostFix",
                                             rpieGlobals.RULE_SYSTEM)

            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE, f"GPSDAT = {json.dumps(self.GPSDAT)}")

        if ("RMC" in gpsStart):
            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Valid RMC from GNSS/GPS")

            chkVal = 0
            for ch in gpsStr[1:]:  # Remove the $
                chkVal ^= ord(ch)
            if (chkVal == int(chkSum, 16)):
                for i, k in enumerate([
                        'strType', 'fixTime', 'status', 'lat', 'latdir', 'lon',
                        'londir', 'speed_over_ground_knots', 'track_made_good','fixDate', 'mag_variation', 'mag_variation_dir', 'faa_mode', 'checksum'
                ]):
                    self.GNSSRMC[k] = gpsComponents[i]

                misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE, f"GNSSRMC = {json.dumps(self.GNSSRMC)}")

        if ("ZDA" in gpsStart):
            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Valid ZDA from GNSS/GPS")
            chkVal = 0
            for ch in gpsStr[1:]:  # Remove the $
                chkVal ^= ord(ch)
            if (chkVal == int(chkSum, 16)):
                for i, k in enumerate([
                        'strType', 'fixTime', 'day', 'mon', 'year', 'lzoneh',
                        'lzonem'
                ]):
                    self.GPSDATE[k] = gpsComponents[i]

                misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE, f"GPSDATE = {json.dumps(self.GPSDATE)}")

        if ("VTG" in gpsStart):
            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Valid VTG from GNSS/GPS")
            chkVal = 0
            for ch in gpsStr[1:]:  # Remove the $
                chkVal ^= ord(ch)

            if (chkVal == int(chkSum, 16)):
                for i, k in enumerate([
                        'strType', 'trueTrack', 'trueTrackRel', 'magnetTrack',
                        'magnetTrackRel', 'speedKnot', 'speedKnotUnit',
                        'speedKm', 'speedKmUnit'
                ]):
                    self.GPSTRACK[k] = gpsComponents[i]
                # print(gpsChars)
                misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE, f"GPSTRACK = {json.dumps(self.GPSTRACK)}")

    def create_datetime(self):
        try:
            if self.GPSDATE["strType"] is not None:

                self.gnsstime = timestamp(self.GPSDAT["fixTime"])
                #this next line untested
                self.gnssdate = datestamp( f'{self.GPSDATE["day"]}{self.GPSDATE["mon"]}{self.GPSDATE["year"]}' )
            else:
                self.gnsstime = timestamp(self.GNSSRMC["fixTime"])
                self.gnssdate = datestamp(self.GNSSRMC["fixDate"])
            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, f"Date = {self.gnssdate}, Time = {self.gnsstime}")
        except Exception as e:
         self.taskdevicepluginconfig[1] = 0 # auto self-defense

def timestamp(s):
    '''
    Converts a timestamp given in "hhmmss[.ss]" ASCII text format to a
    datetime.time object
    '''
    ms_s = s[6:]
    ms = ms_s and int(float(ms_s) * 1000000) or 0

    t = datetime.time(
        hour=int(s[0:2]),
        minute=int(s[2:4]),
        second=int(s[4:6]),
        microsecond=ms)
    return t


def datestamp(s):
    '''
    Converts a datestamp given in "DDMMYY" ASCII text format to a
    datetime.datetime object
    '''
    cok = False
    try:
     res = datetime.datetime.strptime(s, '%d%m%y').date()
     cok = True
    except:
     pass
    if cok==False: #fallback to DDMMYYYY
     try:
      res = datetime.datetime.strptime(s, '%d%m%Y').date()
      cok = True
     except:
      pass
    if cok==False: #return original as lastresort
     res = s
    return res

def dm_to_sd(dm):
    '''
    Converts a geographic co-ordinate given in "degrees/minutes" dddmm.mmmm
    format (eg, "12319.943281" = 123 degrees, 19.943281 minutes) to a signed
    decimal (python float) format
    '''
    # '12319.943281'
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE, f"In dm_to_sd, {dm}")
    if not dm or dm == '0':
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "Not dm :-(")
        return 0.

    try:
        d, m = re.match(r'^(\d+)(\d\d\.\d+)$', dm).groups()
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, f"dm is now sd: {d} and {m}")
        return float(d) + float(m) / 60
    except:
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_DEV, "Tried to convert dm to sd but FAILED :-(")
        return 0.
