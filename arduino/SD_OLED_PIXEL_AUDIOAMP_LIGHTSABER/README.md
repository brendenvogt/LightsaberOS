# ESP32 Lightsaber (SD Audio + OLED + WS2812B + IMU + 2 Buttons)

This is a “full lightsaber” sketch built on the original `SD_OLED_PIXEL_AUDIOAMP` base, with:

- **State machine**: Off → TurningOn → On → Clash / BlasterBlock → Retracting → Off
- **Audio** from SD card (ESP8266Audio MP3 decoder)
- **Blade LEDs** (WS2812B)
- **OLED** shows current saber profile + basic IMU info
- **IMU (MPU9250/MPU6500)** used for **clash detection** (sharp movement)

---

## Controls

- **BTN1 (GPIO32)**:
  - From OFF: **ignite** (turn on saber)
  - From ON: **retract** (turn off saber)
- **BTN2 (GPIO33)**:
  - From OFF: **cycle profiles**
  - From ON: **blaster block** (sound + red pulse)
- **BTN2 long-press (hold ~0.7s, while OFF)**:
  - Enter/exit the **OLED menu**

### OLED menu controls (while OFF)

- **BTN1**: change the current setting/value
- **BTN2**: next menu item
- **Hold BTN2**: exit menu

Buttons are **active-low** using `INPUT_PULLUP`:
- Wire each button **between GPIO and GND** (no external resistor required).

---

## Wiring (same as base project + added buttons + IMU)

### I²C (OLED + IMU)

| Device Pin | ESP32 Pin |
| ---------- | --------- |
| SDA        | GPIO21    |
| SCL        | GPIO22    |
| VCC        | 3.3V      |
| GND        | GND       |

The IMU is expected at I²C address **`0x68`**. At boot the sketch prints the IMU `WHO_AM_I` value to Serial (115200). Typical values:
- `0x71` = MPU9250
- `0x70` = MPU6500

### Buttons

| Button | ESP32 Pin |
| ------ | --------- |
| BTN1   | GPIO32    |
| BTN2   | GPIO33    |

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

### I²S Audio (MAX98357)

| MAX98357 Pin | ESP32 Pin |
| ------------ | --------- |
| BCLK         | GPIO26    |
| LRCK         | GPIO25    |
| DIN          | GPIO27    |
| GND          | GND       |
| VIN          | 3.3V / 5V |

---

## SD card “Profile” structure (IMPORTANT)

This version is designed to match **ProffieOS/TeensySaber SD card layout** (like the `ProffieOS_SD_Card` folder in this repo).

### Profiles are top-level folders

Your SD card root should look like:

- `/TeensySF/`
- `/SmthJedi/`
- `/SmthGrey/`
- `/RgueCmdr/`
- `/tracks/` (ignored by this sketch)
- `readme.txt` (ignored)

Each **top-level folder** is treated as a **profile**. The OLED shows the folder name.

### Sound filename mapping (inferred)

Inside each profile folder, the sketch picks a **random matching `.wav`** for each event:

- **Ignite / turn-on**: `out*.wav` (example: `out01.wav`)
- **Hum (looped by restart)**: `hum*.wav` (example: `hum01.wav`)
- **Clash**: `clsh*.wav` (example: `clsh01.wav`)
- **Blaster block**: `blst*.wav` (example: `blst01.wav`)
- **Retract / turn-off**: `in*.wav` (example: `in01.wav`)

Other Proffie files like `swingh*.wav`, `swingl*.wav`, `lock*.wav`, `smoothsw.ini`, `config.ini` can exist; this sketch currently ignores them (easy to extend later).

---

## Notes / limitations (current implementation)

- The hum track is treated as a “loop” by **restarting it when it ends**.
- Clash/blaster **interrupt** the hum: the sketch plays the effect, then resumes hum.
- “Clash” is detected using **gyro magnitude threshold** (tune `clash_gyro_thresh` per your build).


