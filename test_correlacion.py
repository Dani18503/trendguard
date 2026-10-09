"""Test Bloque 4 - Correlacion entre activos."""
import json
import os
import ccxt
from dotenv import load_dotenv
import multi_asset

load_dotenv("/home/ubuntu/trendguard/.env")

with open("runtime_config.json") as f:
    config = json.load(f)

print("=== TEST BLOQUE 4 - CORRELACION ===\n")

exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_SECRET"),
    "options": {"defaultType": "future"},
    "enableRateLimit": True,
})
exchange.set_sandbox_mode(True)

# Descargar velas reales
dfs = multi_asset.fetch_all_assets(exchange, config, timeframe="1d", limit=300)
print(f"Velas descargadas: {len(dfs)} activos\n")

# Escenario A: sin posiciones -> cualquier senal debe pasar
print("--- Escenario A: sin posiciones abiertas ---")
state_a = {s: {"current_position": None} for s in dfs}
r_a = multi_asset.apply_correlation_filter("ETH/USDT:USDT", "buy", dfs, state_a, config)
print(f"  ETH buy -> allowed={r_a['allowed']} | {r_a['reason']}")

# Escenario B: BTC LONG + queremos abrir ETH
print("\n--- Escenario B: BTC abierto + ETH quiere entrar ---")
state_b = {
    "BTC/USDT:USDT": {"current_position": "long", "entry_price": 85000, "cantidad": 0.05},
    "ETH/USDT:USDT": {"current_position": None},
    "SOL/USDT:USDT": {"current_position": None},
}
r_b = multi_asset.apply_correlation_filter("ETH/USDT:USDT", "buy", dfs, state_b, config)
print(f"  ETH buy -> allowed={r_b['allowed']} | {r_b['reason']}")

# Escenario C: BTC LONG + queremos abrir SOL
print("\n--- Escenario C: BTC abierto + SOL quiere entrar ---")
r_c = multi_asset.apply_correlation_filter("SOL/USDT:USDT", "buy", dfs, state_b, config)
print(f"  SOL buy -> allowed={r_c['allowed']} | {r_c['reason']}")

# Escenario D: senal hold no debe ser filtrada
print("\n--- Escenario D: senal 'hold' no se filtra ---")
r_d = multi_asset.apply_correlation_filter("ETH/USDT:USDT", "hold", dfs, state_b, config)
print(f"  ETH hold -> {r_d['reason']}")

print("\n=== CORRELACIONES REALES ===")
import pandas as pd
for pair in [("BTC/USDT:USDT", "ETH/USDT:USDT"), ("BTC/USDT:USDT", "SOL/USDT:USDT"), ("ETH/USDT:USDT", "SOL/USDT:USDT")]:
    if pair[0] in dfs and pair[1] in dfs:
        r1 = dfs[pair[0]]['close'].pct_change().dropna()
        r2 = dfs[pair[1]]['close'].pct_change().dropna()
        aligned = pd.concat([r1, r2], axis=1, join='inner')
        corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        print(f"  {pair[0].split(':')[0]} vs {pair[1].split(':')[0]}: {corr:.4f}")

print("\n=== FIN TEST BLOQUE 4 ===")
