import os
import asyncio
import logging
from datetime import datetime

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIGURATION
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Default location: Chuadanga
LATITUDE = 23.6401
LONGITUDE = 88.8410
LOCATION_NAME = "চুয়াডাঙ্গা"

TIMEZONE = "Asia/Dhaka"

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# WEATHER CODE → BANGLA
# =========================

WEATHER_CODES = {
    0: "☀️ পরিষ্কার আকাশ",
    1: "🌤️ প্রধানত পরিষ্কার",
    2: "⛅ আংশিক মেঘলা",
    3: "☁️ মেঘলা",
    45: "🌫️ কুয়াশা",
    48: "🌫️ ঘন কুয়াশা",
    51: "🌦️ হালকা গুঁড়ি গুঁড়ি বৃষ্টি",
    53: "🌦️ মাঝারি গুঁড়ি গুঁড়ি বৃষ্টি",
    55: "🌧️ ঘন গুঁড়ি গুঁড়ি বৃষ্টি",
    61: "🌦️ হালকা বৃষ্টি",
    63: "🌧️ মাঝারি বৃষ্টি",
    65: "🌧️ ভারী বৃষ্টি",
    71: "🌨️ হালকা তুষারপাত",
    73: "🌨️ মাঝারি তুষারপাত",
    75: "❄️ ভারী তুষারপাত",
    80: "🌦️ হালকা বৃষ্টির ঝাপটা",
    81: "🌧️ মাঝারি বৃষ্টির ঝাপটা",
    82: "⛈️ ভারী বৃষ্টির ঝাপটা",
    95: "⛈️ বজ্রঝড়",
    96: "⛈️ বজ্রঝড় ও শিলাবৃষ্টি",
    99: "⛈️ প্রবল বজ্রঝড় ও শিলাবৃষ্টি",
}


# =========================
# GET WEATHER
# =========================

