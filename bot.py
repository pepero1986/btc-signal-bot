import requests
import os
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

last_signal = None


def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=15
    )


def get_closes():
    url = "https://api.kucoin.com/api/v1/market/candles"

    params = {
        "type": "15min",   # ⬅️ تغییر تایم‌فریم
        "symbol": "BTC-USDT"
    }

    r = requests.get(url, params=params, timeout=15).json()

    if r.get("code") != "200000":
        raise Exception(str(r))

    data = r["data"]

    # close price index is usually 2
    closes = [float(c[2]) for c in data]
    closes.reverse()

    return closes


def ema(values, period):
    multiplier = 2 / (period + 1)
    value = values[0]

    for price in values[1:]:
        value = price * multiplier + value * (1 - multiplier)

    return value


def rsi(values, period=14):
    if len(values) < period + 1:
        return 50

    gains = 0
    losses = 0

    for i in range(-period, 0):
        diff = values[i] - values[i - 1]

        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)

    avg_gain = gains / period
    avg_loss = losses / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def get_signal(prices):
    ema9 = ema(prices[-60:], 9)
    ema21 = ema(prices[-60:], 21)
    ema50 = ema(prices[-60:], 50)

    rsi_value = rsi(prices)

    trend_up = ema9 > ema21 > ema50
    trend_down = ema9 < ema21 < ema50

    if trend_up and rsi_value < 40:
        return f"BUY\nRSI={rsi_value:.1f}"

    if trend_down and rsi_value > 60:
        return f"SELL\nRSI={rsi_value:.1f}"

    return f"NO TRADE\nRSI={rsi_value:.1f}"


def run():
    global last_signal

    try:
        prices = get_closes()
        signal = get_signal(prices)

        # ⛔ جلوگیری از اسپم
        if signal != last_signal:
            send_telegram(
                f"📊 BTC 15m Signal\n\n{signal}"
            )
            last_signal = signal

    except Exception as e:
        send_telegram(f"⚠️ ERROR: {e}")


run()
