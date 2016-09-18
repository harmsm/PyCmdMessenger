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
