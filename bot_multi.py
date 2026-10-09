"""
TrendGuard - Bot Multi-Activo (Fase 7, Bloque 5)
Produccion: BTC + ETH + SOL con drawdown y correlacion.
"""
import time
import ccxt
import pandas as pd
import json
import os
from dotenv import load_dotenv
from indicators import add_all_indicators
from strategy import generate_signal, calculate_position_size
from notifier import send_telegram_message
import risk_manager as rm
import multi_asset


load_dotenv('/home/ubuntu/trendguard/.env')

CONFIG_FILE = '/home/ubuntu/trendguard/runtime_config.json'
STATE_FILE = '/home/ubuntu/trendguard/state.json'


# === EXCHANGE ===
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})

try:
    exchange.enable_demo_trading(True)
    print("[OK] Modo Demo Trading ACTIVADO")
except Exception as e:
    print(f"[!] Error activando Demo Trading: {e}")

_config_init = json.load(open(CONFIG_FILE))
for _sym in multi_asset.get_enabled_assets(_config_init):
    _spot = multi_asset.symbol_to_ohlcv(_sym)
    try:
        exchange.set_leverage(3, _spot)
        print(f"[OK] Leverage 3x en {_spot}")
    except Exception as e:
        print(f"[!] No se pudo set leverage en {_spot}: {e}")


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f)


def get_balance():
    try:
        info = exchange.fetch_balance()
        return float(info['USDT']['free'])
    except Exception as e:
        print(f"[!] Error leyendo balance: {e}")
        return 5000.0


def execute_order(symbol_spot, side, cantidad):
    try:
        orden = exchange.create_market_order(symbol_spot, side, cantidad)
        time.sleep(1.5)
        oa = exchange.fetch_order(orden['id'], symbol_spot)
        precio = oa['average'] if oa.get('average') else None
        cant = oa['filled'] if oa.get('filled') else cantidad
        return {'ok': True, 'precio': precio, 'cantidad': cant}
    except Exception as e:
        print(f"[!] Error orden {side} {symbol_spot}: {e}")
        send_telegram_message(f"[X] Error orden {side} {symbol_spot}: {e}")
        return {'ok': False, 'error': str(e)}


def build_report(results, equity, dd_pct, max_dd, balance):
    now = pd.Timestamp.now().strftime('%H:%M')
    lines = [
        "📊 Reporte TrendGuard MULTI-ACTIVO",
        f"🕐 Hora: {now}",
        f"💰 Equity: ${equity:,.2f}",
        f"🛡️ Drawdown: {dd_pct:.2%} / Limite {max_dd:.2%}",
        f"💵 Balance Libre: ${balance:,.2f} USDT",
        "",
    ]
    for sym, r in results.items():
        spot = sym.split(':')[0]
        pos = r.get('position') or 'none'
        price = r.get('price')
        ptxt = f"${price:,.2f}" if price else "N/A"
        sig = r['signal'].upper()
        emoji = "🟢" if r['signal'] == 'buy' else ("🔴" if r['signal'] in ('sell','close_long','close_short') else "⚪")
        lines.append(f"{emoji} {spot}: {sig} @ {ptxt} | pos: {pos}")
    return "\n".join(lines)


print("🚀 Iniciando TrendGuard MULTI-ACTIVO (Fase 7, Bloque 5)...")
send_telegram_message("🚀 TrendGuard Bot ONLINE - MULTI-ACTIVO (BTC/ETH/SOL) - Fase 7")

config = load_json(CONFIG_FILE)
state = load_json(STATE_FILE)

state, migrated = multi_asset.migrate_state_to_multi(state, config)
if migrated:
    print("[OK] State migrado a formato multi-activo")
    save_json(state, STATE_FILE)

enabled_assets = multi_asset.get_enabled_assets(config)
max_dd = config['drawdown']['max_daily_pct']

print(f"[*] Activos: {enabled_assets}")
print(f"[*] Drawdown max: {max_dd:.2%}")

ultimo_reporte = 0  # Forzar reporte inmediato en el primer ciclo
ciclos = 0

