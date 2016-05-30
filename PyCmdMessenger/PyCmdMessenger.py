### COMMAND FORMATS

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
import re, warnings, multiprocessing, time, struct

class PyCmdMessenger:
    """
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.
    """
    
    def __init__(self,
                 board_instance,
                 command_names,
                 command_formats=None,
                 field_separator=",",
                 command_separator=";",
                 escape_separator="/")
        """
        Input:
            board_instance:
                instance of ArduinoBoard initialized with correct serial 
                connection (points to correct serial with correct baud rate) and
                correct board parameters (float bytes, etc.)

            command_names:
                a list or tuple of the command names specified in the arduino
                .ino file *in the same order they are listed there.*  

            command_formats:
                SOMETHING

            field_separator:
                character that separates fields within a message
                Default: ","

            command_separator:
                character that separates messages (commands) from each other
                Default: ";" 
       
            escape_separator:
                escape character to allow separators within messages.
                Default: "/"
 
            The separators and escape_separator should match what's
            in the arduino code that initializes the CmdMessenger.  The default
            separator values match the default values as of CmdMessenger 4.0. 
        """

        self.board = board_instance

        self.command_names = command_names[:]
        self._cmd_name_to_int = dict([(n,i)
                                      for i,n in enumerate(self.command_names)])

        self._cmd_name_to_format = {}

        self.field_separator = field_separator
        self.command_separator = command_separator
        self.escape_separator = escape_separator
   
        self.byte_field_sep = self.field_separator.encode("ascii")
        self.byte_command_sep = self.command_separator.encode("ascii")
        self.byte_escape_sep = self.escape_separator.encode("ascii")

        self._send_methods = {"c":self._send_char,
                              "i":self._send_int,
                              "I":self._send_unsigned_int,
                              "l":self._send_long,
                              "L":self._send_unsigned_long,
                              "f":self._send_float,
                              "d":self._send_double,
                              "s":self._send_string,
                              "?":self._send_bool,
                              "g":self._send_guess}

        self._recv_methods = {"c":self._recv_char,
                              "i":self._recv_int,
                              "I":self._recv_unsigned_int,
                              "l":self._recv_long,
                              "L":self._recv_unsigned_long,
                              "f":self._recv_float,
                              "d":self._recv_double,
                              "s":self._recv_string,
                              "?":self._recv_bool,
                              "g":self._recv_guess}


        ## MULTITHREADING -------- DO XXX KEEP?
        self._listener_thread = None
        self._listener_manager = multiprocessing.Manager()
        self._received_messages = self._listener_manager.list()
        self._lock = multiprocessing.RLock()

    def send(self,cmd,*args,arg_formats=None):
        """
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  

        arg_formats is an optional (but highly recommended!) keyword that 
        specifies the formats to use for each argument when passed to the
        arduino. If specified here, arg_formats supercedes cmd_arg_formats
        specified on a per-command basis when the class was initialized.  
        """

        if len(args) < 1:
            err = "You must specify a command (and maybe parameters).\n"
            raise ValueError(err)

        # Turn the command into an integer.
        try:
            command_as_int = self._cmd_name_to_int[cmd]
        except KeyError:
            err = "Command '{}' not recognized.\n".format(cmd)
            raise ValueError(err)

        # Figure out what formats to use for each argument.  
        arg_format_list = []
        if arg_formats != None:

            # The user specified formats
            arg_format_list = list(arg_formats)

        else:
            try:
                # See if class was initialized with a format for arguments to this
                # command
                arg_formats = self._cmd_name_to_format[args[0]]
            except KeyError:
                # if not, guess for all arguments
                arg_format_list = ["g" for i in range(len(args[1:]))]

        if len(arg_format_list) != len(args[1:]):
            err = "Number of argument formats must match the number of arguments."
            raise ValueError(err)

        # Go through each argument and create a bytes representation in the
        # proper format to send.
        fields = [struct.pack('i',command_as_int)[0]]
        for i, a in enumerate(args[1:]):
            fields.append(self._send_methods[arg_format_list[i]](a))

        # Make something that looks like cmd,field1,field2,field3;
        compiled_bytes = b"{}{}".format(self._bytes_field_separator.join(fields),
                                        self._bytes_cmd_separator)

        # Send the message (waiting for lock in case a listener or receive
        # command is going). 
        with self._lock:
            self.board.write(compiled_bytes)

    def receive(self,arg_formats=None):
        """
        Recieve commands coming off the serial port. 

        arg_formats is an optional (but highly recommended!) string that 
        specifies how to parse the incoming arguments.  If specified here,
        arg_formats supercedes cmd_arg_formats specified on a per-command
        basis when the class was initialized.  
        """

        # Read serial input until nothing or a command ending character is 
        # reached
        msg = []
        tmp = b'XXX'
        while tmp != self._byte_cmd_separator and tmp != b'':

            tmp = self.board.read()

            # Deal with escaped cmd separators (e.g. test/;this -> test;this)
            if tmp == self._byte_cmd_separator and msg[-1] == self._byte_escape_character:
                msg[-1] == tmp
                tmp = b'XXX' 
            else: 
                msg.append(tmp)
        
  
        # No message received given timeouts
        if len(msg) == 0:
            return None

        # Record the time the message arrived
        message_time = time.time()

        # Reassmble the message into a string 
        joined_msg = b''.join(msg).strip()

        # Make sure the message terminated properly
        if msg[-1] != self.byte_cmd_separator:
            err = "Incomplete message ({})".format(joined_msg.decode())
            raise PCMMangledMessageError(err)

        # Split on field separator (e.g. ',')
        tmp_fields = joined_msg[:-1].split(self.byte_field_separator)

        # Combine fields based on escaped separators (e.g. x/,x -> x,x)
        fields = [tmp_fields[0]]
        for i in range(1,len(tmp_fields)):
            if fields[i-1][-1] == self.byte_escape_character:
                fields[i-1] = b''.join(fields[i-1][:-1],tmp_fields[i])
            else:
                fields.append(tmp_fields[i])

        # Get the command name.
        cmd = fields[0].strip().decode()
        try:
            cmd_name = self.command_names[cmd]
        except KeyError:
            w = "Recieved unrecognized command ({}).".format(cmd)
            Warning(w)
        
        # Figure out what formats to use for each argument.  
        arg_format_list = []
        if arg_formats != None:

            # The user specified formats
            arg_format_list = list(arg_formats)

        else:
            try:
                # See if class was initialized with a format for arguments to this
                # command
                arg_formats = self._cmd_name_to_format[args[0]]
            except KeyError:
                # if not, guess for all arguments
                arg_format_list = ["g" for i in range(len(args[1:]))]

        if len(arg_format_list) != len(fields[1:]):
            err = "Number of argument formats must match the number of arguments."
            raise ValueError(err)
      
        received = []
        for i, f in enumerate(fields[1:]):
            received.append(self._recv_methods[arg_format_list[i]](f))
        
        return command_name, received, message_time

    def _send_char(self,value):
        """
        Convert a single char to a bytes object.
        """

        if type(value) != str and type(value) != bytes:
            err = "char requires a string or bytes array of length 1"
            raise ValueError(err)

        if len(value) > 0:
            err = "char must be a single character, not {}".format(value)
            raise ValueError(err)

        if type(value) != bytes:
            value = value.encode("ascii")

        return struct.pack('c',value)


    def _send_int(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object Check
        bounds for signed int.
        """

        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)
            warn = "Coercing {} into int ({})".format(value,new_value)
            Warning(warn)
            value = new_value

        # Range check
        if value > self.board.max_int or value < self.board.min_int:
            err = "Value {} exceeds the size of the board's int.".format(value)
            raise ValueError(err)
           
        return struct.pack("i",v)
 
    def _send_unsigned_int(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object. Check
        bounds for unsigned int.
        """
        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)
            warn = "Coercing {} into int ({})".format(value,new_value)
            Warning(warn)
            value = new_value

        # Range check
        if value > self.board.unsigned_int_max or value < self.board.unsigned_int_min:
            err = "Value {} exceeds the size of the board's unsigned int.".format(value)
            raise ValueError(err)
           
        return struct.pack("I",value)

    def _send_long(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object. Check
        bounds for signed long.
        """

        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)
            warn = "Coercing {} into int ({})".format(value,new_value)
            Warning(warn)
            value = new_value

        # Range check
        if value > self.board.long_max or value < self.board.long_min:
            err = "Value {} exceeds the size of the board's long.".format(value)
            raise ValueError(err)
           
        return struct.pack("l",value)
 
    def _send_unsigned_long(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object. 
        Check bounds for unsigned long.
        """

        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)
            warn = "Coercing {} into int ({})".format(value,new_value)
            Warning(warn)
            value = new_value

        # Range check
        if value > self.board.unsigned_long_max or value < self.board.unsigned_long_min:
            err = "Value {} exceeds the size of the board's unsigned long.".format(value)
            raise ValueError(err)
           
        return struct.pack("L",value)

    def _send_float(self,value):
        """
        Return a float as a IEEE 754 format bytes object.
        """

        # convert to float. this will throw a ValueError if the type is not 
        # readily converted
        if type(value) != float:
            value = float(value)

        # Range check
        if value > self.board.float_max or value < self.board.float_min:
            err = "Value {} exceeds the size of the board's float.".format(value)
            raise ValueError(err)

        if self.board.float_bytes == 4:
            return struct.pack("f",value)
        elif self.board.float_bytes == 8:
            return struct.pack("d",value)
        else:
            err = "float bytes should be 4 (32 bit) or 8 (64 bit)"
            raise PCMBadSpecError(err)
 
    def _send_double(self,value):
        """
        Return a float as a IEEE 754 format bytes object.
        """

        # convert to float. this will throw a ValueError if the type is not 
        # readily converted
        if type(value) != float:
            value = float(value)

        # Range check
        if value > self.board.float_max or value < self.board.float_min:
            err = "Value {} exceeds the size of the board's float.".format(value)
            raise ValueError(err)

        if self.board.float_bytes == 4:
            return struct.pack("f",value)
        elif self.board.float_bytes == 8:
            return struct.pack("d",value)
        else:
            err = "double bytes should be 4 (32 bit) or 8 (64 bit)"
            raise PCMBadSpecError(err)
        

    def _send_string(self,value):
        """
        Convert a string to a bytes object.  If value is not a string, it is
        be converted to one with a standard string.format call.
        """

        if type(value) == bytes:
            return value

        return "{}".format(value).encode("ascii")

    def _send_bool(self,value):
        """
        Convert a boolean value into a bytes object.  Uses 0 and 1 as output.
        """

        # Sanity check.
        if type(value) != bool and value not in [0,1]:
            err = "{} is not boolean.".format(value)
            raise ValueError(err)

        return struct.pack("?",value)

    def _send_guess(self,value):
        """
        Send the argument as a string in a way that should (probably, maybe!) be
        processed properly by C++ calls like atoi, atof, etc.  This method is
        NOT RECOMMENDED, particularly for floats, because values are often 
        mangled silently.  Instead, specify a format (e.g. "f") and use the 
        CmdMessenger::readBinArg<CAST> method (e.g. c.readBinArg<float>();) to
        read the values on the arduino side.
        """

        if type(value) != str and type(value) != bytes:
            w = "Warning: Sending {} as a string. This can give wildly incorrect values. Consider specifying a format and sending binary data.".format(value)
            Warning(w)

        if type(a) == float:
            return "{:.10e}".format(value).encode("ascii")
        elif type(a) == bool:
            return "{}".format(int(value)).encode("ascii")
        else:
            if type(value) == bytes:
                return value
            else:
                return "{}".format(value).encode("ascii")


    def _recv_char(self,value):
        """
        Recieve a char in binary format, returning as string.
        """

        return struct.unpack("c",value)[0]

    def _recv_int(self,value):
        """
        Recieve a 4-byte int in binary format, returning as python int.
        """

        return struct.unpack("i",value)[0]

    def _recv_unsigned_int(self,value):
        """
        Recieve a 4-byte unsigned int in binary format, returning as python int.
        """

        return struct.unpack("I",value)[0]

    def _recv_long(self,value):
        """
        Recieve a 4-byte long in binary format, returning as python int.
        """

        return struct.unpack("l",value)[0]

    def _recv_unsigned_long(self,value):
        """
        Recieve a 4-byte unsigned long in binary format, returning as python int.
        """

        return struct.unpack("L",value)[0]

    def _recv_float(self,value):
        """
        Recieve a float in binary format, returning as python float.
        """

        if self.board.float_bytes === 4:
            return struct.unpack("f",value)[0]
        elif self.board.float_bytes == 8:
            return struct.unpack("d",value)[0]
        else:
            err = "Cannot parse float of {} bytes.".format(self.board.float_bytes)
            raise ValueError(err)

    def _recv_double(self,value):
        """
        Recieve a double in binary format, returning as python float.
        """

        if self.board.double_bytes === 4:
            return struct.unpack("f",value)[0]
        elif self.board.double_bytes == 8:
            return struct.unpack("d",value)[0]
        else:
            err = "Cannot parse float of {} bytes.".format(self.board.double_bytes)
            raise ValueError(err)
            
    def _recv_string(self,value):
        """
        Recieve a binary (bytes) string, returning a python string.
        """

        s = value.decode('ascii')

        # Strip null characters
        s = s.strip("\x00")

        # Strip other white space
        s = s.strip()

        return s

    def _recv_bool(self,value):
        """
        Receive a binary bool, return as python bool.
        """
        
        return struct.unpack("?",value)[0]

    def _recv_guess(self,value):
        """
        Take the binary spew and try to make it into a float or integer.  If 
        that can't be done, return a string.  

        Note: this is generally a bad idea, as values can be seriously mangled
        by going from float -> string -> float.  You'll generally be better off
        using a format specifier and binary argument passing.
        """

        w = "Warning: Guessing input format for {}. This can give wildly incorrect values. Consider specifying a format and sending binary data.".format(value)
        Warning(w)

        try:
            float(value)

            if len(value.split(".")) == 1:
                # integer
                return int(value)
            else:
                # float
                return float(value)

        except ValueError:
            pass

        # Return as string
        return self._recv_string(value)

















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

    def close(self):
        """
        Close the serial connection.
        """

        self._serial_handle.close()

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
        
