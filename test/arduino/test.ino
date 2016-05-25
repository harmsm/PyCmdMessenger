/* -----------------------------------------------------------------------------
 * Test .ino file to verify PyCmdMessenger functionality.  Should be compiled
 * with CmdMessenger.h and CmdMessenger.cpp in the sketch directory, then 
 * loaded onto the arduino prior to running run_test.py from the 
 * PyCmdMessenger/test/run_tests.py script.
 *----------------------------------------------------------------------------*/

#include "CmdMessenger.h"

const int BAUD_RATE = 9600;
CmdMessenger c = CmdMessenger(Serial,',',';','/');

/* Define available CmdMessenger commands */
enum {
    send_string,
    send_float,
    send_int,
    send_two_int,
    receive_string,
    receive_float,
    receive_int,
    receive_two_int,
    result,
    error,
};

void on_unknown_command(void){
    c.sendCmd(error,"Command without callback.");
}

void on_send_string(void){
    c.sendCmd(result,"A string with /, and /; escape");
}

void on_send_float(void){
    c.sendCmd(result,99.9);
}

void on_send_int(void){
    c.sendCmd(result,-10);
}

void on_send_two_int(void){

    int i;

    c.sendCmdStart(result);
    c.sendCmdArg(-10);
    c.sendCmdArg(10);
    c.sendCmdEnd();

}

void on_receive_string(void){
    char * value = c.readStringArg();
    c.sendCmd(result,"got it!");
}

void on_receive_float(void){
    float value = c.readFloatArg();
    c.sendCmd(result,value*10.0);
}

void on_receive_int(void){
    int value = c.readInt16Arg();
    c.sendCmd(result,value*10);
}

void on_receive_two_int(void){

    int value1 = c.readInt16Arg();
    int value2 = c.readInt16Arg();

    c.sendCmdStart(result);
    c.sendCmdArg(10*value1);
    c.sendCmdArg(10*value2);
    c.sendCmdEnd();

}

/* Define callbacks for CmdMessenger commands */
void attach_callbacks(void) { 
  
    // Attach callback methods
    c.attach(on_unknown_command);

    c.attach(send_string,on_send_string);
    c.attach(send_float,on_send_float);
    c.attach(send_int,on_send_int);
    c.attach(send_two_int,on_send_two_int);

    c.attach(receive_string,on_receive_string);
    c.attach(receive_float,on_receive_float);
    c.attach(receive_int,on_receive_int);
    c.attach(receive_two_int,on_receive_two_int);

}

void setup() {
    Serial.begin(BAUD_RATE);
    c.printLfCr();  // <-- This is critical, as python library assumes newlines
    attach_callbacks();    
}

void loop() {
    c.feedinSerialData();
}
