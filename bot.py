import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CRON_SECRET = os.getenv("CRON_SECRET")

app = Flask(__name__)

LAT = 23.6400
LON = 88.8500

TIMEZONE = "Asia/Dhaka"

# আগের আবহাওয়ার snapshot
# একই Render process চলতে থাকা অবস্থায় comparison করবে
LAST_SNAPSHOT = None


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


def get_risk_level(
    rain_6,
    next_6_prob,
    thunderstorm,
    wind,
    gust
):
    """
    Overall weather risk.
    """

    if thunderstorm or gust >= 60:
        return (
            "🔴",
            "উচ্চ ঝুঁকি",
            "বিশেষ সতর্কতা প্রয়োজন।"
        )

    if (
        rain_6 >= 20
        or next_6_prob >= 80
        or wind >= 40
        or gust >= 50
    ):
        return (
            "🟠",
            "বেশি সতর্কতা",
            "আবহাওয়ার পরিবর্তনের দিকে নজর রাখুন।"
        )

    if (
        rain_6 >= 5
        or next_6_prob >= 50
        or wind >= 30
        or gust >= 40
    ):
        return (
            "🟡",
            "সতর্কতা",
            "পরবর্তী কয়েক ঘণ্টার আবহাওয়া নজরে রাখুন।"
        )

    return (
        "🟢",
        "স্বাভাবিক",
        "বড় ধরনের আবহাওয়া ঝুঁকি নেই।"
    )


def get_weather_data():

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

    return response.json()


