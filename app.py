import os
import time
import threading
import requests
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

@app.route("/")
def home():
    return "Taahlilgaar Bot is running!"

@app.route("/health")
def health():
    return {"status": "ok"}

def telegram_bot():
    if not TOKEN:
        print("BOT_TOKEN is missing!")
        return

    api = f"https://api.telegram.org/bot{TOKEN}/"
    offset = None

    while True:
        try:
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset

            response = requests.get(
                api + "getUpdates",
                params=params,
                timeout=35
            )
            response.raise_for_status()

            for update in response.json().get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")
                if not message or not message.get("text"):
                    continue

                chat_id = message["chat"]["id"]
                text = message["text"].strip()

                if text == "/start":
                    reply = (
                        "سلام! 👋 به ربات تحلیلگر بازار خوش آمدی.\n\n"
                        "🤖 ربات با موفقیت فعال شده است.\n"
                        "📊 مرحله بعد: اضافه کردن تحلیل ارزهای دیجیتال.\n\n"
                        "برای راهنمایی، دستور /help را بفرست."
                    )
                elif text == "/help":
                    reply = (
                        "راهنمای ربات 📚\n\n"
                        "/start : شروع کار\n"
                        "/help : راهنما\n\n"
                        "قابلیت تحلیل بازار در مراحل بعد اضافه می‌شود."
                    )
                else:
                    reply = (
                        "پیامت دریافت شد! ✅\n"
                        "فعلاً نسخه آزمایشی ربات فعال است."
                    )

                requests.post(
                    api + "sendMessage",
                    json={"chat_id": chat_id, "text": reply},
                    timeout=15
                ).raise_for_status()

        except Exception as error:
            print("Telegram connection error:", error)
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(
        target=telegram_bot,
        daemon=True
    ).start()

    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
