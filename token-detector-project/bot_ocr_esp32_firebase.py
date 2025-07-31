from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import threading
import requests
import cv2
import numpy as np
import pyrebase
import json
import time
import asyncio
from datetime import datetime

# === Konfigurasi ===
ESP32_CAM_URL = "http://192.168.0.0/capture"
BOT_TOKEN = "*"

with open("firebase_config.json") as f:
    config = json.load(f)

firebase = pyrebase.initialize_app(config)
db = firebase.database()

DIGITS_LOOKUP = {
    (1,1,1,1,1,1,0): '0',
    (1,1,0,0,0,0,0): '1',
    (1,0,1,1,0,1,1): '2',
    (1,1,1,0,0,1,1): '3',
    (1,1,0,0,1,0,1): '4',
    (0,1,1,0,1,1,1): '5',
    (0,1,1,1,1,1,1): '6',
    (1,1,0,0,0,1,0): '7',
    (1,1,1,1,1,1,1): '8',
    (1,1,1,0,1,1,1): '9'
}

# === OCR Constants ===
H_W_Ratio = 1.9
THRESHOLD = 35
arc_tan_theta = 6.0

# === Global for dynamic chat ID ===
chat_id_pengguna = None

def preprocess(img, threshold=35):
    clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(6,6))
    img = clahe.apply(img)
    dst = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 127, threshold)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (5,5))
    dst = cv2.morphologyEx(dst, cv2.MORPH_CLOSE, kernel)
    dst = cv2.morphologyEx(dst, cv2.MORPH_OPEN, kernel)
    return dst

def helper_extract(one_d_array, threshold=20):
    res, flag, temp = [], 0, 0
    for i in range(len(one_d_array)):
        if one_d_array[i] < 12 * 255:
            if flag > threshold:
                start, end = i - flag, i
                temp = end
                if end - start > 20:
                    res.append((start, end))
            flag = 0
        else:
            flag += 1
    else:
        if flag > threshold:
            start, end = temp, len(one_d_array)
            if end - start > 50:
                res.append((start, end))
    return res

def find_digits_positions(img, reserved_threshold=20):
    digits_positions = []
    img_array = np.sum(img, axis=0)
    horizon_position = helper_extract(img_array, threshold=reserved_threshold)
    img_array = np.sum(img, axis=1)
    vertical_position = helper_extract(img_array, threshold=reserved_threshold * 4)
    if len(vertical_position) > 1:
        vertical_position = [(vertical_position[0][0], vertical_position[-1][1])]
    for h in horizon_position:
        for v in vertical_position:
            digits_positions.append(list(zip(h, v)))
    return digits_positions

def recognize_digits(digits_positions, input_img):
    digits = []
    for c in digits_positions:
        x0, y0 = c[0]
        x1, y1 = c[1]
        roi = input_img[y0:y1, x0:x1]
        h, w = roi.shape
        suppose_W = max(1, int(h / H_W_Ratio))
        if w < suppose_W / 2:
            x0 = x0 + w - suppose_W
            roi = input_img[y0:y1, x0:x1]
            w = roi.shape[1]

        center_y = h // 2
        quater_y_1 = h // 4
        quater_y_3 = quater_y_1 * 3
        center_x = w // 2
        line_width = 5
        width = (max(int(w * 0.15), 1) + max(int(h * 0.15), 1)) // 2
        small_delta = int(h / arc_tan_theta) // 4

        segments = [
            ((w-2*width, quater_y_1-line_width), (w, quater_y_1+line_width)),
            ((w-2*width, quater_y_3-line_width), (w, quater_y_3+line_width)),
            ((center_x-line_width-small_delta, h-2*width), (center_x-small_delta+line_width, h)),
            ((0, quater_y_3-line_width), (2*width, quater_y_3+line_width)),
            ((0, quater_y_1-line_width), (2*width, quater_y_1+line_width)),
            ((center_x-line_width, 0), (center_x+line_width, 2*width)),
            ((center_x-line_width, center_y-line_width), (center_x+line_width, center_y+line_width)),
        ]
        on = [0] * len(segments)
        for (i, ((xa, ya), (xb, yb))) in enumerate(segments):
            seg_roi = roi[ya:yb, xa:xb]
            total = cv2.countNonZero(seg_roi)
            area = (xb - xa) * (yb - ya) * 0.9
            if total / float(area) > 0.25:
                on[i] = 1

        digit = DIGITS_LOOKUP.get(tuple(on), "*")
        digits.append(str(digit))
    return ''.join(digits)

