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
        else:
            print("📩 Señal recibida:", data, flush=True)

        if not data or "type" not in data:
            return "❌ Datos inválidos", 400

        if data["type"] == "buy":
            print("📤 Ejecutando orden BUY para LTCUSDT...", flush=True)
            place_order("BUY")
        elif data["type"] == "sell":
            print("📤 Ejecutando orden SELL para LTCUSDT...", flush=True)
            place_order("SELL")
        else:
            return "❌ Tipo de orden no reconocido", 400

        return "✅ Orden procesada", 200

    return '🔁 Esperando señales desde TradingView...'

import hmac
import hashlib
import time

def place_order(order_type):
    print(f"📨 Recibida señal: {order_type}", flush=True)

    try:
        response = requests.get(BASE_URL + "/openApi/swap/v2/server/time")
        print("🔎 Respuesta completa del servidor de hora:", response.text, flush=True)
        data = response.json()
    except Exception as e:
        print("❌ Error obteniendo timestamp:", e, flush=True)
        return

    if "serverTime" not in data.get("data", {}):
        print("⚠️ Respuesta inesperada del servidor:", data, flush=True)
        return

    timestamp = str(data["data"]["serverTime"])
    print(f"✅ Timestamp del servidor: {timestamp}", flush=True)

    params = {
        "symbol": "LTC-USDT",
        "price": "",  # vacío para MARKET
        "vol": "0.1",  # cambia según tu gestión de riesgo
        "side": "BUY" if order_type == "BUY" else "SELL",
        "type": 1,  # MARKET ORDER
        "openType": "ISOLATED",
        "positionId": "",  # vacío para crear nueva posición
        "leverage": "5",  # ajusta tu apalancamiento
        "externalOid": str(int(time.time() * 1000)),
        "stopLossPrice": "",
        "takeProfitPrice": "",
        "timestamp": timestamp
    }

    # Firma
    query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
    signature = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    headers = {
        "X-BX-APIKEY": API_KEY
    }

    # Envío
    try:
        full_url = BASE_URL + ORDER_ENDPOINT + f"?{query_string}&sign={signature}"
        response = requests.post(full_url, headers=headers)
        print("📬 Respuesta de la orden:", response.text, flush=True)
    except Exception as e:
        print("❌ Error al enviar la orden:", e, flush=True)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
