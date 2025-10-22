#include <Arduino.h>
#include <OneWire.h>  
#include <DallasTemperature.h>

#define dados 27  // Pino do sensor DS18B20

#define PIN_COLD 18
#define PIN_HOT 19

void setup() {
  Serial.begin(9600);
  delay(2000);  // Estabiliza serial
  pinMode(PIN_HOT,OUTPUT);
  pinMode(PIN_COLD,OUTPUT);
}

void loop() {
  digitalWrite(PIN_COLD,HIGH);
}