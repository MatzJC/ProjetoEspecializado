
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QLabel, QHBoxLayout, QMessageBox, QComboBox
)
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
import serial.tools.list_ports
from Worker import SerialWorker


class Interface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Temperatura - ESP32")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        # --- Entradas de parâmetros ---
        input_layout = QHBoxLayout()

        self.ref_label = QLabel("Temperatura de Referência (°C):")
        self.ref_input = QLineEdit()
        self.time_label = QLabel("Tempo de Assentamento (s):")
        self.time_input = QLineEdit()

        input_layout.addWidget(self.ref_label)
        input_layout.addWidget(self.ref_input)
        input_layout.addWidget(self.time_label)
        input_layout.addWidget(self.time_input)

        layout.addLayout(input_layout)

        # --- Escolha da porta serial ---
        port_layout = QHBoxLayout()
        self.port_label = QLabel("Porta Serial:")
        self.port_select = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_select)

        layout.addLayout(port_layout)

        # --- Botão de conectar ---
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.start_worker)
        layout.addWidget(self.connect_button)

        # --- Gráfico ---
        self.graph = pg.PlotWidget()
        self.graph.setBackground('w')
        self.graph.setLabel('left', 'Temperatura (°C)')
        self.graph.setLabel('bottom', 'Tempo (s)')
        self.curve = self.graph.plot(pen=pg.mkPen('r', width=2))
        layout.addWidget(self.graph)

        # --- Dados ---
        self.temps = []
        self.time_data = []
        self.t0 = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(500)

        self.worker = None
        self.setLayout(layout)

    def refresh_ports(self):
        self.port_select.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_select.addItem(port.device)

    def start_worker(self):
        try:
            port = self.port_select.currentText()
            referencia = float(self.ref_input.text())
            tempo = float(self.time_input.text())
            baudrate = 115200

            self.worker = SerialWorker(port, baudrate, referencia, tempo, self.data_callback)
            self.worker.start()

            QMessageBox.information(self, "Conexão", f"Conectado à {port}")
        except ValueError:
            QMessageBox.warning(self, "Erro", "Insira valores válidos para referência e tempo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def data_callback(self, temperatura):
        """Recebe dados da thread serial e atualiza o gráfico."""
        if len(self.time_data) == 0:
            self.t0 = pg.ptime.time()

        t = pg.ptime.time() - self.t0
        self.time_data.append(t)
        self.temps.append(temperatura)

        # Limita tamanho da lista
        if len(self.time_data) > 500:
            self.time_data = self.time_data[-500:]
            self.temps = self.temps[-500:]

    def update_plot(self):
        if self.time_data and self.temps:
            self.curve.setData(self.time_data, self.temps)

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.join()
        event.accept()


def launch():
    app = QApplication(sys.argv)
    window = Interface()
    window.show()
    sys.exit(app.exec())





