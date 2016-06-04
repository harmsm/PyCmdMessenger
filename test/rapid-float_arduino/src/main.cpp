#include "CmdMessenger.h"  

CmdMessenger c = CmdMessenger(Serial, ',',';','/');

enum
{
    double_ping,
    double_pong,
};

void on_double_ping(void){
    double value = c.readBinArg<double>();
    c.sendBinCmd(double_pong, value);

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

