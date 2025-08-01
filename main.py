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

def place_order(order_type):
    print(f"📨 Recibida señal: {order_type}", flush=True)

    # Obtener timestamp del servidor de BingX
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

    timestamp = str(data["data"]["serverTime"])
    print(f"✅ Timestamp del servidor: {timestamp}", flush=True)

    # Datos para la orden real
    payload = {
        "symbol": "LTCUSDT",
        "side": order_type,            # BUY o SELL
        "price": "",                   # vacío para MARKET
        "quantity": "0.1",             # ajusta el tamaño de la orden
        "tradeType": "MARKET",         # tipo de orden
        "timestamp": timestamp
    }

    # Construir query string ordenado alfabéticamente
    query_string = '&'.join([f"{key}={payload[key]}" for key in sorted(payload)])

    # Crear firma
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # URL final con firma
    url = BASE_URL + ORDER_ENDPOINT + f"?{query_string}&signature={signature}"

    # Encabezados
    headers = {
        "X-BX-APIKEY": API_KEY
    }

    # Enviar solicitud POST
    try:
        res = requests.post(url, headers=headers)
        print("📬 Respuesta de la orden:", res.text, flush=True)
    except Exception as e:
        print("❌ Error al enviar orden:", e, flush=True)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
