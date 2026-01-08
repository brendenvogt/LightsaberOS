#include <Arduino.h>
#include "SaberFwd.h"
#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <math.h>

// Audio (ESP8266Audio)
#include <AudioFileSourceSD.h>
#include <AudioFileSourceBuffer.h>
#include <AudioGeneratorWAV.h>
#include <AudioOutputI2S.h>

// OLED
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// WS2812B
#include <Adafruit_NeoPixel.h>

// =====================
// Pins (same as base project)
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
#define BTN1_PIN 32  // Saber on/off
#define BTN2_PIN 33  // Profile / blaster

// IMU (MPU9250/MPU6500 family) I2C address
#define IMU_ADDR 0x68

// Audio volume (0.0 = mute, 1.0 = max). Start low; MAX98357 amps get loud fast.
// Adjustable via the on-device menu.
static float g_volume = 0.12f;

// =====================
// Objects
// =====================
Adafruit_SSD1306 display(128, 32, &Wire, -1);
Adafruit_NeoPixel pixels(PIXEL_COUNT, PIXEL_PIN, NEO_GRB + NEO_KHZ800);

AudioGeneratorWAV *wav = nullptr;
AudioFileSourceSD *sdFile = nullptr;
AudioFileSourceBuffer *bufFile = nullptr;
AudioOutputI2S *out = nullptr;

// =====================
// Buttons (debounced)
// =====================
struct DebouncedButton {
  uint8_t pin;
  bool stablePressed;
  bool rawLastPressed;
  uint32_t lastChangeMs;
  uint32_t pressedSinceMs;
  bool longFired;
};

static const uint32_t DEBOUNCE_MS = 35;
DebouncedButton btn1{BTN1_PIN, false, false, 0, 0, false};
DebouncedButton btn2{BTN2_PIN, false, false, 0, 0, false};

struct ButtonEvents {
  bool pressed;
  bool released;
  bool isDown;
};

static ButtonEvents buttonUpdate(DebouncedButton &b) {
  bool rawPressed = (digitalRead(b.pin) == LOW);

  if (rawPressed != b.rawLastPressed) {
    b.rawLastPressed = rawPressed;
    b.lastChangeMs = millis();
  }

  bool prevStable = b.stablePressed;
  if ((millis() - b.lastChangeMs) >= DEBOUNCE_MS) {
    b.stablePressed = b.rawLastPressed;
  }

  bool pressedEdge = (b.stablePressed && !prevStable);
  bool releasedEdge = (!b.stablePressed && prevStable);

  // Track press timing for long-press (used by some callers)
  if (pressedEdge) {
    b.pressedSinceMs = millis();
    b.longFired = false;
  }
  if (releasedEdge) {
    b.longFired = false;
  }

  return ButtonEvents{pressedEdge, releasedEdge, b.stablePressed};
}

static bool buttonLongPressEdge(DebouncedButton &b, uint32_t holdMs) {
  if (!b.stablePressed) return false;
  if (b.longFired) return false;
  if (millis() - b.pressedSinceMs < holdMs) return false;
  b.longFired = true;
  return true;
}

// =====================
// IMU (minimal register driver)
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
  for (size_t i = 0; i < len; i++) buf[i] = Wire.read();
  return true;
}

static uint8_t imuWhoAmI() {
  uint8_t v = 0xFF;
  (void)i2cReadRegs(IMU_ADDR, 0x75, &v, 1); // WHO_AM_I
  return v;
}

static bool imuInit() {
  if (!i2cWriteReg(IMU_ADDR, 0x6B, 0x00)) return false; // PWR_MGMT_1 wake
  delay(10);
  (void)i2cWriteReg(IMU_ADDR, 0x1A, 0x03); // CONFIG DLPF
  (void)i2cWriteReg(IMU_ADDR, 0x1B, (1 << 3)); // GYRO_CONFIG ±500 dps
  (void)i2cWriteReg(IMU_ADDR, 0x1C, (2 << 3)); // ACCEL_CONFIG ±8g
  (void)i2cWriteReg(IMU_ADDR, 0x1D, 0x03); // ACCEL_CONFIG2 DLPF
  return (imuWhoAmI() != 0xFF);
}

