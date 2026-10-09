"""Test Bloque 3.2+3.3 - Velas reales + migracion state."""
import json
import os
import ccxt
from dotenv import load_dotenv
import multi_asset

load_dotenv("/home/ubuntu/trendguard/.env")

with open("runtime_config.json") as f:
    config = json.load(f)

print("=== TEST BLOQUE 3.2 - VELAS REALES ===\n")

# Crear exchange (testnet)
exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_SECRET"),
    "options": {"defaultType": "future"},
    "enableRateLimit": True,
})
exchange.set_sandbox_mode(True)
print(f"Exchange: {exchange.id} (sandbox)\n")

# Descargar velas reales de los 3 activos
print("--- Descarga de velas ---")
dataframes = multi_asset.fetch_all_assets(exchange, config, timeframe="1d", limit=300)

for sym, df in dataframes.items():
    print(f"  {sym}: {len(df)} velas | ultimo close: ${df['close'].iloc[-1]:,.2f}")

# Procesar con state vacio
state = {}
results = multi_asset.process_all_assets(dataframes, state, config)

print("\n--- Senales por activo ---")
for sym, r in results.items():
    price_txt = f"${r['price']:,.2f}" if r['price'] else "N/A"
    print(f"  {sym}: {r['signal']} @ {price_txt}")
    print(f"      -> {r['mensaje']}")

print("\n=== TEST BLOQUE 3.3 - MIGRACION STATE ===\n")

# State viejo (flat) para probar migracion
state_viejo = {
    "current_position": "long",
    "entry_price": 85935.6,
    "max_price": 86500.0,
    "min_price": 0.0,
    "cantidad": 0.0886,
    "drawdown": {"date_utc": "2026-10-08", "day_start_equity": 5000, "triggered_today": False},
}

print("State viejo (flat):")
print(json.dumps(state_viejo, indent=2)[:300])

state_nuevo, migrated = multi_asset.migrate_state_to_multi(state_viejo, config)

print(f"\nMigracion ejecutada: {migrated}")
print("\nState nuevo (multi-activo):")
print(json.dumps(state_nuevo, indent=2))

# Verificar
assert migrated == True, "Debio migrar"
assert "current_position" not in state_nuevo, "Ya no debe tener flat"
assert "BTC/USDT:USDT" in state_nuevo, "Debe tener BTC"
assert state_nuevo["BTC/USDT:USDT"]["current_position"] == "long", "Debe preservar posicion"
assert "ETH/USDT:USDT" in state_nuevo, "Debe inicializar ETH"
assert "SOL/USDT:USDT" in state_nuevo, "Debe inicializar SOL"
assert "drawdown" in state_nuevo, "Debe preservar drawdown"
print("\nOK: migracion correcta")

# Probar idempotencia (no debe migrar 2 veces)
state_nuevo_2, migrated_2 = multi_asset.migrate_state_to_multi(state_nuevo, config)
assert migrated_2 == False, "No debe migrar dos veces"
print("OK: idempotente (no re-migra)")

print("\n=== FIN TEST BLOQUE 3.2 + 3.3 ===")
