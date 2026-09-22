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
    61: "🌦️ হালকা বৃষ্টি",
    63: "🌧️ মাঝারি বৃষ্টি",
    65: "🌧️ ভারী বৃষ্টি",
    80: "🌦️ বৃষ্টির ঝাপটা",
    81: "🌧️ বৃষ্টির ঝাপটা",
    82: "⛈️ ভারী বৃষ্টির ঝাপটা",
    95: "⛈️ বজ্রঝড়",
    96: "⛈️ বজ্রঝড় ও শিলাবৃষ্টি",
    99: "⛈️ শক্তিশালী বজ্রঝড় ও শিলাবৃষ্টি"
}


def get_weather_report():

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}"
        f"&longitude={LON}"
        "&current=temperature_2m,"
        "relative_humidity_2m,"
        "apparent_temperature,"
        "precipitation,"
        "weather_code,"
        "wind_speed_10m,"
        "wind_gusts_10m"
        "&hourly=temperature_2m,"
        "precipitation_probability,"
        "precipitation,"
        "weather_code,"
        "wind_speed_10m"
        "&daily=temperature_2m_max,"
        "temperature_2m_min,"
        "precipitation_sum,"
        "precipitation_probability_max"
        "&timezone=Asia%2FDhaka"
        "&forecast_days=2"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    current = data["current"]
    hourly = data["hourly"]
    daily = data["daily"]

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

    rain_prob = hourly["precipitation_probability"]
    rain_amount = hourly["precipitation"]

    next_1 = rain_prob[0]
    next_3 = max(rain_prob[:3])
    next_6 = max(rain_prob[:6])

    rain_1 = sum(rain_amount[:1])
    rain_3 = sum(rain_amount[:3])
    rain_6 = sum(rain_amount[:6])

    today_max = daily["temperature_2m_max"][0]
    today_min = daily["temperature_2m_min"][0]
    today_rain = daily["precipitation_sum"][0]

    today_rain_probability = (
        daily["precipitation_probability_max"][0]
    )

    alerts = []

    if next_6 >= 70:
        alerts.append(
            "🌧️ আগামী কয়েক ঘণ্টায় বৃষ্টির সম্ভাবনা বেশি।"
        )

    if rain_6 >= 20:
        alerts.append(
            "⚠️ আগামী ৬ ঘণ্টায় ভারী বৃষ্টির সম্ভাবনা রয়েছে।"
        )

    next_codes = hourly["weather_code"][:6]

    if any(
        code in [95, 96, 99]
        for code in next_codes
    ):
        alerts.append(
            "⛈️ আগামী কয়েক ঘণ্টায় বজ্রঝড়ের সম্ভাবনা রয়েছে।"
        )

    if wind >= 35 or gust >= 50:
        alerts.append(
            "💨 বাতাসের গতি বেশি—সতর্ক থাকুন।"
        )

    if not alerts:
        alerts.append(
            "✅ বড় ধরনের আবহাওয়া সতর্কতা নেই।"
        )

    farming = []

    if next_3 >= 60:
        farming.append(
            "🌾 বৃষ্টির সম্ভাবনা বেশি—সাধারণভাবে এখন স্প্রে না করাই নিরাপদ।"
        )

    if next_6 >= 70:
        farming.append(
            "💧 সেচ দেওয়ার আগে আগামী কয়েক ঘণ্টার বৃষ্টির সম্ভাবনা বিবেচনা করুন।"
        )

    if rain_6 >= 10:
        farming.append(
            "🌱 জমিতে পানি জমলে দ্রুত নিষ্কাশনের ব্যবস্থা রাখুন।"
        )

    if not farming:
        farming.append(
            "✅ বর্তমানে বড় ধরনের আবহাওয়াজনিত কৃষি সতর্কতা নেই।"
        )

    now = datetime.now(
        ZoneInfo("Asia/Dhaka")
    ).strftime("%d-%m-%Y %I:%M %p")

    alert_text = "\n".join(
        f"• {x}" for x in alerts
    )

    farming_text = "\n".join(
        f"• {x}" for x in farming
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

🌧️ বৃষ্টির সম্ভাবনা

⏱️ ১ ঘণ্টা: {next_1}%
⏱️ ৩ ঘণ্টা: {next_3}%
⏱️ ৬ ঘণ্টা: {next_6}%

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


@app.route("/")
def home():
    return "🌦️ বাংলা আবহাওয়া বট চালু আছে!"


@app.route("/health")
def health():
    return "OK"


@app.route("/cron/weather")
def cron_weather():
    # নিরাপত্তা যাচাই
    provided_key = request.headers.get("X-Cron-Key")

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

        # কোনো response body পাঠানো হবে না
        return "", 204

    except Exception as e:
        print("ERROR:", str(e))
        return "", 500

@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json(silent=True)

    if not update:
        return "OK"

    message = update.get("message")

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
            "আমি বাংলা আবহাওয়া বট।\n\n"
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

        except Exception:

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

        except Exception:

            send_message(
                chat_id,
                "❌ বৃষ্টির তথ্য আনতে সমস্যা হয়েছে।"
            )

    elif text == "/forecast":

        send_message(
            chat_id,
            "📅 বিস্তারিত পূর্বাভাস ব্যবস্থা পরবর্তী ধাপে যুক্ত করা হবে।"
        )

    elif text == "/help":

        send_message(
            chat_id,
            "🤖 বাংলা আবহাওয়া বট\n\n"
            "/start\n"
            "/weather\n"
            "/rain\n"
            "/forecast\n"
            "/help"
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
