import asyncio
import json
import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ==========================================
# KONFIGURASI
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
API_TOKEN = os.getenv("BOT_TOKEN", "8609265918:AAHTbLGxdKd3xdL6CrPXTlppUva-ISPb6GU").strip()
ADMIN_IDS = [8036153537, 8851258385]
CHAT_ID = -1003113573881
THREAD_ID = 10511

if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN kosong. Isi environment variable BOT_TOKEN di Railway.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

sent_today = set()
reminder_sent = set()
background_tasks = []


def is_admin(user_id):
    return user_id in ADMIN_IDS


def load_schedule():
    schedule_file = BASE_DIR / "jadwal.json"
    with schedule_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("jadwal.json harus berupa object JSON {PASARAN: HH:MM}")

    for pasaran, jam in data.items():
        datetime.strptime(jam, "%H:%M")

    return data


def generate_prediction():
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)
    hari = now.strftime("%A")
    tgl = now.strftime("%d %B %Y")

    hari_indo = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu",
    }

    header = (
        "🎰 <b>PREDIKSI TOGEL HARI INI</b>\n"
        f"🗓️ {hari_indo.get(hari, hari)}, {tgl}\n\n"
    )

    bb = "".join(random.sample("0123456789", 5))
    colok = " • ".join(random.sample("0123456789", 2))
    sial = random.choice("0123456789")
    d2 = " ".join("".join(random.choices("0123456789", k=2)) for _ in range(8))
    d3 = "".join(random.choices("0123456789", k=3))
    shio = random.choice([
        "Tikus", "Kerbau", "Harimau", "Kelinci", "Naga", "Ular",
        "Kuda", "Kambing", "Monyet", "Ayam", "Anjing", "Babi",
    ])

    return (
        header
        + f"🔢 <b>BB Fullset:</b> {bb}\n"
        + f"🎯 <b>Colok Jitu:</b> {colok}\n"
        + f"❌ <b>Angka Sial:</b> {sial}\n\n"
        + f"🎲 <b>2D:</b>\n{d2}\n\n"
        + f"💥 <b>3D:</b> {d3}\n"
        + f"🐉 <b>Shio:</b> {shio}\n\n"
        + "━━━━━━━━━━━━━━━\n"
        + "🔮 Utamakan Prediksi Sendiri . Main bijak dan sadar cuan."
    )


async def notify_admin(text):
    try:
        await bot.send_message(ADMIN_IDS[0], text)
    except Exception as exc:
        logger.exception("Gagal mengirim notifikasi admin: %s", exc)


async def send_prediction(pasaran):
    teks = f"<b>🧿 PREDIKSI PASARAN {pasaran.upper()}</b>\n\n{generate_prediction()}"

    buttons = types.InlineKeyboardMarkup(row_width=2)
    buttons.add(
        types.InlineKeyboardButton(
            "🎮 LOGIN BANDARTOTO",
            url="https://bandartotopola.com/",
        ),
        types.InlineKeyboardButton(
            "🎁 PROMO BANDARTOTO",
            url="https://promosi2.bandartotoprediksi.com/",
        ),
    )

    try:
        msg = await bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=THREAD_ID,
            text=teks,
            reply_markup=buttons,
        )
        await bot.pin_chat_message(
            chat_id=CHAT_ID,
            message_id=msg.message_id,
            disable_notification=True,
        )
    except Exception as exc:
        logger.exception("Gagal kirim prediksi %s: %s", pasaran, exc)
        await notify_admin(f"❌ Gagal kirim ke grup thread: {exc}")
        return False

    sent_today.add(pasaran)
    await notify_admin(
        f"✅ Prediksi pasaran <b>{pasaran}</b> berhasil dikirim ke grup thread."
    )
    return True


