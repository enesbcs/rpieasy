#! /usr/bin/env python3
#
#  Copyright (C) 2004-2020 Savoir-faire Linux Inc. Inc
#
# Author: Guillaume Roguez <guillaume.roguez@savoirfairelinux.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.
#

"""DRing controlling class through DBUS"""

import sys
import os
import random
import time
import hashlib
import threading

from threading import Thread
from functools import partial
from lib.dringctrl.errorsDring import DRingCtrlAccountError, DRingCtrlError, DRingCtrlDBusError, DRingCtrlDeamonError
from gi.repository import GLib, GObject # pip3 install PyGObject

try:
    import dbus # apt install dbus-x11
    import dbus.mainloop.glib
    from dbus.mainloop.glib import DBusGMainLoop # pip3 install dbus-python
except ImportError as e:
    raise DRingCtrlError(str(e))


DBUS_DEAMON_OBJECT = 'cx.ring.Ring'
DBUS_DEAMON_PATH = '/cx/ring/Ring'


class DRingCtrl(Thread):
    def __init__(self, name, autoAnswer):
        if sys.version_info[0] < 3:
            super(DRingCtrl, self).__init__()
        else:
            super().__init__()
        global nmainloop
        self.registered = False
        self.activeCalls = {}  # list of active calls (known by the client)
        self.activeConferences = {}  # list of active conferences
        self.account = None  # current active account
        self.name = name # client name
        self.autoAnswer = autoAnswer

        self.currentCallId = ""
        self.currentConfId = ""

        self.isStop = False
        # Glib MainLoop for processing callbacks
        self.loop = GLib.MainLoop()

        # client registered to sflphoned ?
        self.register()
#        print("dringctrl init ended")

#    def __del__(self):
#        try:
#         self.unregister()
#        except:
#         pass
#        #self.loop.quit() # causes exception

    def stopThread(self):
        self.isStop = True

    def notifications(self,bus, message):
      try:
       if DBUS_DEAMON_PATH in message.get_path():
        proc = False
        if message.get_member() == "callStateChanged":
         proc = True
         ct = 0
         cid = 0
         stat = 0
         for arg in message.get_args_list():
#          print(arg)#debug
          if ct==0:
           cid = arg
          elif ct==1:
           stat = arg
           if stat == "INCOMING":
            stat = "RINGING"
          elif ct==2:
           self.onCallStateChanged(cid,stat,arg)
           if stat=="RINGING":
            try:
             callDetails = self.getCallDetails(cid)
             self.onIncomingCall(callDetails['ACCOUNTID'],cid,callDetails['PEER_NUMBER'])
            except Exception as e:
             print(e)
           break
          ct+=1
        elif message.get_member() == "incomingAccountMessage":
         proc = True
         ct = 0
         aid = 0
         mid = 0
         fromid = 0
         al = message.get_args_list()
         api2 = False
         if len(al)==3:
          api2 = True
         for arg in message.get_args_list():
          if ct==0:
           aid = arg
          elif ct==1:
           mid = arg
          elif ct==2:
           fromid = arg
          elif ct==3:
           if api2:
            arg = fromid
            fromid = mid
            mid = aid
           if "text/plain" in arg:
            self.onIncomingAccountMessage(aid,mid,fromid,arg)
            break
          ct+=1
#        if proc==False:
#         print("----",message.get_path(),message.get_member())
#         print([arg for arg in message.get_args_list()])
      except:
       pass
      return True

    def register(self):
        global nmainloop
        if self.registered:
            return

        try:
            # register the main loop for d-bus events
            dbus.set_default_main_loop(nmainloop)
            bus = dbus.SessionBus(mainloop=nmainloop)