struct ImuSample {
  float ax_g, ay_g, az_g;
  float gx_rads, gy_rads, gz_rads;
  float pitch_deg, roll_deg;
};

static bool imuRead(ImuSample &s) {
  uint8_t buf[14];
  if (!i2cReadRegs(IMU_ADDR, 0x3B, buf, sizeof(buf))) return false;

  auto be16 = [&](int i) -> int16_t { return (int16_t)((buf[i] << 8) | buf[i + 1]); };

  int16_t ax = be16(0);
  int16_t ay = be16(2);
  int16_t az = be16(4);
  int16_t gx = be16(8);
  int16_t gy = be16(10);
  int16_t gz = be16(12);

  // Configured scales
  const float ACC_LSB_PER_G = 4096.0f;     // ±8g
  const float GYRO_LSB_PER_DPS = 65.5f;    // ±500 dps
  const float DEG2RAD = 0.017453292519943295f;

  s.ax_g = (float)ax / ACC_LSB_PER_G;
  s.ay_g = (float)ay / ACC_LSB_PER_G;
  s.az_g = (float)az / ACC_LSB_PER_G;

  float gx_dps = (float)gx / GYRO_LSB_PER_DPS;
  float gy_dps = (float)gy / GYRO_LSB_PER_DPS;
  float gz_dps = (float)gz / GYRO_LSB_PER_DPS;
  s.gx_rads = gx_dps * DEG2RAD;
  s.gy_rads = gy_dps * DEG2RAD;
  s.gz_rads = gz_dps * DEG2RAD;

  s.pitch_deg = atan2f(-s.ax_g, sqrtf(s.ay_g * s.ay_g + s.az_g * s.az_g)) * 57.2957795f;
  s.roll_deg  = atan2f(s.ay_g, s.az_g) * 57.2957795f;

  return true;
}

// =====================
// Profile (loaded from SD)
// =====================
struct SaberProfile {
  // Proffie/Teensy-style: each top-level folder on SD card is a profile.
  // Example: "/TeensySF", "/SmthJedi", etc.
  String name; // directory name
  String dir;  // absolute directory path (leading '/')

  // LED config (defaults; can be extended later to parse per-profile config files)
  uint8_t bladeR = 0;
  uint8_t bladeG = 120;
  uint8_t bladeB = 255;
  uint8_t brightness = 40;

  // Motion config
  float clashGyroThresh = 6.0f; // rad/s magnitude threshold
  uint32_t clashCooldownMs = 400;
};

// Top-level folders we should ignore when scanning for profiles
static const char *IGNORE_DIR_TRACKS = "tracks";
static SaberProfile profile;

// =====================
// Proffie sound indexing (performance)
// =====================
// Scanning a directory on SD can be slow; we cache the matching filenames for the current
// profile once (on profile load), then random-pick from the cached list instantly.
struct SoundList {
  static const uint8_t MAX = 32;
  uint8_t count = 0;
  char names[MAX][32]; // filename only (no path)
};

static SoundList s_out;
static SoundList s_in;
static SoundList s_hum;
static SoundList s_clsh;
static SoundList s_blst;

static void soundListClear(SoundList &l) { l.count = 0; }

static void soundListAdd(SoundList &l, const String &name) {
  if (l.count >= SoundList::MAX) return;
  strncpy(l.names[l.count], name.c_str(), sizeof(l.names[l.count]) - 1);
  l.names[l.count][sizeof(l.names[l.count]) - 1] = '\0';
  l.count++;
}

static bool lowerStartsWith(const String &s, const char *prefix) {
  String t = s;
  t.toLowerCase();
  return t.startsWith(prefix);
}

