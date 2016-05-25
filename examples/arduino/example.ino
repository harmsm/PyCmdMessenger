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

