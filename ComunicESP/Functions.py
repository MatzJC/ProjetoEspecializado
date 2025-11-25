
import serial
import time

def conectarESP32(porta, baud):
    try:
        conexao = serial.Serial(porta, baud, timeout=1)
        time.sleep(2)
        print("Conexão serial estabelecida com o ESP32.")
        return conexao
    except serial.SerialException as e:
        raise RuntimeError(f"Erro ao conectar na porta serial: {e}")

def enviaDados(referencia, port, tempo):
    try:
        port.write(f"{referencia}\n{tempo}\n".encode())
    except serial.SerialException as e:
        print(f"Erro ao enviar dados: {e}")

def recebeDados(referencia, port, silent=False):
    try:
        if port.in_waiting > 0:
            # Decodifica ignorando bytes inválidos
            linha = port.readline().decode("utf-8", errors="ignore").strip()

            if not linha:
                return None

            # Filtra somente caracteres válidos para um número
            linha_filtrada = "".join(c for c in linha if c.isdigit() or c in ".-")

            if not linha_filtrada:
                if not silent:
                    print(f"Dado inválido recebido (lixo ignorado): {linha!r}")
                return None

            try:
                temperatura_atual = float(linha_filtrada)
                if not silent:
                    print(f"Temperatura atual: {temperatura_atual}°C")
                return temperatura_atual
            except ValueError:
                if not silent:
                    print(f"Dado não numérico recebido: {linha!r}")
                return None

    except serial.SerialException as e:
        print(f"Erro na comunicação serial: {e}")

    return None

def saveData(teste):
    with open("ComunicESP/algo.txt",'a') as f:
        for i in teste:
            f.write(f'{i}\n')
        f.write("Fim do teste\n")
