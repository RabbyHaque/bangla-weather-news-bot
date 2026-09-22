import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CRON_SECRET = os.getenv("CRON_SECRET")

app = Flask(__name__)

# Chuadanga
LAT = 23.6400
LON = 88.8500

TIMEZONE = "Asia/Dhaka"

WEATHER_CODES = {
    0: "☀️ পরিষ্কার আকাশ",
    1: "🌤️ প্রধানত পরিষ্কার",
    2: "⛅ আংশিক মেঘলা",
    3: "☁️ মেঘলা",
    45: "🌫️ কুয়াশা",
    48: "🌫️ কুয়াশা",

    51: "🌦️ হালকা গুঁড়ি বৃষ্টি",
    53: "🌦️ গুঁড়ি বৃষ্টি",
    55: "🌧️ বেশি গুঁড়ি বৃষ্টি",

    56: "🌧️ হিমায়িত গুঁড়ি বৃষ্টি",
    57: "🌧️ ভারী হিমায়িত গুঁড়ি বৃষ্টি",

    61: "🌦️ হালকা বৃষ্টি",
    63: "🌧️ মাঝারি বৃষ্টি",
    65: "🌧️ ভারী বৃষ্টি",

    66: "🌧️ হিমায়িত বৃষ্টি",
    67: "🌧️ ভারী হিমায়িত বৃষ্টি",

    71: "🌨️ হালকা তুষারপাত",
    73: "🌨️ মাঝারি তুষারপাত",
    75: "❄️ ভারী তুষারপাত",
    77: "❄️ তুষার কণা",

    80: "🌦️ বৃষ্টির ঝাপটা",
    81: "🌧️ মাঝারি বৃষ্টির ঝাপটা",
    82: "⛈️ ভারী বৃষ্টির ঝাপটা",

    85: "🌨️ তুষারের ঝাপটা",
    86: "❄️ ভারী তুষারের ঝাপটা",

    95: "⛈️ বজ্রঝড়",
    96: "⛈️ বজ্রঝড় ও শিলাবৃষ্টি",
    99: "⛈️ শক্তিশালী বজ্রঝড় ও শিলাবৃষ্টি"
}