while True:
    try:
        ciclos += 1
        print(f"\n=== CICLO {ciclos} ===")

        balance = get_balance()
        equity = balance

        dd_state = rm.reset_drawdown_if_new_day(state.get('drawdown', {}), equity)
        state['drawdown'] = dd_state

        triggered, dd_pct = rm.check_daily_drawdown(equity, dd_state['day_start_equity'], max_dd)
        dd_pct_disp = max(0.0, dd_pct)

        if triggered and not dd_state.get('triggered_today'):
            dd_state['triggered_today'] = True
            state['drawdown'] = dd_state
            print(f"[!!!] DRAWDOWN DISPARADO ({dd_pct:.2%})")
            send_telegram_message(f"📊 DRAWDOWN DIARIO\nEquity: ${equity:,.2f}\nCaida: {dd_pct:.2%}\nCerrando posiciones...")
            for sym in enabled_assets:
                asset = state.get(sym, {})
                pos = asset.get('current_position')
                if pos:
                    spot = multi_asset.symbol_to_ohlcv(sym)
                    side = 'sell' if pos == 'long' else 'buy'
                    cant = asset.get('cantidad', 0)
                    if cant > 0:
                        execute_order(spot, side, cant)
                    asset['current_position'] = None
                    asset['entry_price'] = 0.0
                    asset['max_price'] = 0.0
                    asset['min_price'] = 0.0
                    asset['cantidad'] = 0.0
                    state[sym] = asset
            save_json(state, STATE_FILE)

        if dd_state.get('triggered_today'):
            print(f"[*] BLOQUEADO por drawdown. Reset 00:00 UTC.")
            if time.time() - ultimo_reporte >= 900:
                ultimo_reporte = time.time()
                send_telegram_message(f"🛡️ Bot BLOQUEADO por drawdown\nDD: {dd_pct_disp:.2%}\nReset: 00:00 UTC")
            time.sleep(60)
            continue

        dataframes = multi_asset.fetch_all_assets(exchange, config, timeframe='1d', limit=300)
        results = multi_asset.process_all_assets(dataframes, state, config)

        for sym, r in results.items():
            signal = r['signal']
            price = r['price']
            spot = multi_asset.symbol_to_ohlcv(sym)
            asset = state.get(sym, {'current_position': None, 'entry_price': 0.0, 'max_price': 0.0, 'min_price': 0.0, 'cantidad': 0.0})

            if signal == 'hold':
                print(f"  {spot}: {r['mensaje']}")
                continue

            if signal in ['buy', 'sell']:
                filt = multi_asset.apply_correlation_filter(sym, signal, dataframes, state, config)
                if not filt['allowed']:
                    print(f"  [X] {spot}: BLOQUEADA - {filt['reason']}")
                    continue

                atr = dataframes[sym].iloc[-1]['atr_14']
                sl = price - (3.0 * atr) if signal == 'buy' else price + (3.0 * atr)

                risk = config.get('risk_per_trade', 0.02)
                if filt.get('half_risk'):
                    risk = risk / 2

                cant = calculate_position_size(balance, risk, price, sl)
                if cant <= 0:
                    continue

                side = 'buy' if signal == 'buy' else 'sell'
                res = execute_order(spot, side, cant)
                if res['ok']:
                    pr = res['precio'] or price
                    cr = res['cantidad']
                    asset['current_position'] = 'long' if signal == 'buy' else 'short'
                    asset['entry_price'] = pr
                    asset['max_price'] = pr if signal == 'buy' else 0.0
                    asset['min_price'] = pr if signal == 'sell' else 0.0
                    asset['cantidad'] = cr
                    state[sym] = asset
                    save_json(state, STATE_FILE)
                    send_telegram_message(f"🟢 {side.upper()} {spot} @ ${pr:,.2f} | cant {cr:.6f} | riesgo {risk*100:.2f}%")

            elif signal == 'close_long':
                cant = asset.get('cantidad', 0)
                if cant > 0:
                    execute_order(spot, 'sell', cant)
                    send_telegram_message(f"🔴 CIERRE LONG {spot} @ ${price:,.2f}")
                asset.update({'current_position': None, 'entry_price': 0.0, 'max_price': 0.0, 'min_price': 0.0, 'cantidad': 0.0})
                state[sym] = asset
                save_json(state, STATE_FILE)

            elif signal == 'close_short':
                cant = asset.get('cantidad', 0)
                if cant > 0:
                    execute_order(spot, 'buy', cant)
                    send_telegram_message(f"🔴 CIERRE SHORT {spot} @ ${price:,.2f}")
                asset.update({'current_position': None, 'entry_price': 0.0, 'max_price': 0.0, 'min_price': 0.0, 'cantidad': 0.0})
                state[sym] = asset
                save_json(state, STATE_FILE)

        if time.time() - ultimo_reporte >= 900:
            ultimo_reporte = time.time()
            report = build_report(results, equity, dd_pct_disp, max_dd, balance)
            send_telegram_message(report)
            print("[OK] Reporte enviado a Telegram")

        time.sleep(60)

    except Exception as e:
        print(f"[X] Error general: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)
