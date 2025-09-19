#include <Arduino.h>

#define PWM_PIN 18
#define PWM_CHANNEL 0
#define PWM_FREQ 1000
#define PWM_RESOLUTION 10 // 10 bits (0-1023)

#define MAX_BUFFER 50   // Tamanho máximo do comando
char buffer[MAX_BUFFER];
byte indexBuffer = 0;

float y=0;
float u=0;
int rho=5;
float P1=rho;
float P2=0;
float P3=0;
float P4=rho;
float a=0;
float b=0;
float r=15;
float k=1;
float eant=r;
float uant=0;

void setup() {
  Serial.begin(115200);
  delay(2000);

  // Configura PWM
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PWM_PIN, PWM_CHANNEL);
}

void loop() {
  // Simula leitura de temperatura (trocar por sensor real)
  float temp = 25.5 + (random(-50, 50) / 100.0); 
  Serial.print("TEMP:");
  Serial.println(temp, 2);

  float h1=(u*P1-y*P2)/(1+((u*u)*P1-u*y*P3-u*y*P2+(y*y)*P4));
  float h2=(u*P3-y*P4)/(1+((u*u)*P1-u*y*P3-u*y*P2+(y*y)*P4));
  
  a=a+h1*temp-u*a*h1+y*b*h1;
  b=b+h2*temp-u*a*h2+y*b*h2;

  float P1temp=P1;
  float P2temp=P2;
  P1=P1-P1*h1*u+P3*h1*y;
  P2=P2-P2*h1*u+P4*h1*y;
  P3=-h2*u*P1temp+(1+h2*y)*P3;
  P4=-h2*u*P2temp+(1+h2*y)*P4;

  float e=r-temp;

  float tau=1/(2*log(-a));
  float c=-exp(-1/tau);

  u=((k+k*c)*e+(k*c*a+k*a)*eant-b*c*u+(k*b+k*c*b)*uant)/b;

  if(u>255){
    u=255;
  }
  else if(u<0){
    u=0;
  }

  eant=e;
  uant=u;
  y=temp;

  ledcWrite(PWM_PIN,u);
}