static bool lowerEndsWith(const String &s, const char *suffix) {
  String t = s;
  t.toLowerCase();
  return t.endsWith(suffix);
}

static void indexSoundsForCurrentProfile() {
  soundListClear(s_out);
  soundListClear(s_in);
  soundListClear(s_hum);
  soundListClear(s_clsh);
  soundListClear(s_blst);

  File d = SD.open(profile.dir.c_str());
  if (!d || !d.isDirectory()) { if (d) d.close(); return; }

  File e = d.openNextFile();
  while (e) {
    if (!e.isDirectory()) {
      String name = String(e.name());
      if (lowerEndsWith(name, ".wav")) {
        if (lowerStartsWith(name, "out"))  soundListAdd(s_out, name);
        else if (lowerStartsWith(name, "in"))   soundListAdd(s_in, name);
        else if (lowerStartsWith(name, "hum"))  soundListAdd(s_hum, name);
        else if (lowerStartsWith(name, "clsh")) soundListAdd(s_clsh, name);
        else if (lowerStartsWith(name, "blst")) soundListAdd(s_blst, name);
      }
    }
    e.close();
    e = d.openNextFile();
  }
  d.close();
}

static bool loadProfileFromDir(const String &dirPath) {
  // Defaults
  profile = SaberProfile();
  profile.dir = dirPath;
  int slash = dirPath.lastIndexOf('/');
  if (slash >= 0 && slash < (int)dirPath.length() - 1) profile.name = dirPath.substring(slash + 1);
  else profile.name = dirPath;

  // Optional: some Proffie packs include config.ini/smoothsw.ini; we currently ignore them
  // (but we keep the parser helper above if you want to extend later).
  indexSoundsForCurrentProfile();
  return true;
}

static bool loadFirstProfile() {
  File root = SD.open("/");
  if (!root) return false;
  if (!root.isDirectory()) { root.close(); return false; }

  File entry = root.openNextFile();
  while (entry) {
    if (entry.isDirectory()) {
      String name = String(entry.name());
      if (name.equalsIgnoreCase(IGNORE_DIR_TRACKS)) { entry.close(); entry = root.openNextFile(); continue; }
      String dir = String("/") + name;
      entry.close();
      root.close();
      return loadProfileFromDir(dir);
    }
    entry.close();
    entry = root.openNextFile();
  }

  root.close();
  return false;
}

static bool loadNextProfile() {
  // Very simple: scan and pick the next directory lexicographically after current name.
  // If none, wrap to first.
  String current = profile.name;
  String bestNext = "";
  String bestWrap = "";

  File root = SD.open("/");
  if (!root) return false;
  if (!root.isDirectory()) { root.close(); return false; }

  File entry = root.openNextFile();
  while (entry) {
    if (entry.isDirectory()) {
      String name = String(entry.name());
      if (name.equalsIgnoreCase(IGNORE_DIR_TRACKS)) { entry.close(); entry = root.openNextFile(); continue; }
      if (bestWrap == "" || name < bestWrap) bestWrap = name;
      if (name > current && (bestNext == "" || name < bestNext)) bestNext = name;
    }
    entry.close();
    entry = root.openNextFile();
  }
  root.close();

  String pick = (bestNext != "") ? bestNext : bestWrap;
  if (pick == "") return false;
  return loadProfileFromDir(String("/") + pick);
}

// =====================
// Audio helpers
// =====================
static void audioEnsureOut() {
  if (out != nullptr) return;
  out = new AudioOutputI2S();
  out->SetPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  out->SetGain(g_volume);
}

static void audioSetVolume(float v) {
  g_volume = constrain(v, 0.0f, 1.0f);
  if (out != nullptr) out->SetGain(g_volume);
}

static void audioStop() {
  if (wav) {
    wav->stop();
    delete wav;
    wav = nullptr;
  }
  if (bufFile) {
    delete bufFile;
    bufFile = nullptr;
  }
  if (sdFile) {
    delete sdFile;
    sdFile = nullptr;
  }
}

