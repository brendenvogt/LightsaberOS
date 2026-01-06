#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <Wire.h>

// Audio
#include <AudioFileSourceSD.h>
#include <AudioGeneratorMP3.h>
#include <AudioOutputI2S.h>

// OLED
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// WS2812B
#include <Adafruit_NeoPixel.h>

// =====================
// Pins
// =====================
#define SD_CS      5
#define SPI_MOSI  23
#define SPI_MISO  19
#define SPI_SCK   18

#define I2S_BCLK  26
#define I2S_LRC   25
#define I2S_DOUT  27

#define OLED_SDA  21
#define OLED_SCL  22

#define PIXEL_PIN   16
#define PIXEL_COUNT 10

// =====================
// Objects
// =====================
AudioGeneratorMP3 *mp3;
AudioFileSourceSD *file;
AudioOutputI2S *out;

Adafruit_SSD1306 display(128, 32, &Wire, -1);
Adafruit_NeoPixel pixels(PIXEL_COUNT, PIXEL_PIN, NEO_GRB + NEO_KHZ800);

// =====================
// Setup
// =====================
void setup() {

  Serial.begin(115200);

  // SD Card
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  SD.begin(SD_CS);

  // I2C OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(100000);   // important on ESP32
  delay(100);              // let OLED power stabilize
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
    while (true);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("ESP32 Audio");
  display.println("MP3 Player");
  display.display();   // THIS IS REQUIRED

  // WS2812B
  pixels.begin();
  pixels.setBrightness(40);
  pixels.clear();
  pixels.show();

  // Audio
  out = new AudioOutputI2S();
  out->SetPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  out->SetGain(0.2);

  file = new AudioFileSourceSD("/MYMUSIC.mp3");
  mp3  = new AudioGeneratorMP3();
  mp3->begin(file, out);
}

// =====================
// Loop
// =====================
void loop() {

  // Audio
  if (mp3->isRunning()) {
    mp3->loop();
  }

  // Simple pixel animation
  static uint16_t hue = 0;
  for (int i = 0; i < PIXEL_COUNT; i++) {
    pixels.setPixelColor(i, pixels.ColorHSV(hue + i * 4000, 255, 255));
  }
  pixels.show();
  hue += 256;

  // OLED refresh (lightweight)
  static uint32_t last = 0;
  if (millis() - last > 500) {
    last = millis();
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Playing:");
    display.println("MYMUSIC.mp3");
    display.display();
  }
}
