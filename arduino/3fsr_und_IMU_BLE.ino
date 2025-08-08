#include <Arduino_LSM6DSOX.h>  // Library for the IMU module (accelerometer + gyroscope)
#include <ArduinoBLE.h>        // Library for Bluetooth Low Energy (BLE)

// Number of connected FSR sensors
#define NUM_SENSORS 3 
const int forceSensorPins[NUM_SENSORS] = {A0, A1, A2};  // FSRs connected to analog pins A0, A1, A2

float voltage_ref = 3.3;  // Reference voltage
float r_m = 10000.0;      // Series resistor (in ohms), connected with the FSR in voltage divider

// Define BLE service and characteristic (for sending sensor data)
BLEService sensorService("180C");  // Standard BLE service UUID
BLECharacteristic dataChar("2A56", BLERead | BLENotify, 60); // BLE characteristic with max 60 bytes

// Global variables for accelerometer values
float Ax, Ay, Az;

void setup() {
  Serial.begin(9600);                  // Start serial communication
  while (!Serial && millis() < 3000);  // Wait for USB connection (max 3 seconds)

  // Initialize BLE
  if (!BLE.begin()) {
    pinMode(LED_BUILTIN, OUTPUT);      // Use LED to indicate error
    while (1) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(300);
      digitalWrite(LED_BUILTIN, LOW);
      delay(300);
    }
  }

  // Configure BLE device
  BLE.setLocalName("RP2040_Sensor");             // Device name
  BLE.setAdvertisedService(sensorService);       // Make service discoverable
  sensorService.addCharacteristic(dataChar);     // Add characteristic to service
  BLE.addService(sensorService);                 // Register service
  BLE.advertise();                               // Start BLE advertising

  // Initialize IMU
  if (!IMU.begin()) {
    Serial.println("IMU init failed!");
    while (1);  // Stop execution on error
  }

  analogReadResolution(10);         // Set analog resolution to 10-bit 
  delay(1000);                     

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // Turn on LED: advertising active
}

void loop() {
  // Wait for BLE connection from PC
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());

    // While BLE connection is active
    while (central.connected()) {
      float fsr_resistances[NUM_SENSORS];  // Array for FSR resistances

      // Read all FSR sensors
      for (int i = 0; i < NUM_SENSORS; i++) {
        int analogReading = analogRead(forceSensorPins[i]);                   // Read voltage
        float voltage = analogReading * (voltage_ref / 1023.0);              // Convert to actual voltage
        float r_fsr = (voltage == 0) ? NAN : r_m * ((voltage_ref / voltage) - 1.0);  // Calculate resistance
        fsr_resistances[i] = r_fsr;
      }

      // Read accelerometer data
      if (IMU.accelerationAvailable()) {
        IMU.readAcceleration(Ax, Ay, Az);  // Values in g

        // Create payload string with values in m/s² and Ohms 
        String payload = String(Ax * 9.81, 2) + "\t" +
                         String(Ay * 9.81, 2) + "\t" +
                         String(Az * 9.81, 2) + "\t" +
                         String(fsr_resistances[0], 1) + "\t" +
                         String(fsr_resistances[1], 1) + "\t" +
                         String(fsr_resistances[2], 1);

        dataChar.writeValue(payload.c_str());  // Send data via BLE
        Serial.println(payload);               // Debug output to Serial Monitor
      }

      delay(100);  // 10 Hz sampling rate 
    }

    Serial.println("Disconnected");  // Connection was lost
  }
}
