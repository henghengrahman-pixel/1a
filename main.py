import random
import asyncio
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from config import BOT_TOKEN, CHANNELS, BUTTONS
from game_list import GAMES


bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()


# ==========================================
# DAPATKAN WAKTU WIB (UTC+7)
# ==========================================
def get_wib_time():
    return datetime.now(timezone.utc) + timedelta(hours=7)


# ==========================================
# PERIODE JAM GACOR 30 MENIT
# ==========================================
def get_gacor_period():
    now = get_wib_time()

    start = now.replace(
        second=0,
        microsecond=0
    )

    end = start + timedelta(minutes=30)

    return (
        start.strftime("%H:%M"),
        end.strftime("%H:%M")
    )


# ==========================================
# GENERATE PESAN RTP GACOR
# ==========================================
def generate_message():
    start, end = get_gacor_period()

    header = (
        "<b>🎰 RTP SLOT GACOR HARI INI</b>\n"
        f"🕓 JAM GACOR : <b>{start} - {end} WIB</b>\n\n"
    )

    def bar(val):
        filled = max(
            0,
            min(
                10,
                round((val - 90) / 10 * 10)
            )
        )

        return "█" * filled + "░" * (10 - filled)

    games = []

    # Aman jika jumlah game kurang dari 4
    total_games = min(4, len(GAMES))

    for g in random.sample(GAMES, total_games):
        rtp = random.randint(92, 98)

        games.append(
            (
                g["name"].upper(),
                g["provider"].upper(),
                rtp
            )
        )

    # Urutkan RTP tertinggi
    games.sort(
        key=lambda x: x[2],
        reverse=True
    )

    body = ""

    for name, provider, rtp in games:

        if rtp >= 97:
            emoji = "🔥"
        elif rtp >= 95:
            emoji = "⚡️"
        else:
            emoji = "✨"

        body += (
            f"{emoji} <b>{name}</b> — <i>{provider}</i>\n"
            f"🎯 {rtp}% {bar(rtp)}\n\n"
        )

    footer = (
        "🚀 Waktunya Panen Menang di BANDARTOTO!! Jaga Profit!!"
    )

    return header + body + footer


# ==========================================
# GENERATE BUTTON
# ==========================================
def generate_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=BUTTONS["play"],
                url=BUTTONS["play_url"]
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS["promo"],
                url=BUTTONS["promo_url"]
            )
        ]
    ])


# ==========================================
# KIRIM PESAN KE SEMUA CHANNEL
# ==========================================
async def send_to_channels():
    message = generate_message()
    buttons = generate_buttons()

    for channel in CHANNELS:
        try:
            await bot.send_message(
                chat_id=channel,
                text=message,
                parse_mode=ParseMode.HTML,
                reply_markup=buttons,
                disable_web_page_preview=True
            )

            print(
                f"[SUCCESS] "
                f"{get_wib_time().strftime('%d-%m-%Y %H:%M:%S')} WIB "
                f"-> {channel}"
            )

        except Exception as error:
            print(
                f"[ERROR] Gagal kirim ke {channel}: {error}"
            )


# ==========================================
# JALANKAN SCHEDULER
# ==========================================
async def start_scheduler():

    # Kirim setiap 30 menit
    scheduler.add_job(
        send_to_channels,
        trigger="interval",
        minutes=30,
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

    print("======================================")
    print(" BOT RTP BANDARTOTO AKTIF")
    print(" INTERVAL : 30 MENIT")
    print(" MAINTENANCE : DIHAPUS")
    print("======================================")

    # Kirim langsung saat bot pertama kali hidup
    await send_to_channels()

    try:
        while True:
            await asyncio.sleep(3600)

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    asyncio.run(start_scheduler())
