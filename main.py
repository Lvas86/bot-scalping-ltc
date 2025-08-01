from flask import Flask, request
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Cargar claves desde el archivo .env
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://open-api.bingx.com"

# 👉 Endpoint para ejecutar órdenes
ORDER_ENDPOINT = "/openApi/swap/v2/trade/order"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            print("⚠️ No se recibió JSON válido", flush=True)
            return "❌ Datos inválidos", 400

        print("📩 Señal recibida:", data, flush=True)

        order_type = data["type"].lower()

        if order_type == "buy":
            print("📤 Ejecutando orden BUY para LTCUSDT...", flush=True)
            place_order("BUY")
        elif order_type == "sell":
            print("📤 Ejecutando orden SELL para LTCUSDT...", flush=True)
            place_order("SELL")
        else:
            return "❌ Tipo de orden no reconocido", 400

        return "✅ Orden procesada", 200

    return '🔁 Esperando señales desde TradingView...'


import hmac
import hashlib

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

    # ⚙️ Datos de la orden
    order_data = {
        "symbol": "LTC-USDT",
        "side": order_type,
        "type": "MARKET",
        "positionSide": "LONG" if order_type == "BUY" else "SHORT",
        "quantity": "0.03",  # puedes ajustar este valor
        "timestamp": timestamp,
        "recvWindow": "5000",
    }

    # 🔐 Crear la firma
    query_string = "&".join([f"{k}={v}" for k, v in order_data.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    order_data["signature"] = signature

    # 📡 Enviar la solicitud
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-BX-APIKEY": API_KEY
    }

    try:
        response = requests.post(BASE_URL + ORDER_ENDPOINT, headers=headers, data=order_data)
        print("📬 Respuesta de la orden:", response.text, flush=True)
    except Exception as e:
        print("❌ Error al enviar la orden:", e, flush=True)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
