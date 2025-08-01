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

import hashlib
import hmac
import time
import json

def place_order(order_type):
    print(f"📨 Recibida señal: {order_type}", flush=True)

    # Obtener el tiempo del servidor
    try:
        response = requests.get(BASE_URL + "/openApi/swap/v2/server/time")
        print("🔎 Respuesta completa del servidor de hora:", response.text, flush=True)
        data = response.json()
    except Exception as e:
        print("❌ Error obteniendo timestamp:", e, flush=True)
        return

    if "serverTime" not in data["data"]:
        print("⚠️ Respuesta inesperada del servidor:", data, flush=True)
        return

    timestamp = str(int(data["data"]["serverTime"]))
    print(f"✅ Timestamp del servidor: {timestamp}", flush=True)

    # 🔧 Parámetros obligatorios de la orden
    params = {
        "symbol": "LTC-USDT",
        "price": "0",                  # Obligatorio, pero se ignora en orden de mercado
        "vol": "1",                    # Volumen del contrato
        "side": order_type,           # BUY o SELL
        "type": "MARKET",             # MARKET o LIMIT
        "positionSide": "LONG" if order_type == "BUY" else "SHORT",
        "leverage": "1",              # Puedes cambiarlo si quieres apalancamiento
        "openType": "ISOLATED",
        "timestamp": timestamp,
        "recvWindow": "5000"
    }

    # Convertir a cadena de consulta ordenada
    query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])

    # Firmar la consulta
    signature = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    # Agregar la firma a los parámetros
    query_string += f"&signature={signature}"

    headers = {
        "X-BX-APIKEY": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        url = BASE_URL + ORDER_ENDPOINT
        response = requests.post(url, headers=headers, data=query_string)
        print("📬 Respuesta de la orden:", response.text, flush=True)
    except Exception as e:
        print("❌ Error al enviar la orden:", e, flush=True)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
