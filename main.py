import os
import requests
from flask import Flask

app = Flask(__name__)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "8609436988:AAEEcnQgqZtlWPcOvMHgJGPhK8pTAz-TBeQ"
TELEGRAM_CHAT_ID = "5573340878"

def send_instant_msg():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": "🔥 Direct Test Message from Render Server!"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(">>> Instant Telegram Result:", res.json())
    except Exception as e:
        print(">>> Instant Telegram Error:", e)

# Server එක start වෙන ගමන්ම Message එක යවනවා
send_instant_msg()

@app.route('/')
def home():
    # Link එකට ගියාමත් Message එකක් Telegram එකට යනවා
    send_instant_msg()
    return "Deriv Bot is Live and Ready!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
