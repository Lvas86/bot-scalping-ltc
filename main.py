import hmac
import hashlib
import requests
import os
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://open-api.bingx.com"
ORDER_ENDPOINT = "/openApi/swap/v2/trade/order"
LEVERAGE_ENDPOINT = "/openApi/swap/v2/user/leverage"

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    print(f"📥 Método recibido: {request.method}", flush=True)
    print(f"📦 Cuerpo crudo: {request.data}", flush=True)

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            print("⚠️ No se recibió JSON válido", flush=True)
        else:
            print("📩 Señal recibida:", data, flush=True)

        if not data or "type" not in data:
            return "❌ Datos inválidos", 400

        if data["type"].lower() == "buy":
            print("📤 Ejecutando orden BUY para LTCUSDT...", flush=True)
            place_order("BUY")
        elif data["type"].lower() == "sell":
            print("📤 Ejecutando orden SELL para LTCUSDT...", flush=True)
            place_order("SELL")
        else:
            return "❌ Tipo de orden no reconocido", 400

        return "✅ Orden procesada", 200

    return '🔁 Esperando señales desde TradingView...'

def place_order(order_type):
    print(f"📨 Recibida señal: {order_type}", flush=True)

    try:
        response = requests.get(BASE_URL + "/openApi/swap/v2/server/time")
        print("🔎 Respuesta completa del servidor de hora:", response.text, flush=True)
        data = response.json()
    except Exception as e:
        print("❌ Error obteniendo timestamp:", e, flush=True)
        return

    if "data" not in data or "serverTime" not in data["data"]:
        print("⚠️ Respuesta inesperada del servidor:", data, flush=True)
        return

    timestamp = str(int(data["data"]["serverTime"]))
    print(f"✅ Timestamp del servidor: {timestamp}", flush=True)

    # ⚙️ Configurar apalancamiento
    leverage_payload = {
        "symbol": "LTC-USDT",
        "leverage": 10,
        "side": order_type,
        "timestamp": timestamp,
        "recvWindow": "5000",
    }
    leverage_qs = "&".join([f"{k}={v}" for k, v in leverage_payload.items()])
    leverage_sig = hmac.new(API_SECRET.encode(), leverage_qs.encode(), hashlib.sha256).hexdigest()
    leverage_payload["signature"] = leverage_sig

    try:
        leverage_response = requests.post(BASE_URL + LEVERAGE_ENDPOINT, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-BX-APIKEY": API_KEY
        }, data=leverage_payload)
        print(f"⚙️ Respuesta apalancamiento: {leverage_response.text}", flush=True)
    except Exception as e:
        print("❌ Error al establecer apalancamiento:", e, flush=True)

    # 📝 Crear orden de entrada
    order_data = {
        "symbol": "LTC-USDT",
        "side": order_type,
        "type": "MARKET",
        "positionSide": "LONG" if order_type == "BUY" else "SHORT",
        "quantity": "0.8",
        "timestamp": timestamp,
        "recvWindow": "5000",
    }
    query_string = "&".join([f"{k}={v}" for k, v in order_data.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    order_data["signature"] = signature

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-BX-APIKEY": API_KEY
    }

    try:
        response = requests.post(BASE_URL + ORDER_ENDPOINT, headers=headers, data=order_data)
        print("📬 Respuesta de la orden:", response.text, flush=True)
    except Exception as e:
        print("❌ Error al enviar la orden:", e, flush=True)
        return

    # TP y SL solo si se ejecuta correctamente la orden
    try:
        order_resp = response.json()
        if order_resp["code"] == 0 and "order" in order_resp["data"]:
            avg_price = float(order_resp["data"]["order"]["avgPrice"])
            qty = order_resp["data"]["order"]["executedQty"]

            tp_price = round(avg_price * 1.01, 2)
            sl_price = round(avg_price * 0.99, 2)

            print(f"🎯 TP en {tp_price}, 🛑 SL en {sl_price}", flush=True)

            for order_type, price in [("TP", tp_price), ("SL", sl_price)]:
                odata = {
                    "symbol": "LTC-USDT",
                    "side": "SELL" if order_type == "TP" else "SELL",
                    "type": "TAKE_PROFIT_MARKET" if order_type == "TP" else "STOP_MARKET",
                    "positionSide": "LONG",
                    "quantity": qty,
                    "stopPrice": price,
                    "timestamp": timestamp,
                    "recvWindow": "5000"
                }
                q_str = "&".join([f"{k}={v}" for k, v in odata.items()])
                odata["signature"] = hmac.new(API_SECRET.encode(), q_str.encode(), hashlib.sha256).hexdigest()
                r = requests.post(BASE_URL + ORDER_ENDPOINT, headers=headers, data=odata)
                print(f"📦 Orden {order_type} enviada: {r.text}", flush=True)
    except Exception as e:
        print("⚠️ Error al calcular o enviar TP/SL:", e, flush=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
