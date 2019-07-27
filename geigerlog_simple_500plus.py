#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# 'geigerlog_simple_500plus.py' fully supports GMC-500plus counters
# with double tubes. It collects data from both tubes 1st and 2nd, and
# reports and logs the values combined (CPM, CPS) and separately (CPM1st,
# CPM2nd, CPS1st, CPM2nd).
#
# This version 0.2 now also auto-accounts for counter firmwares delivering
# 4 bytes instead of the previous ones delivering 2-bytes only!
#
# But it works with any other counter just as well. However, then the CP*1st
# and CP*2nd values will be the same as the 'CPM' and 'CPS' values.
#
# Runs on both Python2 and Python3
#
# Start program from the command line with:   geigerlog_simple_500plus.py
# Stop program with:                          CTRL-C
#
# based on:
# http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=5148
# http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=5304 Reply#40
# http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=5121 Reply#21 (ikerrg)
#
# Format of the log:
#       Index, Year-Month-Day Hour:Minute:Second, CPM, CPS, CPM1st, CPM2nd, CPS1st, CPS2nd
# e.g.:   123, 2017-07-21 10:52:37,               601,  14,    530,     71,     12,      2


###############################################################################
#    This file is part of GeigerLog.
#
#    GeigerLog is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GeigerLog is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with GeigerLog.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

__author__          = "ullix"
__copyright__       = "Copyright 2016, 2017, 2018"
__credits__         = [""]
__license__         = "GPL3"
__version__         = "0.2.2"


###############################################################################
# CUSTOMIZE HERE  --  adjust these settings to your situation   ###############
# uncomment any lines you want to make active, and comment out other lines
# by removing or setting the '#' at the beginning of the line

my_port      = '/dev/ttyUSB0'           # likely USB/Serial port on Linux
#my_port      = '/dev/ttyUSB1'          # possible USB/Serial port on Linux
#my_port      = 'COM3'                  # likely USB/Serial port on Windows
#my_port      = 'COM12'                 # possible USB/Serial port on Windows

my_baudrate  = 57600                    # baudrate; typically 57600 or 115200
#my_baudrate  = 115200                  # baudrate; typically 57600 or 115200

my_timeout   = 3                        # timeout in sec for the serial port
my_cycletime = 1                        # seconds between calls
my_logfile   = 'simple.log'             # filename for the log file

debug = False
#debug = True                            # set to True for testing

# List for ONLY those counters with a 4-BYTE answer to the CPM*, CPS* commands
# all others will be 2-BYTE counters
# add new counters, or same counter but with new firmware
# continue the scheme; make sure every new line ends with a COMMA !
signature4ByteCounter = (
                         "GMC-500+Re 1.18",
                         "GMC-500+Re 1.21",
                         "my new one here and comma" ,
                        )

###############################################################################

import time                             # time formatting and more
import sys                              # system functions
import serial                           # communication with serial port
import serial.tools.list_ports          # allows listing of serial ports
import psycopg2                         # allows database access

## Database Settings

def 

def dprint(debug, *args):
    """Print only when debug== True"""

    if debug:        print("DEBUG:", args)


def writeLog(tStamp, wcommand, rlength, srec, value):
    """No logging, just a printout, and only when debug is set to True"""

    if not debug: return

    strsrec = str(srec)
    if sys.version_info[0] == 3:
        print("{:<19s}, Command: {:<14s}, Bytes:{:2d},   Value: {:6.4g},  Record:".format(tStamp, str(wcommand), rlength, value), strsrec )
    else:
        print("{:<19s}, Command: {:<14s}, Bytes:{:2d},   Value: {:6.4g},  Record:".format(tStamp, str(wcommand), rlength, value) , srec)


def timeStamp():
    return time.strftime("%Y-%m-%d %H:%M:%S") # get time stamp


def getExtraByte():
    """read single bytes until no further bytes coming, and return combined bytes"""

    xrec = b""
    try: # failed when called from 2nd instance of GeigerLog; just to avoid error
        bytesWaiting = ser.in_waiting
    except:
        bytesWaiting = 0

    if bytesWaiting == 0:
        dprint(debug, "getExtraByte: No extra bytes waiting for reading")
        pass
    else:
        dprint(debug, "getExtraByte: Bytes waiting: {}".format(bytesWaiting))
        while True:                # read single byte until nothing is returned
            x = ser.read(1)
            if len(x) == 0: break
            xrec += x
    dprint(debug, "getExtraByte: xrec:", xrec)

    return xrec


def getVersion():
    """get the version of the Geiger counter and its firmware; serves as
    identifier for 2 and 4 byte system"""

    ser.write(b'<GETVER>>')
    srec  = ser.read(14)    # newer counters may have 15 (or more?) bytes
                            # old e.g. "GMC-300Re 4.22"     # 14 bytes
                            # new e.g. "GMC-500+Re 1.18"    # 15 bytes
    srec += getExtraByte()  # if there is a 15th or more byte to read

    dprint(debug, "Raw GETVER answer is:")
    dprint(debug, srec)

    # convert to a string unless it already is one
    if sys.version_info[0] == 3:
        # Py3: srec is a byte sequence; decode to a string
        strVersion = srec.decode()  # convert to string
    else:
        # Py2: srec is already a string
        strVersion = srec           # already a string

