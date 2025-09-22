import serial
import time
import sys

porta_serial = 'COM3'  
baudrate = 115200      # ESP32 agora roda estável em 115200

referencia = 5.0  # °C desejada(trocar para o valor ser fornecido pelo usuário)
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
                porta_serial.write(referencia.encode())
                print(f'Referência enviada: {referencia}°C')
            except KeyboardInterrupt:
                print("Comunicação encerrada.")
                porta_serial.close() # Fecha a conexão serial
        time.sleep(0.5)

except serial.SerialException as e:
    print(f"Erro ao conectar na porta serial: {e}")
    sys.exit()

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Porta serial fechada.")
