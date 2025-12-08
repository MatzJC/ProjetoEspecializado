# Interface.py
import sys
import time
import serial.tools.list_ports
import pyqtgraph as pg

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QLabel, QHBoxLayout, QMessageBox, QComboBox, QGridLayout
)
from PyQt6.QtCore import QTimer, Qt

# Importe o Worker e seus Sinais
from Worker import SerialWorker, WorkerSignals

class Interface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Temperatura - ESP32")
        self.setGeometry(200, 200, 1000, 700)

        # =====================
        #  ESTILO QSS
        # =====================
        self.qss = """
        QWidget {
            background-color: #2B2B2B;
            color: #F0F0F0;
            font-family: Arial, sans-serif;
            font-size: 11pt;
        }
        QLabel {
            background-color: transparent;
        }
        QLineEdit, QComboBox {
            background-color: #3C3C3C;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 8px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #0078D7;
            background-color: #454545;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QPushButton {
            background-color: #0078D7;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #005A9E;
        }
        QPushButton:pressed {
            background-color: #004C82;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #999;
        }
        #connectButton {
            background-color: #28A745; /* Verde */
        }
        #connectButton:hover {
            background-color: #218838;
        }
        #stopButton {
            background-color: #DC3545; /* Vermelho */
        }
        #stopButton:hover {
            background-color: #C82333;
        }
        #updateButton {
            background-color: #FFC107; /* Laranja/Amarelo */
            color: #212529;
        }
        #updateButton:hover {
            background-color: #E0A800;
        }
        #refreshButton {
            background-color: #17A2B8; /* Azul Info */
        }
        #refreshButton:hover {
            background-color: #138496;
        }
        PlotWidget {
            border-radius: 5px;
            border: 1px solid #444;
        }
        """
        # Aplicando o estilo
        self.setStyleSheet(self.qss)


        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15) 
        main_layout.setContentsMargins(15, 15, 15, 15)
        # =====================
        #  SEÇÃO DE ENTRADAS (LAYOUT MELHORADO)
        # =====================
        # Trocado para QGridLayout para melhor alinhamento
        input_layout = QGridLayout()
        input_layout.setSpacing(10)

        self.ref_label = QLabel("Temperatura de Referência (°C):")
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Ex: 50.5") # Ajuda o usuário

        self.time_label = QLabel("Tempo de Assentamento (s):")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("Ex: 300") # Ajuda o usuário

        # Adiciona os widgets ao grid
        input_layout.addWidget(self.ref_label, 0, 0)
        input_layout.addWidget(self.ref_input, 0, 1)
        input_layout.addWidget(self.time_label, 1, 0)
        input_layout.addWidget(self.time_input, 1, 1)

        main_layout.addLayout(input_layout)

        # =====================
        #  SEÇÃO DE PORTAS (LAYOUT MELHORADO)
        # =====================
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Porta serial:"))
        self.port_select = QComboBox()
        self.refresh_ports()
        # Adiciona stretch factor '1' para o ComboBox preencher o espaço
        port_layout.addWidget(self.port_select, 1) 

        self.refresh_button = QPushButton("Atualizar Portas")
        # ADICIONADO setObjectName para o QSS funcionar
        self.refresh_button.setObjectName("refreshButton") 
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_button)

        main_layout.addLayout(port_layout)

        # =====================
        #  BOTÕES DE CONTROLE (CORRIGIDO)
        # =====================
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Iniciar Teste")
        self.connect_button.setObjectName("connectButton") # ADICIONADO
        self.connect_button.clicked.connect(self.start_worker)
        
        self.stop_button = QPushButton("Encerrar Teste")
        self.stop_button.setObjectName("stopButton") # ADICIONADO
        self.stop_button.clicked.connect(self.stop_worker)
        self.stop_button.setEnabled(False)
        
        self.update_button = QPushButton("Atualizar Parâmetros")
        self.update_button.setObjectName("updateButton") # ADICIONADO
        self.update_button.clicked.connect(self.update_parameters)
        self.update_button.setEnabled(False) # ADICIONADO (começa desabilitado)

        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.stop_button)
        # CORREÇÃO: Adicionando o botão que faltava ao layout
        button_layout.addWidget(self.update_button) 

        main_layout.addLayout(button_layout)

        # =====================
        #  VISUALIZAÇÃO DE STATUS
        # =====================
        status_layout = QGridLayout()
        status_layout.setVerticalSpacing(15)
        font_big = self.font()
        font_big.setPointSize(16)
        font_big.setBold(True)

        self.label_ref = QLabel("Ref: -- °C")
        self.label_current = QLabel("Atual: -- °C")
        self.label_error = QLabel("Erro: -- °C")
        self.label_time = QLabel("Tempo: 0.0 s")

        for lbl in [self.label_ref, self.label_current, self.label_error, self.label_time]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(font_big)
            # Adiciona cor branca para destacar no fundo escuro
            lbl.setStyleSheet("color: #FFFFFF; background-color: transparent;")

        status_layout.addWidget(self.label_ref, 0, 0)
        status_layout.addWidget(self.label_current, 0, 1)
        status_layout.addWidget(self.label_error, 1, 0)
        status_layout.addWidget(self.label_time, 1, 1)

        main_layout.addLayout(status_layout)

        # =====================
        #  GRÁFICO
        # =====================
        self.graph = pg.PlotWidget()
        self.graph.setBackground('w') # Fundo branco para o gráfico
        self.graph.setLabel('left', 'Temperatura (°C)')
        self.graph.setLabel('bottom', 'Tempo (s)')
        self.graph.showGrid(x=True, y=True, alpha=0.3) # Adiciona grade
        self.curve = self.graph.plot(pen=pg.mkPen('r', width=2))
        main_layout.addWidget(self.graph)

        # =====================
        #  VARIÁVEIS DE ESTADO
        # =====================
        self.temps = []
        self.time_data = []
        self.start_time = None
        self.referencia = None
        self.test_running = False
        self.worker = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(500)

        self.setLayout(main_layout)

    # -------------------------
    # MÉTODOS DE CONTROLE
    # -------------------------
    def refresh_ports(self):
        """Atualiza lista de portas COM disponíveis"""
        self.port_select.clear()
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_select.addItem("Nenhuma porta encontrada")
        else:
            for port in ports:
                self.port_select.addItem(port.device)

    def start_worker(self):
        """Inicia o teste e a thread de comunicação"""
        try:
            port = self.port_select.currentText()
            if port == "Nenhuma porta encontrada":
                raise Exception("Nenhuma porta serial selecionada.")
                
            self.referencia = float(self.ref_input.text())
            tempo = float(self.time_input.text())
            baudrate = 115200

            # Limpa dados do gráfico anterior
            self.temps = []
            self.time_data = []
            self.curve.setData(self.time_data, self.temps)

            # 1. Crie o worker (sem callback)
            self.worker = SerialWorker(port, baudrate, self.referencia, tempo)
            
            # 2. Conecte os sinais aos slots
            self.worker.signals.data_received.connect(self.handle_data_received)
            self.worker.signals.error.connect(self.handle_worker_error)
            self.worker.signals.finished.connect(self.handle_worker_finished)
            
            self.worker.start()

            # Atualiza UI
            self.label_ref.setText(f"Ref: {self.referencia:.2f} °C")
            self.label_current.setText("Atual: -- °C")
            self.label_error.setText("Erro: -- °C")
            self.label_time.setText("Tempo: 0.0 s")
            
            self.test_running = True
            
            # self.start_time será definido no primeiro dado recebido
            self.start_time = None 

            self.connect_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.update_button.setEnabled(True)

            # Desabilita controles de setup
            self.ref_input.setEnabled(False)
            self.time_input.setEnabled(True) 
            self.port_select.setEnabled(False)
            self.refresh_button.setEnabled(False)

            QMessageBox.information(self, "Conexão", f"Conectado à {port}")

        except ValueError:
            QMessageBox.warning(self, "Erro", "Insira valores válidos para referência e tempo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            if self.worker:
                self.worker = None

    def update_parameters(self):
        try:
            nova_ref = float(self.ref_input.text())
            novo_tempo = float(self.time_input.text())
            if self.worker and self.worker.is_alive():
                self.worker.update_parameters(nova_ref, novo_tempo)
                
                # Atualiza a referência local na GUI também
                self.referencia = nova_ref
                self.label_ref.setText(f"Ref: {self.referencia:.2f} °C")
                QMessageBox.information(self, "Atualizado", "Parâmetros enviados.")
                
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores inválidos")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível atualizar: {e}")

    def stop_worker(self):
        if self.worker:
            self.worker.stop()

            
        self.test_running = False
        self.connect_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_button.setEnabled(False)

        # Reabilita controles de setup
        self.ref_input.setEnabled(True)
        self.time_input.setEnabled(True)
        self.port_select.setEnabled(True)
        self.refresh_button.setEnabled(True)
        
        print("Teste encerrado pelo usuário.")
        # QMessageBox.information(self, "Encerrado", "Teste finalizado com sucesso.")

    # ------------------------------------------------------------------
    # NOVOS SLOTS PARA COMUNICAÇÃO SEGURA COM A THREAD
    # ------------------------------------------------------------------

    def handle_data_received(self, temperatura):
        if not self.test_running:
            return

        # Primeiro dado: define o tempo inicial
        if self.start_time is None:
            self.start_time = time.time()

        t = time.time() - self.start_time
        erro = self.referencia - temperatura

        self.time_data.append(t)
        self.temps.append(temperatura)

        # Atualiza labels (AGORA É SEGURO!)
        self.label_current.setText(f"Atual: {temperatura:.2f} °C")
        self.label_error.setText(f"Erro: {erro:.2f} °C")
        self.label_time.setText(f"Tempo: {t:.1f} s")

        # Se atingiu a referência, para o cronômetro automaticamente
        if abs(erro) <= 0.5:  
            if self.test_running: 
                print("Atingiu a referência, parando automaticamente.")
                self.test_running = False 
                
                final_time = t 
                
                QTimer.singleShot(0, self.stop_worker)
                QTimer.singleShot(100, lambda: QMessageBox.information(
                    self,
                    "Estabilizado",
                    f"Referência alcançada em {final_time:.1f} segundos!"
                ))
                
    def handle_worker_error(self, error_message):
        QMessageBox.critical(self, "Erro na Thread", f"A comunicação foi interrompida: {error_message}")
        #if self.test_running:
        #    self.stop_worker() # Para a UI

    def handle_worker_finished(self):
        print("Thread do worker finalizada.")
        if self.test_running:
            self.stop_worker()
        self.worker = None 

    # ------------------------------------------------------------------
    # MÉTODOS RESTANTES (sem alteração)
    # ------------------------------------------------------------------

    def update_plot(self):
        """Atualiza o gráfico periodicamente"""
        if self.time_data and self.temps:
            self.curve.setData(self.time_data, self.temps)

    def closeEvent(self, event):
        """Intercepta fechamento da janela"""
        if self.test_running:
            reply = QMessageBox.question(
                self,
                "Encerrar teste",
                "Um teste está em andamento. Deseja encerrá-lo e sair?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
        else:
            reply = QMessageBox.StandardButton.Yes

        if reply == QMessageBox.StandardButton.Yes:
            if self.worker:
                self.worker.stop()
                # Não precisa de .join() aqui, apenas sinalize para parar.
            event.accept()
        else:
            event.ignore()


def launch():
    app = QApplication(sys.argv)
    window = Interface()
    window.show()
    sys.exit(app.exec())
