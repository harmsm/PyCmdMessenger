### COMMAND FORMATS

__description__ = \
"""
PyCmdMessenger

Class for communication with an arduino using the CmdMessenger serial
communication library.  
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-20"

import serial
import re, warnings, multiprocessing, time, struct

class CmdMessenger:
    """
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.
    """
    
    def __init__(self,
                 board_instance,
                 commands,
                 field_separator=",",
                 command_separator=";",
                 escape_separator="/",
                 warnings=True):
        """
        Input:
            board_instance:
                instance of ArduinoBoard initialized with correct serial 
                connection (points to correct serial with correct baud rate) and
                correct board parameters (float bytes, etc.)

            commands:
                a list or tuple of commands specified in the arduino .ino file
                *in the same order* they are listed there.  commands should be
                a list of lists, where the first element in the list specifies
                the command name and the second the formats for the arguments.
                (e.g. commands = [["who_are_you",""],["my_name_is","s"]])

            field_separator:
                character that separates fields within a message
                Default: ","

            command_separator:
                character that separates messages (commands) from each other
                Default: ";" 
       
            escape_separator:
                escape character to allow separators within messages.
                Default: "/"

            warnings:
                warnings for user
                Default: True
 
            The separators and escape_separator should match what's
            in the arduino code that initializes the CmdMessenger.  The default
            separator values match the default values as of CmdMessenger 4.0. 
        """

        self.board = board_instance
        if not self.board.connected:
            err = "Arduino not connected on {}\n".format(self.board.device)
            raise IOError(err)

        self.commands = commands[:]
        self.field_separator = field_separator
        self.command_separator = command_separator
        self.escape_separator = escape_separator
        self.give_warnings = warnings

        self._cmd_name_to_int = {}
        self._int_to_cmd_name = {}
        self._cmd_name_to_format = {}
        for i, c in enumerate(commands):
            self._cmd_name_to_int[c[0]] = i
            self._int_to_cmd_name[i] = c[0]
            self._cmd_name_to_format[c[0]] = c[1]
 
        self._byte_field_sep = self.field_separator.encode("ascii")
        self._byte_command_sep = self.command_separator.encode("ascii")
        self._byte_escape_sep = self.escape_separator.encode("ascii")
        self._escaped_characters = [self._byte_field_sep,
                                    self._byte_command_sep,
                                    self._byte_escape_sep,
                                    b'\0']

        self._null_escape_re = re.compile(b'\0')
        self._escape_re = re.compile("([{}{}{}\0])".format(self.field_separator,
                                                           self.command_separator,
                                                           self.escape_separator).encode('ascii'))

        self._send_methods = {"c":self._send_char,
                              "b":self._send_byte,
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
                              "b":self._recv_byte,
                              "i":self._recv_int,
                              "I":self._recv_unsigned_int,
                              "l":self._recv_long,
                              "L":self._recv_unsigned_long,
                              "f":self._recv_float,
                              "d":self._recv_double,
                              "s":self._recv_string,
                              "?":self._recv_bool,
                              "g":self._recv_guess}

    def send(self,cmd,*args,arg_formats=None):
        """
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  

        arg_formats is an optional string that specifies the formats to use for
        each argument when passed to the arduino. If specified here,
        arg_formats supercedes formats specified on initialization.  
        """

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
                arg_format_list = self._cmd_name_to_format[cmd]
            except KeyError:
                # if not, guess for all arguments
                arg_format_list = ["g" for i in range(len(args))]
  
        # Deal with "*" format  
        arg_format_list = self._treat_star_format(arg_format_list,args)

        if len(args) > 0:
            if len(arg_format_list) != len(args):
                err = "Number of argument formats must match the number of arguments."
                raise ValueError(err)

        # Go through each argument and create a bytes representation in the
        # proper format to send.  Escape appropriate characters. 
        fields = ["{}".format(command_as_int).encode("ascii")]
        for i, a in enumerate(args):
            fields.append(self._send_methods[arg_format_list[i]](a))
            fields[-1] = self._escape_re.sub(self._byte_escape_sep + r"\1".encode("ascii"),fields[-1])

        # Make something that looks like cmd,field1,field2,field3;
        compiled_bytes = self._byte_field_sep.join(fields) + self._byte_command_sep

        # Send the message.
        self.board.write(compiled_bytes)

    def receive(self,arg_formats=None):
        """
        Recieve commands coming off the serial port. 

        arg_formats is an optimal keyword that specifies the formats to use to
        parse incoming arguments.  If specified here, arg_formats supercedes
        the formats specified on initialization.  
        """

        # Read serial input until a command separator or empty character is
        # reached 
        msg = [[]]
        raw_msg = []
        escaped = False
        command_sep_found = False
        while True:

            tmp = self.board.read()
            raw_msg.append(tmp)

            if escaped:

                # Either drop the escape character or, if this wasn't really
                # an escape, keep previous escape character and new character
                if tmp in self._escaped_characters:
                    msg[-1].append(tmp)
                    escaped = False
                else:
                    msg[-1].append(self._byte_escape_sep)
                    msg[-1].append(tmp)
                    escaped = False
            else:

                # look for escape character
                if tmp == self._byte_escape_sep:
                    escaped = True

                # or field separator
                elif tmp == self._byte_field_sep:
                    msg.append([])

                # or command separator
                elif tmp == self._byte_command_sep:
                    command_sep_found = True
                    break

                # or any empty characater 
                elif tmp == b'':
                    break

                # okay, must be something
                else:
                    msg[-1].append(tmp)
  
        # No message received given timeouts
        if len(msg) == 1 and len(msg[0]) == 0:
            return None

        # Make sure the message terminated properly
        if not command_sep_found:
          
            # empty message (likely from line endings being included) 
            joined_raw = b''.join(raw_msg) 
            if joined_raw.strip() == b'':
                return  None
           
            err = "Incomplete message ({})".format(joined_raw.decode())
            raise EOFError(err)

        # Turn message into fields
        fields = [b''.join(m) for m in msg]

        # Get the command name.
        cmd = fields[0].strip().decode()
        try:
            cmd_name = self._int_to_cmd_name[int(cmd)]
        except (ValueError,IndexError):

            if self.give_warnings:
                cmd_name = "unknown"
                w = "Recieved unrecognized command ({}).".format(cmd)
                warnings.warn(w,Warning)
        
        # Figure out what formats to use for each argument.  
        arg_format_list = []
        if arg_formats != None:

            # The user specified formats
            arg_format_list = list(arg_formats)

        else:
            try:
                # See if class was initialized with a format for arguments to this
                # command
                arg_format_list = self._cmd_name_to_format[cmd_name]
            except KeyError:
                # if not, guess for all arguments
                arg_format_list = ["g" for i in range(len(fields[1:]))]

        # Deal with "*" format  
        arg_format_list = self._treat_star_format(arg_format_list,fields[1:])

        if len(fields[1:]) > 0:
            if len(arg_format_list) != len(fields[1:]):
                err = "Number of argument formats must match the number of recieved arguments."
                raise ValueError(err)

        received = []
        for i, f in enumerate(fields[1:]):
            received.append(self._recv_methods[arg_format_list[i]](f))
        
        # Record the time the message arrived
        message_time = time.time()

        return cmd_name, received, message_time

    def _treat_star_format(self,arg_format_list,args):
        """
        Deal with "*" format if specified.
        """

        num_stars = len([a for a in arg_format_list if a == "*"])
        if num_stars > 0:

            # Make sure the repeated format argument only occurs once, is last,
            # and that there is at least one format in addition to it.
            if num_stars == 1 and arg_format_list[-1] == "*" and len(arg_format_list) > 1:

                # Trim * from end
                arg_format_list = arg_format_list[:-1]

                # If we need extra arguments...
                if len(arg_format_list) < len(args):
                    f = arg_format_list[-1]
                    len_diff = len(args) - len(arg_format_list)
                    tmp = list(arg_format_list)
                    tmp.extend([f for i in range(len_diff)])
                    arg_format_list = "".join(tmp)
            else:
                err = "'*' format must occur only once, be at end of string, and be preceded by at least one other format."
                raise ValueError(err)

        return arg_format_list 

    def _send_char(self,value):
        """
        Convert a single char to a bytes object.
        """

        if type(value) != str and type(value) != bytes:
            err = "char requires a string or bytes array of length 1"
            raise ValueError(err)

        if len(value) != 1:
            err = "char must be a single character, not \"{}\"".format(value)
            raise ValueError(err)

        if type(value) != bytes:
            value = value.encode("ascii")

        if value in self._escaped_characters:
            err = "Cannot send a control character as a single char to arduino.  Send as string instead."
            raise OverflowError(err)

        return struct.pack('c',value)

    def _send_byte(self,value):
        """
        Convert a numerical value into an integer, then to a byte object. Check
        bounds for byte.
        """

        # Coerce to int. This will throw a ValueError if the value can't
        # actually be converted.
        if type(value) != int:
            new_value = int(value)

            if self.give_warnings:
                w = "Coercing {} into int ({})".format(value,new_value)
                warnings.warn(w,Warning)
                value = new_value

        # Range check
        if value > 255 or value < 0:
            err = "Value {} exceeds the size of the board's byte.".format(value)
            raise OverflowError(err)

        return struct.pack("B",value)

    def _send_int(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object Check
        bounds for signed int.
        """

        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)

            if self.give_warnings:
                w = "Coercing {} into int ({})".format(value,new_value)
                warnings.warn(w,Warning)
                value = new_value

        # Range check
        if value > self.board.int_max or value < self.board.int_min:
            err = "Value {} exceeds the size of the board's int.".format(value)
            raise OverflowError(err)
           
        return struct.pack(self.board.int_type,value)
 
    def _send_unsigned_int(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object. Check
        bounds for unsigned int.
        """
        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)

            if self.give_warnings:
                w = "Coercing {} into int ({})".format(value,new_value)
                warnings.warn(w,Warning)
                value = new_value

        # Range check
        if value > self.board.unsigned_int_max or value < self.board.unsigned_int_min:
            err = "Value {} exceeds the size of the board's unsigned int.".format(value)
            raise OverflowError(err)
           
        return struct.pack(self.board.unsigned_int_type,value)

    def _send_long(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object. Check
        bounds for signed long.
        """

        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)
            
            if self.give_warnings:
                w = "Coercing {} into int ({})".format(value,new_value)
                warnings.warn(w,Warning)
                value = new_value

        # Range check
        if value > self.board.long_max or value < self.board.long_min:
            err = "Value {} exceeds the size of the board's long.".format(value)
            raise OverflowError(err)
           
        return struct.pack(self.board.long_type,value)
 
    def _send_unsigned_long(self,value):
        """
        Convert a numerical value into an integer, then to a bytes object. 
        Check bounds for unsigned long.
        """

        # Coerce to int. This will throw a ValueError if the value can't 
        # actually be converted.
        if type(value) != int:
            new_value = int(value)

            if self.give_warnings:
                w = "Coercing {} into int ({})".format(value,new_value)
                warnings.warn(w,Warning)
                value = new_value

        # Range check
        if value > self.board.unsigned_long_max or value < self.board.unsigned_long_min:
            err = "Value {} exceeds the size of the board's unsigned long.".format(value)
            raise OverflowError(err)
          
        return struct.pack(self.board.unsigned_long_type,value)

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
            raise OverflowError(err)

        return struct.pack(self.board.float_type,value)
 
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
            raise OverflowError(err)

        return struct.pack(self.board.double_type,value)

    def _send_string(self,value):
        """
        Convert a string to a bytes object.  If value is not a string, it is
        be converted to one with a standard string.format call.  
        """

        if type(value) != bytes:
            value = "{}".format(value).encode("ascii")

        return value

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

        if type(value) != str and type(value) != bytes and self.give_warnings:
            w = "Warning: Sending {} as a string. This can give wildly incorrect values. Consider specifying a format and sending binary data.".format(value)
            warnings.warn(w,Warning)

        if type(value) == float:
            return "{:.10e}".format(value).encode("ascii")
        elif type(value) == bool:
            return "{}".format(int(value)).encode("ascii")
        else:
            return self._send_string(value)

    def _recv_char(self,value):
        """
        Recieve a char in binary format, returning as string.
        """

        return struct.unpack("c",value)[0].decode("ascii")

    def _recv_byte(self,value):
        """
        Recieve a byte in binary format, returning as python int.
        """

        return struct.unpack("B",value)[0]

    def _recv_int(self,value):
        """
        Recieve an int in binary format, returning as python int.
        """
        return struct.unpack(self.board.int_type,value)[0]

    def _recv_unsigned_int(self,value):
        """
        Recieve an unsigned int in binary format, returning as python int.
        """

        return struct.unpack(self.board.unsigned_int_type,value)[0]

    def _recv_long(self,value):
        """
        Recieve a long in binary format, returning as python int.
        """

        return struct.unpack(self.board.long_type,value)[0]

    def _recv_unsigned_long(self,value):
        """
        Recieve an unsigned long in binary format, returning as python int.
        """

        return struct.unpack(self.board.unsigned_long_type,value)[0]

    def _recv_float(self,value):
        """
        Recieve a float in binary format, returning as python float.
        """

        return struct.unpack(self.board.float_type,value)[0]

    def _recv_double(self,value):
        """
        Recieve a double in binary format, returning as python float.
        """

        return struct.unpack(self.board.double_type,value)[0]
            
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

        if self.give_warnings:
            w = "Warning: Guessing input format for {}. This can give wildly incorrect values. Consider specifying a format and sending binary data.".format(value)
            warnings.warn(w,Warning)

        tmp_value = value.decode()

        try:
            float(tmp_value)

            if len(tmp_value.split(".")) == 1:
                # integer
                return int(tmp_value)
            else:
                # float
                return float(tmp_value)

        except ValueError:
            pass

        # Return as string
        return self._recv_string(value)


