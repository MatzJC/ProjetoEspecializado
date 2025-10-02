#include <Arduino.h>
#include <OneWire.h>  
#include <DallasTemperature.h>

#define dados 27  // Pino do sensor DS18B20

#define PWM_PIN 18
#define PWM_CHANNEL 0
#define PWM_FREQ 1000
#define PWM_RESOLUTION 10  // 10 bits (0-1023)

float y = 0;
float u = 0;
int rho = 5;
float P1 = rho;
float P2 = 0;
float P3 = 0;
float P4 = rho;
float a = 0;
float b = 0;
float r = 20;  // Referência inicial
float k = 1;
float eant = r;
float uant = 0;
float tau = 5;  // Tempo inicial

unsigned long tempo_ant = 0;
unsigned long ts = 500;  // Aumentado para 500ms (evita WDT, sync com Python)

float y_ini = 0;

String receivedMessage = "";
bool first_line_received = false;  // Flag para parse de linhas

// Timers para não-bloqueio
unsigned long last_sensor_read = 0;
const unsigned long sensor_interval = 1000;  // Lê sensor a cada 1s (não a cada ts!)

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
  delay(100);  // Pequeno delay para sensor
  y_ini = sensors.getTempCByIndex(0);
  if (y_ini == DEVICE_DISCONNECTED_C) {
    y_ini = 0;  // Default
  }
  Serial.println(y_ini);
}

void readValues() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();  // Remove \r, espaços
    
    if (line.length() > 0 && line.toFloat() != 0.0) {  // Ignora linhas vazias ou inválidas
      if (!first_line_received) {
        r = line.toFloat();
        first_line_received = true;
        Serial.println(r);
      } else {
        tau = line.toFloat();
        first_line_received = false;
        Serial.println(tau);
      }
    }
  }
}

void loop() {
  unsigned long now = millis();
  
  if (now - tempo_ant >= ts) {
    // Leitura de sensor (não-bloqueante: só se passou 1s)
    if (now - last_sensor_read >= sensor_interval) {
      sensors.requestTemperatures();
      delay(100);  // Necessário para DS18B20 conversão
      float raw_temp = sensors.getTempCByIndex(0);
      if (raw_temp != DEVICE_DISCONNECTED_C) {
        y = y_ini - raw_temp;  // Seu cálculo (ajuste se necessário)
      } else {
        y = 0;  // Default em erro
        
      }
      last_sensor_read = now;
      Serial.println(y, 2);  // Debug: Envia sempre
    }

    // Lê comandos serial (não bloqueia)
    if (Serial.available()) {
      readValues();
    }

    // Cálculos do controlador (com proteção contra div/0)
    float denom = 1 + (u * u * P1 - u * y * P3 - u * y * P2 + y * y * P4);
    if (denom == 0) {  // Proteção!
      denom = 1e-6;  // Valor pequeno para evitar crash
      
    }
    
    float h1 = (u * P1 - y * P2) / denom;
    float h2 = (u * P3 - y * P4) / denom;
    
    a = a + h1 * (y - u * a) + y * b * h1;  // Corrigido: assumindo 'temp' era erro anterior
    b = b + h2 * (y - u * a) + y * b * h2;  // Ajuste se 'temp' for diferente

    // Atualização de P (temporárias para evitar race)
    float P1temp = P1;
    float P2temp = P2;
    P1 = P1 - P1 * h1 * u + P3 * h1 * y;
    P2 = P2 - P2 * h1 * u + P4 * h1 * y;
    P3 = -h2 * u * P1temp + (1 + h2 * y) * P3;
    P4 = -h2 * u * P2temp + (1 + h2 * y) * P4;

    float e = r - y;  // Erro: referência - atual

    // Controlador Dhalin (com proteção NaN)
    float c = -exp(-ts / 1000.0 / tau);  // ts em ms, tau em s → divida por 1000
    float num = (k + k * c) * e + (k * c * a + k * a) * eant - b * c * u + (k * b + k * c * b) * uant;
    if (isnan(num) || isinf(num)) {  // Protege contra NaN/Inf
      u = uant;  // Mantém anterior
    } else {
      u = num / b;
      if (isnan(u) || isinf(u)) u = uant;
    }

    // Limita u para PWM (10-bit: 0-1023)
    if (u > 1023) u = 1023;
    else if (u < 0) u = 0;

    eant = e;
    uant = u;

    // Aplica PWM
    ledcWrite(PWM_CHANNEL, (int)u);  // Cast para int

    // Debug: Print estado a cada ciclo
    Serial.print(e, 2);
    Serial.println((int)u);

    tempo_ant = now;
  }
  
  // Pequeno yield para não monopolizar CPU
  yield();
}


