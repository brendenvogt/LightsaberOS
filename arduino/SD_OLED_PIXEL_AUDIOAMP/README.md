
# ESP32 SD I²S Music Player with OLED & WS2812B LEDs

This project is a **compact ESP32-based MP3 player** that plays music from a microSD card through an **I²S amplifier**, displays information on a **128x32 SSD1306 OLED**, and adds visual effects using a **strip of WS2812B LEDs**.

It is based on the **ESP8266Audio** library for low-memory MP3 decoding and is compatible with ESP32 boards.

---

## Features

* Plays MP3 files from microSD card via **I²S** (MAX98357 or similar amplifier)
* Displays current track info and status on a **128x32 OLED**
* Drives a **strip of WS2812B LEDs** for animations or visualizations
* Lightweight and optimized for ESP32 flash/RAM
* Fully configurable pins for flexibility

---

## Hardware Requirements

| Component                       | Notes                                                 |
| ------------------------------- | ----------------------------------------------------- |
| ESP32 development board         | Any standard ESP32 with enough pins                   |
| microSD card + reader           | FAT32 formatted                                       |
| I²S amplifier                   | e.g., MAX98357A                                       |
| 128x32 OLED                     | SSD1306 driver, I²C interface                         |
| WS2812B LEDs                    | Up to 10 pixels tested; separate 5V power recommended |
| Wires / breadboard / connectors | For connections                                       |

---

## Pin Connections

### I²C OLED

| OLED Pin | ESP32 Pin |
| -------- | --------- |
| SDA      | GPIO21    |
| SCL      | GPIO22    |
| VCC      | 3.3V      |
| GND      | GND       |

### I²S Audio (MAX98357)

| MAX98357 Pin | ESP32 Pin |
| ------------ | --------- |
| BCLK         | GPIO26    |
| LRCK         | GPIO25    |
| DIN          | GPIO27    |
| GND          | GND       |
| VIN          | 3.3V / 5V |

### WS2812B LED Strip

| Strip Pin | ESP32 Pin                                         |
| --------- | ------------------------------------------------- |
| Data      | GPIO16                                            |
| 5V        | 5V power (separate from ESP32 5V if high current) |
| GND       | ESP32 GND                                         |

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

Install the following **Arduino libraries** via Library Manager:

* [ESP8266Audio](https://github.com/earlephilhower/ESP8266Audio)
* [Adafruit SSD1306](https://github.com/adafruit/Adafruit_SSD1306)
* [Adafruit GFX](https://github.com/adafruit/Adafruit-GFX-Library)
* [Adafruit NeoPixel](https://github.com/adafruit/Adafruit_NeoPixel)

---

## Installation

1. Format microSD card as **FAT32** and add an MP3 file called `MYMUSIC.mp3` in the root directory.
2. Connect ESP32, OLED, WS2812B, SD card, and I²S amp according to the pin table above.
3. Open the Arduino IDE and select your **ESP32 board**.
4. Install all required libraries via **Tools > Manage Libraries**.
5. Upload the provided sketch to the ESP32.

---

## Usage

* On boot, the OLED will display **“ESP32 Audio Ready”**.
* The audio will start playing automatically from `MYMUSIC.mp3`.
* WS2812B LEDs will run a simple color animation.
* The OLED will update periodically to show track info.

---

## Important Notes

1. **Powering OLED and LEDs**:

   * OLED is safe at 3.3V.
   * WS2812B LEDs are power-hungry; if using more than a few LEDs, provide separate 5V power.

2. **I²C Timing**:

   * On ESP32, the OLED I²C clock is limited to **100kHz** to ensure reliability:

     ```cpp
     Wire.setClock(100000);
     ```

3. **Audio Library**:

   * Using **ESP8266Audio** keeps flash/RAM usage small.
   * MP3 decoding is done on the ESP32; higher bitrates (>320kbps) may affect performance.

4. **WS2812B Animations**:

   * Keep updates fast but avoid long blocking delays to prevent audio glitches.

---

## Customization

* **Change track name**: Update `"/MYMUSIC.mp3"` in the sketch.
* **Add more LEDs**: Increase `PIXEL_COUNT` in the sketch.
* **OLED messages**: Update `display.println()` calls to show battery voltage, track progress, etc.

---

## Troubleshooting

| Problem           | Solution                                                                               |
| ----------------- | -------------------------------------------------------------------------------------- |
| OLED stays blank  | Verify SDA/SCL pins, call `display.display()`, check address (0x3C for 128x32 SSD1306) |
| WS2812B flickers  | Check power; use capacitor across 5V/GND; add resistor (220Ω) on data line             |
| Audio not playing | Verify SD card format and file name; check I²S wiring; reduce MP3 bitrate              |

---

## References

* [ESP8266Audio GitHub](https://github.com/earlephilhower/ESP8266Audio)
* [Adafruit SSD1306 Library](https://github.com/adafruit/Adafruit_SSD1306)
* [Adafruit NeoPixel Library](https://github.com/adafruit/Adafruit_NeoPixel)
* [MAX98357 I²S Amp Datasheet](https://www.adafruit.com/product/3006)
* [DroneBot Workshop ESP32 Audio Tutorial](https://dronebotworkshop.com/esp32-i2s-mp3-player/)

---

## License

BSD-licensed. You may use, modify, and redistribute this project with proper attribution to original libraries and contributors.

---

If you want, I can **also produce a “full ready-to-upload sketch” README package**, combining **audio + SSD1306 + WS2812B animation**, with all the working initialization details built-in — so you can just drop it on your ESP32.

Do you want me to do that?
