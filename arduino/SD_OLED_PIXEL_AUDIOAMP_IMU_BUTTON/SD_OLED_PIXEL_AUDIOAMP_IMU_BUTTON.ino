#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <math.h>

// Audio (ESP8266Audio)
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

// Buttons (active-low w/ internal pullups)
#define BTN1_PIN 32
#define BTN2_PIN 33

// IMU (MPU9250/MPU6500 family) I2C address
#define IMU_ADDR 0x68

// =====================
// Objects
// =====================
AudioGeneratorMP3 *mp3 = nullptr;
AudioFileSourceSD *file = nullptr;
AudioOutputI2S *out = nullptr;

Adafruit_SSD1306 display(128, 32, &Wire, -1);
Adafruit_NeoPixel pixels(PIXEL_COUNT, PIXEL_PIN, NEO_GRB + NEO_KHZ800);

// =====================
// Button debounce
// =====================
struct DebouncedButton {
  uint8_t pin;
  bool stablePressed;
  bool lastStablePressed;
  bool rawLastPressed;
  uint32_t lastChangeMs;
};

static const uint32_t DEBOUNCE_MS = 35;

DebouncedButton btn1{BTN1_PIN, false, false, false, 0};
DebouncedButton btn2{BTN2_PIN, false, false, false, 0};

static bool buttonPressedEdge(DebouncedButton &b) {
  bool rawPressed = (digitalRead(b.pin) == LOW);

  if (rawPressed != b.rawLastPressed) {
    b.rawLastPressed = rawPressed;
    b.lastChangeMs = millis();
  }

  if ((millis() - b.lastChangeMs) >= DEBOUNCE_MS) {
    b.stablePressed = b.rawLastPressed;
  }

  bool pressedEdge = (b.stablePressed && !b.lastStablePressed);
  b.lastStablePressed = b.stablePressed;
  return pressedEdge;
}

// =====================
// IMU low-level helpers
// =====================
static bool i2cWriteReg(uint8_t addr, uint8_t reg, uint8_t value) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(value);
  return (Wire.endTransmission() == 0);
}

static bool i2cReadRegs(uint8_t addr, uint8_t startReg, uint8_t *buf, size_t len) {
  Wire.beginTransmission(addr);
  Wire.write(startReg);
  if (Wire.endTransmission(false) != 0) return false;
  size_t got = Wire.requestFrom((int)addr, (int)len);
  if (got != len) return false;
  for (size_t i = 0; i < len; i++) {
    buf[i] = Wire.read();
  }
  return true;
}

static uint8_t imuWhoAmI() {
  uint8_t v = 0xFF;
  (void)i2cReadRegs(IMU_ADDR, 0x75, &v, 1); // WHO_AM_I
  return v;
}

static bool imuInit() {
  // Wake up device
  if (!i2cWriteReg(IMU_ADDR, 0x6B, 0x00)) return false; // PWR_MGMT_1 = 0 (wake)
  delay(10);

  // CONFIG: DLPF
  (void)i2cWriteReg(IMU_ADDR, 0x1A, 0x03); // CONFIG, DLPF ~44Hz-ish (common stable setting)

  // Gyro: ±500 dps
  // GYRO_CONFIG: FS_SEL = 1 -> bits[4:3] = 01
  (void)i2cWriteReg(IMU_ADDR, 0x1B, (1 << 3));

  // Accel: ±8g
  // ACCEL_CONFIG: AFS_SEL = 2 -> bits[4:3] = 10
  (void)i2cWriteReg(IMU_ADDR, 0x1C, (2 << 3));

  // ACCEL_CONFIG2: DLPF for accel
  (void)i2cWriteReg(IMU_ADDR, 0x1D, 0x03);

  // Quick sanity read
  uint8_t who = imuWhoAmI();
  return (who != 0xFF);
}

struct ImuSample {
  float ax_ms2, ay_ms2, az_ms2;
  float gx_rads, gy_rads, gz_rads;
  float temp_c;
  float pitch_deg, roll_deg;
};

static bool imuReadSample(ImuSample &s) {
  uint8_t buf[14];
  if (!i2cReadRegs(IMU_ADDR, 0x3B, buf, sizeof(buf))) return false; // ACCEL_XOUT_H

  auto be16 = [&](int i) -> int16_t {
    return (int16_t)((buf[i] << 8) | buf[i + 1]);
  };

  int16_t ax = be16(0);
  int16_t ay = be16(2);
  int16_t az = be16(4);
  int16_t t  = be16(6);
  int16_t gx = be16(8);
  int16_t gy = be16(10);
  int16_t gz = be16(12);

  // Configured scales:
  // Accel ±8g => 4096 LSB/g
  // Gyro  ±500 dps => 65.5 LSB/(deg/s)
  const float ACC_LSB_PER_G = 4096.0f;
  const float GYRO_LSB_PER_DPS = 65.5f;
  const float G = 9.80665f;
  const float DEG2RAD = 0.017453292519943295f;

  float ax_g = (float)ax / ACC_LSB_PER_G;
  float ay_g = (float)ay / ACC_LSB_PER_G;
  float az_g = (float)az / ACC_LSB_PER_G;

  s.ax_ms2 = ax_g * G;
  s.ay_ms2 = ay_g * G;
  s.az_ms2 = az_g * G;

  float gx_dps = (float)gx / GYRO_LSB_PER_DPS;
  float gy_dps = (float)gy / GYRO_LSB_PER_DPS;
  float gz_dps = (float)gz / GYRO_LSB_PER_DPS;

  s.gx_rads = gx_dps * DEG2RAD;
  s.gy_rads = gy_dps * DEG2RAD;
  s.gz_rads = gz_dps * DEG2RAD;

  // MPU temp conversion (MPU6500/9250 family)
  // Temp in °C = (TEMP_OUT / 333.87) + 21.0
  s.temp_c = ((float)t / 333.87f) + 21.0f;

  // Pitch/Roll from accel
  s.pitch_deg = atan2f(-ax_g, sqrtf(ay_g * ay_g + az_g * az_g)) * 57.2957795f;
  s.roll_deg  = atan2f(ay_g, az_g) * 57.2957795f;

  return true;
}

