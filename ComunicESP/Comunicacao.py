import serial
import time
import sys

porta_serial = 'COM3'  
baudrate = 115200      # ESP32 agora roda estável em 115200

referencia = 5.0  # °C desejada
Kp = 40           # ganho proporcional

try:
    ser = serial.Serial(porta_serial, baudrate, timeout=1)
    time.sleep(2)  # tempo para estabilizar a conexão
    print("Conexão serial estabelecida com o ESP32.")

    # 🔹 Descarta qualquer dado que ainda esteja no buffer
    ser.reset_input_buffer()

    while True:
        if ser.in_waiting > 0:
            try:
                linha = ser.readline().decode('utf-8', errors='ignore').strip()
            except UnicodeDecodeError:
                linha = ""  # ignora se der erro

            # 🔹 Filtra: só mostra TEMP e PWM
            if linha.startswith("TEMP:"):
                print(f"ESP32: {linha}")

                try:
                    temp_atual = float(linha.split(":")[1])
                    erro = referencia - temp_atual
                    pwm = int(max(0, min(1023, Kp * erro)))

                    comando = f"SET_PWM:{pwm}\n"
                    ser.write(comando.encode('utf-8'))
                    print(f"Python: Temp={temp_atual:.2f} | Erro={erro:.2f} | PWM={pwm}")
                except (IndexError, ValueError):
                    print("⚠ Erro ao interpretar leitura do ESP32.")

            elif linha.startswith("PWM"):
                print(f"ESP32: {linha}")

        time.sleep(0.5)

except serial.SerialException as e:
    print(f"Erro ao conectar na porta serial: {e}")
    sys.exit()

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Porta serial fechada.")
