#PyCmdMessenger

Python class for communication with an arduino using the
[CmdMessenger](https://github.com/thijse/Arduino-CmdMessenger) serial
communication library. It allows sending and recieving of messages with
arguments, as well as a recieving via a listener on its own thread.

This project is not affiliated with the CmdMessenger project, though it
obviously builds off of their excellent work.

### Installation:
 * From github: 
    + `git clone https://github.com/harmsm/PyCmdMessenger.git` 
    + `cd PyCmdMessenger`
    + `sudo python3 setup.py install`
 * From pipi:
    + `sudo pip3 install PyCmdMessenger`

For python 2.7, replace `python3` with `python` and `pip3` with `pip`.

To test the library:
 * Clone the source from git
 * Compile the arduino sketch in the `test` directory
 * Transfer the compiled sketch to an arduino plugged into the computer
 * Run the `test/run_test.py` script.  This will pass a variety of data types
   between the local computer and the arduino.

### Compatibility
 * Compatibility: python 3.x, python 2.7
 * Should work on all platforms supported by pyserial.  
 * Tested on a Raspberry Pi (raspbian) and linux machine (Ununtu 15.10).  Have 
not tested on Windows or OSX.

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
--------------

A typical CmdMessenger message has the following structure:

```
Cmd Id, param 1, [...] , param N;
```

The PyCmdMessenger class constructs/parses these strings, as well as sending 
them over the serial connection via pyserial.  

To ensure stable communication with PyCmdMessenger:

 * PyCmdMessenger instances must be given a list of command names in the *same*
   order as those commands are specified in the arduino sketch.  
 * Separators must match between the PyCmdMessenger instance and the arduino
   sketch. 
   + field separator (default ",")
   + command separator (default ";")
   + escape separator, so field and command separators can be sent within
     strings (default "/")
 * Baud rate must match between PyCmdMessenger class and arduino sketch. 
    
A basic example is shown below.  These files are in the 
[examples](https://github.com/harmsm/PyCmdMessenger/tree/master/examples) directory.
 
###Arduino sketch

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
    c.sendCmdStart(sum_is);
    c.sendCmdBinArg(value1 + value2);
    c.sendCmdEnd();

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

# List of command_names in arduino file. These must be in the same order as in
# the sketch.
command_names = ["who_are_you","my_name_is","sum_two_ints","sum_is","error"]

# List of data types being sent/recieved for each command, again in the same 
# order. 
command_formats = ["","s","ii","i","s"]

# Initialize the messenger
c = PyCmdMessenger.CmdMessenger(arduino,
                                command_names=command_names,
                                command_formats=command_formats)

# Send
c.send("who_are_you")
# Receive. Should give ["my_name_is","Bob",TIME_RECIEVED]
msg = c.receive()
print(msg)

# Send with multiple parameters
c.send("sum_two_ints",4,1)
msg = c.receive()

# should give ["sum_is",5,TIME_RECEIVED]
print(msg)
```

## Sending from python to arduino
| name | arduino type  | Python Type              | Receive call                                         |
|------|---------------|--------------------------|------------------------------------------------------|
| "b"  | bool          | bool                     | bool value = c.readBinArg<bool>();                   |
| "i"  | int           | int                      | int value = c.readBinArg<int>();                     |
| "I"  | unsigned int  | int                      | unsigned int value = c.readBinArg<unsigned int>();   |
| "l"  | long          | int                      | long value = c.readBinArg<long>();                   |
| "L"  | unsigned long | int                      | unsigned long value = c.readBinArg<unsigned long>(); |
| "f"  | float         | float                    | float value = c.readBinArg<float>();                 |
| "d"  | double        | float                    | double value = c.readBinArg<double>();               |
| "c"  | char          | str or bytes, length = 1 | char value = c.readBinArg<char>();                   |
| "s"  | char[]        | str or bytes             | char *value = c.readStringArg();                     |


// Receive single value
int value = c.readBinArg<int>();

// Receive multiple values
int value1 = c.readBinArg<int>();
int value2 = c.readBinArg<int>();

// Send single value (COMMAND_NAME must be enumerated at top of sketch)
c.sendBinCmd(COMMAND_NAME,value);

// Send multiple values via a single command
c.sendCmdStart(COMMAND_NAME);
c.sendBinArg(value1);
c.sendBinArg(value2);
c.sendCmdEnd();


##Python API reference
----------------------

###Module PyCmdMessenger
---------------------

####Classes
-------
CmdMessenger 
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.

    Static methods
    --------------
    __init__(self, board_instance, command_names, command_formats=None, field_separator=',', command_separator=';', escape_separator='/', warnings=True)
        Input:
        board_instance:
            instance of ArduinoBoard initialized with correct serial 
            connection (points to correct serial with correct baud rate) and
            correct board parameters (float bytes, etc.)

        command_names:
            a list or tuple of the command names specified in the arduino
            .ino file *in the same order they are listed there.*  

        command_formats:
            a list or tuple of strings that specify the formats of the
            commands in command names.  Optional but *highly* recommmended.
            Default: None

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

        arg_formats optional, but highly recommended if you do not initialize
        the class instance with a command_formats argument.  The keyword  
        specifies the formats to use to parse incoming arguments.  If specified
        here, arg_formats supercedes command_formats specified on initialization.

    send(self, cmd, *args)
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  

        arg_formats optional, but highly recommended if you do not initialize
        the class instance with a command_formats argument.  The keyword  
        specifies the formats to use for each argument when passed to the
        arduino. If specified here, arg_formats supercedes command_formats
        specified on initialization.

    Instance variables
    ------------------
    board

    command_formats

    command_names

    command_separator

    escape_separator

    field_separator

    give_warnings

ArduinoBoard 
    Class for connecting to an Arduino board over USB using PyCmdMessenger.  
    The board holds the serial handle (which, in turn, holds the device name,
    baud rate, and timeout) and the board parameters (size of data types in 
    bytes, etc.).  The default parameters are for an ArduinoUno board.

    Static methods
    --------------
    __init__(self, device, baud_rate=9600, timeout=1.0, settle_time=2.0, int_bytes=2, long_bytes=4, float_bytes=4, double_bytes=4)
        Serial connection parameters:
            
            device: serial device (e.g. /dev/ttyACM0)
            baud_rate: baud rate set in the compiled sketch
            timeout: timeout for serial reading and writing
            settle_time: how long to wait before trying to access serial port

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
