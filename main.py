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
        print(f"📩 Señal recibida: {data}")

        if not data or "type" not in data:
            return "❌ Datos inválidos", 400

        if data["type"] == "buy":
            print("📤 Ejecutando orden BUY para LTCUSDT...")
            # Aquí llamas a tu función de orden de compra
            place_order("BUY")
        elif data["type"] == "sell":
            print("📤 Ejecutando orden SELL para LTCUSDT...")
            # Aquí llamas a tu función de orden de venta
            place_order("SELL")
        else:
            return "❌ Tipo de orden no reconocido", 400

        return "✅ Orden procesada", 200

    return '🔁 Esperando señales desde TradingView...'

def place_order(order_type):
    print(f"📨 Recibida señal: {order_type}")

    # Consultar el timestamp del servidor de BingX
    try:
        response = requests.get(BASE_URL + "/openApi/swap/v2/server/time")
        print("🔎 Respuesta completa del servidor de hora:", response.text)
        data = response.json()
    except Exception as e:
        print("❌ Error obteniendo timestamp:", e)
        return

    if "serverTime" not in data:
        print("⚠️ Respuesta inesperada del servidor:", data)
        return

    timestamp = str(int(data["serverTime"]))

    # Aquí continúa tu lógica para firmar y enviar la orden
    print(f"✅ Timestamp del servidor: {timestamp}")

    # Simulación: solo muestra el tipo de orden por ahora
    print(f"📤 Enviando orden {order_type}... (esto es una prueba)")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
