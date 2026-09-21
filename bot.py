import os
import logging
import requests

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

LATITUDE = 23.6401
LONGITUDE = 88.8410
LOCATION_NAME = "চুয়াডাঙ্গা"

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# =========================
# FLASK APP
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "বাংলা আবহাওয়া Telegram Bot চালু আছে ✅"


@app.route("/health")
def health():
    return "OK"


# =========================
# WEATHER CODES
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
    80: "🌦️ বৃষ্টির ঝাপটা",
    81: "🌧️ মাঝারি বৃষ্টির ঝাপটা",
    82: "⛈️ ভারী বৃষ্টির ঝাপটা",
    95: "⛈️ বজ্রঝড়",
    96: "⛈️ বজ্রঝড় ও শিলাবৃষ্টি",
    99: "⛈️ প্রবল বজ্রঝড় ও শিলাবৃষ্টি",
}


# =========================
# WEATHER API
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
        "timezone": "Asia/Dhaka",
        "forecast_days": 2,
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# =========================
# WEATHER MESSAGE
# =========================

def weather_message():

    data = get_weather()

    current = data["current"]

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    rain = current["rain"]
    precipitation = current["precipitation"]
    wind = current["wind_speed_10m"]
    code = current["weather_code"]

    condition = WEATHER_CODES.get(
        code,
        "🌦️ পরিবর্তনশীল আবহাওয়া"
    )

    message = f"""
🌦️ <b>বাংলা আবহাওয়া আপডেট</b>

📍 এলাকা: <b>{LOCATION_NAME}</b>

🌡️ তাপমাত্রা: <b>{temperature}°C</b>
💧 আর্দ্রতা: <b>{humidity}%</b>
🌧️ বৃষ্টি: <b>{rain} mm</b>
💦 বৃষ্টিপাত: <b>{precipitation} mm</b>
💨 বাতাস: <b>{wind} km/h</b>

☁️ আবহাওয়া:
<b>{condition}</b>

🌾 <b>কৃষি সতর্কতা</b>
"""

    if rain > 0:

        message += """
🌧️ বর্তমানে বৃষ্টি হচ্ছে।

⚠️ এখন কীটনাশক বা ছত্রাকনাশক স্প্রে না করাই ভালো।
"""

    elif code in [95, 96, 99]:

        message += """
⛈️ বজ্রঝড়ের সম্ভাবনা রয়েছে।

⚠️ খোলা মাঠে কাজ করার সময় সতর্ক থাকুন।
"""

    elif temperature >= 35:

        message += """
🔥 তাপমাত্রা বেশি।

💧 ফসলে পানির প্রয়োজন বাড়তে পারে।
"""

    else:

        message += """
✅ বর্তমানে বড় ধরনের আবহাওয়া সতর্কতা নেই।
"""

    return message


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
🌦️ <b>স্বাগতম!</b>

আমি আপনার বাংলা আবহাওয়া বট।

/weather - বর্তমান আবহাওয়া
/forecast - পূর্বাভাস
/rain - বৃষ্টির সম্ভাবনা
/help - সাহায্য
""",
        parse_mode="HTML"
    )


# =========================
# WEATHER COMMAND
# =========================

async def weather(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        message = weather_message()

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

    except Exception as error:

        logger.error(error)

        await update.message.reply_text(
            "❌ আবহাওয়ার তথ্য পাওয়া যাচ্ছে না।"
        )


# =========================
# FORECAST
# =========================

async def forecast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        data = get_weather()

        hourly = data["hourly"]

        message = "📅 <b>আগামী কয়েক ঘণ্টার পূর্বাভাস</b>\n\n"

        for i in range(
            min(12, len(hourly["time"]))
        ):

            time = hourly["time"][i]
            temp = hourly["temperature_2m"][i]
            probability = hourly[
                "precipitation_probability"
            ][i]

            code = hourly["weather_code"][i]

            condition = WEATHER_CODES.get(
                code,
                "🌦️ পরিবর্তনশীল"
            )

            message += (
                f"🕐 {time[11:16]}\n"
                f"🌡️ {temp}°C\n"
                f"🌧️ বৃষ্টির সম্ভাবনা: "
                f"{probability}%\n"
                f"{condition}\n\n"
            )

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

    except Exception as error:

        logger.error(error)

        await update.message.reply_text(
            "❌ পূর্বাভাস পাওয়া যাচ্ছে না।"
        )


# =========================
# RAIN
# =========================

async def rain(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        data = get_weather()

        probabilities = data["hourly"][
            "precipitation_probability"
        ][:12]

        maximum = max(probabilities)

        if maximum >= 70:

            text = f"""
🌧️ <b>বৃষ্টির সতর্কতা</b>

আগামী কয়েক ঘণ্টায় সর্বোচ্চ
বৃষ্টির সম্ভাবনা:

<b>{maximum}%</b>

⚠️ বাইরে যাওয়ার আগে আবহাওয়া দেখে নিন।
"""

        elif maximum >= 40:

            text = f"""
🌦️ <b>বৃষ্টির সম্ভাবনা রয়েছে</b>

সর্বোচ্চ সম্ভাবনা:

<b>{maximum}%</b>
"""

        else:

            text = f"""
☀️ <b>বৃষ্টির সম্ভাবনা কম</b>

সর্বোচ্চ সম্ভাবনা:

<b>{maximum}%</b>
"""

        await update.message.reply_text(
            text,
            parse_mode="HTML"
        )

    except Exception as error:

        logger.error(error)

        await update.message.reply_text(
            "❌ বৃষ্টির তথ্য পাওয়া যাচ্ছে না।"
        )


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
🤖 <b>বটের কমান্ড</b>

/weather — বর্তমান আবহাওয়া
/forecast — পূর্বাভাস
/rain — বৃষ্টির সম্ভাবনা
/help — সাহায্য
""",
        parse_mode="HTML"
    )


# =========================
# TELEGRAM APPLICATION
# =========================

telegram_app = None


def create_bot():

    global telegram_app

    telegram_app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CommandHandler("weather", weather)
    )

    telegram_app.add_handler(
        CommandHandler("forecast", forecast)
    )

    telegram_app.add_handler(
        CommandHandler("rain", rain)
    )

    telegram_app.add_handler(
        CommandHandler("help", help_command)
    )

    return telegram_app


if __name__ == "__main__":

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN পাওয়া যায়নি।"
        )

    bot = create_bot()

    print(
        "🌦️ বাংলা আবহাওয়া Telegram Bot চালু হচ্ছে..."
    )

    bot.run_polling()
