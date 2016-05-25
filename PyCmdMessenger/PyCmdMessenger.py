__description__ = \
"""
PyCmdMessenger

Class for communication with an arduino using the CmdMessenger serial
communication library.  This class requires the baud rate and separators 
match between the PyCmdMessenger class instance and the arduino sketch.  The 
library also assumes the serial data are binary strings, and that each 
command sent by the arduino has a \r\n line-ending.  
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-20"

import serial
import re, warnings, multiprocessing, time

class PyCmdMessenger:
    """
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.
    """
    
    def __init__(self,
                 device,
                 command_names,
                 timeout=0.25,
                 baud_rate=9600,
                 field_separator=",",
                 command_separator=";",
                 escape_separator="/",
                 convert_strings=True):
        """
        Input:
            device:
                device location (e.g. /dev/ttyACM0)

            command_names:
                a list or tuple of the command names specified in the arduino
                .ino file *in the same order they are listed there.*  

            timeout:
                time to wait on a given serial request before giving up
                (seconds).  Default: 0.25

            baud_rate: 
                serial baud rate. Default: 9600

            field_separator:
                character that separates fields within a message
                Default: ","

            command_separator:
                character that separates messages (commands) from each other
                Default: ";" 
       
            escape_separator:
                escape character to allow separators within messages.
                Default: "/"
 
            convert_strings:
                on receiving, try to intelligently convert parameters to
                integers or floats. Default: True

            The baud_rate, separators, and escape_separator should match what's
            in the arduino code that initializes the CmdMessenger.  The default
            separator values match the default values as of CmdMessenger 4.0. 
        """

        self.device = device

        self.command_names = command_names[:]
        self._cmd_name_to_int = dict([(n,i)
                                      for i,n in enumerate(self.command_names)])

        self.timeout = timeout
        self.baud_rate = baud_rate
        self.field_separator = field_separator
        self.command_separator = command_separator
        self.escape_separator = escape_separator

        self._esc_pattern = re.compile(r"([{}{}])".format(self.field_separator,
                                                          self.command_separator))
        self._esc_sub_str = r"{}\\1".format(self.escape_separator)

        self._serial_handle = serial.Serial(self.device,
                                            self.baud_rate,
                                            timeout=self.timeout)

        self._listener_thread = None
        self._listener_manager = multiprocessing.Manager()
        self._received_messages = self._listener_manager.list()
        self._lock = multiprocessing.Lock()
       
    def send(self,*args):
        """
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  The function will convert
        python data types to strings, as well as escaping all separator
        characters.
        """

        if len(args) < 1:
            err = "You must specify a command (and maybe parameters).\n"
            raise ValueError(err)

        # Turn arguments into strings, replacing separators with escaped separators
        try:
            command_as_int = self._cmd_name_to_int[args[0]]
        except KeyError:
            err = "Command '{}' not recognized.\n".format(args[0])
            raise ValueError(err)

        params = [self._esc_pattern.sub(self._esc_sub_str,"{}".format(a))
                  for a in args[1:]]

        strings = ["{}".format(command_as_int)]
        strings.extend(params)

        # compile the final string
        compiled_string = "{};".format(",".join(strings))

        # Send the message (waiting for lock in case a listener or receive
        # command is going). 
        with self._lock:
            self._serial_handle.write(compiled_string.encode('ascii'))

    def receive(self):
        """
        Read a single serial message sent by CmdMessage library.  
        """

        # Read raw serial
        with self._lock:
            message = self._serial_handle.readline().decode().strip("\r\n")

        return self._parse_message(message)

    def receive_from_listener(self,warn=True):
        """
        Return messages that have been grabbed by the listener.
        
        Input:
            warn: warn if the listener is not actually active.
        """

        if self._listener_thread == None and warn == True:
            warnings.warn("Not currently listening.")

        with self._lock:
            out = self._received_messages[:]
            self._received_messages = self._listener_manager.list()

        return out

    def receive_all(self):
        """
        Get all messages from the arduino (both from listener and the complete
        current serial buffer).
        """

        # Grab messages already in the received_queue
        msg_list = self.receive_from_listener(warn=False)[:]

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

    def listen(self,listen_delay=0.25):
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

    def stop_listening(self):
        """
        Stop an existing listening thread.
        """

        if self._listener_thread == None:
            warnings.warn("Not currently listening.\n")
        else:
            self._listener_thread.terminate() 
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
        message_list = re.split(r'(?<!\{}){}'.format(self.escape_separator,
                                                     self.command_separator),
                                                     message)
        
        # Grab non-empty messages
        message_list = [m for m in message_list if m.strip() != ""]

        # Make sure that only a single message was received.
        if len(message_list) > 1:
            err = "Mangled message received.  Has multiple commands on one line.\n"
            raise ValueError(err)

        m = message_list[0]

        # Split message on field separator, ignoring escaped separtaors
        fields = re.split(r'(?<!\{}){}'.format(self.escape_separator,
                                               self.field_separator),m)
        command = fields[0]

        # Try to convert the command integer into a named command string
        try:
            command = self.command_names[int(command)]
        except (ValueError,IndexError):
            pass

        # Parse all of the fields
        field_out = []
        for f in fields[1:]:

            try:
                float(f)

                if len(f.split(".")) == 1:
                    # integer
                    field_out.append(int(f))
                else:
                    # float
                    field_out.append(float(f))

            except ValueError:
                # keep as a string
                field_out.append(f)

        return message_time, command, field_out
      
    def _listen(self):
        """
        Private function that should be run within a Process instance.  This 
        looks for an incoming message and then appends that (timestamped) 
        to the message queue. 
        """

        while True:

            tmp = self.receive()
            if tmp != None:
                with self._lock:
                    self._received_messages.append(tmp)

            time.sleep(self._listen_delay)
        