// =====================
// App state
// =====================
static const char *kMp3Path = "/MYMUSIC.mp3";
static bool audioEnabled = true;
static bool bladeOn = true;
static bool showRaw = false; // toggled by BTN2 (raw accel/gyro vs angles)

static void startAudio() {
  if (out == nullptr) {
    out = new AudioOutputI2S();
    out->SetPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
    out->SetGain(0.2);
  }

  if (file != nullptr) {
    delete file;
    file = nullptr;
  }
  file = new AudioFileSourceSD(kMp3Path);

  if (mp3 != nullptr) {
    delete mp3;
    mp3 = nullptr;
  }
  mp3 = new AudioGeneratorMP3();
  mp3->begin(file, out);
}

static void stopAudio() {
  if (mp3 != nullptr) {
    mp3->stop();
    delete mp3;
    mp3 = nullptr;
  }
  if (file != nullptr) {
    delete file;
    file = nullptr;
  }
}

static void drawBoot(const char *l1, const char *l2) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(l1);
  display.println(l2);
  display.display();
}

// =====================
// Setup
// =====================
void setup() {
  Serial.begin(115200);

  // SD Card
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  (void)SD.begin(SD_CS);

  // I2C bus (OLED + IMU)
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(100000);   // important on ESP32 (reliability)
  delay(100);              // let OLED power stabilize

  // OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
    while (true) {}
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  // Buttons
  pinMode(BTN1_PIN, INPUT_PULLUP);
  pinMode(BTN2_PIN, INPUT_PULLUP);

  // LEDs
  pixels.begin();
  pixels.setBrightness(40);
  pixels.clear();
  pixels.show();

  // Audio
  startAudio();

  // IMU
  bool imuOk = imuInit();
  uint8_t who = imuWhoAmI();
  Serial.print("IMU WHO_AM_I @0x68 = 0x");
  Serial.println(who, HEX);
  // Typical: 0x71 (MPU9250), 0x70 (MPU6500)

  if (imuOk) {
    drawBoot("ESP32 Audio + IMU", "IMU OK @0x68");
  } else {
    drawBoot("ESP32 Audio + IMU", "IMU NOT FOUND");
  }
  delay(600);
}

// =====================
// Loop
// =====================
void loop() {
  // Buttons:
  // - BTN1 toggles audio play/pause
  // - BTN2 toggles display page AND blade on/off
  if (buttonPressedEdge(btn1)) {
    audioEnabled = !audioEnabled;
    if (audioEnabled) startAudio();
    else stopAudio();
  }
  if (buttonPressedEdge(btn2)) {
    showRaw = !showRaw;
    bladeOn = !bladeOn;
  }

  // Audio service
  if (mp3 != nullptr && mp3->isRunning()) {
    mp3->loop();
  }

  // Pixel animation (keep lightweight)
  static uint16_t hue = 0;
  if (bladeOn) {
    for (int i = 0; i < PIXEL_COUNT; i++) {
      pixels.setPixelColor(i, pixels.ColorHSV(hue + i * 4000, 255, 255));
    }
  } else {
    for (int i = 0; i < PIXEL_COUNT; i++) pixels.setPixelColor(i, 0);
  }
  pixels.show();
  hue += 256;

  // IMU + OLED refresh (10 Hz)
  static uint32_t lastOled = 0;
  if (millis() - lastOled >= 100) {
    lastOled = millis();

    ImuSample s{};
    bool ok = imuReadSample(s);

    display.clearDisplay();
    display.setCursor(0, 0);

    // Line 1: status
    display.print(audioEnabled ? "AUD:ON " : "AUD:OFF ");
    display.print(bladeOn ? "B:ON " : "B:OFF ");
    display.print(showRaw ? "RAW" : "ANG");

    if (!ok) {
      display.setCursor(0, 12);
      display.println("IMU read failed");
      display.display();
      return;
    }

    if (!showRaw) {
      // Page: angles + gyro z
      display.setCursor(0, 12);
      display.print("P:");
      display.print(s.pitch_deg, 1);
      display.print(" R:");
      display.print(s.roll_deg, 1);

      display.setCursor(0, 22);
      display.print("Gz:");
      display.print(s.gz_rads, 2);
      display.print(" T:");
      display.print(s.temp_c, 0);
      display.print("C");
    } else {
      // Page: raw accel (m/s^2)
      display.setCursor(0, 12);
      display.print("Ax:");
      display.print(s.ax_ms2, 1);
      display.print(" Ay:");
      display.print(s.ay_ms2, 1);

      display.setCursor(0, 22);
      display.print("Az:");
      display.print(s.az_ms2, 1);
      display.print(" m/s2");
    }

    display.display();
  }
}


