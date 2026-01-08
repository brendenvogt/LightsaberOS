#pragma once

#include <Arduino.h>

// Arduino IDE auto-generates function prototypes at the top of the sketch.
// If those prototypes reference types defined later in the .ino, compilation can fail.
// Forward-declare the types used in function signatures here, and include this header
// near the top of the .ino (before the auto-generated prototypes).

struct DebouncedButton;
struct ImuSample;
struct SoundList;
enum class SaberState : uint8_t;


