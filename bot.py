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

load_dotenv('/home/ubuntu/trendguard/.env')

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})

try:
    exchange.enable_demo_trading(True)
    print("✅ Modo Demo Trading ACTIVADO")
except Exception as e:
    print(f"⚠️ Error activando Demo Trading: {e}")

try:
    exchange.set_leverage(3, 'BTC/USDT')
    print("✅ Apalancamiento configurado a 3x")
except Exception as e:
    print(f"⚠️ No se pudo configurar apalancamiento: {e}")

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

state = load_state()
current_position = state.get("current_position")
entry_price = state.get("entry_price", 0.0)
max_price = state.get("max_price", 0.0)
min_price = state.get("min_price", 0.0)
cantidad = state.get("cantidad", 0.0)

print("🤖 Iniciando TrendGuard Bot (Fase 5 - Estrategia Definitiva)...")
send_telegram_message("🚀 TrendGuard Bot ONLINE - Fase 5: Estrategia SMA200+Donchian55 activada.")

ultimo_reporte = time.time()

while True:
    try:
        # 1. Leer balance real de la cuenta Demo
        try:
            balance_info = exchange.fetch_balance()
            balance = balance_info['USDT']['free']
        except Exception as e:
            print(f"⚠️ Error leyendo balance, usando 5000 por defecto: {e}")
            balance = 5000.0

        # 2. Descargar datos y calcular indicadores (velas diarias)
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=300)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = add_all_indicators(df)

        # 3. Evaluar estrategia
        signal, price, mensaje = generate_signal(
            df, current_position=current_position, entry_price=entry_price,
            max_price=max_price, min_price=min_price
        )

        # 4. Ejecutar acciones basadas en la señal
        if signal == 'hold':
            print(f"[{pd.Timestamp.now().strftime('%H:%M')}] {mensaje}")

        elif signal in ['buy', 'sell']:
            print(f"🚀 SEÑAL: {mensaje}")
            atr_actual = df.iloc[-1]['atr_14']
            stop_loss_price = price - (3.0 * atr_actual) if signal == 'buy' else price + (3.0 * atr_actual)

            cantidad = calculate_position_size(balance, 0.02, price, stop_loss_price)
            print(f"   -> Balance: ${balance:.2f} | Tamaño: {cantidad:.6f} BTC")

            try:
                order_side = 'buy' if signal == 'buy' else 'sell'
                orden = exchange.create_market_order('BTC/USDT', order_side, cantidad)

                time.sleep(1.5)
                orden_actualizada = exchange.fetch_order(orden['id'], 'BTC/USDT')

                precio_real = orden_actualizada['average'] if orden_actualizada['average'] else price
                cantidad_real = orden_actualizada['filled'] if orden_actualizada['filled'] else cantidad
                comision = orden_actualizada['fee']['cost'] if orden_actualizada['fee'] else 0.0

                print(f"   -> ✅ Orden ejecutada a {precio_real:.2f} | Cantidad: {cantidad_real:.6f}")
                send_telegram_message(f"✅ ORDEN EJECUTADA\nTipo: {order_side.upper()}\nPrecio: {precio_real:.2f}\nCantidad: {cantidad_real:.6f} BTC")

                current_position = 'long' if signal == 'buy' else 'short'
                entry_price = precio_real
                max_price = precio_real if current_position == 'long' else None
                min_price = precio_real if current_position == 'short' else None
                cantidad = cantidad_real

                state = {"current_position": current_position, "entry_price": entry_price, "max_price": max_price, "min_price": min_price, "cantidad": cantidad}
                save_state(state)

            except Exception as e:
                print(f"   -> ❌ Error al ejecutar orden: {e}")
                send_telegram_message(f"❌ Error al ejecutar orden: {e}")

        elif signal == 'close_long':
            print(f"🔄 CIERRE: {mensaje}")
            try:
                exchange.create_market_order('BTC/USDT', 'sell', cantidad)
                send_telegram_message(f"🔄 CIERRE LONG\nPrecio: {price:.2f}\nEsperando nueva señal.")
                current_position = None
                state = {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0}
                save_state(state)
            except Exception as e:
                print(f"Error cerrando Long: {e}")
                send_telegram_message(f"❌ Error al cerrar Long: {e}")

        elif signal == 'close_short':
            print(f"🔄 CIERRE: {mensaje}")
            try:
                exchange.create_market_order('BTC/USDT', 'buy', cantidad)
                send_telegram_message(f"🔄 CIERRE SHORT\nPrecio: {price:.2f}\nEsperando nueva señal.")
                current_position = None
                state = {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0}
                save_state(state)
            except Exception as e:
                print(f"Error cerrando Short: {e}")
                send_telegram_message(f"❌ Error al cerrar Short: {e}")

        # 5. Reporte cada 15 minutos exactos
        if time.time() - ultimo_reporte >= 900:
            ultimo_reporte = time.time()
            estado_posicion = current_position if current_position else "Ninguna"
            pnl = 0.0
            if current_position == 'long':
                pnl = (price - entry_price) * cantidad
            elif current_position == 'short':
                pnl = (entry_price - price) * cantidad
            pnl_texto = f"{pnl:+.2f} USDT" if current_position else "0.00 USDT"

            reporte = (f"📊 Reporte TrendGuard\n"
                       f"⏱️ Hora: {pd.Timestamp.now().strftime('%H:%M')}\n"
                       f"💰 Precio BTC: ${price:.2f}\n"
                       f"📌 Posición: {estado_posicion.upper()}\n"
                       f"📈 P&L Actual: {pnl_texto}\n"
                       f"💵 Balance Libre: ${balance:.2f} USDT")
            send_telegram_message(reporte)

        time.sleep(60)

    except Exception as e:
        print(f"❌ Error general: {e}")
        time.sleep(10)