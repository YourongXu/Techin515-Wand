#include <magic_wand_inferencing.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// ==== Pin Definitions ====
#define LED_PIN 43      // D6
#define BUTTON_PIN 1    // GPIO1
#define SAMPLE_RATE_MS 10
#define CAPTURE_DURATION_MS 5000
#define INFERENCE_INTERVAL_MS 3000

// ==== Global Variables ====
Adafruit_MPU6050 mpu;
float features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];
bool capturing = false;
unsigned long last_sample_time = 0;
unsigned long capture_start_time = 0;
unsigned long last_inference_time = 0;
int sample_count = 0;
bool last_button_state = HIGH; // Button uses pull-up, default state is HIGH
bool button_triggered = false;

// ==== Setup ====
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  pinMode(BUTTON_PIN, INPUT_PULLUP);  // Set button as input with internal pull-up

  // Quick blink to indicate readiness
  digitalWrite(LED_PIN, HIGH);
  delay(200);
  digitalWrite(LED_PIN, LOW);

  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) delay(10);
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("MPU6050 ready");
}

// ==== Blink LED ====
void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

// ==== Provide feature data to classifier ====
int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
  memcpy(out_ptr, features + offset, length * sizeof(float));
  return 0;
}

// ==== Run ML inference ====
void run_inference() {
  signal_t signal;
  signal.total_length = EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE;
  signal.get_data = &raw_feature_get_data;

  ei_impulse_result_t result = { 0 };
  EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

  if (res != EI_IMPULSE_OK) {
    Serial.println("Classifier failed");
    return;
  }

  float max_val = 0;
  const char* label = "";
  for (int i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
    if (result.classification[i].value > max_val) {
      max_val = result.classification[i].value;
      label = result.classification[i].label;
    }
  }

  Serial.print("Detected: ");
  Serial.print(label);
  Serial.print(" (");
  Serial.print(max_val * 100, 1);
  Serial.println("%)");

  // LED response based on prediction
  if (strcmp(label, "O") == 0) {
    blinkLED(6);
  } else if (strcmp(label, "V") == 0) {
    blinkLED(3);
  } else if (strcmp(label, "A") == 0) {
    blinkLED(1);
  }
}

// ==== Capture accelerometer data ====
void capture_data() {
  if (millis() - last_sample_time >= SAMPLE_RATE_MS) {
    last_sample_time = millis();

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    if (sample_count < EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE / 3) {
      int i = sample_count * 3;
      features[i]     = a.acceleration.x;
      features[i + 1] = a.acceleration.y;
      features[i + 2] = a.acceleration.z;
      sample_count++;
    }

    if (millis() - capture_start_time >= CAPTURE_DURATION_MS) {
      capturing = false;
      run_inference();
    }
  }
}

// ==== Main Loop ====
void loop() {
  unsigned long now = millis();

  // Detect falling edge of button (from HIGH to LOW)
  bool button_state = digitalRead(BUTTON_PIN);
  if (last_button_state == HIGH && button_state == LOW && !capturing) {
    button_triggered = true;
    Serial.println("Button pressed, starting inference...");
  }
  last_button_state = button_state;

  // Start new data capture if button triggered
  if (button_triggered) {
    sample_count = 0;
    capturing = true;
    capture_start_time = now;
    last_sample_time = now;
    button_triggered = false;
  }

  // If currently capturing, gather data
  if (capturing) {
    capture_data();
  }
}
