from flask import Flask, request
import os
import requests
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://open-api.bingx.com"
ORDER_ENDPOINT = "/openApi/swap/v2/trade/order"
LEVERAGE_ENDPOINT = "/openApi/swap/v2/trade/leverage"

@app.route('/', methods=['GET', 'POST'])
def home():
    print(f"📥 Método recibido: {request.method}", flush=True)
    print(f"📦 Cuerpo crudo: {request.data}", flush=True)

    if request.method == 'POST':
        data = request.get_json()
        if not data or "type" not in data:
            return "❌ Datos inválidos", 400

        print("📩 Señal recibida:", data, flush=True)

        if data["type"].lower() == "buy":
            print("📤 Ejecutando orden BUY para LTCUSDT...", flush=True)
            place_order("BUY")
        elif data["type"].lower() == "sell":
            print("📤 Ejecutando orden SELL para LTCUSDT...", flush=True)
            place_order("SELL")
        else:
            return "❌ Tipo de orden no reconocido", 400

        return "✅ Orden procesada", 200

    return "🔁 Esperando señales desde TradingView..."

def place_order(order_type):
    print(f"📨 Recibida señal: {order_type}", flush=True)

    # Obtener timestamp
    try:
        response = requests.get(BASE_URL + "/openApi/swap/v2/server/time")
        data = response.json()
        print("🔎 Respuesta completa del servidor de hora:", response.text, flush=True)
        timestamp = str(int(data["data"]["serverTime"]))
        print(f"✅ Timestamp del servidor: {timestamp}", flush=True)
    except Exception as e:
        print("❌ Error al obtener la hora:", e, flush=True)
        return

    # Establecer apalancamiento
    set_leverage(timestamp)

    # Crear orden de mercado
    order_data = {
        "symbol": "LTC-USDT",
        "side": order_type.upper(),
        "type": "MARKET",
        "positionSide": "LONG" if order_type.lower() == "buy" else "SHORT",
        "quantity": "0.8",  # ⚠️ Asegúrate de que es >= 0.1
        "timestamp": timestamp,
        "recvWindow": "5000"
    }
    signed_order = sign_request(order_data)
    headers = {"Content-Type": "application/x-www-form-urlencoded", "X-BX-APIKEY": API_KEY}
    try:
        response = requests.post(BASE_URL + ORDER_ENDPOINT, headers=headers, data=signed_order)
        print("📬 Respuesta de la orden:", response.text, flush=True)
        res_data = response.json()
    except Exception as e:
        print("❌ Error al enviar la orden:", e, flush=True)
        return

    # Enviar TP/SL si la orden fue exitosa
    try:
        order_info = res_data["data"]["order"]
        price = float(order_info["avgPrice"])
        side = order_info["side"]
        qty = order_info["executedQty"]

        tp_price = round(price * 1.01, 2)
        sl_price = round(price * 0.99, 2)
        position = order_info["positionSide"]

        print(f"🎯 TP en {tp_price}, 🛑 SL en {sl_price}", flush=True)

        send_exit_order("TP", price=tp_price, qty=qty, position=position, side=side, timestamp=timestamp)
        send_exit_order("SL", price=sl_price, qty=qty, position=position, side=side, timestamp=timestamp)
    except Exception as e:
        print("⚠️ No se pudo calcular TP/SL:", e, flush=True)

def set_leverage(timestamp):
    data = {
        "symbol": "LTC-USDT",
        "leverage": 10,
        "timestamp": timestamp,
        "recvWindow": "5000"
    }
    signed_data = sign_request(data)
    headers = {"Content-Type": "application/x-www-form-urlencoded", "X-BX-APIKEY": API_KEY}
    try:
        response = requests.post(BASE_URL + LEVERAGE_ENDPOINT, headers=headers, data=signed_data)
        print("⚙️ Respuesta apalancamiento:", response.text, flush=True)
    except Exception as e:
        print("❌ Error al establecer apalancamiento:", e, flush=True)

def send_exit_order(order_type, price, qty, position, side, timestamp):
    order_data = {
        "symbol": "LTC-USDT",
        "side": "SELL" if side == "BUY" else "BUY",
        "type": "LIMIT",
        "positionSide": position,
        "price": str(price),
        "quantity": str(qty),
        "timeInForce": "GTC",
        "reduceOnly": "true",
        "timestamp": timestamp,
        "recvWindow": "5000"
    }
    signed_data = sign_request(order_data)
    headers = {"Content-Type": "application/x-www-form-urlencoded", "X-BX-APIKEY": API_KEY}
    try:
        response = requests.post(BASE_URL + ORDER_ENDPOINT, headers=headers, data=signed_data)
        print(f"📦 Orden {order_type} enviada:", response.text, flush=True)
    except Exception as e:
        print(f"❌ Error en orden {order_type}:", e, flush=True)

def sign_request(data):
    query_string = "&".join([f"{k}={v}" for k, v in data.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    data["signature"] = signature
    return data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
