import os
import requests
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

LAT = 23.6400
LON = 88.8500

WEATHER_CODES = {
    0: "☀️ পরিষ্কার আকাশ",
    1: "🌤️ প্রধানত পরিষ্কার",
    2: "⛅ আংশিক মেঘলা",
    3: "☁️ মেঘলা",
    45: "🌫️ কুয়াশা",
    48: "🌫️ কুয়াশা",
    51: "🌦️ হালকা গুঁড়ি বৃষ্টি",
    53: "🌦️ গুঁড়ি বৃষ্টি",
    55: "🌧️ বেশি গুঁড়ি বৃষ্টি",
    61: "🌦️ হালকা বৃষ্টি",
    63: "🌧️ মাঝারি বৃষ্টি",
    65: "🌧️ ভারী বৃষ্টি",
    80: "🌦️ বৃষ্টির ঝাপটা",
    81: "🌧️ বৃষ্টির ঝাপটা",
    82: "⛈️ ভারী বৃষ্টির ঝাপটা",
    95: "⛈️ বজ্রঝড়",
    96: "⛈️ বজ্রঝড় ও শিলাবৃষ্টি",
    99: "⛈️ বজ্রঝড় ও শিলাবৃষ্টি"
}


def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}"
        f"&longitude={LON}"
        "&current=temperature_2m,relative_humidity_2m,"
        "apparent_temperature,precipitation,weather_code,"
        "wind_speed_10m"
        "&timezone=Asia%2FDhaka"
    )

    r = requests.get(url, timeout=20)
    data = r.json()

    current = data["current"]

    code = current["weather_code"]
    condition = WEATHER_CODES.get(code, "🌤️ আবহাওয়া")

    return (
        "🌦️ *চুয়াডাঙ্গার বর্তমান আবহাওয়া*\n\n"
        f"🌡️ তাপমাত্রা: {current['temperature_2m']}°C\n"
        f"🤒 অনুভূত তাপমাত্রা: {current['apparent_temperature']}°C\n"
        f"💧 আর্দ্রতা: {current['relative_humidity_2m']}%\n"
        f"🌧️ বৃষ্টি: {current['precipitation']} mm\n"
        f"💨 বাতাস: {current['wind_speed_10m']} km/h\n"
        f"☁️ অবস্থা: {condition}"
    )


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        },
        timeout=20
    )


@app.route("/")
def home():
    return "🌦️ বাংলা আবহাওয়া বট চালু আছে!"


@app.route("/health")
def health():
    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True)

    if not update:
        return "OK"

    message = update.get("message")

    if not message:
        return "OK"

    chat_id = message["chat"]["id"]
    text = message.get("text", "").lower()

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
            send_message(chat_id, get_weather())
        except Exception:
            send_message(
                chat_id,
                "❌ আবহাওয়ার তথ্য আনতে সমস্যা হয়েছে।"
            )

    elif text == "/rain":
        try:
            send_message(chat_id, get_weather())
        except Exception:
            send_message(
                chat_id,
                "❌ বৃষ্টির তথ্য আনতে সমস্যা হয়েছে।"
            )

    elif text == "/forecast":
        send_message(
            chat_id,
            "📅 পূর্বাভাস ব্যবস্থা পরবর্তী ধাপে যুক্ত করা হবে।"
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