static void audioPlayFile(const String &absPath) {
  audioStop();
  audioEnsureOut();

  // SD read latency spikes can cause audible crackles if the decoder underruns.
  // Buffering smooths that out on ESP32.
  sdFile = new AudioFileSourceSD(absPath.c_str());
  static const uint32_t AUDIO_BUFFER_BYTES = 16 * 1024; // increase to 32*1024 if you have headroom
  bufFile = new AudioFileSourceBuffer(sdFile, AUDIO_BUFFER_BYTES);
  wav = new AudioGeneratorWAV();
  wav->begin(bufFile, out);
}

static bool audioIsRunning() {
  return (wav != nullptr && wav->isRunning());
}

static void audioLoop() {
  if (wav != nullptr && wav->isRunning()) wav->loop();
}

// =====================
// Saber states
// =====================
enum class SaberState : uint8_t {
  Off,
  TurningOn,
  On,
  Clash,
  BlasterBlock,
  Retracting,
};

static SaberState state = SaberState::Off;

// Anim timing
static uint32_t stateStartMs = 0;
static uint32_t lastFrameMs = 0;

// Effect overlay
static uint8_t effectIndex = 0;
static uint32_t effectStartMs = 0;
static uint32_t effectDurationMs = 180;
static uint32_t effectColor = 0;

// Clash gating
static uint32_t lastClashMs = 0;
static uint32_t lastBlasterMs = 0;
static const uint32_t BLASTER_RETRIGGER_MS = 80; // prevent accidental double-fire spam

// =====================
// UI menu (2-button, OLED)
// =====================
enum class UiMode : uint8_t { Normal, Menu };
static UiMode uiMode = UiMode::Normal;

enum class MenuItem : uint8_t {
  Profile = 0,
  Volume,
  Color,
  Brightness,
  ClashThreshold,
  COUNT
};
static MenuItem menuItem = MenuItem::Profile;

struct ColorPreset { const char *name; uint8_t r, g, b; };
static const ColorPreset COLOR_PRESETS[] = {
  {"Blue",   0, 120, 255},
  {"Green",  0, 255, 80},
  {"Red",    255, 0, 0},
  {"Purple", 160, 0, 255},
  {"Cyan",   0, 255, 255},
  {"White",  255, 255, 255},
  {"Yellow", 255, 180, 0},
};
static uint8_t colorPresetIdx = 0;

static const float VOLUME_STEPS[] = {0.03f, 0.05f, 0.08f, 0.12f, 0.16f, 0.20f, 0.25f};
static uint8_t volumeIdx = 3; // 0.12 default

static const uint8_t BRIGHTNESS_STEPS[] = {20, 40, 60, 80, 100, 120, 160, 200, 255};
static uint8_t brightnessIdx = 1; // 40 default-ish

static void applyColorPreset(uint8_t idx) {
  idx = (uint8_t)(idx % (sizeof(COLOR_PRESETS) / sizeof(COLOR_PRESETS[0])));
  colorPresetIdx = idx;
  profile.bladeR = COLOR_PRESETS[idx].r;
  profile.bladeG = COLOR_PRESETS[idx].g;
  profile.bladeB = COLOR_PRESETS[idx].b;
}

static void uiEnterMenu() {
  uiMode = UiMode::Menu;
  menuItem = MenuItem::Profile;
}

static void uiExitMenu() {
  uiMode = UiMode::Normal;
}

static void uiNextItem() {
  uint8_t i = (uint8_t)menuItem;
  i = (uint8_t)((i + 1) % (uint8_t)MenuItem::COUNT);
  menuItem = (MenuItem)i;
}

