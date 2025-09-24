import time
import Functions as fn
from Worker import SerialWorker

porta_serial = 'COM3'  
baudrate = 115200      # ESP32 agora roda estável em 115200

#referencia = 5.0  # °C desejada(trocar para o valor ser fornecido pelo usuário)

referencia = fn.obterReferencia()

try:
    ser = fn.conectarESP32(porta_serial, baudrate)
except RuntimeError as e:
    print(e)
    exit(1)

# Inicia a thread de comunicação
worker = SerialWorker(porta_serial, baudrate, referencia)
worker.start()

try:
    while True:
            time.sleep(1)
except KeyboardInterrupt:
    print("Interrupção pelo usuário. Encerrando...")
    worker.stop()
    worker.join()
    print("Thread finalizada.")

