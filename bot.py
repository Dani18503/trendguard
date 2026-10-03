# /home/ubuntu/trendguard/bot.py
import time
import ccxt
import pandas as pd
import json
import os
from dotenv import load_dotenv
from indicators import add_all_indicators
from strategy import generate_signal, calculate_position_size
from notifier import send_telegram_message

# ✅ CORRECCIÓN 1: Ruta absoluta para que systemd siempre encuentre el .env
load_dotenv('/home/ubuntu/trendguard/.env')

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True)

# ✅ CORRECCIÓN 2 (Punto A): Archivo para guardar el estado y no olvidar posiciones
STATE_FILE = '/home/ubuntu/trendguard/state.json'

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

# Cargar estado inicial
state = load_state()
current_position = state.get("current_position")
entry_price = state.get("entry_price", 0.0)
max_price = state.get("max_price", 0.0)
min_price = state.get("min_price", 0.0)
cantidad = state.get("cantidad", 0.0)

print("🤖 Iniciando TrendGuard Bot (Fase 4 - Demo Trading)...")
send_telegram_message("🚀 TrendGuard Bot ONLINE - Fase 4: Órdenes activadas en Demo.")

contador = 0

while True:
    try:
        # ✅ CORRECCIÓN 3 (Punto B): Leer balance real de la cuenta Demo
        try:
            balance_info = exchange.fetch_balance()
            balance = balance_info['USDT']['free'] # Saldo disponible para operar
        except Exception as e:
            print(f"⚠️ Error leyendo balance, usando 5000 por defecto: {e}")
            balance = 5000.0

        # 1. Descargar datos y calcular indicadores
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=300)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = add_all_indicators(df)
        
        # 2. Evaluar estrategia
        signal, price, mensaje = generate_signal(
            df, current_position=current_position, entry_price=entry_price, 
            max_price=max_price, min_price=min_price
        )
        
        # 3. Lógica de ejecución
        if signal == 'hold':
            print(f"[{pd.Timestamp.now().strftime('%H:%M')}] {mensaje}")
            
        elif signal in ['buy', 'sell']:
            print(f"🚀 SEÑAL: {mensaje}")
            atr_actual = df.iloc[-1]['atr_14']
            stop_loss_price = price - (1.5 * atr_actual) if signal == 'buy' else price + (1.5 * atr_actual)
            
            # Calculamos el tamaño basado en el balance real leído
            cantidad = calculate_position_size(balance, 0.01, price, stop_loss_price)
            print(f"   -> Balance disponible: ${balance:.2f} | Tamaño posición: {cantidad:.6f} BTC")
            
            try:
                order_side = 'buy' if signal == 'buy' else 'sell'
                orden = exchange.create_market_order('BTC/USDT', order_side, cantidad)
                print(f"   -> ✅ Orden ejecutada: {orden['id']}")
                send_telegram_message(f"✅ ORDEN EJECUTADA\nTipo: {order_side.upper()}\nPrecio: {price:.2f}\nCantidad: {cantidad:.6f} BTC")
                
                # Actualizar y guardar estado
                current_position = 'long' if signal == 'buy' else 'short'
                entry_price = price
                max_price = price if current_position == 'long' else None
                min_price = price if current_position == 'short' else None
                state = {"current_position": current_position, "entry_price": entry_price, "max_price": max_price, "min_price": min_price, "cantidad": cantidad}
                save_state(state)
                
            except Exception as e:
                print(f"   -> ❌ Error al ejecutar orden: {e}")
                send_telegram_message(f"❌ Error al ejecutar orden: {e}")
            
        elif signal == 'reverse_to_short':
            print(f"🔄 REVERSIÓN: {mensaje}")
            try:
                # Cerrar Long y abrir Short
                exchange.create_market_order('BTC/USDT', 'sell', cantidad)
                exchange.create_market_order('BTC/USDT', 'sell', cantidad)
                send_telegram_message(f"🔄 REVERSIÓN A SHORT\nPrecio: {price:.2f}\nAsegurando ganancia y abriendo Short.")
                
                current_position = 'short'
                entry_price = price
                min_price = price
                max_price = None
                state = {"current_position": current_position, "entry_price": entry_price, "max_price": max_price, "min_price": min_price, "cantidad": cantidad}
                save_state(state)
            except Exception as e:
                print(f"Error en reversión: {e}")
                send_telegram_message(f"❌ Error en reversión: {e}")
            
        elif signal == 'reverse_to_long':
            print(f"🔄 REVERSIÓN: {mensaje}")
            try:
                # Cerrar Short y abrir Long
                exchange.create_market_order('BTC/USDT', 'buy', cantidad)
                exchange.create_market_order('BTC/USDT', 'buy', cantidad)
                send_telegram_message(f"🔄 REVERSIÓN A LONG\nPrecio: {price:.2f}\nAsegurando ganancia y abriendo Long.")
                
                current_position = 'long'
                entry_price = price
                max_price = price
                min_price = None
                state = {"current_position": current_position, "entry_price": entry_price, "max_price": max_price, "min_price": min_price, "cantidad": cantidad}
                save_state(state)
            except Exception as e:
                print(f"Error en reversión: {e}")
                send_telegram_message(f"❌ Error en reversión: {e}")

        # 4. Reporte cada 15 minutos
        contador += 1
        if contador % 15 == 0:
            estado_posicion = current_position if current_position else "Ninguna"
            reporte = (f"📊 Reporte TrendGuard\n"
                       f"⏱️ Hora: {pd.Timestamp.now().strftime('%H:%M')}\n"
                       f"💰 Precio BTC: ${price:.2f}\n"
                       f"📌 Posición: {estado_posicion.upper()}\n"
                       f"💵 Balance: ${balance:.2f} USDT")
            send_telegram_message(reporte)

        time.sleep(60)
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        time.sleep(10)