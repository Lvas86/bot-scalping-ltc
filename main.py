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

def place_order(side):
    # Aquí puedes personalizar los parámetros del orden
    payload = {
        "symbol": "LTC-USDT",
        "price": "",  # Si es orden de mercado, déjalo vacío
        "vol": "0.05",  # Cantidad en LTC
        "side": side,
        "type": "1",  # 1 = Orden de mercado
        "open_type": "1",
        "position_id": "",
        "leverage": "5",
        "external_oid": "",
        "stop_loss_price": "",
        "take_profit_price": "",
        "position_mode": "1",
        "timestamp": str(int(requests.get(BASE_URL + "/openApi/swap/v2/server/time").json()['serverTime']))
    }

    # Firma y envía la solicitud (aquí debes implementar tu firma)
    headers = {
        "X-BX-APIKEY": API_KEY
    }

    print(f"➡️ Enviando orden: {side}")
    response = requests.post(BASE_URL + ORDER_ENDPOINT, data=payload, headers=headers)
    print("📨 Respuesta de BingX:", response.text)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