static void uiAdjustCurrent() {
  switch (menuItem) {
    case MenuItem::Profile:
      (void)loadNextProfile();
      pixels.setBrightness(profile.brightness);
      break;
    case MenuItem::Volume:
      volumeIdx = (uint8_t)((volumeIdx + 1) % (sizeof(VOLUME_STEPS) / sizeof(VOLUME_STEPS[0])));
      audioSetVolume(VOLUME_STEPS[volumeIdx]);
      break;
    case MenuItem::Color:
      applyColorPreset((uint8_t)(colorPresetIdx + 1));
      break;
    case MenuItem::Brightness:
      brightnessIdx = (uint8_t)((brightnessIdx + 1) % (sizeof(BRIGHTNESS_STEPS) / sizeof(BRIGHTNESS_STEPS[0])));
      profile.brightness = BRIGHTNESS_STEPS[brightnessIdx];
      pixels.setBrightness(profile.brightness);
      break;
    case MenuItem::ClashThreshold: {
      static const float TH[] = {3.5f, 4.5f, 6.0f, 7.5f, 9.0f};
      static uint8_t thIdx = 2;
      thIdx = (uint8_t)((thIdx + 1) % (sizeof(TH) / sizeof(TH[0])));
      profile.clashGyroThresh = TH[thIdx];
      break;
    }
    case MenuItem::COUNT:
      break;
  }
}

static uint32_t bladeBaseColor() {
  return pixels.Color(profile.bladeR, profile.bladeG, profile.bladeB);
}

static void pixelsSetAll(uint32_t c) {
  for (int i = 0; i < PIXEL_COUNT; i++) pixels.setPixelColor(i, c);
}

// =====================
// LED update throttling (performance)
// =====================
static bool ledDirty = false;
static uint32_t lastLedShowMs = 0;
static const uint32_t LED_FRAME_MS = 16; // ~60 FPS max

static void ledMarkDirty() { ledDirty = true; }

static void ledShowIfDue() {
  if (!ledDirty) return;
  uint32_t now = millis();
  if (now - lastLedShowMs < LED_FRAME_MS) return;
  pixels.show();
  lastLedShowMs = now;
  ledDirty = false;
}

static void pixelsShowOff() {
  pixels.clear();
  ledMarkDirty();
}

static void startOverlay(uint32_t color, uint32_t durationMs) {
  effectIndex = (uint8_t)random(PIXEL_COUNT);
  effectColor = color;
  effectDurationMs = durationMs;
  effectStartMs = millis();
}

static uint8_t scale8(uint8_t v, float f) {
  int outv = (int)roundf(v * f);
  return (uint8_t)constrain(outv, 0, 255);
}

static uint32_t colorScale(uint32_t c, float f) {
  uint8_t r = (uint8_t)(c >> 16);
  uint8_t g = (uint8_t)(c >> 8);
  uint8_t b = (uint8_t)c;
  return pixels.Color(scale8(r, f), scale8(g, f), scale8(b, f));
}

static void renderBladeWithOverlay(float baseLevel01) {
  uint32_t base = colorScale(bladeBaseColor(), baseLevel01);
  pixelsSetAll(base);

  // Apply overlay if active
  uint32_t now = millis();
  if (effectDurationMs > 0 && (now - effectStartMs) < effectDurationMs) {
    float t = (float)(now - effectStartMs) / (float)effectDurationMs; // 0..1
    float amp = 1.0f - t; // decay
    uint32_t ov = colorScale(effectColor, amp);
    pixels.setPixelColor(effectIndex, ov);
  }
  ledMarkDirty();
}

static void enterState(SaberState s) {
  state = s;
  stateStartMs = millis();
}

static void triggerBlaster() {
  // Make blaster feel snappy: always (re)start the sound immediately.
  // This "retrigger" cuts the previous blaster instead of layering/mixing.
  uint32_t now = millis();
  if (now - lastBlasterMs < BLASTER_RETRIGGER_MS) return;
  lastBlasterMs = now;

  if (state == SaberState::Retracting || state == SaberState::Off || state == SaberState::TurningOn) return;
  enterState(SaberState::BlasterBlock);
  playBlaster();
  startOverlay(pixels.Color(255, 0, 0), 220);
}

