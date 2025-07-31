# tokenlistrik-iot

## 📘 Deskripsi Proyek
Sistem ini dirancang untuk membantu pengguna mengecek **sisa token listrik** secara otomatis menggunakan kombinasi **ESP32**, **ESP32-CAM**, **RTC DS3231**, dan **OCR (Optical Character Recognition)**.  
Melalui **Telegram Bot**, pengguna dapat mengirim perintah atau mengatur jadwal pengecekan token. Gambar dari layar 7-segment diambil oleh ESP32-CAM, diproses oleh PC dengan Python, dan hasilnya dikirim kembali melalui Telegram serta disimpan ke Firebase.

## 🧩 Komponen Sistem
- ESP32 38 Pin (Mikrokontroler utama)
- ESP32-CAM (Pengambil gambar layar meteran)
- RTC DS3231 (Real-time clock untuk penjadwalan)
- PC (menjalankan skrip Python & OCR)
- Telegram Bot
- Firebase Realtime Database

## 🚀 Fitur Utama
- 📸 Ambil gambar angka dari meteran token listrik menggunakan ESP32-CAM
- 🕒 Penjadwalan pengecekan otomatis berdasarkan jam dari RTC DS3231
- 🤖 Perintah manual `/cektoken` melalui Telegram
- 📤 Kirim hasil OCR ke Firebase dan Telegram
- 🌐 Komunikasi ESP32 ke PC via HTTP GET

## 🗂 Struktur File
