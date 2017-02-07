#include "CmdMessenger.h"  

/* Basic test code for sending multiple values back and forth with a * format. */

CmdMessenger c = CmdMessenger(Serial, ',',';','/');

enum
{
    multi_ping,        // expects some number of longs
    multi_pong,        // expects some number of longs
};

void on_multi_ping(void){

    int i;
    int series_length;

    // first argument says how many more arguments we're going to get
    series_length = c.readBinArg<int>();

    c.sendCmdStart(multi_pong);
    for (i = 0; i < series_length; i++){
        c.sendCmdBinArg(c.readBinArg<int>()); 
        delay(50);
    }
    c.sendCmdEnd();


}


void attach_callbacks()
{
  c.attach(multi_ping, on_multi_ping);
}

void setup() 
{
  Serial.begin(115200); 
  attach_callbacks();
}

void loop() 
{
  c.feedinSerialData();
}