def get_weather_report():

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LAT,
        "longitude": LON,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_gusts_10m"
        ),

        "hourly": (
            "temperature_2m,"
            "precipitation_probability,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_gusts_10m"
        ),

        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "precipitation_probability_max"
        ),

        "timezone": TIMEZONE,
        "forecast_days": 2
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]
    hourly = data["hourly"]
    daily = data["daily"]

    # -------------------------------------------------
    # বর্তমান আবহাওয়া
    # -------------------------------------------------

    condition = WEATHER_CODES.get(
        current["weather_code"],
        "🌤️ আবহাওয়া"
    )

    temperature = current["temperature_2m"]
    feels_like = current["apparent_temperature"]
    humidity = current["relative_humidity_2m"]
    rain_now = current["precipitation"]
    wind = current["wind_speed_10m"]
    gust = current["wind_gusts_10m"]

    # -------------------------------------------------
    # বর্তমান সময়
    # -------------------------------------------------

    tz = ZoneInfo(TIMEZONE)
    now_dt = datetime.now(tz)

    # Open-Meteo hourly সময়কে datetime-এ রূপান্তর
    hourly_datetimes = []

    for time_string in hourly["time"]:
        dt = datetime.fromisoformat(time_string)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)

        hourly_datetimes.append(dt)

    # বর্তমান সময়ের কাছাকাছি/পরের ঘণ্টা খুঁজে বের করা
    start_index = 0

    for i, dt in enumerate(hourly_datetimes):
        if dt >= now_dt:
            start_index = i
            break

    # আগামী ১, ৩ এবং ৬ ঘণ্টার data
    next_1 = hourly["precipitation_probability"][
        start_index:start_index + 1
    ]

    next_3 = hourly["precipitation_probability"][
        start_index:start_index + 3
    ]

    next_6 = hourly["precipitation_probability"][
        start_index:start_index + 6
    ]

    rain_1_data = hourly["precipitation"][
        start_index:start_index + 1
    ]

    rain_3_data = hourly["precipitation"][
        start_index:start_index + 3
    ]

    rain_6_data = hourly["precipitation"][
        start_index:start_index + 6
    ]

    next_codes = hourly["weather_code"][
        start_index:start_index + 6
    ]

    next_winds = hourly["wind_speed_10m"][
        start_index:start_index + 6
    ]

    next_gusts = hourly["wind_gusts_10m"][
        start_index:start_index + 6
    ]

    # নিরাপদ fallback
    next_1_prob = max(next_1) if next_1 else 0
    next_3_prob = max(next_3) if next_3 else 0
    next_6_prob = max(next_6) if next_6 else 0

    rain_1 = sum(rain_1_data)
    rain_3 = sum(rain_3_data)
    rain_6 = sum(rain_6_data)

    max_next_wind = max(next_winds) if next_winds else 0
    max_next_gust = max(next_gusts) if next_gusts else 0

    # -------------------------------------------------
    # আজকের forecast
    # -------------------------------------------------

    today_max = daily["temperature_2m_max"][0]
    today_min = daily["temperature_2m_min"][0]

    today_rain = daily["precipitation_sum"][0]

    today_rain_probability = (
        daily["precipitation_probability_max"][0]
    )

    # -------------------------------------------------
    # আবহাওয়া সতর্কতা
    # -------------------------------------------------

    alerts = []

    # বৃষ্টি
    if next_1_prob >= 70:
        alerts.append(
            "🌧️ আগামী ১ ঘণ্টায় বৃষ্টির সম্ভাবনা বেশি।"
        )

    elif next_1_prob >= 50:
        alerts.append(
            "🌦️ আগামী ১ ঘণ্টায় বৃষ্টির সম্ভাবনা রয়েছে।"
        )

    if next_3_prob >= 70:
        alerts.append(
            "🌧️ আগামী ৩ ঘণ্টায় বৃষ্টির সম্ভাবনা বেশি।"
        )

    if rain_6 >= 20:
        alerts.append(
            "⚠️ আগামী ৬ ঘণ্টায় উল্লেখযোগ্য পরিমাণ বৃষ্টির সম্ভাবনা রয়েছে।"
        )

    # বজ্রঝড়
    thunderstorm_codes = [95, 96, 99]

    if any(
        code in thunderstorm_codes
        for code in next_codes
    ):
        alerts.append(
            "⛈️ আগামী কয়েক ঘণ্টায় বজ্রঝড়ের সম্ভাবনা রয়েছে।"
        )

    # বাতাস
    if (
        wind >= 35
        or gust >= 50
        or max_next_wind >= 35
        or max_next_gust >= 50
    ):
        alerts.append(
            "💨 বাতাসের গতি/ঝাপটা বেশি হতে পারে—সতর্ক থাকুন।"
        )

    if not alerts:
        alerts.append(
            "✅ বর্তমানে বড় ধরনের আবহাওয়া সতর্কতা নেই।"
        )

    # -------------------------------------------------
    # কৃষি পরামর্শ
    # -------------------------------------------------

    farming = []

    if next_1_prob >= 60:
        farming.append(
            "🌾 বৃষ্টির সম্ভাবনা থাকায় এখন স্প্রে করার আগে "
            "বৃষ্টির সময় বিবেচনা করুন।"
        )

    if next_3_prob >= 60:
        farming.append(
            "💧 সেচ দেওয়ার আগে আগামী কয়েক ঘণ্টার বৃষ্টির "
            "সম্ভাবনা বিবেচনা করুন।"
        )

    if rain_6 >= 10:
        farming.append(
            "🌱 অতিরিক্ত বৃষ্টির ক্ষেত্রে জমিতে পানি জমে থাকলে "
            "নিষ্কাশনের ব্যবস্থা রাখুন।"
        )

    if any(
        code in thunderstorm_codes
        for code in next_codes
    ):
        farming.append(
            "⛈️ বজ্রঝড়ের সময় মাঠে/বরজে কাজ না করে "
            "নিরাপদ স্থানে থাকুন।"
        )

    if temperature >= 35:
        farming.append(
            "🌡️ তাপমাত্রা বেশি—ফসল ও মাটির আর্দ্রতার দিকে নজর রাখুন।"
        )

    if humidity >= 85:
        farming.append(
            "💧 আর্দ্রতা বেশি—ফসলের জমিতে অতিরিক্ত স্যাঁতসেঁতে "
            "অবস্থা ও রোগের লক্ষণ পর্যবেক্ষণ করুন।"
        )

    if not farming:
        farming.append(
            "✅ বর্তমানে বড় ধরনের আবহাওয়াজনিত কৃষি সতর্কতা নেই।"
        )

    # -------------------------------------------------
    # সময়
    # -------------------------------------------------

    now = now_dt.strftime(
        "%d-%m-%Y %I:%M %p"
    )

    # -------------------------------------------------
    # Text তৈরি
    # -------------------------------------------------

    alert_text = "\n".join(
        f"• {item}"
        for item in alerts
    )

    farming_text = "\n".join(
        f"• {item}"
        for item in farming
    )

    message = f"""
🌦️ চুয়াডাঙ্গা আবহাওয়া আপডেট

🕐 সময়: {now}

━━━━━━━━━━━━━━━━━━

🌡️ বর্তমান অবস্থা

🌡️ তাপমাত্রা: {temperature}°C
🤒 অনুভূত: {feels_like}°C
💧 আর্দ্রতা: {humidity}%
☁️ অবস্থা: {condition}
🌧️ বর্তমানে বৃষ্টি: {rain_now} mm
💨 বাতাস: {wind} km/h
💨 সর্বোচ্চ ঝাপটা: {gust} km/h

━━━━━━━━━━━━━━━━━━

🌧️ আগামী কয়েক ঘণ্টার বৃষ্টি

⏱️ ১ ঘণ্টা: {next_1_prob}%
⏱️ ৩ ঘণ্টা: {next_3_prob}%
⏱️ ৬ ঘণ্টা: {next_6_prob}%

💧 ১ ঘণ্টায়: {rain_1:.1f} mm
💧 ৩ ঘণ্টায়: {rain_3:.1f} mm
💧 ৬ ঘণ্টায়: {rain_6:.1f} mm

━━━━━━━━━━━━━━━━━━

📅 আজকের পূর্বাভাস

🌡️ সর্বোচ্চ: {today_max}°C
🌡️ সর্বনিম্ন: {today_min}°C
🌧️ বৃষ্টির সম্ভাবনা: {today_rain_probability}%
💧 সম্ভাব্য বৃষ্টি: {today_rain} mm

━━━━━━━━━━━━━━━━━━

⛈️ আবহাওয়া সতর্কতা

{alert_text}

━━━━━━━━━━━━━━━━━━

🌾 কৃষি পরামর্শ

{farming_text}

━━━━━━━━━━━━━━━━━━

🤖 বাংলা কৃষি ও আবহাওয়া বট
🕐 স্বয়ংক্রিয় আপডেট
"""

    return message.strip()