#### for testing only:
    #strVersion = "GMC-500+Re 1.18"
    #strVersion = "GMC-500+Re 1.21"
    #strVersion = "GMC-500+Re 1.23"
    #strVersion = "GMC-300Re 4.22"
    #strVersion = "xyz-500+Re 1.18"
    #strVersion = "500+Re 1.18"
    #strVersion = "500+Re 1.18abcdefghij"
    #strVersion = "gmc-500+Re 1.18"
######################

    strVersion = strVersion.strip() # cut off white space from both ends

    dprint(debug, "Processed GETVER answer is:", strVersion)

    return strVersion


def BugAlert():

    ba = """ATTENTION Firmware Bugs
    Another reason for the failure could be a firmware bug. Recently discovered:

    Device GMC-500+
    If it has firmware 1.18 then it will report an empty version on the first connect.
    Start this 'geigerlog_simple_500.py' program again, and it should work.
    It is recommended to upgrade the firmware (current new version: 1.21).
    Contact GQ support for the upgrade.

    If your counter has a newer firmware than 1.21, you can adapt this
    'geigerlog_simple_500.py' program by adding a new entry under the
    'Customize Here' section beginning at about line 55 of the program code.
    """

    return ba


def getData(ser, wcommand="", rlength=1, maskHighBit=False):
    """Write to and read from device and convert to value; print, and return value"""

    ser.write(wcommand)
    srec = ser.read(rlength)

    if nbytes == 2:
        if maskHighBit :
            value = get23(srec) & 0x3fff   # mask out high bits, as for CPS* calls
        else:
            value = get23(srec)            # do not mask out high bits, as for CPM* calls
    else:
        value = get23(srec)            # do NOT mask out high bits (is that correct?)

    writeLog(timeStamp(), wcommand, rlength, srec, value)

    return value


def get23(srec):
    """check for size of returned record, return -99 if too short,
    and after adjusting for differences Python2 and Python3 return value"""

    # from: http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=5304 Reply#40
    # getcpm outputs ==>> (MSB) (x) (x) (LSB)
    # example: CPM of 10 is going to be:    00 00 00 0A

    if len(srec) == nbytes:  # ok, got n bytes as expected
        if nbytes == 4:      # "GMC-500+Re 1.18"
            if sys.version_info[0] == 3:
                rec = chr(srec[0]) + chr(srec[1]) + chr(srec[2]) + chr(srec[3])
            else:
                rec = srec
            value = ((ord(rec[0])<< 8 | ord(rec[1])) << 8 | ord(rec[2])) << 8 | ord(rec[3])

        else: # nbytes = 2   # so far all other counters
            if sys.version_info[0] == 3:
                rec = chr(srec[0]) + chr(srec[1])
            else:
                rec = srec
            value = (ord(rec[0])<< 8 | ord(rec[1]))

    else: # bytes missing or too many
        msg = "# byte count error, got {} bytes, expected {}! Is USB-Port and Baudrate customized? (see Quickstart)".format(len(srec), nbytes)
        print(msg + "\7")
        with open(my_logfile, 'a') as log:
            log.write(msg + "\n")
        value = -99

    return value


def getTest(ser):
    """ use only for testing """

    wcommand = b"Test      "
    rlength  = nbytes
    byte1    = 1       # MSB
    byte2    = 1
    byte3    = 1
    byte4    = 1       # LSB

    srec     = b"" + bytes([byte1]) + bytes([byte2]) + bytes([byte3]) + bytes([byte4])
    srec     = srec[:nbytes]
    value    = get23(srec)

    writeLog(timeStamp(), wcommand, rlength, srec, value)

    return value


def getCPS(ser):
    """the normal CPS call; might be the sum of High- and Low- sensitivity tube"""

    return getData(ser, wcommand=b'<GETCPS>>', rlength=nbytes, maskHighBit=True)


def getCPSL(ser):
    """get CPS from High Sensitivity tube; that should be the 'normal' tube"""

    return getData(ser, wcommand=b'<GETCPSL>>', rlength=nbytes, maskHighBit=True)


def getCPSH(ser):
    """get CPS from Low Sensitivity tube; that should be the 2nd tube in the 500+"""

    return getData(ser, wcommand=b'<GETCPSH>>', rlength=nbytes, maskHighBit=True)


def getCPM(ser):
    """the normal CPM call; might get CPM as sum of both tubes' CPM"""

    return getData(ser, wcommand=b'<GETCPM>>', rlength=nbytes)