#            bus.add_match_string_non_blocking("eavesdrop=true") # wildcard
            bus.add_message_filter(self.notifications)

        except dbus.DBusException as e:
            raise DRingCtrlDBusError(str(e))

        if not bus.name_has_owner(DBUS_DEAMON_OBJECT) :
            raise DRingCtrlDBusError(("Unable to find %s in DBUS." % DBUS_DEAMON_OBJECT)
                                     + " Check if dring is running")
        try:
            proxy_instance = bus.get_object(DBUS_DEAMON_OBJECT,
                DBUS_DEAMON_PATH+'/Instance', introspect=False)
            proxy_callmgr = bus.get_object(DBUS_DEAMON_OBJECT,
                DBUS_DEAMON_PATH+'/CallManager', introspect=False)
            proxy_confmgr = bus.get_object(DBUS_DEAMON_OBJECT,
                DBUS_DEAMON_PATH+'/ConfigurationManager', introspect=False)
            proxy_videomgr = bus.get_object(DBUS_DEAMON_OBJECT,
                DBUS_DEAMON_PATH+'/VideoManager', introspect=False)

            self.instance = dbus.Interface(proxy_instance,
                DBUS_DEAMON_OBJECT+'.Instance')
            self.callmanager = dbus.Interface(proxy_callmgr,
                DBUS_DEAMON_OBJECT+'.CallManager')
            self.configurationmanager = dbus.Interface(proxy_confmgr,
                DBUS_DEAMON_OBJECT+'.ConfigurationManager')
            if proxy_videomgr:
                self.videomanager = dbus.Interface(proxy_videomgr,
                    DBUS_DEAMON_OBJECT+'.VideoManager')

        except dbus.DBusException as e:
            raise DRingCtrlDBusError("Unable to bind to dring DBus API")

        try:
            self.instance.Register(os.getpid(), self.name)
            self.registered = True

        except dbus.DBusException as e:
            raise DRingCtrlDeamonError("Client registration failed")

        try:
            proxy_callmgr.connect_to_signal('incomingCall', self.onIncomingCall)
            proxy_callmgr.connect_to_signal('callStateChanged', self.onCallStateChanged)
            proxy_callmgr.connect_to_signal('conferenceCreated', self.onConferenceCreated)
            proxy_confmgr.connect_to_signal('accountsChanged', self.onAccountsChanged)
            proxy_confmgr.connect_to_signal('dataTransferEvent', self.onDataTransferEvent)
            proxy_confmgr.connect_to_signal('incomingAccountMessage', self.onIncomingAccountMessage)

        except dbus.DBusException as e:
            raise DRingCtrlDBusError("Unable to connect to dring DBus signals")

    def unregister(self):
        if not self.registered:
            return

        try:
            self.instance.Unregister(os.getpid())
            self.registered = False
            self.isStop = True
        except:
            raise DRingCtrlDeamonError("Client unregistration failed")

    def isRegistered(self):
        return self.registered

    #
    # Signal handling
    #

    def onIncomingCall_cb(self, callId):
        if self.autoAnswer:
            self.Accept(callId)
        pass

    def onCallHangup_cb(self, callId, dummy=None):
        pass

    def onCallConnecting_cb(self, callId):
        pass

    def onCallRinging_cb(self, callId):
        pass

    def onCallHold_cb(self):
        pass

    def onCallInactive_cb(self):
        pass

    def onCallCurrent_cb(self):
        pass

    def onCallBusy_cb(self):
        pass

    def onCallFailure_cb(self):
        pass

    def onCallOver_cb(self):
        pass

    def onIncomingAccountMessage(self, accountId, messageId, fromAccount, payloads):
        pass

    def onIncomingCall(self, account, callid, to):
        """ On incoming call event, add the call to the list of active calls """

        self.activeCalls[callid] = {'Account': account,
                                         'To': to,
                                      'State': ''}
        self.currentCallId = callid
        self.onIncomingCall_cb(callid)


    def onCallHangUp(self, callid, state):
        """ Remove callid from call list """

        self.activeCalls[callid]['State'] = state
        self.onCallHangup_cb(callid)
        self.currentCallId = ""

    def onCallConnecting(self, callid, state):
        """ Update state for this call to Ringing """

        self.activeCalls[callid]['State'] = state
        self.onCallConnecting_cb(callid)

    def onCallRinging(self, callid, state):
        """ Update state for this call to Ringing """

        self.activeCalls[callid]['State'] = state
        self.onCallRinging_cb(callid)


    def onCallHold(self, callid, state):
        """ Update state for this call to Hold """

        self.activeCalls[callid]['State'] = state
        self.onCallHold_cb()


    def onCallCurrent(self, callid, state):
        """ Update state for this call to current """

        self.activeCalls[callid]['State'] = state
        self.onCallCurrent_cb()

    def onCallInactive(self, callid, state):
        """ Update state for this call to current """

        self.activeCalls[callid]['State'] = state
        self.onCallInactive_cb()

    def onCallBusy(self, callid, state):
        """ Update state for this call to busy """

        self.activeCalls[callid]['State'] = state
        self.onCallBusy_cb()


    def onCallFailure(self, callid, state):
        """ Handle call failure """

        self.activeCalls[callid]['State'] = state
        self.onCallFailure_cb()

    def onCallOver(self, callid):
        """ Handle call failure """

        self.onCallOver_cb()
        del self.activeCalls[callid]

    def onCallStateChanged(self, callid, state, code):
        """ On call state changed event, set the values for new calls,
        or delete the call from the list of active calls
        """
