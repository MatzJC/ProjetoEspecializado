#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// --------------------------------------
// DEFINIÇÕES DE HARDWARE
// --------------------------------------
#define DADOS 27
#define PWM_PIN 18
#define PWM_CHANNEL 0
#define PWM_FREQ 1000
#define PWM_RESOLUTION 8   // seu código usa 8 bits (0–255)

// --------------------------------------
// VARIÁVEIS DO CONTROLADOR
// --------------------------------------
float y = 0, t_ini = 0, yant = 0;
long u = 0;
int rho = 5;
float P1 = rho, P2 = 0, P3 = 0, P4 = rho;
float a = 1e-6, b = 1e-6;
float r = 4;
float k = 1;
float eant = 0;
float uant = 0;
float uant2 = 0;
float tau = 5000;

long tempo_ant = 0;
long tempo = 500;  // período da tarefa
long tempo_ini = 0;

// --------------------------------------
// SENSOR
// --------------------------------------
OneWire oneWire(DADOS);
DallasTemperature sensors(&oneWire);

// --------------------------------------
// FREE RTOS
// --------------------------------------
SemaphoreHandle_t xSerialMutex;
TaskHandle_t TaskControle;

// --------------------------------------
// PROTÓTIPOS
// --------------------------------------
void vControleTask(void *pvParameters);
void vSerialTask(void *pvParameters);
void processarComando(char *cmd);

// Buffer para comandos
#define MAX_BUFFER 50
char buffer[MAX_BUFFER];
byte indexBuffer = 0;

// --------------------------------------
// SETUP
// --------------------------------------
void setup() {
  Serial.begin(115200);
  delay(2000);

  // PWM
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PWM_PIN, PWM_CHANNEL);

  // Sensor
  sensors.begin();
  sensors.setResolution(11);
  sensors.requestTemperatures();
  t_ini = sensors.getTempCByIndex(0);

  yant = 0;
  eant = r;
  tempo_ini = millis();

  // Mutex Serial
  xSerialMutex = xSemaphoreCreateMutex();

  // --------------------------------------
  // CRIAÇÃO DAS TASKS
  // --------------------------------------
  xTaskCreatePinnedToCore(
      vControleTask,
      "ControleTask",
      4096,
      NULL,
      2,
      &TaskControle,
      1
  );

  xTaskCreatePinnedToCore(
      vSerialTask,
      "SerialTask",
      2048,
      NULL,
      1,
      NULL,
      1
  );

  Serial.println("FreeRTOS + Controle iniciados!");
}

// --------------------------------------
// LOOP VAZIO
// --------------------------------------
void loop() {
  // Não usamos loop(), tudo roda em tasks
}

// ============================================================================
//                                TAREFA DE CONTROLE
// ============================================================================
void vControleTask(void *pvParameters) {
  for (;;) {

    unsigned long now = millis();

    // Mantém o tempo de amostragem
    if (now - tempo_ant >= tempo) {

      sensors.requestTemperatures();
      float raw_temp = sensors.getTempCByIndex(0);

      y = t_ini - raw_temp;

      // ---------- Estimador ----------
      float denom = 1 + (uant * uant * P1 - uant * yant * P3 - uant * yant * P2 + yant * yant * P4);
      if (denom == 0) denom = 1e-6;

      float h1 = (uant * P1 - yant * P2) / denom;
      float h2 = (uant * P3 - yant * P4) / denom;

      b = b + h1 * (y - uant * b) + yant * a * h1;
      a = a + h2 * (y - uant * b) + yant * a * h2;

      float P1temp = P1;
      float P2temp = P2;
      P1 = P1 - P1 * h1 * uant + P3 * h1 * yant;
      P2 = P2 - P2 * h1 * uant + P4 * h1 * yant;
      P3 = -h2 * uant * P1temp + (1 + h2 * yant) * P3;
      P4 = -h2 * uant * P2temp + (1 + h2 * yant) * P4;

      float e = (r + 1) - y;

      float taue = (-tempo) / (log(-a));
      tau = taue / 8;

      // ---------- Controlador Dahlín ----------
      float c = -exp(-tempo / tau);
      float num = (k + k * c) * e +
                  (k * c * a + k * a) * eant -
                  b * c * uant +
                  (k * b + k * c * b) * uant2;

      u = num / b;

      /*
    //Controlador PID
    float kg=b/(1+a);
    float wn=1/tau;
    int qsi=1;
    float kc=(2*qsi*wn*taue-1)/kg;
    float ti=(kg*kc)/(taue*(wn*wn));
    u=uant+kc*((e-eant)+(tempo/ti)*e);
    */

    /*
    //PID classico
    u=82.9*e-82.58*eant+uant;
    */

    //Serial.print("Controle: ");
    //Serial.println(u);
    //Inicia o controle em malha aberta para identificar o comportamento base da planta

      // ---------- Identificação inicial ----------
      if ((now - tempo_ini) < 60000) {
        u = 255;
      }

      // ---------- Proteções e saturações ----------
      if (isnan(u) || isinf(u)) u = 255;
      if (u > 255) u = 255;
      if (u < 0)   u = 0;

      ledcWrite(PWM_CHANNEL, (int)u);

      // ---------- Atualiza estados ----------
      eant = e;
      uant2 = uant;
      uant = u;
      yant = y;
      tempo_ant = now;

      // Imprime temperatura
      if (xSemaphoreTake(xSerialMutex, portMAX_DELAY) == pdTRUE) {
        Serial.print("Y: ");
        Serial.print(y);
        Serial.print("  U: ");
        Serial.println(u);
        xSemaphoreGive(xSerialMutex);
      }
    }

    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

// ============================================================================
//                                TAREFA SERIAL
// ============================================================================
void vSerialTask(void *pvParameters) {
  for (;;) {
    while (Serial.available() > 0) {
      char c = Serial.read();

      if (c == '\n') {
        buffer[indexBuffer] = '\0';
        processarComando(buffer);
        indexBuffer = 0;
      } else {
        if (indexBuffer < MAX_BUFFER - 1) {
          buffer[indexBuffer++] = c;
        }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// ----------------------------------------------------------------------------
// COMANDOS SERIAIS
// ----------------------------------------------------------------------------
void processarComando(char *cmd) {
  if (strncmp(cmd, "SET_PWM:", 8) == 0) {
    int duty = atoi(cmd + 8);
    duty = constrain(duty, 0, 255);  // 8 bits

    ledcWrite(PWM_CHANNEL, duty);

    if (xSemaphoreTake(xSerialMutex, portMAX_DELAY) == pdTRUE) {
      Serial.print("PWM manual = ");
      Serial.println(duty);
      xSemaphoreGive(xSerialMutex);
    }
  }
}
