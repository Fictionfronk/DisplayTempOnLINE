// please install Adafruit_BMP280 lib first
// Adafruit_BMP280 lib in Sketch->Includ Library->Library Manager

#include "M5StickC.h"
#include <Adafruit_BMP280.h>
#include "SHT20.h"
#include "yunBoard.h"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

const char* ssid = "AISFibre_C10_609_2.4G";
const char* pass = "TU@C10609";
const char* mqtt_server = "broker.netpie.io";
const int mqtt_port = 1883;
const char* mqtt_Client = "6f755bda-610f-4ab3-98c9-b161abccd2ad";
const char* mqtt_username = "8fgvFpJdrYvgZLNntwr6wJsjiKSvqFm6";
const char* mqtt_password = "o)xrMI*#185ZzY$Vw2DDS!BCC5dJ~MC8";

//#define TokenLine "wvCAFlxWcVMhYzpGXE4E18p3ZIMoBYAgLwIle9vDrvf"

WiFiClient espClient;
PubSubClient client(espClient);

long lastMsg = 0;
int value = 0;
char msg[100];

SHT20 sht20;
Adafruit_BMP280 bmp;

uint32_t update_time = 0;
float tmp, hum;
float pressure;
uint16_t light;

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection…");
    if (client.connect(mqtt_Client, mqtt_username, mqtt_password)) {
      Serial.println("connected");
    }
    else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println("try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  M5.begin();
  Wire.begin(0, 26, 100000);
  M5.Lcd.setRotation(1);
  M5.Lcd.setTextSize(2);
  // RGB888
  // led_set(uint8_t 1, 0x080808);

  if (!bmp.begin(0x76)) {
    Serial.println(F("Could not find a valid BMP280 sensor, check wiring!"));
  }

  /* Default settings from datasheet. */
  bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     /* Operating Mode. */
                  Adafruit_BMP280::SAMPLING_X2,     /* Temp. oversampling */
                  Adafruit_BMP280::SAMPLING_X16,    /* Pressure oversampling */
                  Adafruit_BMP280::FILTER_X16,      /* Filtering. */
                  Adafruit_BMP280::STANDBY_MS_1000); /* Standby time. */

  // put your setup code here, to run once:

  WiFi.begin(ssid, pass);

  Serial.print("WiFi Connecting");

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println();
  Serial.print("connected: ");
  Serial.println(WiFi.localIP());
  client.setServer(mqtt_server, mqtt_port);
}

uint8_t color_light = 5;

void loop() {

  led_set_all((color_light << 16) | (color_light << 8) | color_light);
  if (millis() > update_time) {
    update_time = millis() + 1000;
    tmp = sht20.read_temperature();
    hum = sht20.read_humidity();
    light = light_get();
    pressure = bmp.readPressure();
    M5.Lcd.setCursor(0, 8);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.printf("tmp:%.2f\r\n", tmp);
    M5.Lcd.setTextColor(TFT_GREEN, TFT_BLACK);
    M5.Lcd.printf("hum:%.2f\r\n", hum);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.printf("pre:%.2f\r\n", pressure);
    M5.Lcd.setTextColor(TFT_GREEN, TFT_BLACK);
    M5.Lcd.printf("light:%04d\r\n", light);
  }

  M5.update();

  if (M5.BtnA.wasPressed()) {
    esp_restart();
  }

  delay(10);
  // put your main code here, to run repeatedly:

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  long now = millis();
  if (now - lastMsg > 2000) {
    lastMsg = now;
    ++value;
    String txt1 = "Temperature: " + String(tmp) + "\n";
    String txt2 = "Humidity: " + String(hum) + "\n";
    String txt3 = "Pressure: " + String(pressure);
    String data = txt1 + txt2 + txt3;

    data.toCharArray(msg, (data.length() + 1));
    Serial.println(msg);
    client.publish("@msg/report", msg);
    Serial.println("Published temp to netpie");
    delay(2000);

  }
  delay(1);
  //  String txt1 = "NOW \nTemperature: " + String(tmp) + "\n";
  //  String txt2 = "Humidity: " + String(hum) + "\n";
  //  String txt3 = "Pressure: " + String(pressure);
  //  String msg = txt1 + txt2 + txt3;
  //  NotifyLine(msg);
  //
  //  delay(900000);

}

//void NotifyLine(String t) {
//  WiFiClientSecure client;
//  if (!client.connect("notify-api.line.me", 443)) {
//    Serial.println("Connection failed");
//
//    return;
//  }
//  String req = "";
//  req += "POST /api/notify HTTP/1.1\r\n";
//  req += "Host: notify-api.line.me\r\n";
//  req += "Authorization: Bearer " + String(TokenLine) + "\r\n";
//  req += "Cache-Control: no-cache\r\n";
//  req += "User-Agent: ESP32\r\n";
//  req += "Content-Type: application/x-www-form-urlencoded\r\n";
//  req += "Content-Length: " + String(String("message=" + t).length()) + "\r\n";
//  req += "\r\n";
//  req += "message=" + t;
//  Serial.println(req);
//  client.print(req);
//  delay(20);
//  Serial.println("-------------");
//  while (client.connected()) {
//    String line = client.readStringUntil('\n');
//    if (line == "\r") {
//      break;
//    }
//  }
//}
