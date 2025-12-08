#include <Arduino.h>
#include <OneWire.h>  
#include <DallasTemperature.h>

#define dados 27  // Pino do sensor DS18B20

#define PWM_PIN 18
#define PWM_CHANNEL 0
#define PWM_FREQ 1000
#define PWM_RESOLUTION 10

#define MAX_BUFFER 50
char buffer[MAX_BUFFER];
byte indexBuffer = 0;

SemaphoreHandle_t xSerialMutex;

void vSensorTask(void *pvParameters);
void vSerialTask(void *pvParameters);
void processarComando(char *cmd);

void setup() {
  Serial.begin(115200);
  delay(2000);

  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PWM_PIN, PWM_CHANNEL);

  Serial.println("ESP32 pronto! Iniciando FreeRTOS Tasks...");

  xSerialMutex = xSemaphoreCreateMutex();
  if (xSerialMutex == NULL) {
    Serial.println("Falha ao criar o Mutex!");
    while (1);
  }

  xTaskCreatePinnedToCore(
      vSensorTask,
      "SensorTask",
      2048,
      NULL,
      1,
      NULL,
      1);

  xTaskCreatePinnedToCore(
      vSerialTask,
      "SerialTask",
      2048,
      NULL,
      2,
      NULL,
      1);
}

void loop() {
  // O loop() agora fica vazio
}

void vSensorTask(void *pvParameters) {
  for (;;) {
    float temp = 25.5 + (random(-50, 50) / 100.0);

    if (xSemaphoreTake(xSerialMutex, portMAX_DELAY) == pdTRUE) {
      Serial.print("TEMP:");
      Serial.println(temp, 2);
      xSemaphoreGive(xSerialMutex);
    }

    vTaskDelay(pdMS_TO_TICKS(2000));
  }
}

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

void processarComando(char *cmd) {
  if (strncmp(cmd, "SET_PWM:", 8) == 0) {
    int duty = atoi(cmd + 8);
    duty = constrain(duty, 0, 1023);

    ledcWrite(PWM_CHANNEL, duty);

    if (xSemaphoreTake(xSerialMutex, portMAX_DELAY) == pdTRUE) {
      Serial.print("PWM atualizado para: ");
      Serial.println(duty);
      xSemaphoreGive(xSerialMutex);
    }
  }
}