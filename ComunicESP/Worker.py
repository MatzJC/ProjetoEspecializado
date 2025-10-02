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
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries and not self._stop_event.is_set():
            try:
                self.ser = fn.conectarESP32(self.porta, self.baudrate)
                print("Thread de comunicação iniciada com sucesso.")
                break  # Sai do retry se conectou
            except RuntimeError as e:
                retry_count += 1
                print(f"Tentativa {retry_count} falhou: {e}. Tentando novamente em 2s...")
                time.sleep(2)
                if retry_count >= max_retries:
                    print("Falha após múltiplas tentativas. Thread encerrada.")
                    return

        if self.ser is None:
            return  # Não conseguiu conectar

        try:
            while not self._stop_event.is_set():
                fn.enviaDados(self.referencia, self.ser, self.tempo)
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

