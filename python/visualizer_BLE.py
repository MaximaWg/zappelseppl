# Import notwendiger Bibliotheken
import sys
import asyncio
import threading
import csv
import time
from datetime import datetime
from collections import deque

# Matplotlib und Farbcodierung
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

# PyQt5 GUI und pyqtgraph für schnelle Plots
from PyQt5 import QtGui
from PyQt5 import QtGui
from PyQt5 import QtCore
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph as pg

# 3D Visualisierung (Beschleunigungsvektor)
from vpython import vector, arrow, rate, cross, label

# BLE-Kommunikation
from bleak import BleakScanner, BleakClient

# BLE-Geräteinfos
CHAR_UUID = "2A56" # UUID der BLE-Charakteristik
TARGET_NAME = "RP2040_Sensor" # Gesuchter Gerätename

# CSV-Datei vorbereiten
filename = datetime.now().strftime("%Y-%m-%d_%H-%M") + "_daten.csv"
csv_file = open(filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "ax", "ay", "az", "r1", "r2", "r3"])

# VPython: 3D-Pfeil für Beschleunigung
accel_arrow = arrow(pos=vector(0, 0, 0), axis=vector(0, 0, 0), shaftwidth=0.05, color=vector(0.2, 0.6, 1))
accel_label = label(pos=vector(0, 0.4, 0), text="Acceleration", height=16, border=4,
                    box=False, color=vector(0.2, 0.6, 1))

# Rotationskalibrierung
rotation_axis = vector(1, 0, 0)
rotation_angle = 0
calibrated = False

# Matplotlib: Heatmap-Setup
sensor_positions = {'Ferse': (0.5, 0.25), 'MT1': (0.38, 1.0), 'MT5': (0.62, 1.0)}
sensor_circles = {}
fig, heat_ax = plt.subplots(figsize=(4, 8))
canvas = FigureCanvas(fig)

# Farbverlauf für Heatmap
color_gradient = LinearSegmentedColormap.from_list("custom_redscale",
    ["lightgray", "yellow", "orange", "red", "darkred"])

def norm_force(r_ohm):
    # Normierte Kraftberechnung
    if r_ohm <= 0 or np.isnan(r_ohm): return 0.0
    return np.clip(8000 / r_ohm, 0.0, 1.0)

def force_color(norm_val):
    # Gibt passende Farbe zur normierten Kraft
    return color_gradient(norm_val)

def draw_foot_shape():
    # Fußumriss definieren
    outline = [(0.40, 0.00), (0.35, 0.10), (0.30, 0.25), (0.25, 0.45),
               (0.20, 0.70), (0.18, 0.95), (0.20, 1.20), (0.28, 1.35),
               (0.35, 1.45), (0.43, 1.50), (0.50, 1.52), (0.57, 1.50),
               (0.65, 1.45), (0.72, 1.35), (0.80, 1.20), (0.82, 0.95),
               (0.80, 0.70), (0.75, 0.45), (0.70, 0.25), (0.65, 0.10),
               (0.60, 0.00), (0.40, 0.00)]
    poly = patches.Polygon(outline, closed=True, color='lightgray', zorder=0)
    heat_ax.add_patch(poly)

# Heatmap vorbereiten
def setup_heatmap():
    heat_ax.clear()
    draw_foot_shape()
    for name, (x, y) in sensor_positions.items():
        circle = plt.Circle((x, y), 0.08, facecolor='lightgray',
                            edgecolor='black', linewidth=1.5, zorder=3)
        sensor_circles[name] = circle
        heat_ax.add_patch(circle)
    heat_ax.set_xlim(0, 1)
    heat_ax.set_ylim(0, 1.6)
    heat_ax.set_aspect('equal')
    heat_ax.axis('off')
    heat_ax.set_title("FSR Shoe Insoles", fontsize=14)

    # Farbskala
    norm = Normalize(vmin=0.0, vmax=1.0)
    sm = ScalarMappable(norm=norm, cmap=color_gradient)
    sm.set_array([])  # Dummy-Daten
    cbar = fig.colorbar(sm, ax=heat_ax, fraction=0.046, pad=0.04)
    cbar.set_label("Normalized Resistance", fontsize=12)

setup_heatmap()
fig.tight_layout()
canvas.draw()

# PyQt GUI Setup
app = QtWidgets.QApplication(sys.argv)
main_win = QtWidgets.QMainWindow()
central_widget = QtWidgets.QWidget()
layout = QtWidgets.QGridLayout()
central_widget.setLayout(layout)
main_win.setCentralWidget(central_widget)
main_win.setWindowTitle("Live ACC, FSR + Fußsohle (BLE)")
main_win.resize(1000, 600)

# Beschleunigungsgraph
acc_plot = pg.PlotWidget(title="Accelerometer (m/s²)")
acc_plot.setBackground('w')
acc_plot.setYRange(-20, 20)
acc_plot.setLabel('left', 'Acceleration (m/s²)', **{'color': 'k', 'font-size': '14pt'})
acc_plot.setLabel('bottom', 'Time (s)', **{'color': 'k', 'font-size': '14pt'})
acc_plot.setTitle("Accelerometer (m/s²)", color='k', size='16pt')
tick_font = QtGui.QFont()
tick_font.setPointSize(12)
acc_plot.getAxis('left').setTextPen('k')
acc_plot.getAxis('bottom').setTextPen('k')
acc_plot.getAxis('left').setStyle(tickFont=tick_font)
acc_plot.getAxis('bottom').setStyle(tickFont=tick_font)

