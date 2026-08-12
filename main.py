import asyncio
import logging
import json
from datetime import datetime, timedelta
import pytz
import random
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# === KONFIGURASI ===
API_TOKEN = '8609265918:AAHTbLGxdKd3xdL6CrPXTlppUva-ISPb6GU'
ADMIN_IDS = [8036153537, 8851258385]
CHAT_ID = -1003113573881
THREAD_ID = 10511

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
sent_today = set()
reminder_sent = set()

def is_admin(user_id):
    return user_id in ADMIN_IDS  

def load_schedule():
    with open('jadwal.json') as f:
        return json.load(f)

def generate_prediction():
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)
    hari = now.strftime("%A")
    tgl = now.strftime("%d %B %Y")
    hari_indo = {
        'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
        'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
    }
    header = (
        f"🎰 <b>PREDIKSI TOGEL HARI INI</b>\n"
        f"🗓️ {hari_indo[hari]}, {tgl}\n\n"
    )
    bb = ''.join(random.sample('0123456789', 5))
    colok = ' • '.join(random.sample('0123456789', 2))
    sial = random.choice('0123456789')
    d2 = ' '.join([''.join(random.choices('0123456789', k=2)) for _ in range(8)])
    d3 = ''.join(random.choices('0123456789', k=3))
    shio = random.choice([
        'Tikus', 'Kerbau', 'Harimau', 'Kelinci', 'Naga', 'Ular',
        'Kuda', 'Kambing', 'Monyet', 'Ayam', 'Anjing', 'Babi'
    ])
    return (
        header +
        f"🔢 <b>BB Fullset:</b> {bb}\n"
        f"🎯 <b>Colok Jitu:</b> {colok}\n"
        f"❌ <b>Angka Sial:</b> {sial}\n\n"
        f"🎲 <b>2D:</b>\n{d2}\n\n"
        f"💥 <b>3D:</b> {d3}\n"
        f"🐉 <b>Shio:</b> {shio}\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🔮 Utamakan Prediksi Sendiri . Main bijak dan sadar cuan."
    )

async def send_prediction(pasaran):
    teks = f"<b>🧿 PREDIKSI PASARAN {pasaran.upper()}</b>\n\n{generate_prediction()}"
    buttons = types.InlineKeyboardMarkup()
    buttons.add(
        types.InlineKeyboardButton("🎮 LOGIN BANDARTOTO", url="https://bandartotopola.com/"),
        types.InlineKeyboardButton("🎁 PROMO BANDARTOTO", url="https://promosi2.bandartotoprediksi.com/")
    )
    try:
        msg = await bot.send_message(chat_id=CHAT_ID, message_thread_id=THREAD_ID, text=teks, reply_markup=buttons)
        await bot.pin_chat_message(chat_id=CHAT_ID, message_id=msg.message_id, disable_notification=True)
        await bot.send_message(ADMIN_IDS[0], f"✅ Prediksi pasaran <b>{pasaran}</b> berhasil dikirim ke grup thread.")
    except Exception as e:
        await bot.send_message(ADMIN_IDS[0], f"❌ Gagal kirim ke grup thread: {e}")
    sent_today.add(pasaran)

async def scheduler():
    tz = pytz.timezone("Asia/Jakarta")
    schedule = load_schedule()
    while True:
        now = datetime.now(tz)
        for pasaran, jam_tutup in schedule.items():
            try:
                result_time = datetime.strptime(jam_tutup, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
                prediksi_time = result_time - timedelta(hours=1)
                reminder_time = result_time - timedelta(minutes=10)

                if now.strftime("%H:%M") == prediksi_time.strftime("%H:%M") and pasaran not in sent_today:
                    await send_prediction(pasaran)
                elif now.strftime("%H:%M") == reminder_time.strftime("%H:%M") and pasaran not in reminder_sent:
                    teks = (
                        f"⏰ <b>10 Menit Menuju Result</b>\n"
                        f"Pasaran <b>{pasaran.upper()}</b> akan segera keluar!\n"
                        "Siapkan saldo & prediksi terbaikmu 🎯"
                    )
                    buttons = types.InlineKeyboardMarkup()
                    buttons.add(
                        types.InlineKeyboardButton("🎮 LOGIN RUPIAHTOTO", url="https://rupiahtotoplay.com/"),
                        types.InlineKeyboardButton("🎁 PROMO RUPIAHTOTO", url="https://prediksi3.rupiahtotoprediksi.com/")
                    )
                    await bot.send_message(chat_id=CHAT_ID, message_thread_id=THREAD_ID, text=teks, reply_markup=buttons)
                    reminder_sent.add(pasaran)
            except Exception as e:
                await bot.send_message(ADMIN_IDS[0], f"❌ Gagal proses pasaran <b>{pasaran}</b>: {e}")
        await asyncio.sleep(60)

async def reset_daily():
    global sent_today, reminder_sent
    tz = pytz.timezone("Asia/Jakarta")
    while True:
        now = datetime.now(tz)
        if now.strftime("%H:%M") == "00:00":
            sent_today.clear()
            reminder_sent.clear()
            await bot.send_message(ADMIN_IDS[0], "🔁 Reset data harian sukses.")
            await asyncio.sleep(65)
        await asyncio.sleep(30)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🛑 Silahkan chat Admin Rupiahtoto @rupiahtoto ")
        return
    await message.reply("✅ Bot prediksi aktif. Tunggu jadwal otomatis atau kirim manual dengan /kirim [PASARAN].")

@dp.message_handler(commands=['kirim'])
async def cmd_kirim_manual(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🚫 Hanya admin yang bisa pakai perintah ini.")
        return
    try:
        args = message.get_args().strip().upper()
        jadwal = load_schedule()
        if args in jadwal:
            if args in sent_today:
                await message.reply(f"📛 Pasaran <b>{args}</b> sudah dikirim hari ini.")
            else:
                await send_prediction(args)
                await message.reply(f"🚀 Prediksi pasaran <b>{args}</b> berhasil dikirim.")
        else:
            await message.reply("❌ Pasaran tidak ditemukan.")
    except Exception as e:
        await message.reply(f"⚠️ Gagal kirim prediksi: {e}")

@dp.message_handler(commands=['cekpasaran'])
async def cmd_cekpasaran(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🛑 Akses ditolak. Fitur ini cuma buat admin.")
        return
    jadwal = load_schedule()
    daftar = "\n".join([f"• {k} ({v})" for k, v in sorted(jadwal.items())])
    await message.reply(f"<b>📋 Daftar Pasaran & Jam Tutup:</b>\n\n{daftar}")

@dp.message_handler(commands=['infopasaran'])
async def cmd_infopasaran(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🛑 Cuma admin yang bisa lihat info ini.")
        return
    if not sent_today:
        await message.reply("📭 Belum ada pasaran yang dikirim hari ini.")
    else:
        daftar = "\n".join([f"• {p}" for p in sorted(sent_today)])
        await message.reply(f"<b>📬 Pasaran yang sudah dikirim hari ini:</b>\n\n{daftar}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    loop.create_task(reset_daily())
    executor.start_polling(dp, skip_updates=True)
