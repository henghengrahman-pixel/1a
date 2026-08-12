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

# Dapatkan waktu WIB (UTC+7)
def get_wib_time():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Periode jam gacor 30 menit
def get_gacor_period():
    now = get_wib_time()
    start = now.replace(second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    return start.strftime("%H:%M"), end.strftime("%H:%M")

# Deteksi maintenance Kamis 07:00–09:00 WIB
def is_maintenance():
    now = get_wib_time()
    return now.weekday() == 3 and 7 <= now.hour < 9

# Pesan maintenance
def generate_maintenance_message():
    return (
        "<b>🛠 MAINTENANCE SEMENTARA</b>\n\n"
        "Mohon maaf, Website <b>OmTogel</b> sedang dalam pemeliharaan rutin "
        "untuk meningkatkan kenyamanan bermain.\n\n"
        "🕓 Akan kembali normal pukul <b>09:00 WIB</b>\n"
        "Terima kasih atas pengertiannya 🙏"
    )

# Generate pesan RTP GACOR
def generate_message():
    start, end = get_gacor_period()
    header = (
        "<b>🎰 RTP SLOT GACOR HARI INI</b>\n"
        f"🕓 JAM GACOR : <b>{start} - {end} WIB</b>\n\n"
    )

    def bar(val):
        filled = max(0, min(10, round((val - 90) / 10 * 10)))
        return "█" * filled + "░" * (10 - filled)

    games = []
    for g in random.sample(GAMES, 4):
        rtp = random.randint(92, 98)
        games.append((g["name"].upper(), g["provider"].upper(), rtp))
    games.sort(key=lambda x: x[2], reverse=True)

    body = ""
    for name, prov, rtp in games:
        emoji = "🔥" if rtp >= 97 else ("⚡️" if rtp >= 95 else "✨")
        body += f"{emoji} <b>{name}</b> — <i>{prov}</i>\n🎯 {rtp}% {bar(rtp)}\n\n"

    footer = "🚀 Waktunya Panen Menang di OmTogel!! Jaga Profit!!"
    return header + body + footer

# Kirim pesan ke semua channel
async def send_to_channels():
    if is_maintenance():
        message = generate_maintenance_message()
        for channel in CHANNELS:
            await bot.send_message(
                chat_id=channel,
                text=message,
                parse_mode=ParseMode.HTML
            )
    else:
        message = generate_message()
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=BUTTONS['play'], url=BUTTONS['play_url'])],
            [InlineKeyboardButton(text=BUTTONS['promo'], url=BUTTONS['promo_url'])]
        ])
        for channel in CHANNELS:
            await bot.send_message(
                chat_id=channel,
                text=message,
                parse_mode=ParseMode.HTML,
                reply_markup=buttons
            )

# Jalankan scheduler
async def start_scheduler():
    scheduler.add_job(send_to_channels, 'interval', minutes=30)
    scheduler.start()
    await send_to_channels()  # kirim langsung pertama
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(start_scheduler())