async def scheduler_loop():
    tz = pytz.timezone("Asia/Jakarta")

    while True:
        try:
            schedule = load_schedule()
            now = datetime.now(tz)

            for pasaran, jam_tutup in schedule.items():
                try:
                    result_time = tz.localize(
                        datetime.combine(
                            now.date(),
                            datetime.strptime(jam_tutup, "%H:%M").time(),
                        )
                    )
                    prediksi_time = result_time - timedelta(hours=1)
                    reminder_time = result_time - timedelta(minutes=10)

                    current_hm = now.strftime("%H:%M")

                    if (
                        current_hm == prediksi_time.strftime("%H:%M")
                        and pasaran not in sent_today
                    ):
                        await send_prediction(pasaran)

                    elif (
                        current_hm == reminder_time.strftime("%H:%M")
                        and pasaran not in reminder_sent
                    ):
                        teks = (
                            "⏰ <b>10 Menit Menuju Result</b>\n"
                            f"Pasaran <b>{pasaran.upper()}</b> akan segera keluar!\n"
                            "Siapkan saldo & prediksi terbaikmu 🎯"
                        )

                        buttons = types.InlineKeyboardMarkup(row_width=2)
                        buttons.add(
                            types.InlineKeyboardButton(
                                "🎮 LOGIN RUPIAHTOTO",
                                url="https://rupiahtotoplay.com/",
                            ),
                            types.InlineKeyboardButton(
                                "🎁 PROMO RUPIAHTOTO",
                                url="https://prediksi3.rupiahtotoprediksi.com/",
                            ),
                        )

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            message_thread_id=THREAD_ID,
                            text=teks,
                            reply_markup=buttons,
                        )
                        reminder_sent.add(pasaran)

                except Exception as exc:
                    logger.exception("Gagal proses pasaran %s: %s", pasaran, exc)
                    await notify_admin(
                        f"❌ Gagal proses pasaran <b>{pasaran}</b>: {exc}"
                    )

        except Exception as exc:
            logger.exception("Scheduler error: %s", exc)
            await notify_admin(f"❌ Scheduler error: {exc}")

        await asyncio.sleep(30)


async def reset_daily_loop():
    tz = pytz.timezone("Asia/Jakarta")
    last_reset_date = None

    while True:
        now = datetime.now(tz)

        if now.hour == 0 and now.minute == 0 and last_reset_date != now.date():
            sent_today.clear()
            reminder_sent.clear()
            last_reset_date = now.date()
            logger.info("Reset data harian sukses")
            await notify_admin("🔁 Reset data harian sukses.")

        await asyncio.sleep(20)


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🛑 Silahkan chat Admin Rupiahtoto @rupiahtoto ")
        return

    await message.reply(
        "✅ Bot prediksi aktif. Tunggu jadwal otomatis atau kirim manual "
        "dengan /kirim [PASARAN]."
    )


@dp.message_handler(commands=["kirim"])
async def cmd_kirim_manual(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🚫 Hanya admin yang bisa pakai perintah ini.")
        return

    try:
        args = message.get_args().strip().upper()
        jadwal = load_schedule()

        if not args:
            await message.reply("Gunakan: <code>/kirim NAMA PASARAN</code>")
            return

        if args not in jadwal:
            await message.reply("❌ Pasaran tidak ditemukan.")
            return

        if args in sent_today:
            await message.reply(f"📛 Pasaran <b>{args}</b> sudah dikirim hari ini.")
            return

        success = await send_prediction(args)
        if success:
            await message.reply(f"🚀 Prediksi pasaran <b>{args}</b> berhasil dikirim.")
        else:
            await message.reply(f"❌ Prediksi pasaran <b>{args}</b> gagal dikirim.")

    except Exception as exc:
        logger.exception("Perintah /kirim gagal: %s", exc)
        await message.reply(f"⚠️ Gagal kirim prediksi: {exc}")


@dp.message_handler(commands=["cekpasaran"])
async def cmd_cekpasaran(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🛑 Akses ditolak. Fitur ini cuma buat admin.")
        return

    jadwal = load_schedule()
    daftar = "\n".join(f"• {k} ({v})" for k, v in sorted(jadwal.items()))
    await message.reply(f"<b>📋 Daftar Pasaran & Jam Tutup:</b>\n\n{daftar}")


@dp.message_handler(commands=["infopasaran"])
async def cmd_infopasaran(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("🛑 Cuma admin yang bisa lihat info ini.")
        return

    if not sent_today:
        await message.reply("📭 Belum ada pasaran yang dikirim hari ini.")
        return

    daftar = "\n".join(f"• {p}" for p in sorted(sent_today))
    await message.reply(
        f"<b>📬 Pasaran yang sudah dikirim hari ini:</b>\n\n{daftar}"
    )


async def on_startup(_dispatcher):
    # Validasi file jadwal saat startup supaya error langsung terlihat di log.
    schedule = load_schedule()
    logger.info("Bot startup. %d pasaran dimuat dari jadwal.json", len(schedule))

    background_tasks.append(asyncio.create_task(scheduler_loop()))
    background_tasks.append(asyncio.create_task(reset_daily_loop()))


async def on_shutdown(_dispatcher):
    for task in background_tasks:
        task.cancel()

    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)

    await bot.session.close()
    logger.info("Bot shutdown selesai")


if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )
