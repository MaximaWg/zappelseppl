#include <Arduino_LSM6DSOX.h>

#define NUM_SENSORS 3
const int forceSensorPins[NUM_SENSORS] = {A0, A1, A2};

float voltage_ref = 3.3;
float r_m = 10000.0;  // Serienwiderstand

float Ax, Ay, Az;
//float Gx, Gy, Gz;

void setup() {
  Serial.begin(115200);
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  analogReadResolution(10);  // 10 Bit Auflösung (0–1023)
  delay(1000);               
}

void loop() {
  float fsr_resistances[NUM_SENSORS];

  for (int i = 0; i < NUM_SENSORS; i++) {
    int analogReading = analogRead(forceSensorPins[i]);
    float voltage = analogReading * (voltage_ref / 1023.0);
    float r_fsr = (voltage == 0) ? NAN : r_m * ((voltage_ref / voltage) - 1.0);
    fsr_resistances[i] = r_fsr;
  }

  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
    IMU.readAcceleration(Ax, Ay, Az);
    //IMU.readGyroscope(Gx, Gy, Gz);

    // Daten ausgeben: Gyro (°/s), Acc (m/s²), FSR (Ohm)
    //Serial.print(Gx); Serial.print('\t');
   // Serial.print(Gy); Serial.print('\t');
    //Serial.print(Gz); Serial.print('\t');
    Serial.print(Ax * 9.81); Serial.print('\t');
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
