#include <Arduino_LSM6DSOX.h>  // Library for the IMU module

// Number of FSR sensors used
#define NUM_SENSORS 3
const int forceSensorPins[NUM_SENSORS] = {A0, A1, A2};  // FSR sensors connected to analog pins A0–A2

float voltage_ref = 3.3;  // Reference voltage
float r_m = 10000.0;      // Series resistor (in ohms), forms a voltage divider with the FSR

// Global variables to store IMU data
float Ax, Ay, Az;    // Accelerometer data
//float Gx, Gy, Gz;  // Gyroscope data (commented but prepared)

void setup() {
  Serial.begin(115200);        // Start serial communication at 115200 baud
  while (!Serial);             // Wait for the serial connection

  // Initialize the IMU module
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);                  // If failed, stop the program
  }

  analogReadResolution(10);  // 10-bit analog resolution
  delay(1000);               
}

void loop() {
  float fsr_resistances[NUM_SENSORS];   // Array to store FSR resistances

  // Loop through all FSR sensors
  for (int i = 0; i < NUM_SENSORS; i++) {
    int analogReading = analogRead(forceSensorPins[i]);                // Read voltage from FSR
    float voltage = analogReading * (voltage_ref / 1023.0);            // Convert to actual voltage
    float r_fsr = (voltage == 0) ? NAN : r_m * ((voltage_ref / voltage) - 1.0);  // Calculate resistance
    fsr_resistances[i] = r_fsr; 
  }

  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
    IMU.readAcceleration(Ax, Ay, Az);   // Read acceleration values (in g)
    //IMU.readGyroscope(Gx, Gy, Gz);    // (Optional) Read gyroscope data

    // Output data: Gyro (°/s), Acc (m/s²), FSR (Ohms)
    //Serial.print(Gx); Serial.print('\t');
    //Serial.print(Gy); Serial.print('\t');
    //Serial.print(Gz); Serial.print('\t');
    Serial.print(Ax * 9.81); Serial.print('\t');  // Convert to m/s²
    Serial.print(Ay * 9.81); Serial.print('\t');
    Serial.print(Az * 9.81);

    for (int i = 0; i < NUM_SENSORS; i++) {
      Serial.print('\t');
      Serial.print(fsr_resistances[i]);
    }

    Serial.println();
  }

  delay(100);  // 10 Hz
}
