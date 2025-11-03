#include <Arduino.h>
#include <OneWire.h>  
#include <DallasTemperature.h>

#define dados 27  // Pino do sensor DS18B20

#define PWM_PIN 17
#define PWM_CHANNEL 0
#define PWM_FREQ 1000
#define PWM_RESOLUTION 8  // 10 bits (0-1023)

TaskHandle_t Task1;

//Declaração das variaveis utilizadas
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
float r = 5;  // Referência inicial
float rfinal = 5;
float tfinal = 500;
float k = 1;
float eant = 0;
float uant = 0;
float tau = 5000;  // Tempo inicial

long tempo_ant = 0;
long tempo = 1000;//Tempo de amostragem
long tempo_ini=0;

float rstep = rfinal/(((tfinal*1000)-1)/tempo);

//Preparação do sensor de temperatura
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
  
  //Realiza medição da temperatura inicial
  sensors.begin();
  sensors.requestTemperatures();
  t_ini = sensors.getTempCByIndex(0);
  Serial.println(t_ini);
  //Defini saida, erro e tempo de inicio
  yant=0;
  eant=r-t_ini;
  tempo_ini=millis();
}

void loop() {
  unsigned long now = millis();
  //Mantem o tempo de amostragem constante
  if (now - tempo_ant >= tempo) {
    //Mede a temperatura
    sensors.requestTemperatures();
    float raw_temp = sensors.getTempCByIndex(0);
    //Calcula a variação de temperatura comparado com a incial
    y = t_ini-raw_temp;
    Serial.print("Temperatura: ");
    Serial.println(raw_temp, 2);
    Serial.print("Variação: ");
    Serial.println(y, 2);
    //Serial.print("Referencia: ");
    //Serial.println(r, 2);

    //Estimador MQR
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
    
    
    float taue=(-tempo)/(log(-a));
    tau=taue/8;

      
    //Controlador Dhalin
    float c = -exp(-tempo/tau);
    float num = (k + k * c) * e + (k * c * a + k * a) * eant - b * c * u + (k * b + k * c * b) * uant;
    // (1 + c) * e + (c * a + a) * eant - b * c * u + (b + c * b) * uant;
    // 
    u=num/b;
    

    /*
    //Controlador PID
    float kg=b/(1+a);
    float wn=1/tau;
    int qsi=1;
    float kc=(2*qsi*wn*taue-1)/kg;
    float ti=(kg*kc)/(taue*(wn*wn));
    u=u+kc*((e-eant)+(tempo/ti)*e);
    */

    Serial.print("Erro: ");
    Serial.println(e);
    Serial.print("Controle: ");
    Serial.println(u);

    /*
    //PID classico
    u=82.9*e-82.58*eant+u;
    */

    //Serial.print("Controle: ");
    //Serial.println(u);
    //Inicia o controle em malha aberta para identificar o comportamento base da planta
    if ((now-tempo_ini)<60000)
    {
      u=255;      
    }
    
    //Previne sinais de controle inválidos
    if (isnan(u) || isinf(u)){
      u = 255;
    }

    // Saturação do PWM
    if (u > 255){
      u = 255;
    }
    else if (u < 0){
      u = 0;
    }

    // Aplica PWM
    ledcWrite(PWM_CHANNEL, (int)u);  // Cast para int

    //Atualiza as variaveis que representam o estado anterior do sistema
    eant = e;
    uant = u;
    yant = y;
    tempo_ant = now;
    if(r<rfinal){
      r+=rstep;
    }
  }
  
  // Pequeno yield para não monopolizar CPU
  yield();
}