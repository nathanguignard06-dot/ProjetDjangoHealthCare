
#include <Arduino.h>
#include <WiFi.h>
#include "secrets.h"

const char* ssid = SSID;
const char* password = PASS;

const char* serverIP = "192.168.20.131";
const uint16_t serverPort = 8000;

WiFiClient client;

void setup() {
    Serial.begin(9600);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    Serial.print("Subnet Mask: ");
    Serial.println(WiFi.subnetMask());

    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());

    Serial.println("\nWiFi Connected!");

    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
}

void loop() {
    Serial.println("\nTesting TCP connection...");

    if (client.connect(serverIP, serverPort)) {
        Serial.println("TCP CONNECTION SUCCESSFUL!");
        client.stop();
    }
    else {
        Serial.println("TCP CONNECTION FAILED!");
    }

    delay(5000);
}
