
import threading
import time
import serial
import Functions as fn


class SerialWorker(threading.Thread):
    def __init__(self, porta, baudrate, referencia, tempo, callback=None):
        super().__init__()
        self.porta = porta
        self.baudrate = baudrate
        self.referencia = referencia
        self.tempo = tempo
        self.callback = callback  # Função da interface que receberá dados
        self._stop_event = threading.Event()
        self.ser = None

    def run(self):
        try:
            self.ser = fn.conectarESP32(self.porta, self.baudrate)
            print("Thread de comunicação iniciada com sucesso.")
        except RuntimeError as e:
            print(f"Erro ao conectar: {e}")
            return

        try:
            while not self._stop_event.is_set():
                fn.enviaDados(self.referencia, self.ser, self.tempo)
                temperatura = fn.recebeDados(self.referencia, self.ser, silent=True)
                if temperatura is not None and self.callback:
                    self.callback(temperatura)
                time.sleep(0.5)
        except Exception as e:
            print(f"Erro na thread de comunicação: {e}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("Porta serial fechada (thread).")

    def stop(self):
        self._stop_event.set()

    def update_parameters(self, nova_ref, novo_tempo):
        self.referencia = nova_ref
        self.tempo = novo_tempo