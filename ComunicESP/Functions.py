import serial
import time
import sys

def obterReferencia():
    while True:
        try:
            valor = float(input("Digite a temperatura de referência desejada(°C): "))
            return valor
        except ValueError:
            print("Entrada inválida. Por favor, insira um valor válido.")

def obterTempo():
    while True:
            try:
                valor = float(input("Digite o tempo de assentamento desejado(s): "))
                return valor
            except ValueError:
                print("Entrada inválida. Por favor, insira um valor válido.")

def conectarESP32(porta, baud):
    try:
        conexao = serial.Serial(porta, baud, timeout=1)
        time.sleep(2)  # tempo para estabilizar a conexão
        print("Conexão serial estabelecida com o ESP32.")
        return conexao
    except serial.SerialException as e:
        raise RuntimeError(f"Erro ao conectar na porta serial: {e}")

def enviaDados(referencia, port,tempo):
    port.write(f"{referencia}\n{tempo}\n".encode())
    print(f'Referências enviada: {referencia}°C e {tempo}s')

def recebeDados(referencia, port):
    if port.in_waiting > 0:
        try:
            linha = port.readline().decode().strip()
            if linha:
                try:
                    temperatura_atual = float(linha)
                    print(f'Temperatura atual do sistema: {temperatura_atual}°C')
                    erro = referencia - temperatura_atual
                    print(f'Erro: {erro}°C')
                except ValueError:
                    print(f'Erro ao converter a temperatura recebida: {linha}')
            else:
                print('Nenhum dado recebido.')
        except ValueError:
            print('Erro ao converter a temperatura recebida.')
        except serial.SerialException as e:
            print(f'Erro na comunicação serial: {e}')