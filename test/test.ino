/* -----------------------------------------------------------------------------
 * Test .ino file to verify PyCmdMessenger functionality.  Should be compiled
 * with CmdMessenger.h and CmdMessenger.cpp in the sketch directory, then 
 * loaded onto the arduino prior to running run_test.py from the 
 * PyCmdMessenger/test/run_tests.py script.
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
