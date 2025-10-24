import sys
import time
import serial.tools.list_ports
import pyqtgraph as pg

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QLabel, QHBoxLayout, QMessageBox, QComboBox, QGridLayout
)
from PyQt6.QtCore import QTimer, Qt

from Worker import SerialWorker


class Interface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Temperatura - ESP32")
        self.setGeometry(200, 200, 1000, 700)

        # Layout principal
        main_layout = QVBoxLayout()

        # =====================
        #  SEÇÃO DE ENTRADAS
        # =====================
        input_layout = QHBoxLayout()

        self.ref_label = QLabel("Temperatura de Referência (°C):")
        self.ref_input = QLineEdit()
        self.time_label = QLabel("Tempo de Assentamento (s):")
        self.time_input = QLineEdit()

        input_layout.addWidget(self.ref_label)
        input_layout.addWidget(self.ref_input)
        input_layout.addWidget(self.time_label)
        input_layout.addWidget(self.time_input)

        main_layout.addLayout(input_layout)

        # =====================
        #  SEÇÃO DE PORTAS
        # =====================
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Porta serial:"))
        self.port_select = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_select)

        self.refresh_button = QPushButton("Atualizar Portas")
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_button)

        main_layout.addLayout(port_layout)

        # =====================
        #  BOTÕES DE CONTROLE
        # =====================
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Iniciar Teste")
        self.connect_button.clicked.connect(self.start_worker)
        self.stop_button = QPushButton("Encerrar Teste")
        self.update_button = QPushButton("Atualizar Parâmetros")
        self.stop_button.clicked.connect(self.stop_worker)
        self.stop_button.setEnabled(False)

        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)

        # =====================
        #  VISUALIZAÇÃO DE STATUS
        # =====================
        status_layout = QGridLayout()
        status_layout.setVerticalSpacing(15)
        font_big = self.font()
        font_big.setPointSize(16)
        font_big.setBold(True)

        # Labels de status
        self.label_ref = QLabel("Ref: -- °C")
        self.label_current = QLabel("Atual: -- °C")
        self.label_error = QLabel("Erro: -- °C")
        self.label_time = QLabel("Tempo: 0.0 s")

        for lbl in [self.label_ref, self.label_current, self.label_error, self.label_time]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(font_big)

        status_layout.addWidget(self.label_ref, 0, 0)
        status_layout.addWidget(self.label_current, 0, 1)
        status_layout.addWidget(self.label_error, 1, 0)
        status_layout.addWidget(self.label_time, 1, 1)

        main_layout.addLayout(status_layout)

        # =====================
        #  GRÁFICO
        # =====================
        self.graph = pg.PlotWidget()
        self.graph.setBackground('w')
        self.graph.setLabel('left', 'Temperatura (°C)')
        self.graph.setLabel('bottom', 'Tempo (s)')
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

        # Timer de atualização do gráfico
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
        for port in ports:
            self.port_select.addItem(port.device)

    def start_worker(self):
        """Inicia o teste e a thread de comunicação"""
        try:
            port = self.port_select.currentText()
            self.referencia = float(self.ref_input.text())
            tempo = float(self.time_input.text())
            baudrate = 115200

            self.worker = SerialWorker(port, baudrate, self.referencia, tempo, self.data_callback)
            self.worker.start()

            # Atualiza UI
            self.label_ref.setText(f"Ref: {self.referencia:.2f} °C")
            self.label_current.setText("Atual: -- °C")
            self.label_error.setText("Erro: -- °C")
            self.label_time.setText("Tempo: 0.0 s")
            self.start_time = time.time()
            self.test_running = True

            self.connect_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            QMessageBox.information(self, "Conexão", f"Conectado à {port}")

        except ValueError:
            QMessageBox.warning(self, "Erro", "Insira valores válidos para referência e tempo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def update_parameters(self):
        try:
            nova_ref = float(self.ref_input.text())
            novo_tempo = float(self.time_input.text())
            if self.worker and self.worker.is_alive():
                self.worker.update_parameters(nova_ref, novo_tempo)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores inválidos")

    def stop_worker(self):
        """Para a thread de comunicação"""
        if self.worker:
            self.worker.stop()
            self.worker.join()
            self.worker = None

        self.test_running = False
        self.connect_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.information(self, "Encerrado", "Teste finalizado com sucesso.")

    def data_callback(self, temperatura):
        """Callback da thread serial - recebe temperatura e atualiza dados"""
        if not self.test_running:
            return

        # Primeiro dado
        if len(self.time_data) == 0:
            self.start_time = time.time()

        t = time.time() - self.start_time
        erro = self.referencia - temperatura

        self.time_data.append(t)
        self.temps.append(temperatura)

        # Atualiza labels
        self.label_current.setText(f"Atual: {temperatura:.2f} °C")
        self.label_error.setText(f"Erro: {erro:.2f} °C")
        self.label_time.setText(f"Tempo: {t:.1f} s")

        # Se atingiu a referência, para o cronômetro automaticamente
        if abs(erro) <= 0.5:  # margem de 0.5°C
            self.test_running = False
            self.stop_worker()
            QMessageBox.information(
                self,
                "Estabilizado",
                f"Temperatura de referência alcançada em {t:.1f} segundos!"
            )

    def update_plot(self):
        """Atualiza o gráfico periodicamente"""
        if self.time_data and self.temps:
            self.curve.setData(self.time_data, self.temps)

    def closeEvent(self, event):
        """Intercepta fechamento da janela"""
        reply = QMessageBox.question(
            self,
            "Encerrar teste",
            "Tem certeza que deseja encerrar o teste?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.worker:
                self.worker.stop()
                self.worker.join()
            event.accept()
        else:
            event.ignore()


def launch():
    app = QApplication(sys.argv)
    window = Interface()
    window.show()
    sys.exit(app.exec())
