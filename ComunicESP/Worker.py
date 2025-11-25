import threading
import time
import serial
import Functions as fn
from PyQt6.QtCore import QObject, pyqtSignal

# 1. Agora usa sinais para comunicação com a GUI
class WorkerSignals(QObject):
    data_received = pyqtSignal(float)  # Sinal que carrega a temperatura (float)
    error = pyqtSignal(str)            # Sinal para enviar mensagens de erro (str)
    finished = pyqtSignal()            # Sinal emitido quando a thread termina


class SerialWorker(threading.Thread):
    # 2. Callback retirado e adicionado sinais
    def __init__(self, porta, baudrate, referencia, tempo):
        super().__init__()
        self.porta = porta
        self.baudrate = baudrate
        self.referencia = referencia
        self.tempo = tempo
        self._stop_event = threading.Event()
        self.ser = None
        self.signals = WorkerSignals()  # Instancie os sinais

    def run(self):
        try:
            self.ser = fn.conectarESP32(self.porta, self.baudrate)
            print("Thread de comunicação iniciada com sucesso.")
            
            # 3. Envie os dados UMA VEZ antes do loop
            print("Enviando parâmetros iniciais...")
            fn.enviaDados(self.referencia, self.ser, self.tempo)

        except RuntimeError as e:
            print(f"Erro ao conectar: {e}")
            self.signals.error.emit(str(e)) # Emite sinal de erro
            return
        except Exception as e:
            print(f"Erro inesperado ao conectar: {e}")
            self.signals.error.emit(str(e))
            return

        try:
            while not self._stop_event.is_set():
                # 4. enviaDados não é mais chamado dentro do loop
                
                temperatura = fn.recebeDados(self.referencia, self.ser, silent=True)
                
                if temperatura is not None:
                    # 5. Agora é emitido um sinal com a temperatura recebida
                    self.signals.data_received.emit(temperatura)
                
                time.sleep(0.2) 
                
        except Exception as e:
            print(f"Erro na thread de comunicação: {e}")
            self.signals.error.emit(str(e)) # Emite sinal de erro
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("Porta serial fechada (thread).")
            self.signals.finished.emit() # Emite sinal de finalizado

    def stop(self):
        self._stop_event.set()

    def update_parameters(self, nova_ref, novo_tempo):
        self.referencia = nova_ref
        self.tempo = novo_tempo
        # 6. Envie os dados atualizados aqui
        if self.ser and self.ser.is_open:
            print(f"Enviando parâmetros atualizados: Ref={nova_ref}, Tempo={novo_tempo}")
            fn.enviaDados(self.referencia, self.ser, self.tempo)
        else:
            print("A porta serial não está aberta. Parâmetros serão enviados na conexão.")