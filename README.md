#PyCmdMessenger

Python class for communication with an arduino using the
[CmdMessenger](https://github.com/thijse/Arduino-CmdMessenger) serial
communication library. It sends and recieves messages, automatically converting
python data types to arduino types and vice versa.  

This project is not affiliated with the CmdMessenger project, though it
obviously builds off of their excellent work.

### Installation:
 * From github: 
    + `git clone https://github.com/harmsm/PyCmdMessenger.git` 
    + `cd PyCmdMessenger`
    + `sudo python3 setup.py install`
 * From PyPI:
    + `sudo pip3 install PyCmdMessenger`

To test the library:
 * Clone the source from git
 * Compile the arduino sketch in the `pingpong_arduino` directory
 * Transfer the compiled sketch to an arduino plugged into the computer
 * Run the `test/pingpong_test.py` script.  This will pass a variety of data
   types between the local computer and the arduino.  

### Compatibility
 * Compatibility: Python 3.x (a tweaked version supporting Python 2.7 is [here](https://github.com/zlite/PyCmdMessenger)).
 * Should work on all platforms supported by pyserial.  
 * Known to work on Raspberry Pi (raspbian), linux (Ubuntu 15.10), and Windows 10. 

### Dependencies
 * pyserial (on local machine): https://github.com/pyserial/pyserial
 * CmdMessenger (on Arduino): https://github.com/thijse/Arduino-CmdMessenger

pyserial should be installed automatically by pip or the installaion script. 
For CmdMessenger, please follow the directions on their
[site](https://github.com/thijse/Arduino-CmdMessenger).  Copies of the 
CmdMessenter 4.0 main .cpp and .h files are included in the PyCmdMessenger repo
in the [test/arduino](https://github.com/harmsm/PyCmdMessenger/tree/master/test/arduino) and
[examples/arduino](https://github.com/harmsm/PyCmdMessenger/tree/master/examples/arduino)
directories. 

##Example code

A typical CmdMessenger message has the following structure:

```
Cmd Id, param 1, [...] , param N;
```

The PyCmdMessenger class constructs/parses these strings, as well as sending 
them over the serial connection via pyserial.  

To ensure stable communication with PyCmdMessenger:

 * PyCmdMessenger instances must be given a list of command names in the *same*
   order as those commands are specified in the arduino sketch.  
 * PyCmdMessenger instances should be given a list of the data types for each 
   command in the *same* order as those commands are specified in the arduino
   sketch.
 * Separators must match between the PyCmdMessenger instance and the arduino
   sketch. 
   + field separator (default ",")
   + command separator (default ";")
   + escape separator, so field and command separators can be sent within
     strings (default "/")
 * Baud rate must match between PyCmdMessenger class and arduino sketch. 
    
A basic example is shown below.  These files are in the 
[examples](https://github.com/harmsm/PyCmdMessenger/tree/master/examples) directory.
 
###Arduino

```C

/* -----------------------------------------------------------------------------
 * Example .ino file for arduino, compiled with CmdMessenger.h and
 * CmdMessenger.cpp in the sketch directory. 
 *----------------------------------------------------------------------------*/

#include "CmdMessenger.h"

/* Define available CmdMessenger commands */
enum {
    who_are_you,
    my_name_is,
    sum_two_ints,
    sum_is,
    error,
};

/* Initialize CmdMessenger -- this should match PyCmdMessenger instance */
const int BAUD_RATE = 9600;
CmdMessenger c = CmdMessenger(Serial,',',';','/');

/* Create callback functions to deal with incoming messages */

/* callback */
void on_who_are_you(void){
    c.sendCmd(my_name_is,"Bob");
}

/* callback */
void on_sum_two_ints(void){
   
    /* Grab two integers */
    int value1 = c.readBinArg<int>();
    int value2 = c.readBinArg<int>();

    /* Send result back */ 
    c.sendBinCmd(sum_is,value1 + value2);

}

/* callback */
void on_unknown_command(void){
    c.sendCmd(error,"Command without callback.");
}

/* Attach callbacks for CmdMessenger commands */
void attach_callbacks(void) { 
  
    c.attach(who_are_you,on_who_are_you);
    c.attach(sum_two_ints,on_sum_two_ints);
    c.attach(on_unknown_command);
}

void setup() {
    Serial.begin(BAUD_RATE);
    attach_callbacks();    
}

void loop() {
    c.feedinSerialData();
}

```

### Python
```python

# ------------------------------------------------------------------------------
# Python program using the library to interface with the arduino sketch above.
# ------------------------------------------------------------------------------

import PyCmdMessenger

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles).  
arduino = PyCmdMessenger.ArduinoBoard("/dev/ttyACM0",baud_rate=9600)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["who_are_you",""],
            ["my_name_is","s"],
            ["sum_two_ints","ii"],
            ["sum_is","i"],
            ["error","s"]]

# Initialize the messenger
c = PyCmdMessenger.CmdMessenger(arduino,commands)

# Send
c.send("who_are_you")
# Receive. Should give ["my_name_is",["Bob"],TIME_RECIEVED]
msg = c.receive()
print(msg)

# Send with multiple parameters
c.send("sum_two_ints",4,1)
msg = c.receive()

# should give ["sum_is",[5],TIME_RECEIVED]
print(msg)
```

##Format arguments

The format for each argument sent with a command (or received with a command)
is determined by the command_formats list passed to the CmdMessenger class (see
example above). Alternatively, it can be specified by the keyword arg_formats
passed directly to the `send` or `receive` methods.  The format specification
is in the table below.  If a given command returns a single float value, the
format string for that command would be `"f"`.  If it returns five floats, the
format string would be `"fffff"`.  The types can be mixed and matched at will.
`"si??f"` would specify a command that sends or receives five arguments that are
a string, integer, bool, bool, and float.  If no argument is associated with a
command, an empty string (`""`) or `None` can be used for the format.

###Format reference table

| format | arduino type  | Python Type              | Arduino receive                                       | Arduino send                        |
|--------|---------------|--------------------------|-------------------------------------------------------|-------------------------------------|
| "i"    | int           | int                      | `int value = c.readBinArg<int>();`                    | `c.sendBinCmd(COMMAND_NAME,value);` |
| "b"    | byte          | int                      | `int value = c.readBinArg<byte>();`                   | `c.sendBinCmd(COMMAND_NAME,value);` |
| "I"    | unsigned int  | int                      | `unsigned int value = c.readBinArg<unsigned int>();`  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "l"    | long          | int                      | `long value = c.readBinArg<long>();`                  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "L"    | unsigned long | int                      | `unsigned long value = c.readBinArg<unsigned long>();`| `c.sendBinCmd(COMMAND_NAME,value);` |
| "f"    | float         | float                    | `float value = c.readBinArg<float>();`                | `c.sendBinCmd(COMMAND_NAME,value);` |
| "d"    | double        | float                    | `double value = c.readBinArg<double>();`              | `c.sendBinCmd(COMMAND_NAME,value);` |
| "?"    | bool          | bool                     | `bool value = c.readBinArg<bool>();`                  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "c"    | char          | str or bytes, length = 1 | `char value = c.readBinArg<char>();`                  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "s"    | char[]        | str or bytes             | `char value[SIZE] = c.readStringArg();`               | `c.sendCmd(COMMAND_NAME,value);`    |

PyCmdMessenger takes care of type conversion before anything is sent over the
serial connection.  For example, if the user sends an integer as an `"f"`
(float), PyCmdMessenger will run `float(value)` in python before passing it.
It will warn the user for destructive conversions (say, a float to an
integer).  It will throw a `ValueError` if the conversion cannot be done (e.g.
the string 'ABC' to integer).  It will throw an `OverflowError` if the passed
value cannot be accomodated in the specififed arduino data type (say, by
passing an integer greater than 32767 to a 2-byte integer, or a negative number
to an unsigned int).  The sizes for each arduino type are determined by the
`XXX_bytes` attributes of the ArduinoBoard class.  

With the exception of strings, all data are passed in binary format.  This both
minimizes the number of bits sent and makes sure the sent values are accurate. 
(While you can technically send a float as a string to the arduino, then 
convert it to a float via `atof`, this is extremely unreliable.) 

PyCmdMessenger will also automatically escape separators in strings, both on 
sending and receiving.  For example, the default field separator is `,` an
dthe default escape character is `/`.  If the user sends the string 
`Hello, my name is Bob.`, PyCmdMessenger will convert this to 
`Hello/, my name is Bob.`  CmdMessenger on the arduino will strip out the 
escape character when received.  The same behavior should hold for recieving
from the arduino.  

###Special formats
 * `"*"` tells the CmdMessenger class to repeat the previous format for all 
   remaining arguments, however many there are. This is useful if your arduino
   function sends back an undetermined number of arguments of the same type, 
   for example.  There are a few rules for use:

   + Only one `*` may be specified per format string.
   + The one `*` must occur *last*
   + It must be preceded by a different format that will then be repeated.

   Examples:
   + `"i*"` will use an integer format until it runs out of fields.
   + `"fs?*"` will read/send the first two fields as a `float` and `string`,
     then any remaining fields as `bool`.

##Testing

The [test](https://github.com/harmsm/PyCmdMessenger/tree/master/test) directory
has an arduino sketch (in `pingpong_arduino`) that can be compiled and loaded
onto an arudino, as well as a python test script, `pingpong_test.py`.  This will
send a wide range of values for every data type back and forth to the arduino,
reporting success and failure.  

##Known Issues

 + Opening the serial connection from a linux machine will cause the arduino to reset.  This is a [known issue](https://github.com/pyserial/pyserial/issues/124) with pyserial and the arudino architecture.  This behavior can be prevented on a windows host using by setting `arduino.ArduinoBoard(enable_dtr=False)` (the default). See [issue #9](https://github.com/harmsm/PyCmdMessenger/issues/9) for discussion.  

##Quick reference for CmdMessenger on arduino side
For more details, see the [CmdMessenger](https://github.com/thijse/Arduino-CmdMessenger) project page.

###Receiving
```C
/* c is an instance of CmdMessenger (see example sketch above) */
/* ------- For all types except strings (replace TYPE appropriately) --------*/
int value = c.readBinArg<TYPE>();

/* ----- For strings (replace BUFFER_SIZE with maximum string length) ------ */
char string[BUFFER_SIZE] = c.readStringArg();

```
###Sending
```C
/* COMMAND_NAME must be enumerated at the top of the sketch.  c is an instance
 * of CmdMessenger (see example sketch above) */

/* ------------------- For all types except strings ------------------------*/

// Send single value
c.sendBinCmd(COMMAND_NAME,value);

// Send multiple values via a single command
c.sendCmdStart(COMMAND_NAME);
c.sendCmdBinArg(value1);
c.sendCmdBinArg(value2);
// ...
// ...
c.sendCmdEnd();

/* ------------------------- For strings ------------------------------------- */
// Send single string 
c.sendCmd(COMMAND_NAME,string);

// Send multiple strings via a single command
c.sendCmdStart(COMMAND_NAME);
c.sendCmdArg(string1);
c.sendCmdArg(string2);
// ...
// ...
c.sendCmdEnd();
```

##Release Notes

###0.2.4:
 + Added `byte` data type
 + Binary strings passed back and forth are now explicitly little-endian
 + Added `*` multiple format flag

##Python Classes

```
ArduinoBoard 
    Class for connecting to an Arduino board over USB using PyCmdMessenger.  
    The board holds the serial handle (which, in turn, holds the device name,
    baud rate, and timeout) and the board parameters (size of data types in 
    bytes, etc.).  The default parameters are for an ArduinoUno board.

    Static methods
    --------------
    __init__(self, device, baud_rate=9600, timeout=1.0, settle_time=2.0, enable_dtr=False, int_bytes=2, long_bytes=4, float_bytes=4, double_bytes=4)
        Serial connection parameters:
            
            device: serial device (e.g. /dev/ttyACM0)
            baud_rate: baud rate set in the compiled sketch
            timeout: timeout for serial reading and writing
            settle_time: how long to wait before trying to access serial port
            enable_dtr: use DTR (set to False to prevent arduino reset on connect)

        Board input parameters:
            int_bytes: number of bytes to store an integer
            long_bytes: number of bytes to store a long
            float_bytes: number of bytes to store a float
            double_bytes: number of bytes to store a double

        These can be looked up here:
            https://www.arduino.cc/en/Reference/HomePage (under data types)

        The default parameters work for ATMega328p boards.

    close(self)
        Close serial connection.

    read(self)
        Wrap serial read method.

    readline(self)
        Wrap serial readline method.

    write(self, msg)
        Wrap serial write method.

    Instance variables
    ------------------
    baud_rate

    comm

    device

    double_bytes

    float_bytes

    int_bytes

    int_max

    int_min

    long_bytes

    long_max

    long_min

    settle_time

    timeout

    unsigned_int_max

    unsigned_int_min

    unsigned_long_max

    unsigned_long_min

CmdMessenger 
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.

    Static methods
    --------------
    __init__(self, board_instance, commands, field_separator=',', command_separator=';', escape_separator='/', warnings=True)
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

    receive(self, arg_formats=None)
        Recieve commands coming off the serial port. 

        arg_formats is an optimal keyword that specifies the formats to use to
        parse incoming arguments.  If specified here, arg_formats supercedes
        the formats specified on initialization.

    send(self, cmd, *args)
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  

        arg_formats is an optional string that specifies the formats to use for
        each argument when passed to the arduino. If specified here,
        arg_formats supercedes formats specified on initialization.

    Instance variables
    ------------------
    board

    command_separator

    commands

    escape_separator

    field_separator

    give_warnings
```


