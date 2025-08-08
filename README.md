# ZappelSeppl
# Smart Insole: Stress Detection via Pressure and Motion
This repository contains the full code for the **ZappelSeppl** project – a smart insole system that detects stress indicators based on **pressure (FSR sensors)** and **motion (IMU)**. The data is visualized live via a Python GUI using either a **USB serial** or a **Bluetooth Low Energy (BLE)** connection, depending on the use case.

## Project Summary

- **Sensors:**  
  - 3 Force Sensitive Resistors (FSRs) at heel, MT1, and MT5.
  - LSM6DSOX IMU (accelerometer & gyroscope).
- **Microcontroller:**  
  - Arduino Nano RP2040 Connect
- **Transmission:**  
  - Via USB **or** BLE (Bluetooth Low Energy)
- **Visualization:**  
  - Real-time 3D vector + live plots (PyQt5 + pyqtgraph + vpython)
  - Force heatmap drawn over a stylized foot

## Repository Structure
```
zappelseppl/
├── arduino/
│   ├── 3fsr_and_IMU.ino         ← Arduino sketch for USB serial transmission
│   └── 3fsr_and_IMU_BLE.ino         ← Arduino sketch for BLE (Bluetooth Low Energy)
│
├── python/
│   ├── visualizer.py            ← Python GUI for USB-based data stream
│   └── visualizer_ble.py            ← Python GUI for BLE-based data stream
│
└── README.md                        ← This file
```

## Requirements

- Arduino Nano RP2040 Connect (or compatible BLE board)
- FSR sensors (x3)
- LSM6DSOX IMU (onboard)
- Python (Python 3.8) packages: `bleak` (for BLE only), `pyqtgraph`, `matplotlib`, `pandas`, `scipy`, `vpython`, `pyqt5`

## Arduino Sketches
Located in the **arduino/** folder:
- **3fsr_and_IMU.ino**
  - Transmits sensor data (acceleration and FSR resistance) via serial over USB.
  - Suitable for direct connection to a PC or Raspberry Pi using USB.
- **3fsr_und_IMU_BLE.ino**
  - Sends the same sensor data over Bluetooth Low Energy (BLE).
  - BLE characteristic UUID: 2A56, Service UUID: 180C
  - Advertises itself as RP2040_Sensor.

## Python Visualizations
Located in the **python/** folder:
- **visualizer_usb.py**
  - Connects to the microcontroller via a specified COM port (e.g., COM7).
  - Parses tab-separated sensor data via USB serial.
  - Shows:
      - 3D arrow for acceleration
      - Live plots (accelerometer & FSR)
      - Foot-shaped FSR heatmap
      - Saves data as CSV
- **visualizer_ble.py**
  - Scans and connects to the BLE device RP2040_Sensor.
  - Receives sensor data via BLE notifications.
  - Shows the same GUI components as visualizer_usb.py.

## Features
- Live Visualization:
  - Real-time accelerometer vectors using vpython
  - Real-time plots using pyqtgraph
  - Matplotlib-based FSR heatmap on a custom foot outline
- Data Recording:
  - Automatic CSV export with timestamp and sensor values
- Modular Setup:
  - Choose between USB and BLE mode depending on your experimental setup

## Getting Started

**1. Upload Arduino Sketch**
- Open the appropriate **.ino** file in the Arduino IDE and upload it to the Arduino Nano RP2040 Connect.
  - Use 3fsr_und_IMU.ino for serial mode.
  - Use 3fsr_und_IMU_BLE.ino for Bluetooth mode.
**2. Start Python Visualization**
- Install required dependencies.
- Then run the desired Python file.
  - Make sure the serial port or BLE device is available and not used by another application.

## Notes

- The insole supports real-time use and can be used in combination with stress experiments, motion tracking, or sports biomechanics.
- BLE transmission is limited to 60 bytes per message – data is encoded as a tab-separated string for this reason.

## Outlook

The system can be extended with improved hardware integration, more sensor inputs, and stress level classification features.

## License

This repository is part of a university project and not currently licensed for commercial use.

# Authors

Lena Sandig und Maxima Wiegels
