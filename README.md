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
 * Arduino must send commands with the "\r\n" line ending [NOT SURE THIS IS TRUE]

The programs shown below are in the [examples](https://github.com/harmsm/PyCmdMessenger/tree/master/examples) directory.
 
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
    sum_two_ints,
    result,
    error,
};

/* Initialize CmdMessenger -- this should match PyCmdMessenger instance */
const int BAUD_RATE = 9600;
CmdMessenger c = CmdMessenger(Serial,',',';','/');


/* callback */
void on_unknown_command(void){
    c.sendCmd(error,"Command without callback.");
}

/* callback */
void on_who_are_you(void){
    c.sendCmd(result,"Bob");
}

/* callback */
void on_sum_two_ints(void){
   
    /* Grab two integers */
    int value1 = c.readInt16Arg();
    int value2 = c.readInt16Arg();

    /* Send result back */ 
    c.sendCmdStart(result);
    c.sendCmdArg(value1);
    c.sendCmdArg(value2);
    c.sendCmdArg(value1 + value2);
    c.sendCmdEnd();

}

/* Attach callbacks for CmdMessenger commands */
void attach_callbacks(void) { 
  
    c.attach(on_unknown_command);
    c.attach(who_are_you,on_who_are_you);
    c.attach(sum_two_ints,on_sum_two_ints);
}

void setup() {
    Serial.begin(BAUD_RATE);
    c.printLfCr();  // <-- This is critical, as python library assumes newlines
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
import time

# Initialize instance of class with appropriate device.  command_names must 
# match names and order from arduino file.
c = PyCmdMessenger.PyCmdMessenger("/dev/ttyACM0",
                                  command_names=("who_are_you",
                                                 "sum_two_ints",
                                                 "result",
                                                 "error"))

# Give time for the device to connect
time.sleep(2)

# Send and receive
c.send("who_are_you")
msg = c.receive()

# should give [TIME_IN_S,"result","Bob"]
print(msg)

# Send with multiple parameters
c.send("sum_two_ints",4,1)
msg = c.receive()

# should give [TIME_IN_S,"result",4,1,5]
print(msg)
```

### Python, using listener:

```python
import time
import PyCmdMessenger

c = PyCmdMessenger.PyCmdMessenger("/dev/ttyACM0",
                                  command_names=("who_are_you",
                                                 "sum_two_ints",
                                                 "result",
                                                 "error"))
# wait for connection
time.sleep(2)

# start listening
c.listen()

# stop listening
for i in range(10):
    c.send("who_are_you")

# Do other stuff.  The listener is capturing the output from the arduino on its
# own thread right now.
time.sleep(5)

# Now grab the messages it received in the background.  This should be a list of
# messages with timestamps.
messages = c.receive_from_listener()
for m in messages:
    print(m)

c.stop_listening()
```

##Python API reference
----------------------

####Module PyCmdMessenger
---------------------

####Classes
-------

PyCmdMessenger 
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.

    Ancestors (in MRO)
    ------------------
    PyCmdMessenger.PyCmdMessenger
    builtins.object

    Static methods
    --------------
    __init__(self, device, command_names, timeout=0.25, baud_rate=9600, field_separator=',', command_separator=';', escape_separator='/', convert_strings=True)
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

    listen(self, listen_delay=1)
        Listen for incoming messages on its own thread, appending to recieving
        queue.  

        Input:
            listen_delay: time to wait between checks (seconds)

    receive(self)
        Read a single serial message sent by CmdMessage library.

    receive_all(self)
        Get all messages from the arduino (both from listener and the complete
        current serial buffer).

    receive_from_listener(self, warn=True)
        Return messages that have been grabbed by the listener.

        Input:
            warn: warn if the listener is not actually active.

    send(self, *args)
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  The function will convert
        python data types to strings, as well as escaping all separator
        characters in strings.

    stop_listening(self)
        Stop an existing listening thread.

    Instance variables
    ------------------
    baud_rate

    command_names

    command_separator

    device

    escape_separator

    field_separator

    timeout
