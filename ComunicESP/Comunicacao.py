import serial
import time
import sys

porta_serial = 'COM3'  
baudrate = 115200      # ESP32 agora roda estável em 115200

referencia = 5.0  # °C desejada(trocar para o valor ser fornecido pelo usuário)

try:
    ser = serial.Serial(porta_serial, baudrate, timeout=1)
    time.sleep(2)  # tempo para estabilizar a conexão
    print("Conexão serial estabelecida com o ESP32.")

    # Descarta qualquer dado que ainda esteja no buffer
    ser.reset_input_buffer()

    while True:
        try:
            ser.write(f"{referencia}\n".encode())
            print(f'Referência enviada: {referencia}°C')
            if ser.in_waiting > 0:
                try:
                    linha = ser.readline().decode().strip()
                    if linha:
                        temperatura_atual = float(linha)
                        print(f'Temperatura atual do sistema: {temperatura_atual}°C')
                        erro = referencia - temperatura_atual
                        print(f'Erro: {erro}°C')
                    else:
                        print('Nenhum dado recebido.')
                except ValueError:
                    print('Erro ao converter a temperatura recebida.')
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("Comunicação encerrada pelo usuário.")
            break

except serial.SerialException as e:
    print(f"Erro ao conectar na porta serial: {e}")
    sys.exit()

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Porta serial fechada.")
