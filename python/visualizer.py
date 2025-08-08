# Standard libraries for data handling and time management
import sys
import time
import serial
import numpy as np
from collections import deque
import csv
from datetime import datetime

# PyQt and visualization libraries
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph as pg

# For embedding Matplotlib plotting into the PyQt GUI
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap

# 3D vector visualization with VPython
from vpython import vector, arrow, rate, cross, label

# Serial connection
PORT = 'COM7'
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # Wait until the serial connection is stable

# 3D arrow for displaying acceleration
accel_arrow = arrow(pos=vector(0, 0, 0), axis=vector(0, 0, 0),
                    shaftwidth=0.05, color=vector(0.2, 0.6, 1))

# Label for the acceleration arrow
accel_label = label(
    pos=vector(0, 0.4, 0), text="Acceleration",
    xoffset=0, yoffset=0, space=30,
    height=16, border=4, font='sans',
    box=False, color=vector(0.2, 0.6, 1)
)

# Foot sole view as heatmap
sensor_positions = {'Heel': (0.5, 0.25),
                    'MT1': (0.38, 1.0),
                    'MT5': (0.62, 1.0)}
sensor_circles = {}

# Matplotlib canvas for foot sole visualization
fig, heat_ax = plt.subplots(figsize=(4, 8))
canvas = FigureCanvas(fig)

# Draw foot shape
def draw_foot_shape():
    outline = [
        (0.40, 0.00), (0.35, 0.10), (0.30, 0.25), (0.25, 0.45),
        (0.20, 0.70), (0.18, 0.95), (0.20, 1.20), (0.28, 1.35),
        (0.35, 1.45), (0.43, 1.50), (0.50, 1.52), (0.57, 1.50),
        (0.65, 1.45), (0.72, 1.35), (0.80, 1.20), (0.82, 0.95),
        (0.80, 0.70), (0.75, 0.45), (0.70, 0.25), (0.65, 0.10),
        (0.60, 0.00), (0.40, 0.00)
    ]  # Coordinates of the foot contour
    poly = patches.Polygon(outline, closed=True, color='lightgray', zorder=0)
    heat_ax.add_patch(poly)

# Prepare sensor circles and display
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
    heat_ax.set_title("FSR Shoe Sole", fontsize=14)
    canvas.draw()

setup_heatmap()

# Prepare CSV file for logging
date_string = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = date_string + "_data.csv"
csv_file = open(filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "ax", "ay", "az", "r1", "r2", "r3"])  # Header

# Color map for the heatmap
color_gradient = LinearSegmentedColormap.from_list(
    "custom_redscale", ["lightgray", "yellow", "orange", "red", "darkred"]
)

# Normalize FSR resistance to [0, 1]
def norm_force(r_ohm):
    if r_ohm <= 0 or np.isnan(r_ohm): return 0.0
    return np.clip(8000 / r_ohm, 0.0, 1.0)

# Convert normalized value to color
def force_color(norm_val):
    return color_gradient(norm_val)

# Accelerometer calibration
print("Calibrating accelerometer. Please hold still.")
samples = 100
sum_ax = sum_ay = sum_az = 0
valid = 0
while valid < samples:
    line = ser.readline().decode('utf-8').strip()
    try:
        parts = list(map(float, line.split('\t')))
        if len(parts) < 6: continue
        ax_val, ay_val, az_val = parts[0], parts[1], parts[2]
    except: continue
    sum_ax += ax_val
    sum_ay += ay_val
    sum_az += az_val
    valid += 1

# Determine rotation
initial_vector = vector(sum_ax, sum_ay, sum_az).norm()
target_vector = vector(0, 1, 0)
rotation_axis = cross(initial_vector, target_vector)
if rotation_axis.mag < 1e-6: rotation_axis = vector(1, 0, 0)
rotation_angle = initial_vector.diff_angle(target_vector)

# Initialize PyQt window and layout
app = QtWidgets.QApplication(sys.argv)
main_win = QtWidgets.QMainWindow()
central_widget = QtWidgets.QWidget()
layout = QtWidgets.QGridLayout()
central_widget.setLayout(layout)
main_win.setCentralWidget(central_widget)
main_win.setWindowTitle("Live ACC, FSR + Foot Sole")
main_win.resize(1000, 600)

# Accelerometer plot
acc_plot = pg.PlotWidget(title="Accelerometer (m/s²)")
acc_plot.setBackground('w')
acc_plot.setYRange(-20, 20)
acc_plot.setLabel('left', 'Acceleration (m/s²)')
acc_plot.setLabel('bottom', 'Time (s)')
acc_plot.addLegend()

acc_x = acc_plot.plot(pen='r', name='Ax')
acc_y = acc_plot.plot(pen='g', name='Ay')
acc_z = acc_plot.plot(pen='b', name='Az')

layout.addWidget(acc_plot, 0, 0)

# FSR plot
fsr_plot = pg.PlotWidget(title="FSR Force")
fsr_plot.setBackground('w')
fsr_plot.setYRange(0, 1.1)
fsr_plot.setLabel('left', 'Normalized Force')
fsr_plot.setLabel('bottom', 'Time (s)')
fsr_plot.addLegend()

fsr_1 = fsr_plot.plot(pen='m', name='Heel')
fsr_2 = fsr_plot.plot(pen='c', name='MT1')
fsr_3 = fsr_plot.plot(pen='y', name='MT5')
layout.addWidget(fsr_plot, 1, 0)

# Add matplotlib heatmap to the right
layout.addWidget(canvas, 0, 1, 2, 1)

# Data buffers for live data (sliding window)
buffer_size = 300
acc_buffer = [deque([0]*buffer_size, maxlen=buffer_size) for _ in range(3)]
fsr_buffer = [deque([0]*buffer_size, maxlen=buffer_size) for _ in range(3)]

# Update function for visualization and logging
def update():
    rate(30)
    line = ser.readline().decode('utf-8').strip()
    try:
        parts = list(map(float, line.split('\t')))
        if len(parts) != 6: return
        ax, ay, az = parts[0:3]
        r1, r2, r3 = parts[3:6]
    except: return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    csv_writer.writerow([timestamp, ax, ay, az, r1, r2, r3])
    csv_file.flush()

    # 3D arrow for acceleration
    raw_vec = vector(ax, ay, az)
    rotated_vec = raw_vec.rotate(angle=rotation_angle, axis=rotation_axis)
    accel_arrow.axis = rotated_vec * 0.2

    # Update heatmap colors
    fsr_data = {'Heel': r1, 'MT1': r2, 'MT5': r3}
    for name, r_val in fsr_data.items():
        norm = norm_force(r_val)
        sensor_circles[name].set_facecolor(force_color(norm))
    canvas.draw()

    # Update plots
    for i, val in enumerate([ax, ay, az]):
        acc_buffer[i].append(val)
    for i, val in enumerate([r1, r2, r3]):
        fsr_buffer[i].append(norm_force(val))

    acc_x.setData(list(acc_buffer[0]))
    acc_y.setData(list(acc_buffer[1]))
    acc_z.setData(list(acc_buffer[2]))
    fsr_1.setData(list(fsr_buffer[0]))
    fsr_2.setData(list(fsr_buffer[1]))
    fsr_3.setData(list(fsr_buffer[2]))

    QtWidgets.QApplication.processEvents()

# Start timer and show window
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)

main_win.show()
try:
    main_win.show()
    sys.exit(app.exec_())
finally:
    csv_file.close()

sys.exit(app.exec_())
