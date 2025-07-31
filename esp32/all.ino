// ============ BLYNK ============
#define BLYNK_TEMPLATE_ID "*"
#define BLYNK_TEMPLATE_NAME "*"
#define BLYNK_AUTH_TOKEN "*"

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>

// ============ FIREBASE ============
#include <Firebase_ESP_Client.h>

// ============ RTC + NTP ============
#include <Wire.h>
#include <RTClib.h>
#include "time.h"

// ============ WiFi & Auth ============
#define WIFI_SSID "*"
#define WIFI_PASSWORD "*"

// Firebase config
#define API_KEY "*"
#define DATABASE_URL "*"
#define USER_EMAIL "*"
#define USER_PASSWORD "*"

// ============ Firebase Object ============
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// ============ RTC Object ============
RTC_DS3231 rtc;

// ============ Jadwal ============
int jam1 = -1, menit1 = -1;
int jam2 = -1, menit2 = -1;
unsigned long lastFetchMillis = 0;

// ============ Relay ============
int relayPins[12] = { 32, 33, 25, 26, 15, 2, 4, 5, 27, 14, 12, 13 };
#define ENTER_INDEX 10
String tokenInput = "";

// ============ Sensor Suara ============
#define SOUND_SENSOR_PIN 23
int soundState = 0;
int lastState = 0;
unsigned long lastNotifTime = 0;
const unsigned long cooldownDuration = 60000;

// ============ NTP Config ============
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 7 * 3600;
const int daylightOffset_sec = 0;

// ============ Setup ============
void setup() {
  Serial.begin(115200);
  Wire.begin();

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Menghubungkan ke WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\n✅ WiFi terhubung");

  // Blynk
  Blynk.begin(BLYNK_AUTH_TOKEN, WIFI_SSID, WIFI_PASSWORD);

  // Relay
  for (int i = 0; i < 12; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], HIGH);
  }

  // Sensor suara
  pinMode(SOUND_SENSOR_PIN, INPUT);

  // RTC & Sinkronisasi NTP
  rtc.begin();
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    rtc.adjust(DateTime(timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                        timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec));
    Serial.println("✅ RTC disinkronkan ke waktu NTP");
  } else {
    Serial.println("❌ Gagal sinkron NTP");
  }

  // Firebase
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  auth.user.email = USER_EMAIL;
  auth.user.password = USER_PASSWORD;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  Serial.println("📡 Firebase terhubung");
}

// ============ Fungsi: Tekan Tombol ============
void tekanTombol(int angka) {
  if (angka < 0 || angka > 9) return;
  int pin = relayPins[angka];
  digitalWrite(pin, LOW);
  delay(65);
  digitalWrite(pin, HIGH);
  delay(500);
}

void tekanEnter() {
  int enterPin = relayPins[ENTER_INDEX];
  digitalWrite(enterPin, LOW);
  delay(65);
  digitalWrite(enterPin, HIGH);
  delay(500);
}

// ============ Blynk Write ============
BLYNK_WRITE(V0) {
  tokenInput = param.asString();
  Serial.print("Token diterima: "); Serial.println(tokenInput);

  for (int i = 0; i < tokenInput.length(); i++) {
    char c = tokenInput.charAt(i);
    if (isDigit(c)) {
      int digit = c - '0';
      tekanTombol(digit);
    }
  }

  tekanEnter();
  Blynk.virtualWrite(V1, "Token berhasil dikirim.");
}

// ============ Loop ============
void loop() {
  Blynk.run();

  // SENSOR SUARA + COOLDOWN
  soundState = digitalRead(SOUND_SENSOR_PIN);
  unsigned long nowMillis = millis();
  if (soundState == HIGH && lastState == LOW) {
    if (nowMillis - lastNotifTime > cooldownDuration) {
      Serial.println("🔊 Suara bip terdeteksi! Token hampir habis.");
      Blynk.logEvent("tokenhabis", "Token hampir habis - Suara bip terdeteksi!");
      lastNotifTime = nowMillis;
    } else {
      Serial.println("🔕 Suara deteksi tapi masih cooldown");
    }
  }
  lastState = soundState;

  // WAKTU SEKARANG
  DateTime now = rtc.now();
  int jam = now.hour();
  int menit = now.minute();

  Serial.printf("🕒 Sekarang: %02d:%02d | Jadwal: %02d:%02d & %02d:%02d\n",
                jam, menit, jam1, menit1, jam2, menit2);

  // AMBIL JADWAL DARI FIREBASE
  if (millis() - lastFetchMillis > 10000) {
    lastFetchMillis = millis();
    if (Firebase.RTDB.getInt(&fbdo, "/jadwal/jam1")) jam1 = fbdo.intData();
    if (Firebase.RTDB.getInt(&fbdo, "/jadwal/menit1")) menit1 = fbdo.intData();
    if (Firebase.RTDB.getInt(&fbdo, "/jadwal/jam2")) jam2 = fbdo.intData();
    if (Firebase.RTDB.getInt(&fbdo, "/jadwal/menit2")) menit2 = fbdo.intData();
  }

  // CEK KECOCOKAN JADWAL
  if ((jam == jam1 && menit == menit1) || (jam == jam2 && menit == menit2)) {
    Serial.println("⏰ Jadwal cocok, mengirim trigger ke Firebase...");
    if (Firebase.RTDB.setBool(&fbdo, "/ncr_token/trigger_otomatis", true)) {
      Serial.println("✅ Trigger berhasil dikirim");
    } else {
      Serial.print("❌ Gagal mengirim trigger: ");
      Serial.println(fbdo.errorReason());
    }
    delay(60000); // Tunggu 1 menit agar tidak kirim ulang
  }

  delay(100);
}
