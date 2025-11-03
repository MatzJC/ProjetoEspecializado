import time
import Functions as fn
from Worker import SerialWorker
import serial.tools.list_ports 

if __name__ == "__main__":
    # Lista portas disponíveis para debug (rode isso para confirmar COM3)
    print("Portas COM disponíveis:")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"  {port.device} - {port.description}")
    
    porta_serial = 'COM3'
    baudrate = 115200

    # NÃO abra conexão aqui! Deixe para a thread.
    # Mas verifique se a porta existe (opcional)
    if porta_serial not in [p.device for p in ports]:
        print(f"Porta {porta_serial} não encontrada! Verifique o Gerenciador de Dispositivos.")
        exit(1)

    # Inicia a thread de comunicação
    worker = SerialWorker(porta_serial, baudrate, 0, 0)
    worker.start()

    try:
        while True:
            time.sleep(1)  # Aqui você pode adicionar logs ou UI no futuro
    except KeyboardInterrupt:
        print("Interrupção pelo usuário. Encerrando...")
        worker.stop()
        worker.join()
        print("Thread finalizada.")