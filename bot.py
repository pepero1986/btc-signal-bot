import requests
import os

BOT_TOKEN = os.environ["8446842957:AAFXQR7N-XdjxNpWtwrGrqVLMwvQxBoKtM0"]
CHAT_ID = os.environ["5263792419"]


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
        "type": "1hour",
        "symbol": "BTC-USDT"
    }

    r = requests.get(url, params=params, timeout=15).json()

    if r.get("code") != "200000":
        raise Exception(str(r))

    closes = [float(c[2]) for c in r["data"]]
    closes.reverse()

    return closes


def ema(values, period):
    multiplier = 2 / (period + 1)
    value = values[0]

    for price in values[1:]:
        value = price * multiplier + value * (1 - multiplier)

    return value


def rsi(values, period=14):
    gains = []
    losses = []

    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]

        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def get_signal():
    prices = get_closes()

    ema9 = ema(prices[-60:], 9)
    ema21 = ema(prices[-60:], 21)
    ema50 = ema(prices[-60:], 50)

    rsi_value = rsi(prices)

    trend_up = ema9 > ema21 > ema50
    trend_down = ema9 < ema21 < ema50

    if trend_up and rsi_value < 40:
        return f"🟢 BUY\nRSI={rsi_value:.1f}"

    if trend_down and rsi_value > 60:
        return f"🔴 SELL\nRSI={rsi_value:.1f}"

    return f"🟡 NO TRADE\nRSI={rsi_value:.1f}"


signal = get_signal()

send_telegram(
    f"📊 BTC 1H Signal\n\n{signal}"
)
