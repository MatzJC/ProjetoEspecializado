#include <Arduino.h>
#include <OneWire.h>  
#include <DallasTemperature.h>

#define dados 27  // Pino do sensor DS18B20

#define PWM_PIN 18
#define PWM_CHANNEL 0
#define PWM_FREQ 1000
#define PWM_RESOLUTION 8  // 10 bits (0-1023)

float y = 0;
float t_ini = 0;
float yant =0;
long u = 0;
int rho = 5;
float P1 = rho;
float P2 = 0;
float P3 = 0;
float P4 = rho;
float a = 1e-6;
float b = 1e-6;
float r = 6;  // Referência inicial
float k = 1;
float eant = 0;
float uant = 0;
float tau = 5000;  // Tempo inicial

long tempo_ant = 0;
long tempo = 100;
long tempo_ini=0;

bool first_line_received = true;  // Flag para parse de linhas

OneWire oneWire(dados);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(115200);
  delay(2000);  // Estabiliza serial
  
  // Desativa WDT para debug (comente após testar!)
  disableCore0WDT();
  disableCore1WDT();
  
  // Configura PWM
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PWM_PIN, PWM_CHANNEL);
  
  sensors.begin();
  sensors.requestTemperatures();
  t_ini = sensors.getTempCByIndex(0);
  Serial.println(t_ini);
  yant=0;
  eant=r-t_ini;
  tempo_ini=millis();
}

void loop() {
  unsigned long now = millis();
  
  if (now - tempo_ant >= tempo) {
    sensors.requestTemperatures();
    float raw_temp = sensors.getTempCByIndex(0);
    y = t_ini-raw_temp;
    Serial.println(raw_temp, 2);

    float denom = 1 + (u * u * P1 - u * yant * P3 - u * yant * P2 + yant * yant * P4);
    if (denom == 0) {  // Proteção!
      denom = 1e-6;  // Valor pequeno para evitar crash
    }
    
    float h1 = (u * P1 - yant * P2) / denom;
    float h2 = (u * P3 - yant * P4) / denom;
    
    b = b + h1 * (y - u * b) + yant * a * h1;  // Corrigido: assumindo 'temp' era erro anterior
    a = a + h2 * (y - u * b) + yant * a * h2;  // Ajuste se 'temp' for diferente

    float P1temp = P1;
    float P2temp = P2;
    P1 = P1 - P1 * h1 * u + P3 * h1 * yant;
    P2 = P2 - P2 * h1 * u + P4 * h1 * yant;
    P3 = -h2 * u * P1temp + (1 + h2 * yant) * P3;
    P4 = -h2 * u * P2temp + (1 + h2 * yant) * P4;

    float e = r - y;  // Erro: referência - atual
    // Controlador Dhalin
    float c = -exp(-tempo/tau);
    //float num = (k + k * c) * e + (k * c * a + k * a) * eant - b * c * u + (k * b + k * c * b) * uant;
    //if (isnan(num) || isinf(num)) {  // Protege contra NaN/Inf
    //  u = 255;
    //} else {
    
      //u = num / b;     
    //}
    
    //Controlador PID
    float kg=b/(1+a);
    float wn=1/tau;
    int qsi=1;
    float kc=(2*qsi*wn*tau*2-1)/kg;
    float ti=(kg*kc)/(2*tau*(wn*wn));
    u=u+kc*((e-eant)+(tempo/ti)*e);
    if ((now-tempo_ini)<50000)
    {
      u=255;      
    }
    
    if (isnan(u) || isinf(u)){
      u = 255;
    }
    // Limita u para PWM (10-bit: 0-1023)
    if (u > 255){
      u = 255;
    }
    else if (u < 0){
      u = 0;
    }
    // Aplica PWM
    ledcWrite(PWM_CHANNEL, (int)u);  // Cast para int

    eant = e;
    uant = u;
    yant = y;
    tempo_ant = now;
  }
  
  // Pequeno yield para não monopolizar CPU
  yield();
}