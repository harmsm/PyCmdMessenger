#include "CmdMessenger.h"  

CmdMessenger c = CmdMessenger(Serial, ',',';','/');

enum
{
    double_ping,        // expects three doubles
    double_pong,        // returns three doubles
};

void on_double_ping(void){

    int i;
    double value;

    c.sendCmdStart(double_pong);
    for (i = 0; i < 3; i++){
        value = c.readBinArg<double>();
        c.sendCmdBinArg(value);
    }
    c.sendCmdEnd();

}


void attach_callbacks()
{
  c.attach(double_ping, on_double_ping);
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