def proses_token(pengecekan_otomatis=False):
    try:
        response = requests.get(ESP32_CAM_URL, timeout=5)
        if response.status_code != 200:
            print("❌ Gagal ambil gambar dari ESP32-CAM")
            return None

        with open("image.jpg", "wb") as f:
            f.write(response.content)

        image = cv2.imread("image.jpg")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        processed = preprocess(gray, THRESHOLD)
        digit_pos = find_digits_positions(processed)
        if not digit_pos:
            print("⚠️ Tidak ditemukan digit.")
            return None

        hasil = recognize_digits(digit_pos, processed)
        data = {"angka": hasil}
        db.child("ncr_token").child("terakhir").set(data)
        db.child("ncr_token").child("riwayat").push(data)

        print(f"✅ Hasil OCR: {hasil}")
        return hasil
    except Exception as e:
        print("❌ Error saat proses token:", e)
        return None

# === Telegram Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id_pengguna
    chat_id_pengguna = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id_pengguna, text="✅ Bot aktif.")

async def cek_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id_pengguna
    chat_id_pengguna = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id_pengguna, text="📸 Mengambil gambar...")
    hasil = proses_token()
    if hasil:
        await context.bot.send_message(chat_id=chat_id_pengguna, text=f"✅ Sisa token kamu:\n`{hasil}`", parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=chat_id_pengguna, text="❌ Gagal membaca angka dari gambar.")

async def kirim_gambar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id_pengguna
    chat_id_pengguna = update.effective_chat.id
    try:
        with open("image.jpg", "rb") as img:
            await context.bot.send_photo(chat_id=chat_id_pengguna, photo=InputFile(img), caption="📷 Gambar terakhir")
    except FileNotFoundError:
        await context.bot.send_message(chat_id=chat_id_pengguna, text="❌ Gambar belum tersedia.")

async def set_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id_pengguna
    chat_id_pengguna = update.effective_chat.id
    try:
        if len(context.args) != 2:
            raise ValueError
        jam1, menit1 = map(int, context.args[0].split(":"))
        jam2, menit2 = map(int, context.args[1].split(":"))
        db.child("jadwal").set({
            "jam1": jam1, "menit1": menit1,
            "jam2": jam2, "menit2": menit2
        })
        await context.bot.send_message(chat_id=chat_id_pengguna, text=f"✅ Jadwal diperbarui:\n{jam1:02d}:{menit1:02d} dan {jam2:02d}:{menit2:02d}")
    except:
        await context.bot.send_message(chat_id=chat_id_pengguna, text="❌ Format salah. Gunakan:\n`/setjadwal 12:00 23:59`", parse_mode="Markdown")

def pengecekan_otomatis_loop():
    while True:
        try:
            now = datetime.now()
            time_now_str = now.strftime("%Y-%m-%d %H:%M")
            jam = now.hour
            menit = now.minute
            jadwal = db.child("jadwal").get().val()
            if not jadwal:
                time.sleep(10)
                continue
            for i in [1, 2]:
                jam_db = jadwal.get(f"jam{i}")
                menit_db = jadwal.get(f"menit{i}")
                if jam == jam_db and menit == menit_db:
                    terakhir_cek = db.child("ncr_token").child("terakhir_cek").child(f"jadwal{i}").get().val()
                    if terakhir_cek != time_now_str:
                        hasil = proses_token(pengecekan_otomatis=True)
                        if hasil:
                            asyncio.run(send_otomatis_telegram(jam, menit, hasil))
                            db.child("ncr_token").child("terakhir_cek").child(f"jadwal{i}").set(time_now_str)
        except Exception as e:
            print("❌ Error pengecekan otomatis:", e)
        time.sleep(20)

async def send_otomatis_telegram(jam, menit, hasil):
    try:
        if chat_id_pengguna:
            await telegram_app.bot.send_message(
                chat_id=chat_id_pengguna,
                text=f"🤖 Pengecekan otomatis jam {jam:02d}:{menit:02d}\nSisa token kamu:\n`{hasil}`",
                parse_mode="Markdown"
            )
        else:
            print("⚠️ Bot belum tahu chat_id pengguna.")
    except Exception as e:
        print("❌ Gagal kirim otomatis:", e)

# === Start Bot ===
if __name__ == "__main__":
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("cektoken", cek_token))
    telegram_app.add_handler(CommandHandler("kirimgambar", kirim_gambar))
    telegram_app.add_handler(CommandHandler("setjadwal", set_jadwal))

    threading.Thread(target=pengecekan_otomatis_loop, daemon=True).start()

    print("🤖 Bot Telegram aktif | 🔁 Menunggu jadwal otomatis")
    telegram_app.run_polling()
