#PyCmdMessenger

Python class for communication with an arduino using the CmdMessenger serial
communication library. It allows simple sending and recieving of commands,
getting all commands resident in the serial output buffer at once, and using 
a listener on its own thread to recieve messages as they come in and append
them to a recieved messages list. 

This class requires the baud rate and separators match between the
PyCmdMessenger class instance and the arduino sketch.  The library also
assumes the serial data are binary strings, and that each command send by the
arduino has a \r\n line-ending.  

##Example code

###Arduino sketch

```C

/* -----------------------------------------------------------------------------
 * Minimal .ino file for arduino, compiled with CmdMessenger.h and
 * CmdMessenger.cpp in the sketch directory. 
 *----------------------------------------------------------------------------*/

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
    c.printLfCr();  // <-- This is critical, as python library assumes newlines
    attach_callbacks();    
}

void loop() {
    c.feedinSerialData();
}
```

###Python
```python

# ------------------------------------------------------------------------------
# Minimal python program using the library to interface with the arduino sketch
# above.
# ------------------------------------------------------------------------------

import PyCmdMessenger

# Initialize instance of class with appropriate device.  command_names is
# optional. 
c = PyCmdMessenger.PyCmdMessenger("/dev/ttyACM0",
                                  command_names=("who_are_you",
                                                 "my_name_is",
                                                 "error"))

# Send and recieve
c.send("who_are_you")
msg = c.recieve()

# should give [TIME_IN_MS,"my_name_is","Bob"]
print(msg)
```


##Python API reference

####Module CmdMessenger
-------------------

####Classes
-------
CmdMessenger 
    Basic interface for interfacing over a serial connection to an arduino 
    using the CmdMessenger library.

    Ancestors (in MRO)
    ------------------
    CmdMessenger.CmdMessenger
    builtins.object

    Static methods
    --------------
    __init__(self, device, timeout=0.25, command_names=None, baud_rate=9600, field_separator=',', command_separator=';', escape_character='\\', convert_strings=True)
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

    listen(self, listen_delay=1)
        Listen for incoming messages on its own thread, appending to recieving
        queue.  

        Input:
            listen_delay: time to wait between checks (seconds)

    recieve(self)
        Read a single serial message sent by CmdMessage library.

    recieve_all(self)
        Get all messages that are coming off arduino (listener and the complete
        current serial buffer).

    recieve_from_listener(self, warn=True)
        Return messages that have been grabbed by the listener.

        Input:
            warn: warn if the listener is not actually active.

    send(self, *args)
        Send a command (which may or may not have associated arguments) to an 
        arduino using the CmdMessage protocol.  The command and any parameters
        should be passed as direct arguments to send.  The function will convert
        python data types to strings, as well as escaping problem characters.

    stop_listening(self)
        Stop an existing listening thread.

    Instance variables
    ------------------
    baud_rate

    command_separator

    device

    escape_character

    field_separator

    timeout



