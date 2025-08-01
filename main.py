from flask import Flask, request
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Cargar claves desde el archivo .env
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://api.bingx.com"

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

def place_order(order_type):
    print(f"📨 Recibida señal: {order_type}", flush=True)

    try:
        response = requests.get(BASE_URL + "/openApi/swap/v2/server/time")
        print("🔎 Respuesta completa del servidor de hora:", response.text, flush=True)
        data = response.json()
    except Exception as e:
        print("❌ Error obteniendo timestamp:", e, flush=True)
        return

    if "serverTime" not in data:
        print("⚠️ Respuesta inesperada del servidor:", data, flush=True)
        return

    timestamp = str(int(data["serverTime"]))
    print(f"✅ Timestamp del servidor: {timestamp}", flush=True)

    # Simulación: solo muestra el tipo de orden por ahora
    print(f"📤 Enviando orden {order_type}... (esto es una prueba)", flush=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
