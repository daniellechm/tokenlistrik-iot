#include "esp_camera.h"
#include <WiFi.h>

const char* ssid = "GATOT KACA";
const char* password = "12345678";

WiFiServer server(80);

#define FLASH_GPIO_NUM 4  // GPIO flash LED

void setup() {
  Serial.begin(115200);
  
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW);  // Matikan flash dulu

  // Konfigurasi kamera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = 5;
  config.pin_d1       = 18;
  config.pin_d2       = 19;
  config.pin_d3       = 21;
  config.pin_d4       = 36;
  config.pin_d5       = 39;
  config.pin_d6       = 34;
  config.pin_d7       = 35;
  config.pin_xclk     = 0;
  config.pin_pclk     = 22;
  config.pin_vsync    = 25;
  config.pin_href     = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn     = 32;
  config.pin_reset    = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_CIF;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Inisialisasi kamera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Kamera gagal: 0x%x", err);
    return;
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi terhubung");
  Serial.print("Alamat IP: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Permintaan diterima");
    while (client.connected()) {
      if (client.available()) {
        String req = client.readStringUntil('\r');
        client.readStringUntil('\n');
        
        if (req.indexOf("GET /capture") >= 0) {
          Serial.println("Ambil gambar...");

          // Matikan flash dulu (pastikan kondisi awal)
          digitalWrite(FLASH_GPIO_NUM, LOW);
          delay(100);

          // Ambil gambar
          camera_fb_t * fb = esp_camera_fb_get();
          if (!fb) {
            Serial.println("Gagal ambil gambar");
            client.println("HTTP/1.1 500 Internal Server Error");
            return;
          }

          // Kirim respon HTTP
          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: image/jpeg");
          client.println("Content-Length: " + String(fb->len));
          client.println();
          client.write(fb->buf, fb->len);
          esp_camera_fb_return(fb);

          // Flash tetap mati (bisa aktifkan jika perlu)
          digitalWrite(FLASH_GPIO_NUM, LOW);
        } else {
          client.println("HTTP/1.1 404 Not Found");
          client.println();
        }
        break;
      }
    }
    delay(1);
    client.stop();
    Serial.println("Koneksi ditutup");
  }
}