static void triggerClash() {
  // Allow clash to retrigger (cuts the current sound) for snappy response.
  if (state == SaberState::Retracting || state == SaberState::Off || state == SaberState::TurningOn) return;
  enterState(SaberState::Clash);
  playClash();
  startOverlay(pixels.Color(255, 255, 255), 180);
}

static String pickFromCached(const SoundList &l) {
  if (l.count == 0) return "";
  uint8_t idx = (uint8_t)random(l.count);
  return String(l.names[idx]);
}

static void playIgnite()  { String n = pickFromCached(s_out);  if (n != "") audioPlayFile(profile.dir + "/" + n); }
static void playHum()     { String n = pickFromCached(s_hum);  if (n != "") audioPlayFile(profile.dir + "/" + n); }
static void playClash()   { String n = pickFromCached(s_clsh); if (n != "") audioPlayFile(profile.dir + "/" + n); }
static void playBlaster() { String n = pickFromCached(s_blst); if (n != "") audioPlayFile(profile.dir + "/" + n); }
static void playRetract() { String n = pickFromCached(s_in);   if (n != "") audioPlayFile(profile.dir + "/" + n); }

// =====================
// OLED helpers
// =====================
static void oledBoot(const char *l1, const char *l2) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(l1);
  display.println(l2);
  display.display();
}

static void oledRender(const ImuSample *imuOpt) {
  display.clearDisplay();
  display.setCursor(0, 0);

  if (uiMode == UiMode::Menu) {
    display.println("MENU");
    display.setCursor(0, 10);
    switch (menuItem) {
      case MenuItem::Profile:
        display.print("Profile: ");
        display.println(profile.name);
        break;
      case MenuItem::Volume:
        display.print("Volume: ");
        display.println(g_volume, 2);
        break;
      case MenuItem::Color:
        display.print("Color: ");
        display.println(COLOR_PRESETS[colorPresetIdx].name);
        break;
      case MenuItem::Brightness:
        display.print("Bright: ");
        display.println((int)profile.brightness);
        break;
      case MenuItem::ClashThreshold:
        display.print("ClashG: ");
        display.println(profile.clashGyroThresh, 1);
        break;
      case MenuItem::COUNT:
        break;
    }
    display.setCursor(0, 22);
    display.print("B1=chg B2=next");
    display.display();
    return;
  }

  // Line 1: state + profile
  const char *st = "OFF";
  switch (state) {
    case SaberState::Off: st = "OFF"; break;
    case SaberState::TurningOn: st = "IGN"; break;
    case SaberState::On: st = "ON "; break;
    case SaberState::Clash: st = "CLS"; break;
    case SaberState::BlasterBlock: st = "BLK"; break;
    case SaberState::Retracting: st = "RET"; break;
  }
  display.print(st);
  display.print(" ");
  display.println(profile.name);

  // Line 2+3: IMU summary if on
  if (imuOpt) {
    display.print("G:");
    float gmag = sqrtf(imuOpt->gx_rads * imuOpt->gx_rads + imuOpt->gy_rads * imuOpt->gy_rads + imuOpt->gz_rads * imuOpt->gz_rads);
    display.print(gmag, 1);
    display.print(" P:");
    display.print(imuOpt->pitch_deg, 0);
    display.print(" R:");
    display.println(imuOpt->roll_deg, 0);

    display.print("A:");
    float amag = sqrtf(imuOpt->ax_g * imuOpt->ax_g + imuOpt->ay_g * imuOpt->ay_g + imuOpt->az_g * imuOpt->az_g);
    display.print(amag, 2);
    display.println(" g");
  } else {
    display.println("BTN1: ON/OFF");
    display.println("BTN2: PROFILE");
  }

  display.display();
}

