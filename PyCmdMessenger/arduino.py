__description__ = \
"""
Base class for allowing connections between arduino and PyCmdMessenger instances
via USB.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-30"

import serial

class ArduinoBoard:
    """
    Class for connecting to an Arduino board over USB using PyCmdMessenger.  
    The board holds the serial handle (which, in turn, holds the device name,
    baud rate, and timeout) and the board parameters (size of data types in 
    bytes, etc.).  The default parameters are for an ArduinoUno board.
    """

    def __init__(self,
                 device,
                 baud_rate=9600,
                 timeout=1.0,
                 int_bytes=2,
                 long_bytes=4,
                 float_bytes=4,
                 double_bytes=4):

        """
        Serial connection parameters:
            
            device: serial device (e.g. /dev/ttyACM0)
            baud_rate: baud rate set in the compiled sketch
            timeout: timeout for serial reading and writing

        Board input parameters:
            int_bytes: number of bytes to store an integer
            long_bytes: number of bytes to store a long
            float_bytes: number of bytes to store a float
            double_bytes: number of bytes to store a double

        These can be looked up here:
            https://www.arduino.cc/en/Reference/HomePage (under data types)

        The default parameters should work for most ATMega boards.
        """

        self.device = device
        self.baud_rate = baud_rate
        self.timeout = timeout

        self.int_bytes = int_bytes
        self.long_bytes = long_bytes
        self.float_bytes = float_bytes
        self.double_bytes = double_bytes
        self.max_baud = max_baud

        # Open up the serial port
        self.comm = serial.Serial(self.device,
                                  self.baud_rate,
                                  timeout=self.timeout)

        # Figure out proper type limits given the board specifications
        self.int_min = -2**(8*self.int_bytes-1)
        self.int_max = 2**(8*self.int_bytes-1) - 1

        self.unsigned_int_min = 0
        self.unsigned_int_max = 2**(8*self.int_bytes) - 1

        self.long_min = -2**(8*self.long_bytes-1)
        self.long_max = 2**(8*self.long_bytes-1) - 1

        self.unsigned_long_min = 0
        self.unsigned_long_max = 2**(8*self.long_bytes)-1

        # Set to either IEEE 754 binary32 bit or binary64 bit
        if self.float_bytes == 4: 
            self.float_min = -3.4028235E+38
            self.float_max =  3.4028235E+38
        elif self.float_bytes == 8:
            self.float_min = -1e308
            self.float_max =  1e308
        else:
            err = "float bytes should be 4 (32 bit) or 8 (64 bit)"
            raise PCMBadSpecError(err)
        
        if self.double_bytes == 4: 
            self.double_min = -3.4028235E+38
            self.double_max =  3.4028235E+38
        elif self.double_byes == 8:
            self.double_min = -1e308
            self.double_max =  1e308
        else:
            err = "double bytes should be 4 (32 bit) or 8 (64 bit)"
            raise PCMBadSpecError(err)
        
