# ZappelSeppl
# Smart Insole: Stress Detection via Pressure and Motion
This project implements a smart insole system for detecting stress-related foot pressure and movement patterns using FSR sensors and an IMU.

## Software Components

- **Arduino (C++)**: Reads data from 3 FSR sensors and an IMU and transmits it via Bluetooth Low Energy (BLE).
- **Python (PyCharm)**: Receives BLE data, stores it as CSV, and visualizes it in real time using `pyqtgraph` and `matplotlib`.

## Files

- `3fsr_und_IMU_BLE.ino`: Arduino sketch for data acquisition and BLE transmission.
- `visualizer_BLE.py`: Python script for live data visualization and storage.

## Requirements

- Arduino Nano RP2040 Connect (or compatible BLE board)
- FSR sensors (x3)
- LSM6DSOX IMU (onboard)
- Python packages: `bleak`, `pyqtgraph`, `matplotlib`, `pandas`, `scipy`

## Outlook

The system can be extended with improved hardware integration, more sensor inputs, and stress level classification features.

## License

This project is released for academic and non-commercial use.