// =====================
// Setup / loop
// =====================
void setup() {
  Serial.begin(115200);
  randomSeed((uint32_t)micros());

  // SD
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  bool sdOk = SD.begin(SD_CS);

  // I2C
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(100000);
  delay(100);

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
  pixelsShowOff();

  // IMU
  bool imuOk = imuInit();
  uint8_t who = imuWhoAmI();
  Serial.print("IMU WHO_AM_I @0x68 = 0x");
  Serial.println(who, HEX);

  if (!sdOk) {
    oledBoot("SD init failed", "Check wiring");
  } else if (!loadFirstProfile()) {
    oledBoot("No profiles", "No folders on SD");
  } else if (!imuOk) {
    oledBoot("IMU not found", "0x68 expected");
  } else {
    oledBoot("Lightsaber", profile.name.c_str());
  }

  pixels.setBrightness(profile.brightness);
  delay(600);

  // Initialize menu indices based on current values (best-effort)
  {
    float best = 999.0f;
    for (uint8_t i = 0; i < (sizeof(VOLUME_STEPS) / sizeof(VOLUME_STEPS[0])); i++) {
      float d = fabsf(VOLUME_STEPS[i] - g_volume);
      if (d < best) { best = d; volumeIdx = i; }
    }
  }
  {
    uint8_t bestI = 0;
    uint16_t bestD = 0xFFFF;
    for (uint8_t i = 0; i < (sizeof(COLOR_PRESETS) / sizeof(COLOR_PRESETS[0])); i++) {
      int dr = (int)profile.bladeR - (int)COLOR_PRESETS[i].r;
      int dg = (int)profile.bladeG - (int)COLOR_PRESETS[i].g;
      int db = (int)profile.bladeB - (int)COLOR_PRESETS[i].b;
      uint16_t d = (uint16_t)(abs(dr) + abs(dg) + abs(db));
      if (d < bestD) { bestD = d; bestI = i; }
    }
    applyColorPreset(bestI);
  }
  {
    uint8_t bestI = 0;
    uint16_t bestD = 0xFFFF;
    for (uint8_t i = 0; i < (sizeof(BRIGHTNESS_STEPS) / sizeof(BRIGHTNESS_STEPS[0])); i++) {
      uint16_t d = (uint16_t)abs((int)profile.brightness - (int)BRIGHTNESS_STEPS[i]);
      if (d < bestD) { bestD = d; bestI = i; }
    }
    brightnessIdx = bestI;
  }

  enterState(SaberState::Off);
}

