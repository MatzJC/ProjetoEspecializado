#include <Arduino.h>

#define PWM_PIN 18
#define PWM_CHANNEL 0
#define PWM_FREQ 1000
#define PWM_RESOLUTION 10 // 10 bits (0-1023)

#define MAX_BUFFER 50   // Tamanho máximo do comando
char buffer[MAX_BUFFER];
byte indexBuffer = 0;

// Forward declaration
void processarComando(char *cmd);

void setup() {
  Serial.begin(115200);
  delay(2000);

  // Configura PWM
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PWM_PIN, PWM_CHANNEL);

  Serial.println("ESP32 pronto para comunicação!");
}

void loop() {
  // Simula leitura de temperatura (trocar por sensor real)
  float temp = 25.5 + (random(-50, 50) / 100.0); 
  Serial.print("TEMP:");
  Serial.println(temp, 2);

  // Recebe dados byte a byte
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {  
      buffer[indexBuffer] = '\0';  // Fecha string
      processarComando(buffer);    
      indexBuffer = 0;             
    } else {
      if (indexBuffer < MAX_BUFFER - 1) {
        buffer[indexBuffer++] = c; 
      }
    }
  }

  delay(2000);
}

void processarComando(char *cmd) {
  if (strncmp(cmd, "SET_PWM:", 8) == 0) {
    int duty = atoi(cmd + 8);  // Converte número após "SET_PWM:"
    duty = constrain(duty, 0, 1023);
    ledcWrite(PWM_CHANNEL, duty);
    Serial.print("PWM atualizado para: ");
    Serial.println(duty);
  }
}
