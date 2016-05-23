__description__ = \
"""
Library for communication with an arduino using the CmdMessenger serial
communication library.  This library requires the baud rate and separators 
match between the CmdMessenger class instance and the arduino sketch.  The 
library also assumes the serial data are binary strings, and that each 
command send by the arduino has a \r\n line-ending.  
"""

"""
--------------------------------------------------------------------------------
Minimal .ino file for arduino, compiled with CmdMessenger.h and CmdMessenger.cpp
in the sketch directory. 
--------------------------------------------------------------------------------

#include "CmdMessenger.h"

const int BAUD_RATE = 9600;
CmdMessenger c = CmdMessenger(Serial,',',';','\\');

/* Define available CmdMessenger commands */
enum {
    who_are_you,
    my_name_is,
    error,
};

/* Define callbacks for CmdMessenger commands */
void attach_callbacks(void) { 
  
    // Attach callback methods
    c.attach(on_unknown_command);
    c.attach(who_are_you,on_who_are_you);
}

void on_unknown_command(void){
    c.sendCmd(error,"Command without callback.");
}

void on_who_are_you(void){
    c.sendCmd(my_name_is,"Bob");
}

void setup() {
    Serial.begin(BAUD_RATE);
    c.printLfCr();
    attach_callbacks();    
}

void loop() {
    c.feedinSerialData();
}

--------------------------------------------------------------------------------
Minimal python program using the library to interface with the arduino sketch
above.
--------------------------------------------------------------------------------

import CmdMessenger

# Initialize instance of class with appropriate device.  command_names is
# optional. 
c = CmdMessenger.CmdMessenger("/dev/ttyACM0",
                              command_names=("who_are_you","my_name_is","error"))

# Send and recieve
c.send("who_are_you")
msg = c.recieve()

# should give [TIME_IN_MS,"my_name_is","Bob"]
print(msg)
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-20"

import serial
import re, warnings, multiprocessing

class CmdMessenger:
    """
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.
    """
    
    def __init__(self,
                 device,
                 timeout=0.25,
                 command_names=None,
                 baud_rate=9600,
                 field_separator=",",
                 command_separator=";",
                 escape_character="\\",
                 convert_strings=True):
        """
        Input:
            device:
                device location (e.g. /dev/ttyACM0)

            timeout:
                time to wait on a given serial request before giving up
                (seconds).  Default: 0.25

            command_names:
                a list or tuple of the command names specified in the arduino
                .ino file in the same order they are listed.  It is optional.
                If not specified, the library will give each command its 
                arduino-specified number rather than name. Default: ()
            
            baud_rate: 
                serial baud rate. Default: 9600

            field_separator:
                character that separates fields within a message
                Default: ","

            command_separator:
                character that separates messages (commands) from each other
                Default: ";" 
       
            escape_character:
                escape charcater to allow separators within messages.
 
            convert_strings:
                on receiving, try to intelligently convert parameters to
                integers or floats. Default: True

            The baud_rate, separators, and escape_character should match what's
            in the arduino code that initializes the CmdMessenger.  The default
            values match the default values as of CmdMessenger 3.6. 
        """

        self.device = device
        self.timeout = timeout

        if command_names == None:
            self.command_names = ()
        else:
            self.command_names = command_names

        self.baud_rate = baud_rate
        self.field_separator = field_separator
        self.command_separator = command_separator
        self.escape_character = escape_character

        self._esc_pattern = re.compile(r"([{}{}])".format(self.field_separator,
                                                          self.command_separator))
        self._esc_sub_str = r"{}\\1".format(self.escape_character)

        self._serial_handle = serial.Serial(self.device,
                                            self.baud_rate,
                                            timeout=self.timeout)

        self._listener_thread = None
        self._recieved_messages = None
        self._lock = multiprocessing.Lock()
       
    def send(self,*args):
        """
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  The function will convert
        python data types to strings, as well as escaping problem characters.
        """

        if len(args) < 1:
            err = "You must specify a command (and maybe parameters).\n"
            raise ValueError(err)

        # Turn arguments into strings, replacing separators with escaped separators
        strings = [self._esc_pattern.sub(self._esc_sub_str,"{}".format(a))
                   for a in args]

        # compile the final string
        compiled_string = "{};".format(",".join(strings))

        # Send the message (waiting for lock in case a listener or recieve
        # command is going). 
        with self._lock:
            self._serial_handle.write(compiled_string.encode('ascii'))

    def recieve(self):
        """
        Read a single serial message sent by CmdMessage library.  
        """

        # Read raw serial
        with self._lock:
            message = self._serial_handle.readline().decode().strip("\r\n")

        return self._parse_message(message)

    def recieve_from_listener(self,warn=True):
        """
        Return messages that have been grabbed by the listener.
        
        Input:
            warn: warn if the listener is not actually active.
        """

        if self._listener_thread == None and warn == True:
            warnings.warn("Not currently listening.")

        with self._lock:        
            out = self._recieved_messages[:]
            self._recieved_messages = []

        return out

    def recieve_all(self):
        """
        Get all messages that are coming off arduino (listener and the complete
        current serial buffer).
        """

        # Grab messages already in the recieved_queue
        msg_list = self.recieve_from_listener(warn=False)[:]

        # Now read all lines in the buffer
        with self._lock:
        
            while True:
                message = self._serial_handle.readline().decode().strip("\r\n")
                message = self._parse_message(message)

                if message != None:
                    msg_list.append(message)
                else:
                    break

        return msg_list

    def listen(self,listen_delay=1):
        """
        Listen for incoming messages on its own thread, appending to recieving
        queue.  
        
        Input:
            listen_delay: time to wait between checks (seconds)
        """

        self._listen_delay = listen_delay

        if self._listener_thread != None:
            warnings.warn("Already listening.\n")
        else:
            self._listener_thread = multiprocessing.Process(target=self._listen)
            self._listener_thread.start()
            self._listener_thread.join()    

    def stop_listening(self):
        """
        Stop an existing listening thread.
        """

        if self._listener_thread == None:
            warnings.warn("Not currently listening.\n")
        else:
            self._listener_thread.close() 
            self._listener_thread = None

    def _parse_message(self,message):
        """
        Parse the output of a message (with trailing '\r\n' already stripped),
        returning timestamp, command, and whatever parametres came out.

        Possible outputs:

            None (no message)

            OR

            (RECIEVE_TIME,cmd,[param1,param2,...,paramN])

            If params are empty, they will be returned as an empty list. 
        
            (RECIEVE_TIME,cmd,[])
        """

        message_time = time.time()

        # No message
        if message == "":
            return None

        # Split message by command separator, ignoring escaped command separators
        message_list = re.split(r'(?<!\\){}'.format(self.command_separator),message)
        
        # Grab non-empty messages
        message_list = [m for m in message_list if m.strip() != ""]

        # Make sure that only a single message was recieved.
        if len(message_list) > 1:
            err = "Mangled message recieved.  Has multiple commands on one line.\n"
            raise ValueError(err)

        # Split message on field separator, ignoring escaped separtaors
        fields = re.split(r'(?<!\\){}'.format(self.field_separator),m)
        fields = m.split(self.field_separator)
        command = fields[0]

        # Try to convert the command integer into a named command string
        try:
            command = self.command_names[int(command)]
        except ValueError:
            pass

        # Parse all of the fields
        field_out = []
        for f in fields[1:]:

            if f.isdigit():
                # is it an integer?
                field_out.append(int(f))
            else: 

                try:
                    # is it a float?
                    field_out.append(float(f))
                except ValueError:
                    # keep as a string
                    field_out.append(f)

        return message_time, command, field_out
      
    def _listen(self):
        """
        Private function that should be run within a Process instance.  This 
        looks for an incoming message and then appends that (timestampted) 
        to the message queue. 
        """

        tmp = self._recieve()
        if tmp != None:
            with self._lock:         
                self._recieved_messages.append(tmp)

        time.sleep(self._listen_delay)
        

