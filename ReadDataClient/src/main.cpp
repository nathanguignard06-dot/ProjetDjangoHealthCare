#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "secrets.h"

#define HEART_PIN 33
#define ONE_WIRE_BUS 25

/*--- WIFI CREDENTIALS ---*/
const char* ssid = SSID;
const char* pass = PASS;

/*--- DJANGO API ---*/
const char* apiUrl = API_ENDPOINT;
const char* token = DJANGO_TOKEN;

/*--- GLOBAL VARIABLES ---*/
float temp;
uint16_t rate = 0;

//reading interval heartrate
const unsigned long heartInterval = 20;
unsigned long previousHeartMillis = 0;

//heart rate detect
int previousState = LOW;
unsigned long lastBeat = 0;

const unsigned long minBeatInterval = 300;
const unsigned long maxBeatInterval = 2000;
const unsigned long heartTimeout = 3000;

// BPM moving average
const int sampleCount = 5;
uint16_t bpmSamples[sampleCount] = {0};

int sampleIndex = 0;
int validSamples = 0;

//django transmission interval
const unsigned long interval = 10000;
unsigned long previousMillis = 0;

/*--- DECLARATIONS ---*/
WiFiClient client;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature ds18b20(&oneWire);

void updateHeartRate()
{
    int state = digitalRead(HEART_PIN);
    unsigned long now = millis();

    // Detect rising edge
    if (state == HIGH && previousState == LOW)
    {
        if (lastBeat != 0)
        {
            unsigned long beatInterval = now - lastBeat;

            if (beatInterval >= minBeatInterval &&
                beatInterval <= maxBeatInterval)
            {
                uint16_t bpm = 60000UL / beatInterval;

                // Store BPM in circular array
                bpmSamples[sampleIndex] = bpm;

                sampleIndex = (sampleIndex + 1) % sampleCount;

                if (validSamples < sampleCount)
                {
                    validSamples++;
                }

                // Calculate average
                unsigned long total = 0;

                for (int i = 0; i < validSamples; i++)
                {
                    total += bpmSamples[i];
                }

                rate = total / validSamples;

                //Serial.print("[HEART] BPM: ");
                //Serial.println(rate);
            }
        }

        lastBeat = now;
    }

    previousState = state;

    // Reset BPM when no pulse is detected
    if (lastBeat != 0 && now - lastBeat > heartTimeout)
    {
        rate = 0;
        lastBeat = 0;

        sampleIndex = 0;
        validSamples = 0;

        for (int i = 0; i < sampleCount; i++)
        {
            bpmSamples[i] = 0;
        }
    }
}

void sendToDjango(String jsonPayload)
{
    WiFiClient client;
    HTTPClient http;

    Serial.println("[HTTP] Connecting to Django...");

    if (http.begin(client, apiUrl))
    {
        http.addHeader("Content-Type", "application/json");
        http.addHeader("Authorization", String("Token ") + token);

        Serial.println("[JSON] Sending:");
        Serial.println(jsonPayload);

        int httpCode = http.POST(jsonPayload);

        Serial.printf("[HTTP] Response code: %d\n", httpCode);

        if (httpCode > 0)
        {
            Serial.println("[SERVER] Response:");
            Serial.println(http.getString());
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

    ds18b20.begin();
    pinMode(HEART_PIN, INPUT);
}

void loop()
{
    long unsigned int timer = millis();

    // Continuously monitor heartbeats
    updateHeartRate();

    if(timer - previousMillis >= interval)
    {
        previousMillis = timer;
        
        if (WiFi.status() == WL_CONNECTED)
        {
            Serial.print("Requesting temperatures...");
            ds18b20.requestTemperatures(); // Send the command to get temperatures
            Serial.println("DONE");

            temp = ds18b20.getTempCByIndex(0);
            temp = round(temp * 100.0) / 100.0;

            Serial.print("Heart rate : ");
            Serial.println(rate);
            Serial.print(" External body temperature : ");
            Serial.println(temp);
            Serial.println();

            for(int i = 0; i <= 30; i++)
            {
                Serial.print("-");
                if(i > 29)
                {
                    Serial.println("-");
                    Serial.println();
                }
            }
            // JSON creation
            JsonDocument docTemp, docHeart;

            docTemp["capteur"]  = 2;
            docTemp["valeur"]   = temp;

            docHeart["capteur"] = 1;
            docHeart["valeur"]  = rate;

            // JSON serialization
            String jsonPayloadTemp, jsonPayloadHeart;

            serializeJson(docTemp, jsonPayloadTemp);
            serializeJson(docHeart, jsonPayloadHeart);

            // Send both measurements separately
            sendToDjango(jsonPayloadTemp);
            // Only send BPM when valid
            if (rate > 0)
            {
                sendToDjango(jsonPayloadHeart);
            }
            else
            {
                Serial.println("[HEART] No valid BPM available.");
            }
        }
        else
        {
            Serial.println("[WIFI] Disconnected!");
            WiFi.reconnect();
        }
    }
}