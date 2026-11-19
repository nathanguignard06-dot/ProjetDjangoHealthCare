#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

/*--- WIFI CREDENTIALS ---*/
const char* ssid = SSID;
const char* pass = PASS;

/*--- DJANGO API ---*/
const char* apiUrl = API_ENDPOINT;
const char* token = DJANGO_TOKEN;

WiFiClient client;

void setup()
{
    Serial.begin(115200);

    WiFi.begin(ssid, pass);

    int timeout = 0;

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");

        timeout++;

        if (timeout > 20)
        {
            Serial.println("\n[ERROR] WiFi timeout!");
            ESP.restart();
        }
    }

    Serial.println("\n[TCP] Testing Django connection...");

    WiFiClient testClient;

    if (testClient.connect("192.168.20.131", 8000))
    {
        Serial.println("[TCP] CONNECTION SUCCESSFUL!");
        testClient.stop();
    }
    else
    {
        Serial.println("[TCP] CONNECTION FAILED!");
    }

    Serial.println("\n[WIFI] Connected!");
    Serial.println(WiFi.localIP());
}

void loop()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;

        Serial.println("[HTTP] Connecting to Django...");

        if (http.begin(client, apiUrl))
        {
            // Authentication
            http.addHeader("Content-Type", "application/json");
            http.addHeader("Authorization", String("Token ") + token);

            // Simulated sensor data
            float temperature = 26.57;

            // JSON creation
            JsonDocument doc;

            doc["capteur"] = 2;
            doc["valeur"] = temperature;

            String jsonPayload;
            serializeJson(doc, jsonPayload);

            Serial.println("[JSON] Sending:");
            Serial.println(jsonPayload);

            // Send POST request
            int httpCode = http.POST(jsonPayload);

            Serial.printf("[HTTP] Response code: %d\n", httpCode);

            if (httpCode > 0)
            {
                String response = http.getString();

                Serial.println("[SERVER] Response:");
                Serial.println(response);
            }
            else
            {
                Serial.printf(
                    "[HTTP] Connection failed: %s\n",
                    http.errorToString(httpCode).c_str()
                );
            }

            http.end();
        }
        else
        {
            Serial.println("[HTTP] Unable to initialize connection!");
        }
    }
    else
    {
        Serial.println("[WIFI] Disconnected!");
        WiFi.reconnect();
    }

    delay(60000);
}