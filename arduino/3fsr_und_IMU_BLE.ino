#include <Arduino_LSM6DSOX.h>
#include <ArduinoBLE.h>

#define NUM_SENSORS 3
const int forceSensorPins[NUM_SENSORS] = {A0, A1, A2};

float voltage_ref = 3.3;
float r_m = 10000.0;

BLEService sensorService("180C");
BLECharacteristic dataChar("2A56", BLERead | BLENotify, 60); // BLE max 60 Byte

float Ax, Ay, Az;

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);  // Auf USB warten (max 3s)

  if (!BLE.begin()) {
    pinMode(LED_BUILTIN, OUTPUT);
    while (1) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(300);
      digitalWrite(LED_BUILTIN, LOW);
      delay(300);
    }
  }

  BLE.setLocalName("RP2040_Sensor");
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(dataChar);
  BLE.addService(sensorService);
  BLE.advertise();

  if (!IMU.begin()) {
    Serial.println("IMU init failed!");
    while (1);
  }

  analogReadResolution(10);
  delay(1000);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // Dauerlicht = Werbung läuft
}


void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());

    while (central.connected()) {
      float fsr_resistances[NUM_SENSORS];

      for (int i = 0; i < NUM_SENSORS; i++) {
        int analogReading = analogRead(forceSensorPins[i]);
        float voltage = analogReading * (voltage_ref / 1023.0);
        float r_fsr = (voltage == 0) ? NAN : r_m * ((voltage_ref / voltage) - 1.0);
        fsr_resistances[i] = r_fsr;
      }

      if (IMU.accelerationAvailable()) {
        IMU.readAcceleration(Ax, Ay, Az);

        String payload = String(Ax * 9.81, 2) + "\t" +
                         String(Ay * 9.81, 2) + "\t" +
                         String(Az * 9.81, 2) + "\t" +
                         String(fsr_resistances[0], 1) + "\t" +
                         String(fsr_resistances[1], 1) + "\t" +
                         String(fsr_resistances[2], 1);

        dataChar.writeValue(payload.c_str());
        Serial.println(payload);
      }

      delay(100);  // 10 Hz
    }

    Serial.println("Disconnected");
  }
}