def send_message(chat_id, text):

    url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )

    response.raise_for_status()


# -------------------------------------------------
# Home
# -------------------------------------------------

@app.route("/")
def home():
    return "🌦️ বাংলা আবহাওয়া বট চালু আছে!"


# -------------------------------------------------
# Health Check
# -------------------------------------------------

@app.route("/health")
def health():
    return "", 204


# -------------------------------------------------
# Cron Weather
# -------------------------------------------------

@app.route("/cron/weather")
def cron_weather():

    provided_key = request.headers.get(
        "X-Cron-Key"
    )

    if not CRON_SECRET:
        return "", 500

    if provided_key != CRON_SECRET:
        return "", 401

    if not CHAT_ID:
        return "", 500

    try:

        message = get_weather_report()

        send_message(
            CHAT_ID,
            message
        )

        return "", 204

    except Exception as e:

        print(
            "WEATHER CRON ERROR:",
            str(e)
        )

        return "", 500


# -------------------------------------------------
# Telegram Webhook
# -------------------------------------------------

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

    update = request.get_json(
        silent=True
    )

    if not update:
        return "OK"

    message = update.get(
        "message"
    )

    if not message:
        return "OK"

    chat_id = message["chat"]["id"]

    text = message.get(
        "text",
        ""
    ).lower().strip()

    # /start
    if text == "/start":

        send_message(
            chat_id,
            "🌦️ স্বাগতম!\n\n"
            "আমি বাংলা আবহাওয়া বট।\n\n"
            "🌤️ /weather — বর্তমান আবহাওয়া\n"
            "🌧️ /rain — বৃষ্টির তথ্য\n"
            "📅 /forecast — পূর্বাভাস\n"
            "❓ /help — সাহায্য"
        )

    # /weather
    elif text == "/weather":

        try:

            send_message(
                chat_id,
                get_weather_report()
            )

        except Exception as e:

            print(
                "WEATHER COMMAND ERROR:",
                str(e)
            )

            send_message(
                chat_id,
                "❌ আবহাওয়ার তথ্য আনতে সমস্যা হয়েছে।"
            )

    # /rain
    elif text == "/rain":

        try:

            send_message(
                chat_id,
                get_weather_report()
            )

        except Exception as e:

            print(
                "RAIN COMMAND ERROR:",
                str(e)
            )

            send_message(
                chat_id,
                "❌ বৃষ্টির তথ্য আনতে সমস্যা হয়েছে।"
            )

    # /forecast
    elif text == "/forecast":

        try:

            send_message(
                chat_id,
                get_weather_report()
            )

        except Exception as e:

            print(
                "FORECAST COMMAND ERROR:",
                str(e)
            )

            send_message(
                chat_id,
                "❌ পূর্বাভাস আনতে সমস্যা হয়েছে।"
            )

    # /help
    elif text == "/help":

        send_message(
            chat_id,
            "🤖 বাংলা কৃষি ও আবহাওয়া বট\n\n"
            "/start — বট চালু করুন\n"
            "/weather — বর্তমান আবহাওয়া\n"
            "/rain — বৃষ্টির তথ্য\n"
            "/forecast — পূর্বাভাস\n"
            "/help — সাহায্য"
        )

    return "OK"


# -------------------------------------------------
# Run
# -------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
