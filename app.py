import os
import time
import threading
import requests
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

COINS = {
    "btc": ("bitcoin", "بیت‌کوین"),
    "eth": ("ethereum", "اتریوم"),
    "usdt": ("tether", "تتر"),
    "bnb": ("binancecoin", "بایننس کوین"),
    "sol": ("solana", "سولانا"),
    "doge": ("dogecoin", "دوج‌کوین"),
    "trx": ("tron", "ترون"),
}

def global_price(coin_id):
    url = "https://api.coingecko.com/api/v3/simple/price"
    response = requests.get(
        url,
        params={"ids": coin_id, "vs_currencies": "usd"},
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    return data[coin_id]["usd"]

def nobitex_price(symbol):
    url = "https://api.nobitex.ir/market/stats"
    response = requests.get(
        url,
        params={"srcCurrency": symbol, "dstCurrency": "rls"},
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    pair = symbol + "-rls"
    stats = data.get("stats", {}).get(pair)

    if not stats or not stats.get("latest"):
        raise ValueError("قیمت این ارز در نوبیتکس پیدا نشد")

    rial = float(stats["latest"])
    toman = rial / 10
    return toman

def get_price(symbol):
    symbol = symbol.lower().strip()

    if symbol not in COINS:
        return (
            "این ارز هنوز در فهرست ربات نیست.\n"
            "ارزهای موجود: BTC, ETH, USDT, BNB, SOL, DOGE, TRX"
        )

    coin_id, coin_name = COINS[symbol]
    result = [f"📊 قیمت {coin_name}\n"]

    try:
        usd = global_price(coin_id)
        result.append(f"🌍 بازار جهانی: {usd:,.6g} دلار")
        except Exception as error:
        print("CoinGecko price error:", repr(error))
        result.append("🌍 بازار جهانی: دریافت قیمت ناموفق بود")
    try:
        toman = nobitex_price(symbol)
        result.append(f"🇮🇷 نوبیتکس: {toman:,.0f} تومان")
        except Exception as error:
        print("Nobitex price error:", repr(error))
        result.append("🇮🇷 نوبیتکس: دریافت قیمت ناموفق بود")
    result.append("\n⚠️ این اطلاعات برای بررسی قیمت است، نه تضمین سود.")
    return "\n".join(result)

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
                parts = text.split()

                if text == "/start":
                    reply = (
                        "سلام! 👋 به ربات تحلیلگر بازار خوش آمدی.\n\n"
                        "ربات فعال است. 🤖\n\n"
                        "📊 نمایش قیمت ارزها:\n"
                        "/price btc\n"
                        "/price eth\n"
                        "/price usdt\n\n"
                        "برای راهنما /help را بفرست."
                    )

                elif text == "/help":
                    reply = (
                        "📚 راهنمای ربات\n\n"
                        "/start : شروع کار\n"
                        "/help : راهنما\n"
                        "/price btc : قیمت بیت‌کوین\n"
                        "/price eth : قیمت اتریوم\n"
                        "/price usdt : قیمت تتر\n"
                        "/price bnb : قیمت بایننس کوین\n"
                        "/price sol : قیمت سولانا\n"
                        "/price doge : قیمت دوج‌کوین\n"
                        "/price trx : قیمت ترون\n\n"
                        "قیمت‌ها از منابع عمومی دریافت می‌شوند."
                    )

                elif parts[0].split("@")[0] == "/price":
                    symbol = parts[1] if len(parts) > 1 else "btc"
                    reply = get_price(symbol)

                else:
                    reply = (
                        "دستور را متوجه نشدم. 🤔\n"
                        "برای راهنما /help را بفرست."
                    )

                requests.post(
                    api + "sendMessage",
                    json={"chat_id": chat_id, "text": reply},
                    timeout=20
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
