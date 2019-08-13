# Waveshare PN532 NFC Hat control library.
# Author(s): Yehui from Waveshare
#            Tony DiCola
#
# The MIT License (MIT)
#
# Copyright (c) 2019 Waveshare
# Copyright (c) 2015-2018 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
``pn532-nfc-hat``
====================================================

This module will let you communicate with a PN532 NFC Hat using I2C, SPI or UART.
The main difference is the interfaces implements.
"""

import RPi.GPIO as GPIO


# pylint: disable=bad-whitespace
_PREAMBLE                      = 0x00
_STARTCODE1                    = 0x00
_STARTCODE2                    = 0xFF
_POSTAMBLE                     = 0x00

_HOSTTOPN532                   = 0xD4
_PN532TOHOST                   = 0xD5

# PN532 Commands
_COMMAND_DIAGNOSE              = 0x00
_COMMAND_GETFIRMWAREVERSION    = 0x02
_COMMAND_GETGENERALSTATUS      = 0x04
_COMMAND_READREGISTER          = 0x06
_COMMAND_WRITEREGISTER         = 0x08
_COMMAND_READGPIO              = 0x0C
_COMMAND_WRITEGPIO             = 0x0E
_COMMAND_SETSERIALBAUDRATE     = 0x10
_COMMAND_SETPARAMETERS         = 0x12
_COMMAND_SAMCONFIGURATION      = 0x14
_COMMAND_POWERDOWN             = 0x16
_COMMAND_RFCONFIGURATION       = 0x32
_COMMAND_RFREGULATIONTEST      = 0x58
_COMMAND_INJUMPFORDEP          = 0x56
_COMMAND_INJUMPFORPSL          = 0x46
_COMMAND_INLISTPASSIVETARGET   = 0x4A
_COMMAND_INATR                 = 0x50
_COMMAND_INPSL                 = 0x4E
_COMMAND_INDATAEXCHANGE        = 0x40
_COMMAND_INCOMMUNICATETHRU     = 0x42
_COMMAND_INDESELECT            = 0x44
_COMMAND_INRELEASE             = 0x52
_COMMAND_INSELECT              = 0x54
_COMMAND_INAUTOPOLL            = 0x60
_COMMAND_TGINITASTARGET        = 0x8C
_COMMAND_TGSETGENERALBYTES     = 0x92
_COMMAND_TGGETDATA             = 0x86
_COMMAND_TGSETDATA             = 0x8E
_COMMAND_TGSETMETADATA         = 0x94
_COMMAND_TGGETINITIATORCOMMAND = 0x88
_COMMAND_TGRESPONSETOINITIATOR = 0x90
_COMMAND_TGGETTARGETSTATUS     = 0x8A

_RESPONSE_INDATAEXCHANGE       = 0x41
_RESPONSE_INLISTPASSIVETARGET  = 0x4B

_WAKEUP                        = 0x55

_MIFARE_ISO14443A              = 0x00

# Mifare Commands
MIFARE_CMD_AUTH_A                   = 0x60
MIFARE_CMD_AUTH_B                   = 0x61
MIFARE_CMD_READ                     = 0x30
MIFARE_CMD_WRITE                    = 0xA0
MIFARE_CMD_TRANSFER                 = 0xB0
MIFARE_CMD_DECREMENT                = 0xC0
MIFARE_CMD_INCREMENT                = 0xC1
MIFARE_CMD_STORE                    = 0xC2
MIFARE_ULTRALIGHT_CMD_WRITE         = 0xA2

# Prefixes for NDEF Records (to identify record type)
NDEF_URIPREFIX_NONE                 = 0x00
NDEF_URIPREFIX_HTTP_WWWDOT          = 0x01
NDEF_URIPREFIX_HTTPS_WWWDOT         = 0x02
NDEF_URIPREFIX_HTTP                 = 0x03
NDEF_URIPREFIX_HTTPS                = 0x04
NDEF_URIPREFIX_TEL                  = 0x05
NDEF_URIPREFIX_MAILTO               = 0x06
NDEF_URIPREFIX_FTP_ANONAT           = 0x07
NDEF_URIPREFIX_FTP_FTPDOT           = 0x08
NDEF_URIPREFIX_FTPS                 = 0x09
NDEF_URIPREFIX_SFTP                 = 0x0A
NDEF_URIPREFIX_SMB                  = 0x0B
NDEF_URIPREFIX_NFS                  = 0x0C
NDEF_URIPREFIX_FTP                  = 0x0D
NDEF_URIPREFIX_DAV                  = 0x0E
NDEF_URIPREFIX_NEWS                 = 0x0F
NDEF_URIPREFIX_TELNET               = 0x10
NDEF_URIPREFIX_IMAP                 = 0x11
NDEF_URIPREFIX_RTSP                 = 0x12
NDEF_URIPREFIX_URN                  = 0x13
NDEF_URIPREFIX_POP                  = 0x14
NDEF_URIPREFIX_SIP                  = 0x15
NDEF_URIPREFIX_SIPS                 = 0x16
NDEF_URIPREFIX_TFTP                 = 0x17
NDEF_URIPREFIX_BTSPP                = 0x18
NDEF_URIPREFIX_BTL2CAP              = 0x19
NDEF_URIPREFIX_BTGOEP               = 0x1A
NDEF_URIPREFIX_TCPOBEX              = 0x1B
NDEF_URIPREFIX_IRDAOBEX             = 0x1C
NDEF_URIPREFIX_FILE                 = 0x1D
NDEF_URIPREFIX_URN_EPC_ID           = 0x1E
NDEF_URIPREFIX_URN_EPC_TAG          = 0x1F
NDEF_URIPREFIX_URN_EPC_PAT          = 0x20
NDEF_URIPREFIX_URN_EPC_RAW          = 0x21
NDEF_URIPREFIX_URN_EPC              = 0x22
NDEF_URIPREFIX_URN_NFC              = 0x23

_GPIO_VALIDATIONBIT            = 0x80

_ACK                           = b'\x00\x00\xFF\x00\xFF\x00'
_FRAME_START                   = b'\x00\x00\xFF'
# pylint: enable=bad-whitespace

PN532_ERRORS = {
    0x01: 'PN532 ERROR TIMEOUT',
    0x02: 'PN532 ERROR CRC',
    0x03: 'PN532 ERROR PARITY',
    0x04: 'PN532 ERROR COLLISION_BITCOUNT',
    0x05: 'PN532 ERROR MIFARE_FRAMING',
    0x06: 'PN532 ERROR COLLISION_BITCOLLISION',
    0x07: 'PN532 ERROR NOBUFS',
    0x09: 'PN532 ERROR RFNOBUFS',
    0x0a: 'PN532 ERROR ACTIVE_TOOSLOW',
    0x0b: 'PN532 ERROR RFPROTO',
    0x0d: 'PN532 ERROR TOOHOT',
    0x0e: 'PN532 ERROR INTERNAL_NOBUFS',
    0x10: 'PN532 ERROR INVAL',
    0x12: 'PN532 ERROR DEP_INVALID_COMMAND',
    0x13: 'PN532 ERROR DEP_BADDATA',
    0x14: 'PN532 ERROR MIFARE_AUTH',
    0x18: 'PN532 ERROR NOSECURE',
    0x19: 'PN532 ERROR I2CBUSY',
    0x23: 'PN532 ERROR UIDCHECKSUM',
    0x25: 'PN532 ERROR DEPSTATE',
    0x26: 'PN532 ERROR HCIINVAL',
    0x27: 'PN532 ERROR CONTEXT',
    0x29: 'PN532 ERROR RELEASED',
    0x2a: 'PN532 ERROR CARDSWAPPED',
    0x2b: 'PN532 ERROR NOCARD',
    0x2c: 'PN532 ERROR MISMATCH',
    0x2d: 'PN532 ERROR OVERCURRENT',
    0x2e: 'PN532 ERROR NONAD',
}

class PN532Error(Exception):
    """PN532 error code"""
    def __init__(self, err):
        Exception.__init__(self)
        self.err = err
        self.errmsg = PN532_ERRORS[err]

class BusyError(Exception):
    """Base class for exceptions in this module."""
    pass


class PN532:
    """PN532 driver base, must be extended for I2C/SPI/UART interfacing"""

    def __init__(self, *, debug=False, reset=None):
        """Create an instance of the PN532 class
        """
        self.debug = debug
        if reset:
            if debug:
                print("Resetting")
            self._reset(reset)

        try:
            self._wakeup()
            self.get_firmware_version() # first time often fails, try 2ce
            return
        except (BusyError, RuntimeError):
            pass
        self.get_firmware_version()

    def _gpio_init(self, **kwargs):
        # Hardware GPIO init
        raise NotImplementedError

    def _reset(self, pin):
        # Perform a hardware reset toggle
        raise NotImplementedError

    def _read_data(self, count):
        # Read raw data from device, not including status bytes:
        # Subclasses MUST implement this!
        raise NotImplementedError

    def _write_data(self, framebytes):
        # Write raw bytestring data to device, not including status bytes:
        # Subclasses MUST implement this!
        raise NotImplementedError

    def _wait_ready(self, timeout):
        # Check if busy up to max length of 'timeout' seconds
        # Subclasses MUST implement this!
        raise NotImplementedError

    def _wakeup(self):
        # Send special command to wake up
        raise NotImplementedError

    def _write_frame(self, data):
        """Write a frame to the PN532 with the specified data bytearray."""
        assert data is not None and 1 < len(data) < 255, 'Data must be array of 1 to 255 bytes.'
        # Build frame to send as:
        # - Preamble (0x00)
        # - Start code  (0x00, 0xFF)
        # - Command length (1 byte)
        # - Command length checksum
        # - Command bytes
        # - Checksum
        # - Postamble (0x00)
        length = len(data)
        frame = bytearray(length+7)
        frame[0] = _PREAMBLE
        frame[1] = _STARTCODE1
        frame[2] = _STARTCODE2
        checksum = sum(frame[0:3])
        frame[3] = length & 0xFF
        frame[4] = (~length + 1) & 0xFF
        frame[5:-2] = data
        checksum += sum(data)
        frame[-2] = ~checksum & 0xFF
        frame[-1] = _POSTAMBLE
        # Send frame.
        if self.debug:
            print('Write frame: ', [hex(i) for i in frame])
        self._write_data(bytes(frame))

    def _read_frame(self, length):
        """Read a response frame from the PN532 of at most length bytes in size.
        Returns the data inside the frame if found, otherwise raises an exception
        if there is an error parsing the frame.  Note that less than length bytes
        might be returned!
        """
        # Read frame with expected length of data.
        response = self._read_data(length+7)
        if self.debug:
            print('Read frame:', [hex(i) for i in response])

        # Swallow all the 0x00 values that preceed 0xFF.
        offset = 0
        while response[offset] == 0x00:
            offset += 1
            if offset >= len(response):
                raise RuntimeError('Response frame preamble does not contain 0x00FF!')
        if response[offset] != 0xFF:
            raise RuntimeError('Response frame preamble does not contain 0x00FF!')
        offset += 1
        if offset >= len(response):
            raise RuntimeError('Response contains no data!')
        # Check length & length checksum match.
        frame_len = response[offset]
        if (frame_len + response[offset+1]) & 0xFF != 0:
            raise RuntimeError('Response length checksum did not match length!')
        # Check frame checksum value matches bytes.
        checksum = sum(response[offset+2:offset+2+frame_len+1]) & 0xFF
        if checksum != 0:
            raise RuntimeError('Response checksum did not match expected value: ', checksum)
        # Return frame data.
        return response[offset+2:offset+2+frame_len]

    def call_function(self, command, response_length=0, params=None, timeout=1):
        """Send specified command to the PN532 and expect up to response_length
        bytes back in a response.  Note that less than the expected bytes might
        be returned!  Params can optionally specify an array of bytes to send as
        parameters to the function call.  Will wait up to timeout seconds
        for a response and return a bytearray of response bytes, or None if no
        response is available within the timeout.
        """
        # Build frame data with command and parameters.
        if params is None:
            params = []
        data = bytearray(2+len(params))
        data[0] = _HOSTTOPN532
        data[1] = command & 0xFF
        for i, val in enumerate(params):
            data[2+i] = val
        # Send frame and wait for response.
        try:
            self._write_frame(data)
        except OSError:
            self._wakeup()
            return None
        if not self._wait_ready(timeout):
            return None
        # Verify ACK response and wait to be ready for function response.
        if not _ACK == self._read_data(len(_ACK)):
            raise RuntimeError('Did not receive expected ACK from PN532!')
        if not self._wait_ready(timeout):
            return None
        # Read response bytes.
        response = self._read_frame(response_length+2)
        # Check that response is for the called function.
        if not (response[0] == _PN532TOHOST and response[1] == (command+1)):
            raise RuntimeError('Received unexpected command response!')
        # Return response data.
        return response[2:]

    def get_firmware_version(self):
        """Call PN532 GetFirmwareVersion function and return a tuple with the IC,
        Ver, Rev, and Support values.
        """
        response = self.call_function(_COMMAND_GETFIRMWAREVERSION, 4, timeout=0.5)
        if response is None:
            raise RuntimeError('Failed to detect the PN532')
        return tuple(response)

    def SAM_configuration(self):   # pylint: disable=invalid-name
        """Configure the PN532 to read MiFare cards."""
        # Send SAM configuration command with configuration for:
        # - 0x01, normal mode
        # - 0x14, timeout 50ms * 20 = 1 second
        # - 0x01, use IRQ pin
        # Note that no other verification is necessary as call_function will
        # check the command was executed as expected.
        self.call_function(_COMMAND_SAMCONFIGURATION, params=[0x01, 0x14, 0x01])

    def read_passive_target(self, card_baud=_MIFARE_ISO14443A, timeout=1):
        """Wait for a MiFare card to be available and return its UID when found.
        Will wait up to timeout seconds and return None if no card is found,
        otherwise a bytearray with the UID of the found card is returned.
        """
        # Send passive read command for 1 card.  Expect at most a 7 byte UUID.
        try:
            response = self.call_function(_COMMAND_INLISTPASSIVETARGET,
                                          params=[0x01, card_baud],
                                          response_length=19,
                                          timeout=timeout)
        except BusyError:
            return None # no card found!
        # If no response is available return None to indicate no card is present.
        if response is None:
            return None
        # Check only 1 card with up to a 7 byte UID is present.
        if response[0] != 0x01:
            raise RuntimeError('More than one card detected!')
        if response[5] > 7:
            raise RuntimeError('Found card with unexpectedly long UID!')
        # Return UID of card.
        return response[6:6+response[5]]

    def mifare_classic_authenticate_block(self, uid, block_number, key_number, key):   # pylint: disable=invalid-name
        """Authenticate specified block number for a MiFare classic card.  Uid
        should be a byte array with the UID of the card, block number should be
        the block to authenticate, key number should be the key type (like
        MIFARE_CMD_AUTH_A or MIFARE_CMD_AUTH_B), and key should be a byte array
        with the key data.  Returns True if the block was authenticated, or False
        if not authenticated.
        """
        # Build parameters for InDataExchange command to authenticate MiFare card.
        uidlen = len(uid)
        keylen = len(key)
        params = bytearray(3+uidlen+keylen)
        params[0] = 0x01  # Max card numbers
        params[1] = key_number & 0xFF
        params[2] = block_number & 0xFF
        params[3:3+keylen] = key
        params[3+keylen:] = uid
        # Send InDataExchange request and verify response is 0x00.
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=params,
                                      response_length=1)
        if response[0]:
            raise PN532Error(response[0])
        return response[0] == 0x00

    def mifare_classic_read_block(self, block_number):
        """Read a block of data from the card.  Block number should be the block
        to read.  If the block is successfully read a bytearray of length 16 with
        data starting at the specified block will be returned.  If the block is
        not read then None will be returned.
        """
        # Send InDataExchange request to read block of MiFare data.
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, MIFARE_CMD_READ, block_number & 0xFF],
                                      response_length=17)
        # Check first response is 0x00 to show success.
        if response[0]:
            raise PN532Error(response[0])
            return None
        # Return first 4 bytes since 16 bytes are always returned.
        return response[1:]

    def mifare_classic_write_block(self, block_number, data):
        """Write a block of data to the card.  Block number should be the block
        to write and data should be a byte array of length 16 with the data to
        write.  If the data is successfully written then True is returned,
        otherwise False is returned.
        """
        assert data is not None and len(data) == 16, 'Data must be an array of 16 bytes!'
        # Build parameters for InDataExchange command to do MiFare classic write.
        params = bytearray(19)
        params[0] = 0x01  # Max card numbers
        params[1] = MIFARE_CMD_WRITE
        params[2] = block_number & 0xFF
        params[3:] = data
        # Send InDataExchange request.
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=params,
                                      response_length=1)
        if response[0]:
            raise PN532Error(response[0])
        return response[0] == 0x0

    def ntag2xx_write_block(self, block_number, data):
        """Write a block of data to the card.  Block number should be the block
        to write and data should be a byte array of length 4 with the data to
        write.  If the data is successfully written then True is returned,
        otherwise False is returned.
        """
        assert data is not None and len(data) == 4, 'Data must be an array of 4 bytes!'
        # Build parameters for InDataExchange command to do NTAG203 classic write.
        params = bytearray(3+len(data))
        params[0] = 0x01  # Max card numbers
        params[1] = MIFARE_ULTRALIGHT_CMD_WRITE
        params[2] = block_number & 0xFF
        params[3:] = data
        # Send InDataExchange request.
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=params,
                                      response_length=1)
        if response[0]:
            raise PN532Error(response[0])
        return response[0] == 0x00

    def ntag2xx_read_block(self, block_number):
        """Read a block of data from the card.  Block number should be the block
        to read.  If the block is successfully read a bytearray of length 16 with
        data starting at the specified block will be returned.  If the block is
        not read then None will be returned.
        """
        return self.mifare_classic_read_block(block_number)[0:4] # only 4 bytes per page

    def read_gpio(self, pin=None):
        """Read the state of the PN532's GPIO pins.
        :params pin: <str> specified the pin to read
        :return:
        If 'pin' is None, returns 3 bytes containing the pin state where:
            P3[0] = P30,   P7[0] = 0,   I[0] = I0,
            P3[1] = P31,   P7[1] = P71, I[1] = I1,
            P3[2] = P32,   P7[2] = P72, I[2] = 0,
            P3[3] = P33,   P7[3] = 0,   I[3] = 0,
            P3[4] = P34,   P7[4] = 0,   I[4] = 0,
            P3[5] = P35,   P7[5] = 0,   I[5] = 0,
            P3[6] = 0,     P7[6] = 0,   I[6] = 0,
            P3[7] = 0,     P7[7] = 0,   I[7] = 0,
        If 'pin' is not None, returns the specified pin state.
        """
        response = self.call_function(_COMMAND_READGPIO, response_length=3)
        if not pin:
            return tuple(response[:3])
        pins = {'p3': response[0], 'p7': response[1], 'i': response[2]}
        if pin[:-1].lower() not in pins.keys():
            return False
        return True if pins[pin[:-1].lower()] >> int(pin[-1]) & 1 else False

    def write_gpio(self, pin=None, state=None, p3=None, p7=None):
        """Write the state to the PN532's GPIO pins.
        :params pin: <str> specified the pin to write
        :params state: <bool> pin level
        :params p3: byte to set multiple pins level
        :params p7: byte to set multiple pins level
        If p3 or p7 is not None, set the pins with p3 or p7, there is
        no need to read pin states before write with the param p3 or p7
        bits:
            P3[0] = P30,   P7[0] = 0,
            P3[1] = P31,   P7[1] = P71,
            P3[2] = P32,   P7[2] = P72,
            P3[3] = P33,   P7[3] = nu,
            P3[4] = P34,   P7[4] = nu,
            P3[5] = P35,   P7[5] = nu,
            P3[6] = nu,    P7[6] = nu,
            P3[7] = Val,   P7[7] = Val,
        For each port that is validated (bit Val = 1), all the bits are applied
        simultaneously. It is not possible for example to modify the state of
        the port P32 without applying a value to the ports P30, P31, P33, P34
        and P35.

        If p3 and p7 are None, set one pin with the params 'pin' and 'state'
        """
        params = bytearray(2)
        if (p3 is not None) or (p7 is not None):
            # 0x80, the validation bit.
            params[0] = 0x80 | p3 & 0xFF if p3 else 0x00
            params[1] = 0x80 | p7 & 0xFF if p7 else 0x00
            self.call_function(_COMMAND_WRITEGPIO, params=params)
        else:
            if pin[:-1].lower() not in ('p3', 'p7'):
                return
            p3, p7, _ = self.read_gpio()
            if pin[:-1].lower() == 'p3':
                if state:
                    # 0x80, the validation bit.
                    params[0] = 0x80 | p3 | (1 << int(pin[-1])) & 0xFF
                else:
                    params[0] = 0x80 | p3 & ~(1 << int(pin[-1])) & 0xFF
                params[1] = 0x00    # leave p7 unchanged
            if pin[:-1].lower() == 'p7':
                if state:
                    # 0x80, the validation bit.
                    params[1] = 0x80 | p7 | (1 << int(pin[-1])) & 0xFF
                else:
                    params[1] = 0x80 | p7 & ~(1 << int(pin[-1])) & 0xFF
                params[0] = 0x00    # leave p3 unchanged
            self.call_function(_COMMAND_WRITEGPIO, params=params)

    def tg_init_as_target(self,
        mode,
        mifare_params=None,
        felica_params=None,
        nfcid3t=None,
        gt=None,
        tk=None,
        timeout=60
    ):
        """The host controller uses this command to configure the PN532 as
        target.
        :params mode: a byte indicating which mode the PN532 should respect.
        :params mifare_params: information needed to be able to be
        activated at 106 kbps in passive mode.
        :params felica_params: information to be able to respond to a polling
        request at 212/424 kbps in passive mode.
        :params nfcid3t: used in the ATR_RES in case of ATR_REQ received from
        the initiator
        :params gt: an array containing the general bytes to be used in the
        ATR_RES. This information is optional and the length is not fixed
        (max. 47 bytes),
        :params tk: an array containing the historical bytes to be used in the
        ATS when PN532 is in ISO/IEC14443-4 PICC emulation mode. This
        information is optional.
        :returns mode: a byte indicating in which mode the PN532 has been
        activated.
        :returns initiator_command: an array containing the first valid frame
        received by the PN532 once the PN532 has been initialized.
        """
        if not mifare_params:
            mifare_params = [0] * 6
        if not felica_params:
            felica_params = [0] * 18
        if not nfcid3t:
            nfcid3t = [0] * 10
        params = []
        params.append(mode)
        params += mifare_params
        params += felica_params
        params += nfcid3t
        if gt:
            params.append(len(gt))
            params += gt
        else:
            params.append(0x00)
        if tk:
            params.append(len(tk))
            params += tk
        else:
            params.append(0x00)
        # Try to read 64 bytes although the response length is not fixed
        response = self.call_function(_COMMAND_TGINITASTARGET, 64, params=params, timeout=timeout)
        if response:
            mode_activated = response[0]
            initiator_command = response[1:]
            return (mode_activated, initiator_command)
