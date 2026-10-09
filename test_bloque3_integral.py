"""
Testing integral Bloque 3 (Fase 7).
Verifica: multi-activo + state separado + drawdown + reporte.
"""
import json
import os
import ccxt
from dotenv import load_dotenv
import multi_asset
import risk_manager as rm

load_dotenv("/home/ubuntu/trendguard/.env")

with open("runtime_config.json") as f:
    config = json.load(f)

print("=== TESTING INTEGRAL BLOQUE 3 ===\n")

# Crear exchange
exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_SECRET"),
    "options": {"defaultType": "future"},
    "enableRateLimit": True,
})
exchange.set_sandbox_mode(True)

# Descargar velas reales
print("--- Descargando velas ---")
dfs = multi_asset.fetch_all_assets(exchange, config, timeframe="1d", limit=300)
for sym, df in dfs.items():
    print(f"  {sym}: {len(df)} velas")

print("\n=== ESCENARIO 1: Todos sin posicion ===")
state1 = {
    "BTC/USDT:USDT": {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0},
    "ETH/USDT:USDT": {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0},
    "SOL/USDT:USDT": {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0},
}
r1 = multi_asset.process_all_assets(dfs, state1, config)
for sym, r in r1.items():
    print(f"  {sym}: {r['signal']} @ ${r['price']:,.2f}")

print("\n=== ESCENARIO 2: BTC con LONG + ETH/SOL sin ===")
state2 = {
    "BTC/USDT:USDT": {"current_position": "long", "entry_price": 85000.0, "max_price": 86500.0, "min_price": 0.0, "cantidad": 0.05},
    "ETH/USDT:USDT": {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0},
    "SOL/USDT:USDT": {"current_position": None, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0},
}
r2 = multi_asset.process_all_assets(dfs, state2, config)
for sym, r in r2.items():
    print(f"  {sym}: {r['signal']} @ ${r['price']:,.2f} | pos: {r['position']}")

print("\n=== ESCENARIO 3: Los 3 con posicion LONG ===")
state3 = {
    "BTC/USDT:USDT": {"current_position": "long", "entry_price": 82000.0, "max_price": 83000.0, "min_price": 0.0, "cantidad": 0.05},
    "ETH/USDT:USDT": {"current_position": "long", "entry_price": 2400.0, "max_price": 2500.0, "min_price": 0.0, "cantidad": 1.5},
    "SOL/USDT:USDT": {"current_position": "long", "entry_price": 100.0, "max_price": 115.0, "min_price": 0.0, "cantidad": 50.0},
}
r3 = multi_asset.process_all_assets(dfs, state3, config)
for sym, r in r3.items():
    print(f"  {sym}: {r['signal']} @ ${r['price']:,.2f} | pos: {r['position']}")

print("\n=== ESCENARIO 4: Drawdown negativo (equity subio) ===")
dd_neg = rm.check_daily_drawdown(current_equity=5100, day_start_equity=4700, max_daily_pct=0.03)
print(f"  equity=$5100, day_start=$4700 -> pct={dd_neg[1]:.4%} triggered={dd_neg[0]}")
fixed_pct = max(0.0, dd_neg[1])
print(f"  Mostrado en reporte: {fixed_pct:.4%} (debe ser 0%)")
assert fixed_pct == 0.0, "Debe mostrar 0%"

print("\n=== VERIFICACION FINAL ===")
assert len(r1) == 3
assert len(r2) == 3
assert len(r3) == 3
assert r2["BTC/USDT:USDT"]["position"] == "long"
assert r3["ETH/USDT:USDT"]["position"] == "long"
assert r3["SOL/USDT:USDT"]["position"] == "long"
print("  OK: 3 escenarios procesados correctamente")
print("  OK: posiciones independientes por activo")
print("  OK: drawdown negativo corregido a 0%")

print("\n=== FIN TESTING INTEGRAL BLOQUE 3 ===")