def getCPML(ser):
    """get CPM from High Sensitivity tube; that should be the 'normal' tube"""

    return getData(ser, wcommand=b'<GETCPML>>', rlength=nbytes)


def getCPMH(ser):
    """get CPM from Low Sensitivity tube; that should be the 2nd tube in the 500+"""

    return getData(ser, wcommand=b'<GETCPMH>>', rlength=nbytes)

##############################################################################

nbytes = 0    # placeholder for the number of bytes returned on CPM*/CPS* calls

# Find the USB-to-Serial ports on this system and list them
# use one of the ports found here for 'my_port' above
# if there is more than 1 port, make sure to use the correct one!
print ("\nUSB-to-Serial Ports found on this system:")
my_ports =  serial.tools.list_ports.comports()
if len(my_ports) == 0:
    print("No USB-to-Serial Ports found on this system - Cannot run without one. Exiting.")
    sys.exit(1)

for p in my_ports :
    print ("     " + str(p))
print(" ")


# Print versions and settings
print("{:50s} : {}".format("my Version of geigerlog_simple_500plus.py", __version__))
print("{:50s} : {}".format("my Python Version", sys.version.split(" ")[0]))
print(" ")
if sys.version_info[0] != 3 and sys.version_info[0] != 2:
    print("Python Version is unknown - Only Python Version 2.X and 3.X are supported")
    sys.exit(1)

print("{:50s} : {}".format("my Serial Port"             , my_port))
print("{:50s} : {}".format("my Serial Baudrate"         , my_baudrate))
print("{:50s} : {}".format("my Serial Timeout (sec)"    , my_timeout))
print("{:50s} : {}".format("my Cycle time (sec)"        , my_cycletime))
print("{:50s} : {}".format("my Log file"                , my_logfile))


# open the serial port
ser = serial.Serial(my_port, my_baudrate, timeout=my_timeout)


# is it a classic 2-byte counter or a new 4-byte counter ?
my_counter_version = getVersion()
print("{:50s} : {}".format("my Counter Version"         , my_counter_version))

if len(my_counter_version) == 0:
    e1 = """
ERROR:
    The Geiger counter gave no answer to the version request.
    Cannot continue without version. Try restarting geigerlog.
    Perhaps the counter needs to be rebootet or even Factory resetted!
    """
    print(e1)
    print(BugAlert())
    sys.exit()

if len(my_counter_version) not in (14, 15):
    e2 = """
ERROR:
    The Geiger counter gave incomplete answer to the version request.
    Cannot continue without proper version. Try restarting geigerlog.
    Perhaps the counter needs to be rebootet or even Factory resetted!
    """
    print(e2)
    print(BugAlert())
    sys.exit()

if not "GMC-" in my_counter_version:
    e3 = """
    ERROR: The Geiger counter gave an improper answer to the version request.
    Cannot continue without proper version. Try restarting geigerlog.
    Perhaps the counter needs to be rebootet or even Factory resetted!
    """
    print(e3)
    print(BugAlert())
    sys.exit()


if my_counter_version in signature4ByteCounter: nbytes  = 4
else:                                           nbytes  = 2
print("{:50s} : {}".format("@  Byte Counts"             , nbytes))
print("")

# open the logfile for writing, clearing previous content
with open(my_logfile, 'w') as log:
    log.write("# Log file created with: 'geigerlog_simple_500plus.py', Version: {}\n".format(__version__))
    log.write("# Python Version: {}\n".format(sys.version.replace('\n', "")))
    log.write("# Index,            DateTime,    CPM,    CPS, CPM1st, CPM2nd, CPS1st, CPS2nd\n")

# run the loop
print("Now logging:")
getExtraByte() # clean the pipeline before logging!

index = 0
while True:
    ts     = timeStamp()

    cpm    = getCPM (ser)                  # get CPM
    cps    = getCPS (ser)                  # get CPS
    cpm1st = getCPML(ser)                  # get CPM from normal tube, = 1st tube
    cpm2nd = getCPMH(ser)                  # get CPM from extra tube,  = 2nd tube

    cps1st = getCPSL(ser)                  # get CPS from normal tube, = 1st tube
    cps2nd = getCPSH(ser)                  # get CPS from extra tube,  = 2nd tube

# for TESTING ONLY
    #cps2nd = getTest(ser)                  # call a test funktion

    cpxlist = (index, ts, cpm, cps, cpm1st, cpm2nd, cps1st, cps2nd)
    print ("{} {}, CPM={}, CPS={}, CPM1st={}, CPM2nd={}, CPS1st={}, CPS2nd={}"           .format(*cpxlist))
    with open(my_logfile, 'a') as log:
        log.write("{:7d}, {:19s}, {:6.2f}, {:6.2f}, {:6.2f}, {:6.2f}, {:6.2f}, {:6.2f}\n".format(*cpxlist))

    time.sleep(my_cycletime)               # sleep for my_cycletime seconds
    index += 1

