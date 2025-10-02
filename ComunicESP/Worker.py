import threading
import time
import Functions as fn

class SerialWorker(threading.Thread):
    def __init__(self, porta, baudrate, referencia, tempo):
        super().__init__()
        self.porta = porta
        self.baudrate = baudrate
        self.referencia = referencia
        self.tempo = tempo
        self._stop_event = threading.Event()
        self.ser = None

    def run(self):
        try:
            self.ser = fn.conectarESP32(self.porta, self.baudrate)
        except RuntimeError as e:
            print(e)
            return

        print("Thread de comunicação iniciada.")
        try:
            while not self._stop_event.is_set():
                fn.enviaDados(self.referencia, self.ser,self.tempo)
                fn.recebeDados(self.referencia, self.ser)
                time.sleep(0.5)
        except Exception as e:
            print(f"Erro na thread de comunicação: {e}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("Porta serial fechada (thread).")

    def stop(self):
        self._stop_event.set()