def analyze_weather(data):

    current = data["current"]
    hourly = data["hourly"]
    daily = data["daily"]

    tz = ZoneInfo(TIMEZONE)
    now_dt = datetime.now(tz)

    # -------------------------------------------------
    # Current weather
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
    # Find current/future hourly index
    # -------------------------------------------------

    start_index = 0

    for i, time_string in enumerate(hourly["time"]):

        dt = datetime.fromisoformat(time_string)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)

        if dt >= now_dt:
            start_index = i
            break

    # -------------------------------------------------
    # Next hours
    # -------------------------------------------------

    rain_prob_1 = hourly[
        "precipitation_probability"
    ][start_index:start_index + 1]

    rain_prob_3 = hourly[
        "precipitation_probability"
    ][start_index:start_index + 3]

    rain_prob_6 = hourly[
        "precipitation_probability"
    ][start_index:start_index + 6]

    rain_amount_1 = hourly[
        "precipitation"
    ][start_index:start_index + 1]

    rain_amount_3 = hourly[
        "precipitation"
    ][start_index:start_index + 3]

    rain_amount_6 = hourly[
        "precipitation"
    ][start_index:start_index + 6]

    next_codes = hourly[
        "weather_code"
    ][start_index:start_index + 6]

    next_winds = hourly[
        "wind_speed_10m"
    ][start_index:start_index + 6]

    next_gusts = hourly[
        "wind_gusts_10m"
    ][start_index:start_index + 6]

    next_1_prob = (
        max(rain_prob_1)
        if rain_prob_1
        else 0
    )

    next_3_prob = (
        max(rain_prob_3)
        if rain_prob_3
        else 0
    )

    next_6_prob = (
        max(rain_prob_6)
        if rain_prob_6
        else 0
    )

    rain_1 = sum(rain_amount_1)
    rain_3 = sum(rain_amount_3)
    rain_6 = sum(rain_amount_6)

    max_next_wind = (
        max(next_winds)
        if next_winds
        else 0
    )

    max_next_gust = (
        max(next_gusts)
        if next_gusts
        else 0
    )

    thunderstorm_codes = [95, 96, 99]

    thunderstorm = any(
        code in thunderstorm_codes
        for code in next_codes
    )

    # -------------------------------------------------
    # Risk
    # -------------------------------------------------

    risk_icon, risk_name, risk_description = get_risk_level(
        rain_6=rain_6,
        next_6_prob=next_6_prob,
        thunderstorm=thunderstorm,
        wind=max(wind, max_next_wind),
        gust=max(gust, max_next_gust)
    )

    # -------------------------------------------------
    # Smart alerts
    # -------------------------------------------------

    alerts = []

    # Rain
    if next_1_prob >= 70:
        alerts.append(
            "🌧️ আগামী ১ ঘণ্টায় বৃষ্টির সম্ভাবনা খুব বেশি।"
        )

    elif next_1_prob >= 50:
        alerts.append(
            "🌦️ আগামী ১ ঘণ্টায় বৃষ্টির সম্ভাবনা রয়েছে।"
        )

    if next_3_prob >= 80:
        alerts.append(
            "🌧️ আগামী ৩ ঘণ্টায় বৃষ্টির সম্ভাবনা খুব বেশি।"
        )

    if rain_6 >= 20:
        alerts.append(
            "💧 আগামী ৬ ঘণ্টায় উল্লেখযোগ্য বৃষ্টির সম্ভাবনা রয়েছে।"
        )

    # Thunderstorm
    if thunderstorm:
        alerts.append(
            "⛈️ আগামী কয়েক ঘণ্টায় বজ্রঝড়ের সম্ভাবনা রয়েছে।"
        )

    # Wind
    if (
        wind >= 35
        or gust >= 50
        or max_next_wind >= 35
        or max_next_gust >= 50
    ):
        alerts.append(
            "💨 বাতাসের গতি/ঝাপটা বেশি হতে পারে।"
        )

    if not alerts:
        alerts.append(
            "✅ বর্তমানে বড় ধরনের আবহাওয়া সতর্কতা নেই।"
        )

    # -------------------------------------------------
    # Agriculture advice
    # -------------------------------------------------

    farming = []

    if next_1_prob >= 60:
        farming.append(
            "🌧️ বৃষ্টির সম্ভাবনা বেশি—কৃষি কাজ বা স্প্রে করার "
            "সময় বৃষ্টির সম্ভাবনা বিবেচনা করুন।"
        )

    if next_3_prob >= 60:
        farming.append(
            "💧 সেচ দেওয়ার আগে আগামী কয়েক ঘণ্টার বৃষ্টির "
            "সম্ভাবনা বিবেচনা করুন।"
        )

    if rain_6 >= 10:
        farming.append(
            "🌱 বেশি বৃষ্টি হলে জমিতে পানি জমছে কি না "
            "নজরে রাখুন এবং প্রয়োজন হলে নিষ্কাশনের ব্যবস্থা করুন।"
        )

    if thunderstorm:
        farming.append(
            "⛈️ বজ্রঝড়ের সময় মাঠে কাজ না করে নিরাপদ স্থানে থাকুন।"
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
    # Today's forecast
    # -------------------------------------------------

    today_max = daily[
        "temperature_2m_max"
    ][0]

    today_min = daily[
        "temperature_2m_min"
    ][0]

    today_rain = daily[
        "precipitation_sum"
    ][0]

    today_rain_probability = daily[
        "precipitation_probability_max"
    ][0]

    return {
        "temperature": temperature,
        "feels_like": feels_like,
        "humidity": humidity,
        "rain_now": rain_now,
        "wind": wind,
        "gust": gust,
        "condition": condition,

        "next_1_prob": next_1_prob,
        "next_3_prob": next_3_prob,
        "next_6_prob": next_6_prob,

        "rain_1": rain_1,
        "rain_3": rain_3,
        "rain_6": rain_6,

        "today_max": today_max,
        "today_min": today_min,
        "today_rain": today_rain,
        "today_rain_probability": today_rain_probability,

        "max_next_wind": max_next_wind,
        "max_next_gust": max_next_gust,

        "thunderstorm": thunderstorm,

        "risk_icon": risk_icon,
        "risk_name": risk_name,
        "risk_description": risk_description,

        "alerts": alerts,
        "farming": farming
    }


def get_smart_change(data):

    global LAST_SNAPSHOT

    if LAST_SNAPSHOT is None:

        LAST_SNAPSHOT = {
            "next_3_prob": data["next_3_prob"],
            "next_6_prob": data["next_6_prob"],
            "rain_6": data["rain_6"],
            "thunderstorm": data["thunderstorm"],
            "wind": data["wind"],
            "gust": data["gust"]
        }

        return "🆕 প্রথম আপডেট — নতুন আবহাওয়া তথ্য পাওয়া গেছে।"

    previous = LAST_SNAPSHOT

    changes = []

    # Rain probability change
    rain_change = (
        data["next_6_prob"]
        - previous["next_6_prob"]
    )

    if rain_change >= 30:

        changes.append(
            f"🌧️ বৃষ্টির সম্ভাবনা বেড়েছে "
            f"{previous['next_6_prob']}% → "
            f"{data['next_6_prob']}%"
        )

    elif rain_change <= -30:

        changes.append(
            f"☀️ বৃষ্টির সম্ভাবনা কমেছে "
            f"{previous['next_6_prob']}% → "
            f"{data['next_6_prob']}%"
        )

    # Rain amount change
    rain_amount_change = (
        data["rain_6"]
        - previous["rain_6"]
    )

    if rain_amount_change >= 10:

        changes.append(
            f"💧 সম্ভাব্য বৃষ্টির পরিমাণ বেড়েছে "
            f"{previous['rain_6']:.1f} → "
            f"{data['rain_6']:.1f} mm"
        )

    # Thunderstorm change
    if (
        data["thunderstorm"]
        and not previous["thunderstorm"]
    ):

        changes.append(
            "⛈️ নতুন করে বজ্রঝড়ের সম্ভাবনা দেখা দিয়েছে।"
        )

    elif (
        not data["thunderstorm"]
        and previous["thunderstorm"]
    ):

        changes.append(
            "🌤️ আগের তুলনায় বজ্রঝড়ের সম্ভাবনা কমেছে।"
        )

    # Wind change
    wind_change = (
        data["gust"]
        - previous["gust"]
    )

    if wind_change >= 15:

        changes.append(
            f"💨 বাতাসের ঝাপটা বেড়েছে "
            f"{previous['gust']:.1f} → "
            f"{data['gust']:.1f} km/h"
        )

    # Save current snapshot
    LAST_SNAPSHOT = {
        "next_3_prob": data["next_3_prob"],
        "next_6_prob": data["next_6_prob"],
        "rain_6": data["rain_6"],
        "thunderstorm": data["thunderstorm"],
        "wind": data["wind"],
        "gust": data["gust"]
    }

    if not changes:

        return (
            "🟢 বড় কোনো পরিবর্তন নেই — "
            "আবহাওয়া মোটামুটি স্থিতিশীল।"
        )

    return "\n".join(
        f"• {change}"
        for change in changes
    )


def get_weather_report():

    data = get_weather_data()

    weather = analyze_weather(data)

    smart_change = get_smart_change(weather)

    now = datetime.now(
        ZoneInfo(TIMEZONE)
    ).strftime(
        "%d-%m-%Y %I:%M %p"
    )

    alert_text = "\n".join(
        f"• {item}"
        for item in weather["alerts"]
    )

    farming_text = "\n".join(
        f"• {item}"
        for item in weather["farming"]
    )

    message = f"""
🌦️ চুয়াডাঙ্গা স্মার্ট আবহাওয়া

🕐 {now}

━━━━━━━━━━━━━━━━━━

{weather["risk_icon"]} আবহাওয়ার অবস্থা: {weather["risk_name"]}
{weather["risk_description"]}

━━━━━━━━━━━━━━━━━━

🌡️ বর্তমান অবস্থা

🌡️ তাপমাত্রা: {weather["temperature"]}°C
🤒 অনুভূত: {weather["feels_like"]}°C
💧 আর্দ্রতা: {weather["humidity"]}%
☁️ অবস্থা: {weather["condition"]}
🌧️ বর্তমানে বৃষ্টি: {weather["rain_now"]} mm
💨 বাতাস: {weather["wind"]} km/h
💨 সর্বোচ্চ ঝাপটা: {weather["gust"]} km/h

━━━━━━━━━━━━━━━━━━

🌧️ আগামী কয়েক ঘণ্টা

⏱️ ১ ঘণ্টা: {weather["next_1_prob"]}%
⏱️ ৩ ঘণ্টা: {weather["next_3_prob"]}%
⏱️ ৬ ঘণ্টা: {weather["next_6_prob"]}%

💧 ১ ঘণ্টায়: {weather["rain_1"]:.1f} mm
💧 ৩ ঘণ্টায়: {weather["rain_3"]:.1f} mm
💧 ৬ ঘণ্টায়: {weather["rain_6"]:.1f} mm

━━━━━━━━━━━━━━━━━━

🔄 সর্বশেষ আপডেটের পরিবর্তন

{smart_change}

━━━━━━━━━━━━━━━━━━

⛈️ আবহাওয়া সতর্কতা

{alert_text}

━━━━━━━━━━━━━━━━━━

🌾 কৃষি পরামর্শ

{farming_text}

━━━━━━━━━━━━━━━━━━

📅 আজ

🌡️ সর্বোচ্চ: {weather["today_max"]}°C
🌡️ সর্বনিম্ন: {weather["today_min"]}°C
🌧️ বৃষ্টির সম্ভাবনা: {weather["today_rain_probability"]}%
💧 সম্ভাব্য বৃষ্টি: {weather["today_rain"]} mm

━━━━━━━━━━━━━━━━━━

🤖 বাংলা স্মার্ট আবহাওয়া বট
🕐 প্রতি ১৫ মিনিটে স্বয়ংক্রিয় আপডেট
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


@app.route("/")
def home():
    return "🌦️ বাংলা স্মার্ট আবহাওয়া বট চালু আছে!"


@app.route("/health")
def health():
    return "", 204


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

    if text == "/start":

        send_message(
            chat_id,
            "🌦️ স্বাগতম!\n\n"
            "আমি বাংলা স্মার্ট আবহাওয়া বট।\n\n"
            "🌤️ /weather — বর্তমান আবহাওয়া\n"
            "🌧️ /rain — বৃষ্টির তথ্য\n"
            "📅 /forecast — পূর্বাভাস\n"
            "❓ /help — সাহায্য"
        )

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

    elif text == "/help":

        send_message(
            chat_id,
            "🤖 বাংলা স্মার্ট আবহাওয়া বট\n\n"
            "/start — বট চালু করুন\n"
            "/weather — বর্তমান আবহাওয়া\n"
            "/rain — বৃষ্টির তথ্য\n"
            "/forecast — পূর্বাভাস\n"
            "/help — সাহায্য"
        )

    return "OK"


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