acc_plot.addLegend(labelTextSize='12pt')
acc_x = acc_plot.plot(pen=pg.mkPen(color=(0, 0, 150), width=3), name='Ax')
acc_y = acc_plot.plot(pen=pg.mkPen(color=(230, 159, 0), width=3), name='Ay')
acc_z = acc_plot.plot(pen=pg.mkPen(color=(86, 180, 233), width=3), name='Az')
layout.addWidget(acc_plot, 0, 0)

# FSR-Graph
fsr_plot = pg.PlotWidget(title="FSR")
fsr_plot.setBackground('w')
fsr_plot.setYRange(0, 1.1)
fsr_plot.setLabel('left', 'Normalized Resistance', **{'color': 'k', 'font-size': '14pt'})
fsr_plot.setLabel('bottom', 'Time (s)', **{'color': 'k', 'font-size': '14pt'})
fsr_plot.setTitle("FSR", color='k', size='16pt')
fsr_plot.getAxis('left').setTextPen('k')
fsr_plot.getAxis('bottom').setTextPen('k')
fsr_plot.getAxis('left').setStyle(tickFont=tick_font)
fsr_plot.getAxis('bottom').setStyle(tickFont=tick_font)

fsr_plot.addLegend(labelTextSize='12pt')
fsr_1 = fsr_plot.plot(pen=pg.mkPen(color=(204, 121, 167), width=3), name='Ferse')
fsr_2 = fsr_plot.plot(pen=pg.mkPen(color=(0, 158, 115), width=3), name='MT1')
fsr_3 = fsr_plot.plot(pen=pg.mkPen(color=(50, 50, 50), width=3), name='MT5')
layout.addWidget(fsr_plot, 1, 0)

# Heatmap einfügen
layout.addWidget(canvas, 0, 1, 2, 2)

# Datenpuffer vorbereiten
buffer_size = 300
acc_buffer = [deque([0]*buffer_size, maxlen=buffer_size) for _ in range(3)]
fsr_buffer = [deque([0]*buffer_size, maxlen=buffer_size) for _ in range(3)]
x_vals = deque(np.linspace(-buffer_size/10, 0, buffer_size), maxlen=buffer_size)

# BLE-Daten verarbeiten
def process_ble_data(data_str):
    global rotation_angle, rotation_axis, calibrated
    parts = data_str.strip().split('\t')
    if len(parts) != 6:
        return
    try:
        ax, ay, az = map(float, parts[0:3])
        r1, r2, r3 = map(float, parts[3:6])
    except:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    csv_writer.writerow([timestamp, ax, ay, az, r1, r2, r3])
    csv_file.flush()

    # Beschleunigungsvektor rotieren
    raw_vec = vector(ax, ay, az)
    if not calibrated:
        initial_vector = raw_vec.norm()
        target_vector = vector(0, 1, 0)
        rotation_axis = cross(initial_vector, target_vector)
        if rotation_axis.mag < 1e-6:
            rotation_axis = vector(1, 0, 0)
        rotation_angle = initial_vector.diff_angle(target_vector)
        calibrated = True
    rotated_vec = raw_vec.rotate(angle=rotation_angle, axis=rotation_axis)
    accel_arrow.axis = rotated_vec * 0.2

    # Heatmap einfärben
    fsr_data = {'Ferse': r1, 'MT1': r2, 'MT5': r3}
    for name, r_val in fsr_data.items():
        sensor_circles[name].set_facecolor(force_color(norm_force(r_val)))
    canvas.draw()

    # Graph aktualisieren
    for i, val in enumerate([ax, ay, az]):
        acc_buffer[i].append(val)
    for i, val in enumerate([r1, r2, r3]):
        fsr_buffer[i].append(norm_force(val))
    x_vals.append(x_vals[-1] + 0.1)

    acc_x.setData(x_vals, acc_buffer[0])
    acc_y.setData(x_vals, acc_buffer[1])
    acc_z.setData(x_vals, acc_buffer[2])
    fsr_1.setData(x_vals, fsr_buffer[0])
    fsr_2.setData(x_vals, fsr_buffer[1])
    fsr_3.setData(x_vals, fsr_buffer[2])

    QtWidgets.QApplication.processEvents()

# BLE-Verbindung aufbauen
async def main_ble():
    print("Suche nach BLE-Geräten...")
    devices = await BleakScanner.discover()
    addr = next((d.address for d in devices if TARGET_NAME in (d.name or "")), None)
    if not addr:
        print("Zielgerät nicht gefunden.")
        return
    print(f"Verbinde mit {addr}...")
    async with BleakClient(addr) as client:
        print("Verbunden, Kalibrierung läuft, bitte ruhig halten.")
        def callback(_, data):
            process_ble_data(data.decode('utf-8'))
        await client.start_notify(CHAR_UUID, callback)
        while True:
            await asyncio.sleep(0.01)

# BLE-Thread starten
def start_ble_thread():
    asyncio.run(main_ble())

threading.Thread(target=start_ble_thread, daemon=True).start()

# GUI starten
main_win.show()
sys.exit(app.exec_())