#        print(("On call state changed " + callid + " " + state))

        if callid not in self.activeCalls:
#            print("This call didn't exist!: " + callid + ". Adding it to the list.")
            callDetails = self.getCallDetails(callid)
            self.activeCalls[callid] = {'Account': callDetails['ACCOUNTID'],
                                             'To': callDetails['PEER_NUMBER'],
                                          'State': state,
                                          'Code': code }

        self.currentCallId = callid

        if state == "HUNGUP":
            self.onCallHangUp(callid, state)
        elif state == "CONNECTING":
            self.onCallConnecting(callid, state)
        elif state == "RINGING" or state == "INCOMING":
            self.onCallRinging(callid, state)
        elif state == "CURRENT":
            self.onCallCurrent(callid, state)
        elif state == "HOLD":
            self.onCallHold(callid, state)
        elif state == "BUSY":
            self.onCallBusy(callid, state)
        elif state == "FAILURE":
            self.onCallFailure(callid, state)
        elif state == "OVER":
            self.onCallOver(callid)
        elif state == "INACTIVE":
            self.onCallInactive(callid,state)
        else:
            print("unknown state:" + str(state))
#        print(state)

    def onConferenceCreated_cb(self):
        pass

    def onConferenceCreated(self, confId):
        self.currentConfId = confId
        self.onConferenceCreated_cb()

    def onDataTransferEvent(self, transferId, code):
        pass

    #
    # Account management
    #

    def _valid_account(self, account):
        account = account or self.account
        if account is None:
            raise DRingCtrlError("No provided or current account!")
        return account

    def isAccountExists(self, account):
        """ Checks if the account exists"""

        return account in self.getAllAccounts()

    def isAccountEnable(self, account=None):
        """Return True if the account is enabled. If no account is provided, active account is used"""

        return self.getAccountDetails(self._valid_account(account))['Account.enable'] == "true"

    def isAccountRegistered(self, account=None):
        """Return True if the account is registered. If no account is provided, active account is used"""

        return self.getVolatileAccountDetails(self._valid_account(account))['Account.registrationStatus'] in ('READY', 'REGISTERED')

    def isAccountOfType(self, account_type, account=None):
        """Return True if the account type is the given one. If no account is provided, active account is used"""

        return self.getAccountDetails(self._valid_account(account))['Account.type'] == account_type

    def getAllAccounts(self, account_type=None):
        """Return a list with all accounts"""

        acclist =  map(str, self.configurationmanager.getAccountList())
        if account_type:
            acclist = filter(partial(self.isAccountOfType, account_type), acclist)
        return list(acclist)

    def getAllEnabledAccounts(self):
        """Return a list with all enabled-only accounts"""

        return [x for x in self.getAllAccounts() if self.isAccountEnable(x)]

    def getAllRegisteredAccounts(self):
        """Return a list with all registered-only accounts"""

        return [x for x in self.getAllAccounts() if self.isAccountRegistered(x)]

    def getAccountDetails(self, account=None):
        """Return a list of string. If no account is provided, active account is used"""

        account = self._valid_account(account)
        if self.isAccountExists(account):
            return self.configurationmanager.getAccountDetails(account)
        return []

    def getVolatileAccountDetails(self, account=None):
        """Return a list of string. If no account is provided, active account is used"""

        account = self._valid_account(account)
        if self.isAccountExists(account):
            return self.configurationmanager.getVolatileAccountDetails(account)
        return []

    def setActiveCodecList(self, account=None, codec_list=''):
        """Activate given codecs on an account. If no account is provided, active account is used"""

        account = self._valid_account(account)
        if self.isAccountExists(account):
            codec_list = [dbus.UInt32(x) for x in codec_list.split(',')]
            self.configurationmanager.setActiveCodecList(account, codec_list)

    def addAccount(self, details=None):
        """Add a new account account

        Add a new account to the daemon. Default parameters are \
        used for missing account configuration field.

        Required parameters are type, alias, hostname, username and password

        input details
        """

        if details is None:
            raise DRingCtrlAccountError("Must specifies type, alias, hostname, \
                                  username and password in \
                                  order to create a new account")

        return str(self.configurationmanager.addAccount(details))

    def removeAccount(self, accountID=None):
        """Remove an account from internal list"""

        if accountID is None:
            raise DRingCtrlAccountError("Account ID must be specified")

        self.configurationmanager.removeAccount(accountID)

    def setAccountByAlias(self, alias):
        """Define as active the first account who match with the alias"""

        for testedaccount in self.getAllAccounts():
            details = self.getAccountDetails(testedaccount)
            if (details['Account.enable'] == 'true' and
                details['Account.alias'] == alias):
                self.account = testedaccount
                return
        raise DRingCtrlAccountError("No enabled account matched with alias")

    def getAccountByAlias(self, alias):
        """Get account name having its alias"""

        for account in self.getAllAccounts():
            details = self.getAccountDetails(account)
            if details['Account.alias'] == alias:
                return account

        raise DRingCtrlAccountError("No account matched with alias")

    def setAccount(self, account):
        """Define the active account

        The active account will be used when sending a new call
        """

        if account in self.getAllAccounts():
            self.account = account
        else:
            print(account)
            raise DRingCtrlAccountError("Not a valid account")

    def setFirstRegisteredAccount(self):
        """Find the first enabled account and define it as active"""

        rAccounts = self.getAllRegisteredAccounts()
        if 0 == len(rAccounts):
            raise DRingCtrlAccountError("No registered account !")
        self.account = rAccounts[0]

    def setFirstActiveAccount(self):
        """Find the first enabled account and define it as active"""

        aAccounts = self.getAllEnabledAccounts()
        if 0 == len(aAccounts):
            raise DRingCtrlAccountError("No active account !")
        self.account = aAccounts[0]

    def getAccount(self):
        """Return the active account"""

        return self.account

    def setAccountEnable(self, account=None, enable=False):
        """Set account enabled"""

        account = self._valid_account(account)
        if enable == True:
            details = self.getAccountDetails(account)
            details['Account.enable'] = "true"
            self.configurationmanager.setAccountDetails(account, details)
        else:
            details = self.getAccountDetails(account)
            details['Account.enable'] = "false"
            self.configurationmanager.setAccountDetails(account, details)

    def setAccountRegistered(self, account=None, register=False):
        """ Tries to register the account"""

        account = self._valid_account(account)
        self.configurationmanager.sendRegister(account, register)

    def onAccountsChanged(self):
        print("Accounts changed")

    #
    # Codec manager
    #

    def getAllCodecs(self):
        """ Return all codecs"""

        return [int(x) for x in self.configurationmanager.getCodecList()]

    def getCodecDetails(self, account, codecId):
        """ Return codec details"""
        codecId=dbus.UInt32(codecId)
        return self.configurationmanager.getCodecDetails(account, codecId)

    def getActiveCodecs(self, account=None):
        """ Return all active codecs on given account"""

        account = self._valid_account(account)
        return [int(x) for x in self.configurationmanager.getActiveCodecList(account)]

    def setVideoCodecBitrate(self, account, bitrate):
        """ Change bitrate for all codecs  on given account"""

        for codecId in self.configurationmanager.getActiveCodecList(account):
            details = self.configurationmanager.getCodecDetails(account, codecId)
            details['CodecInfo.bitrate'] = str(bitrate)
            if details['CodecInfo.type'] == 'VIDEO':
                self.configurationmanager.setCodecDetails(account, codecId, details)
    #
    # Call management
    #

    def getAllCalls(self):
        """Return all calls handled by the daemon"""

        return [str(x) for x in self.callmanager.getCallList()]

    def getCallDetails(self, callid):
        """Return informations on this call if exists"""

        return self.callmanager.getCallDetails(callid)

    def printClientCallList(self):
        print("Client active call list:")
        print("------------------------")
        for call in self.activeCalls:
            print("\t" + call)

    def Call(self, dest, account=None):
        """Start a call and return a CallID

        Use the current account previously set using setAccount().
        If no account specified, first registered one in account list is used.

        return callID Newly generated callidentifier for this call
        """

        if dest is None or dest == "":
            raise DRingCtrlError("Invalid call destination")

        # Set the account to be used for this call
        if not self.account:
            self.setFirstRegisteredAccount()

        if self.account != "IP2IP" and not self.isAccountRegistered():
            raise DRingCtrlAccountError("Can't place a call without a registered account")

        # Send the request to the CallManager
        callid = self.callmanager.placeCall(self.account, dest)
        if callid:
            # Add the call to the list of active calls and set status to SENT
            self.activeCalls[callid] = {'Account': self.account, 'To': dest, 'State': 'SENT' }

        return callid


    def HangUp(self, callid):
        """End a call identified by a CallID"""

        if not self.account:
            self.setFirstRegisteredAccount()

        if callid is None or callid == "":
            pass # just to see

        self.callmanager.hangUp(callid)


    def Transfer(self, callid, to):
        """Transfert a call identified by a CallID"""

        if callid is None or callid == "":
            raise DRingCtrlError("Invalid callID")

        self.callmanager.transfert(callid, to)

    def Refuse(self, callid):
        """Refuse an incoming call identified by a CallID"""

        print("Refuse call " + callid)

        if callid is None or callid == "":
            raise DRingCtrlError("Invalid callID")

        self.callmanager.refuse(callid)


    def Accept(self, callid):
        """Accept an incoming call identified by a CallID"""

        print("Accept call " + callid)
        if not self.account:
            self.setFirstRegisteredAccount()

        if not self.isAccountRegistered():
            raise DRingCtrlAccountError("Can't accept a call without a registered account")

        if callid is None or callid == "":
            raise DRingCtrlError("Invalid callID")

        self.callmanager.accept(callid)


    def Hold(self, callid):
        """Hold a call identified by a CallID"""

        if callid is None or callid == "":
            raise DRingCtrlError("Invalid callID")

        self.callmanager.hold(callid)


    def UnHold(self, callid):
        """Unhold an incoming call identified by a CallID"""

        if callid is None or callid == "":
            raise DRingCtrlError("Invalid callID")

        self.callmanager.unhold(callid)


    def Dtmf(self, key):
        """Send a DTMF"""

        self.callmanager.playDTMF(key)


    def _GenerateCallID(self):
        """Generate Call ID"""

        m = hashlib.md5()
        t = int( time.time() * 1000 )
        r = int( random.random()*100000000000000000 )
        m.update(str(t) + str(r))
        callid = m.hexdigest()
        return callid


    def createConference(self, call1Id, call2Id):
        """ Create a conference given the two call ids """

        self.callmanager.joinParticipant(call1Id, call2Id)


    def hangupConference(self, confId):
        """ Hang up each call for this conference """

        self.callmanager.hangUpConference(confId)

    def switchInput(self, callid, inputName):
        """switch to input if exist"""

        return self.callmanager.switchInput(callid, inputName)

    def interruptHandler(self, signum, frame):
        print('Signal handler called with signal ' + str(signum))
        self.stopThread()

    def printAccountDetails(self, account):
        details = self.getAccountDetails(account)
        print(account)
        for k in sorted(details.keys()):
            print("  %s: %s" % (k, details[k]))
        print()

    def sendFile(self, *args, **kwds):
        return self.configurationmanager.sendFile(*args, **kwds)

    def sendTextMessage(self, account, to, message):
        return self.configurationmanager.sendTextMessage(account, to, { 'text/plain': message })

    def getContactDetails(self, account, uri):
        return self.configurationmanager.getContactDetails(account, uri)

    def getContacts(self, account):
        return self.configurationmanager.getContacts(account)

    def lookupName(self, name, account="", nameserver=""):
        return self.configurationmanager.lookupName(account,nameserver,name)

    def run(self):
        """Processing method for this thread"""
        try:
         context = self.loop.get_context()
        except Exception as e:
         print("r",e)#debug
        while self.isStop==False:
            context.iteration(False)
            time.sleep(0.05) # without sleep CPU will be running at 100%
#            if self.isStop:
#                print("++++++++++++++++++ EXIT ++++++++++++++++++++++")
#                return
#print("init mainloop")
#dbus.mainloop.glib.threads_init()
#GLib.threads_init()
#GObject.threads_init()
nmainloop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#gmainloop = GLib.MainLoop()
#print("init glib ok")
