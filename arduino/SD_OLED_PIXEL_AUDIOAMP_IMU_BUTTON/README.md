# ESP32 SD I²S Music Player + OLED + WS2812B + IMU + Buttons

This sketch is based on the original `SD_OLED_PIXEL_AUDIOAMP` project, and adds:

- Two **debounced buttons**
- An **MPU9250/MPU6500-family IMU** on I²C (address `0x68`)
- Live **IMU accel/gyro + pitch/roll** output on the **SSD1306 128x32 OLED**

---

## Features

- Plays `MYMUSIC.mp3` from microSD (SPI) using **ESP8266Audio**
- Outputs audio to an I²S amp (MAX98357 or similar)
- OLED status + IMU data pages
- WS2812B LED animation (blade on/off)
- Buttons:
  - **BTN1**: toggle audio play/pause (restart from beginning when re-enabled)
  - **BTN2**: toggle OLED page (angles vs raw accel) **and** toggle blade LEDs on/off

---

## Pin Connections (same as original + added BTN/IMU)

### I²C (OLED + IMU)

| Device Pin | ESP32 Pin |
| ---------- | --------- |
| SDA        | GPIO21    |
| SCL        | GPIO22    |
| VCC        | 3.3V      |
| GND        | GND       |

Notes:
- IMU is expected at I²C address `0x68`
- The sketch prints `WHO_AM_I` on Serial at boot (115200). Common values:
  - `0x71` = MPU9250
  - `0x70` = MPU6500

### Buttons (active-low)

| Button | ESP32 Pin | Wiring |
| ------ | --------- | ------ |
| BTN1   | GPIO32    | button between GPIO32 and GND (uses `INPUT_PULLUP`) |
| BTN2   | GPIO33    | button between GPIO33 and GND (uses `INPUT_PULLUP`) |

### I²S Audio (MAX98357)

| MAX98357 Pin | ESP32 Pin |
| ------------ | --------- |
| BCLK         | GPIO26    |
| LRCK         | GPIO25    |
| DIN          | GPIO27    |
| GND          | GND       |
| VIN          | 3.3V / 5V |

### WS2812B LED Strip

| Strip Pin | ESP32 Pin |
| --------- | --------- |
| Data      | GPIO16    |
| 5V        | 5V power (separate recommended if many LEDs) |
| GND       | ESP32 GND |

### microSD Card (SPI)

| SD Pin | ESP32 Pin |
| ------ | --------- |
| CS     | GPIO5     |
| MOSI   | GPIO23    |
| MISO   | GPIO19    |
| SCK    | GPIO18    |
| VCC    | 3.3V      |
| GND    | GND       |

---

## Software Requirements

Install via Arduino Library Manager:

- ESP8266Audio
- Adafruit SSD1306
- Adafruit GFX Library
- Adafruit NeoPixel

No dedicated MPU9250 library is required in this version; the IMU is read via basic I²C register reads.

---

## SD Card

1. Format microSD as **FAT32**
2. Put `MYMUSIC.mp3` at the **root** of the card


