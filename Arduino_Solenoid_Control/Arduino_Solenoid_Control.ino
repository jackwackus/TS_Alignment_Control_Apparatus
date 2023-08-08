/*
Author: Jack Connor
Date Created: 2020

This is an Arduino program that turns on and off a digital pin in response to a serial command.
The program saves the state of the digital pin as an integer: 0 = off, 1 = on.
If the pin state is off, the program turns the pin on. If the pin state is on, the program turns the pin off.
*/

int relay = 8; //Pin 8
int toggle = 0; //binary toggle on and off

void setup()
{
  Serial.begin(9600);
  pinMode(relay, OUTPUT);
}

void loop() 
{
  if (Serial.available())
  {
    if (Serial.read() == 060)
    {
      if (toggle == 1)
      {
        toggle = 0;
        digitalWrite(relay, LOW);
      }
      else
      {
        toggle = 1;
        digitalWrite(relay, HIGH);
      }
    }
  }
  delay(100);
}
