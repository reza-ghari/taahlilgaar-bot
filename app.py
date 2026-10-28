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
        params={
            "ids": coin_id,
            "vs_currencies": "usd"
        },
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    if coin_id not in data or "usd" not in data[coin_id]:
        raise ValueError("قیمت در پاسخ بازار جهانی موجود نیست")

    return float(data[coin_id]["usd"])


def nobitex_price(symbol):
    url = "https://api.nobitex.ir/market/stats"

    response = requests.get(
        url,
        params={
            "srcCurrency": symbol,
            "dstCurrency": "rls"
        },
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    pair = symbol + "-rls"
    stats = data.get("stats", {}).get(pair)

    if not stats or not stats.get("latest"):
        raise ValueError("قیمت این ارز در پاسخ نوبیتکس موجود نیست")

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

    result.append(
        "\n⚠️ قیمت‌ها ممکن است با تأخیر همراه باشند. "
        "این اطلاعات تضمین‌کننده سود نیستند."
    )

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
            updates = response.json().get("result", [])

            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("message")

                if not message or not message.get("text"):
                    continue

                chat_id = message["chat"]["id"]
                message_text = message["text"].strip()
                parts = message_text.split()

                command = parts[0].split("@")[0].lower()

                if command == "/start":
                    reply = (
                        "سلام! 👋 به ربات تحلیلگر بازار خوش آمدی.\n\n"
                        "🤖 ربات با موفقیت فعال شده است.\n\n"
                        "📊 برای دریافت قیمت ارزها، دستورهای زیر را بفرست:\n"
                        "/price btc\n"
                        "/price eth\n"
                        "/price usdt\n\n"
                        "برای راهنما /help را بفرست."
                    )

                elif command == "/help":
                    reply = (
                        "📚 راهنمای ربات\n\n"
                        "/start : شروع کار\n"
                        "/help : راهنما\n\n"
                        "📊 دستورهای قیمت:\n"
                        "/price btc : بیت‌کوین\n"
                        "/price eth : اتریوم\n"
                        "/price usdt : تتر\n"
                        "/price bnb : بایننس کوین\n"
                        "/price sol : سولانا\n"
                        "/price doge : دوج‌کو
