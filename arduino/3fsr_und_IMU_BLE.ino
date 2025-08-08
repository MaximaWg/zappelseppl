#include <Arduino_LSM6DSOX.h>  // Bibliothek für das IMU-Modul (Accelerometer + Gyroskop)
#include <ArduinoBLE.h>        // Bibliothek für Bluetooth Low Energy (BLE)

// Anzahl der angeschlossenen FSR-Sensoren
#define NUM_SENSORS 3 
const int forceSensorPins[NUM_SENSORS] = {A0, A1, A2};  // FSRs an analogen Pins A0, A1, A2

float voltage_ref = 3.3;  // Referenzspannung
float r_m = 10000.0;      // Serienwiderstand (in Ohm), der mit dem FSR verschaltet ist

// BLE-Service und -Charakteristik definieren (für Senden von Sensordaten)
BLEService sensorService("180C");  // Standard BLE-Service-UUID
BLECharacteristic dataChar("2A56", BLERead | BLENotify, 60); // BLE mit max. 60 Byte

// Globale Variablen für die Beschleunigungswerte
float Ax, Ay, Az;

void setup() {
  Serial.begin(9600);                  // Serielle Schnittstelle starten
  while (!Serial && millis() < 3000);  // Auf USB-Verbindung warten (max 3s)

  // BLE initialisieren
  if (!BLE.begin()) {
    pinMode(LED_BUILTIN, OUTPUT);      // Fehleranzeige über LED
    while (1) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(300);
      digitalWrite(LED_BUILTIN, LOW);
      delay(300);
    }
  }

  // BLE-Gerät konfigurieren
  BLE.setLocalName("RP2040_Sensor");             // Gerätename
  BLE.setAdvertisedService(sensorService);       // Service bekanntmachen
  sensorService.addCharacteristic(dataChar);     // Charakteristik zum Service hinzufügen
  BLE.addService(sensorService);                 // Service registrieren
  BLE.advertise();                               // BLE-Werbung starten

  // IMU initialisieren
  if (!IMU.begin()) {
    Serial.println("IMU init failed!");
    while (1);  // Stoppt bei Fehler
  }

  analogReadResolution(10);         // Analoge Auflösung auf 10 Bit setzen 
  delay(1000);                     

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // LED leuchtet dauerhaft: Werbung aktiv
}

void loop() {
  // Warten auf eine BLE-Verbindung mit PC
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());

    // Während BLE-Verbindung aktiv ist
    while (central.connected()) {
      float fsr_resistances[NUM_SENSORS];  // Array für FSR-Widerstände

      // Alle FSR-Sensoren auslesen
      for (int i = 0; i < NUM_SENSORS; i++) {
        int analogReading = analogRead(forceSensorPins[i]);                   // Spannung einlesen
        float voltage = analogReading * (voltage_ref / 1023.0);              // In Spannung umrechnen
        float r_fsr = (voltage == 0) ? NAN : r_m * ((voltage_ref / voltage) - 1.0);  // Widerstand berechnen
        fsr_resistances[i] = r_fsr;
      }

      // Beschleunigungsdaten einlesen
      if (IMU.accelerationAvailable()) {
        IMU.readAcceleration(Ax, Ay, Az);  // Werte in g

        // Nutzlast-String mit Werten in m/s² und Ohm erzeugen 
        String payload = String(Ax * 9.81, 2) + "\t" +
                         String(Ay * 9.81, 2) + "\t" +
                         String(Az * 9.81, 2) + "\t" +
                         String(fsr_resistances[0], 1) + "\t" +
                         String(fsr_resistances[1], 1) + "\t" +
                         String(fsr_resistances[2], 1);

        dataChar.writeValue(payload.c_str());  // Daten via BLE verschicken
        Serial.println(payload);               // Debug-Ausgabe im Seriellen Monitor
      }

      delay(100);  // 10 Hz Sampling-Rate 
    }

    Serial.println("Disconnected");  // Verbindung wurde getrennt
  }
}