void loop() {
  // Service audio continuously
  audioLoop();

  // Buttons
  ButtonEvents b1e = buttonUpdate(btn1);
  ButtonEvents b2e = buttonUpdate(btn2);

  // Menu long-press threshold
  static const uint32_t MENU_HOLD_MS = 1000;
  static bool btn2LongHandled = false;
  static uint32_t btn2PressMs = 0;

  if (b2e.pressed) {
    btn2PressMs = millis();
    btn2LongHandled = false;
  }

  // IMU sample only when saber is on-ish (reduce bus load)
  // Also throttle IMU reads so we don't starve audio / input handling.
  ImuSample imu{};
  bool imuValid = false;
  bool onish = (state != SaberState::Off);
  if (onish) {
    static uint32_t lastImuMs = 0;
    const uint32_t IMU_PERIOD_MS = 10; // 100 Hz
    uint32_t now = millis();
    if (now - lastImuMs >= IMU_PERIOD_MS) {
      lastImuMs = now;
      imuValid = imuRead(imu);
    }
  }

  // BTN logic
  if (state == SaberState::Off) {
    // Long-press BTN2 enters/exits menu (only while OFF).
    // We trigger on "still held after MENU_HOLD_MS" and we trigger at most once per press.
    if (b2e.isDown && !btn2LongHandled && (millis() - btn2PressMs >= MENU_HOLD_MS)) {
      btn2LongHandled = true;
      if (uiMode == UiMode::Menu) uiExitMenu();
      else uiEnterMenu();
    }

    if (uiMode == UiMode::Menu) {
      // Menu controls:
      // - BTN1 press: adjust value immediately
      // - BTN2 short press (release before long threshold): next item
      if (b1e.pressed) uiAdjustCurrent();
      if (b2e.released && !btn2LongHandled) uiNextItem();
    } else {
      // Normal OFF controls:
      // - BTN1 press: ignite
      // - BTN2 short press (release before long threshold): next profile
      if (b1e.pressed) {
        enterState(SaberState::TurningOn);
        playIgnite();
      }
      if (b2e.released && !btn2LongHandled) {
        (void)loadNextProfile();
        pixels.setBrightness(profile.brightness);
      }
    }
  } else {
    // Saber is on-ish
    if (b1e.pressed && state != SaberState::Retracting) {
      enterState(SaberState::Retracting);
      playRetract();
    } else if (b2e.pressed) {
      // Allow spamming blaster while already in BlasterBlock (retrigger)
      triggerBlaster();
    }
  }

  // IMU clash detection (on-ish states; allow retriggering clash for responsiveness)
  if (imuValid && state != SaberState::Off && state != SaberState::TurningOn && state != SaberState::Retracting) {
    float gmag = sqrtf(imu.gx_rads * imu.gx_rads + imu.gy_rads * imu.gy_rads + imu.gz_rads * imu.gz_rads);
    uint32_t now = millis();
    if (gmag >= profile.clashGyroThresh && (now - lastClashMs) >= profile.clashCooldownMs) {
      lastClashMs = now;
      triggerClash();
    }
  }

  // State rendering/updates (LEDs + audio transitions)
  uint32_t now = millis();
  switch (state) {
    case SaberState::Off: {
      pixelsShowOff();
      break;
    }
    case SaberState::TurningOn: {
      // Blade extend over 550ms
      const uint32_t dur = 550;
      float t = (float)(now - stateStartMs) / (float)dur;
      t = constrain(t, 0.0f, 1.0f);

      int lit = (int)roundf(t * PIXEL_COUNT);
      uint32_t c = bladeBaseColor();
      for (int i = 0; i < PIXEL_COUNT; i++) {
        pixels.setPixelColor(i, (i < lit) ? c : 0);
      }
      ledMarkDirty();

      if ((now - stateStartMs) >= dur) {
        enterState(SaberState::On);
        playHum();
      }
      break;
    }
    case SaberState::On: {
      renderBladeWithOverlay(1.0f);

      // If hum finished (non-looping), restart it.
      if (!audioIsRunning()) {
        playHum();
      }
      break;
    }
    case SaberState::Clash: {
      renderBladeWithOverlay(1.0f);

      // When clash file ends, return to ON and resume hum
      if (!audioIsRunning()) {
        enterState(SaberState::On);
        playHum();
      }
      break;
    }
    case SaberState::BlasterBlock: {
      renderBladeWithOverlay(1.0f);
      if (!audioIsRunning()) {
        enterState(SaberState::On);
        playHum();
      }
      break;
    }
    case SaberState::Retracting: {
      // Blade retract over 550ms
      const uint32_t dur = 550;
      float t = (float)(now - stateStartMs) / (float)dur;
      t = constrain(t, 0.0f, 1.0f);

      int lit = (int)roundf((1.0f - t) * PIXEL_COUNT);
      uint32_t c = bladeBaseColor();
      for (int i = 0; i < PIXEL_COUNT; i++) {
        pixels.setPixelColor(i, (i < lit) ? c : 0);
      }
      ledMarkDirty();

      if ((now - stateStartMs) >= dur && !audioIsRunning()) {
        audioStop();
        enterState(SaberState::Off);
      }
      break;
    }
  }

  // Commit LED updates at a bounded frame rate
  ledShowIfDue();

  // OLED refresh (5 Hz)
  if (now - lastFrameMs >= 200) {
    lastFrameMs = now;
    if (state == SaberState::Off) oledRender(nullptr);
    else oledRender(imuValid ? &imu : nullptr);
  }
}


