#include <Arduino_LSM6DSOX.h>  // Bibliothek für das IMU-Modul

// Anzahl der verwendeten FSR-Sensoren
#define NUM_SENSORS 3
const int forceSensorPins[NUM_SENSORS] = {A0, A1, A2};  // FSR-Sensoren an analogen Pins A0–A2

float voltage_ref = 3.3;  // Referenzspannung
float r_m = 10000.0;      // Serienwiderstand (in Ohm), zusammen mit dem FSR als Spannungsteiler

// Globale Variablen zur Speicherung der IMU-Daten
float Ax, Ay, Az;    // Accelerometer-Daten
//float Gx, Gy, Gz;  // Gyroskop-Daten (auskommentiert, aber vorbereitet)

void setup() {
  Serial.begin(115200);        // Serielle Kommunikation mit 115200 Baud starten
  while (!Serial);             // Auf serielle Verbindung warten

  // Initialisierung des IMU-Moduls
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);                  // Falls fehlgeschlagen, stoppt das Programm
  }

  analogReadResolution(10);  // 10 Bit analoge Auflösung
  delay(1000);               
}

void loop() {
  float fsr_resistances[NUM_SENSORS];   // Array zur Speicherung der FSR-Widerstände

  // Schleife zum Auslesen aller FSR-Sensoren
  for (int i = 0; i < NUM_SENSORS; i++) {
    int analogReading = analogRead(forceSensorPins[i]);                // Spannung vom FSR auslesen
    float voltage = analogReading * (voltage_ref / 1023.0);            // Umrechnung auf tatsächliche Spannung
    float r_fsr = (voltage == 0) ? NAN : r_m * ((voltage_ref / voltage) - 1.0);  // Widerstandsberechnung
    fsr_resistances[i] = r_fsr; 
  }

  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
    IMU.readAcceleration(Ax, Ay, Az);   // Beschleunigungswerte auslesen (in g)
    //IMU.readGyroscope(Gx, Gy, Gz);    // (Optional) Gyroskopdaten auslesen

    // Daten ausgeben: Gyro (°/s), Acc (m/s²), FSR (Ohm)
    //Serial.print(Gx); Serial.print('\t');
   // Serial.print(Gy); Serial.print('\t');
    //Serial.print(Gz); Serial.print('\t');
    Serial.print(Ax * 9.81); Serial.print('\t');  // Umrechnung in m/s²
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
