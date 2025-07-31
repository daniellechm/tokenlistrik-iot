# tokenlistrik-iot

## 📘 Deskripsi Proyek
Sistem ini dirancang untuk membantu pengguna untuk melakukan pengisian dan monitoring **sisa token listrik&** secara otomatis menggunakan kombinasi **ESP32**, **ESP32-CAM**, **RTC DS3231**, dan **OCR (Optical Character Recognition)**.
Untuk melakukan pengisian ini melalui **Blynk**, dan monitoring ini melalui **Telegram Bot**, pengguna dapat melakukan input nomor pengisian token listrik pada Blynk dan pengguna dapat mengirim perintah atau mengatur jadwal pengecekan token. Gambar dari layar 7-segment diambil oleh ESP32-CAM, diproses oleh PC dengan Python, dan hasilnya dikirim kembali melalui Telegram serta disimpan ke Firebase.


## 🧩 Komponen Sistem
- ESP32 38 Pin (Mikrokontroler utama)
- ESP32-CAM (Pengambil gambar layar meteran)
- RTC DS3231 (Real-time clock untuk penjadwalan)
- PC (menjalankan skrip Python & OCR)
- Blynk
- Telegram Bot
- Firebase Realtime Database

## 🚀 Fitur Utama
- ⬇️ Pengisian nomor token listrik melalui Blynk dan menggerakkan solenoid sebagai penekan keypad pada Meteran
- 📸 Ambil gambar angka dari meteran token listrik menggunakan ESP32-CAM
- 🕒 Penjadwalan pengecekan otomatis berdasarkan jam dari RTC DS3231
- 🤖 Perintah manual `/cektoken` melalui Telegram
- 📤 Kirim hasil OCR ke Firebase dan Telegram
- 🌐 Komunikasi ESP32 ke PC via HTTP GET

## 🗂 Struktur File
1. bot_ocr_esp32_firebase.py         # Script utama Python untuk kamera, OCR, Firebase, dan Telegram
   - firebase_config.json            # Konfigurasi koneksi ke Firebase
   - ds3231.ino                      # Kode Arduino untuk ESP32 + RTC DS3231
   - image.jpg                       # Gambar token yang akan diproses

## 📷 Alur Sistem Pengisian Token Listrik
1. Pengguna melakukan input nomor pengisian token listrik pada TextInput melalui Blynk
2. Pengguna menekan tombol Enter pada Keyboard
3. Solenoid bergerak sesuai nomor yang dimasukkan oleh pengguna

## 📷 Alur Sistem Monitoring Sisa Token
1. **Pengguna kirim perintah** `/cektoken` atau sistem aktif otomatis berdasarkan RTC.
2. ESP32 mengirim perintah ke ESP32-CAM untuk mengambil **gambar layar 7-segment**.
3. Gambar dikirim ke PC melalui HTTP → diproses dengan **OCR (Tesseract / OpenCV)**.
4. Hasil angka dikirim ke:
   - Firebase Realtime Database
   - Telegram Bot pengguna

## 💬 Contoh Output Telegram
pengecekan otomatis jam 12:00
sisa token kamu:
127

## 🔧 Setup dan Instalasi
### 1. Siapkan Firebase
- Buat project di Firebase
- Tambahkan Realtime Database
- Unduh kredensial admin (`firebase_config.json`)

### 2. Buat Telegram Bot
- Cari `@BotFather` di Telegram
- Buat bot baru → Simpan Token

### 3. Instal Dependensi Python
```bash
pip install pyTelegramBotAPI firebase-admin opencv-python pytesseract flask requests

Pastikan Tesseract OCR sudah terinstal:
Windows: https://github.com/tesseract-ocr/tesseract
Tambahkan PATH Tesseract ke environment variable jika diperlukan

### 4. Upload ds3231.ino ke ESP32
- Pastikan koneksi RTC DS3231 benar
- Ganti WiFi SSID dan password di sketch
- Pastikan URL PC sudah sesuai (http://<IP_PC>:<PORT>/autocapture)