def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "hourly": (
            "temperature_2m,"
            "precipitation_probability,"
            "rain,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": TIMEZONE,
        "forecast_days": 2,
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    return response.json()


# =========================
# FORMAT WEATHER MESSAGE
# =========================

def create_weather_message():

    data = get_weather()

    current = data["current"]

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    precipitation = current["precipitation"]
    rain = current["rain"]
    wind = current["wind_speed_10m"]
    weather_code = current["weather_code"]

    weather_text = WEATHER_CODES.get(
        weather_code,
        "🌦️ পরিবর্তনশীল আবহাওয়া"
    )

    now = datetime.now()

    message = f"""
🌦️ <b>বাংলা আবহাওয়া আপডেট</b>

📍 এলাকা: <b>{LOCATION_NAME}</b>
🕐 সময়: {now.strftime("%d-%m-%Y %I:%M %p")}

━━━━━━━━━━━━━━

🌡️ তাপমাত্রা: <b>{temperature}°C</b>
💧 আর্দ্রতা: <b>{humidity}%</b>
🌧️ বর্তমান বৃষ্টি: <b>{rain} mm</b>
💦 বৃষ্টিপাত: <b>{precipitation} mm</b>
💨 বাতাসের গতি: <b>{wind} km/h</b>

☁️ অবস্থা:
<b>{weather_text}</b>

━━━━━━━━━━━━━━

🌾 <b>কৃষি আবহাওয়া সতর্কতা</b>
"""

    # কৃষি সতর্কতা

    if rain > 0:
        message += (
            "\n🌧️ বর্তমানে বৃষ্টি হচ্ছে।"
            "\n⚠️ এই সময়ে কীটনাশক/ছত্রাকনাশক স্প্রে না করাই ভালো।"
        )

    elif weather_code in [95, 96, 99]:
        message += (
            "\n⛈️ বজ্রঝড়ের সম্ভাবনা রয়েছে।"
            "\n⚠️ খোলা মাঠে কাজ করার সময় সতর্ক থাকুন।"
        )

    elif temperature >= 35:
        message += (
            "\n🔥 তাপমাত্রা বেশি।"
            "\n💧 ফসলের পানির চাহিদা বাড়তে পারে।"
        )

    else:
        message += (
            "\n✅ বর্তমানে বড় ধরনের আবহাওয়া সতর্কতা নেই।"
        )

    message += "\n\n🤖 <i>স্বয়ংক্রিয় আবহাওয়া বট</i>"

    return message


# =========================
# /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = """
🌦️ <b>স্বাগতম!</b>

আমি আপনার বাংলা আবহাওয়া ও সংবাদ বট।

এখানে আপনি পাবেন:

🌡️ বর্তমান আবহাওয়া
🌧️ বৃষ্টির পূর্বাভাস
⛈️ আবহাওয়া সতর্কতা
🌾 কৃষি আবহাওয়া পরামর্শ
📰 সর্বশেষ সংবাদ

<b>কমান্ড:</b>

/weather - বর্তমান আবহাওয়া
/forecast - আবহাওয়ার পূর্বাভাস
/rain - বৃষ্টির সম্ভাবনা
/news - সর্বশেষ সংবাদ
/help - সাহায্য

⏰ প্রতি ঘণ্টায় স্বয়ংক্রিয় আপডেট ব্যবস্থা পরবর্তীতে চালু করা হবে।
"""

    await update.message.reply_text(
        message,
        parse_mode="HTML"
    )


# =========================
# /WEATHER
# =========================

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        message = create_weather_message()

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ দুঃখিত, এই মুহূর্তে আবহাওয়ার তথ্য পাওয়া যাচ্ছে না।"
        )


# =========================
# /FORECAST
# =========================

async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        data = get_weather()

        hourly = data["hourly"]

        message = "📅 <b>আগামী কয়েক ঘণ্টার আবহাওয়া</b>\n\n"

        for i in range(0, min(12, len(hourly["time"]))):

            time = hourly["time"][i]
            temp = hourly["temperature_2m"][i]
            rain_probability = hourly["precipitation_probability"][i]

            code = hourly["weather_code"][i]

            condition = WEATHER_CODES.get(
                code,
                "🌦️ পরিবর্তনশীল"
            )

            message += (
                f"🕐 {time[11:16]}\n"
                f"🌡️ {temp}°C\n"
                f"🌧️ বৃষ্টির সম্ভাবনা: {rain_probability}%\n"
                f"{condition}\n\n"
            )

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ পূর্বাভাস পাওয়া যাচ্ছে না।"
        )


# =========================
# /RAIN
# =========================

async def rain(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        data = get_weather()

        hourly = data["hourly"]

        max_probability = max(
            hourly["precipitation_probability"][:12]
        )

        if max_probability >= 70:

            message = f"""
🌧️ <b>বৃষ্টির সতর্কতা</b>

আগামী কয়েক ঘণ্টায় সর্বোচ্চ বৃষ্টির সম্ভাবনা:

<b>{max_probability}%</b>

⚠️ বাইরে যাওয়ার বা কৃষিকাজের আগে আবহাওয়া দেখে নিন।
"""

        elif max_probability >= 40:

            message = f"""
🌦️ <b>বৃষ্টির সম্ভাবনা রয়েছে</b>

সর্বোচ্চ সম্ভাবনা: <b>{max_probability}%</b>

☔ প্রয়োজন হলে ছাতা সঙ্গে রাখুন।
"""

        else:

            message = f"""
☀️ <b>বৃষ্টির সম্ভাবনা কম</b>

আগামী কয়েক ঘণ্টায় সর্বোচ্চ সম্ভাবনা:

<b>{max_probability}%</b>
"""

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ বৃষ্টির তথ্য পাওয়া যাচ্ছে না।"
        )


# =========================
# /NEWS
# =========================

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
📰 <b>বাংলা সংবাদ</b>

News system এখনো তৈরি করা হয়নি।

পরবর্তী ধাপে এখানে:

🇧🇩 বাংলাদেশের সংবাদ
🌎 আন্তর্জাতিক সংবাদ
🌾 কৃষি সংবাদ
🌦️ আবহাওয়া সংবাদ

স্বয়ংক্রিয়ভাবে যুক্ত করা হবে।
""",
        parse_mode="HTML"
    )


# =========================
# /HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
🤖 <b>সহায়তা</b>

🌦️ /weather
বর্তমান আবহাওয়া

📅 /forecast
আগামী কয়েক ঘণ্টার পূর্বাভাস

🌧️ /rain
বৃষ্টির সম্ভাবনা

📰 /news
সর্বশেষ সংবাদ

/start
বট শুরু করুন
""",
        parse_mode="HTML"
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN পাওয়া যায়নি। "
            "Environment variable সেট করুন।"
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("weather", weather)
    )

    application.add_handler(
        CommandHandler("forecast", forecast)
    )

    application.add_handler(
        CommandHandler("rain", rain)
    )

    application.add_handler(
        CommandHandler("news", news)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    print("🤖 বাংলা আবহাওয়া বট চালু হয়েছে...")

    application.run_polling()


if __name__ == "__main__":
    main()
