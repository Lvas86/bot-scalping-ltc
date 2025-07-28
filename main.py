import os
import hmac
import hashlib
import time
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# === Cargar claves desde el archivo .env ===
load_dotenv()
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)

# === Ruta principal para verificar que el bot funciona ===
@app.route('/', methods=['GET'])
def home():
    return "✅ Bot activo y esperando señales desde TradingView..."

# === Ruta para recibir alertas vía Webhook ===
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibió ningún JSON válido'}), 400

    tipo = data.get("tipo")
    precio = float(data.get("precio"))
    tp = float(data.get("tp"))
    sl = float(data.get("sl"))

    print(f"\n📩 Señal recibida: {tipo.upper()} | Precio: {precio} | TP: {tp} | SL: {sl}")

    respuesta = enviar_orden(tipo, precio)
    print(f"📤 Respuesta de BingX: {respuesta.text}")
    return jsonify({"status": "ok", "mensaje": "Señal procesada"})

# === Función para firmar y enviar la orden a BingX ===
def enviar_orden(tipo, precio):
    url = "https://open-api.bingx.com/openApi/swap/v2/trade/order"

    side = "SELL" if tipo == "short" else "BUY"

    timestamp = str(int(time.time() * 1000))
    params = {
        "symbol": "LTC-USDT",
        "price": f"{precio}",
        "vol": "0.1",  # Puedes ajustar esto
        "leverage": "1",
        "side": side,
        "type": "LIMIT",
        "openType": "ISOLATED",
        "positionMode": "ONE_WAY",
        "timestamp": timestamp
    }

    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-BX-APIKEY": API_KEY
    }

    params["signature"] = signature
    response = requests.post(url, headers=headers, data=params)
    return response

# === Iniciar servidor Flask ===
if __name__ == '__main__':
    print("🔁 Esperando señales desde TradingView...")
    app.run(host='0.0.0.0', port=3000)