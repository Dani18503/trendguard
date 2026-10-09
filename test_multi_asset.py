"""Test Bloque 3 - Multi-activo con datos simulados."""
import json
import numpy as np
import pandas as pd
import multi_asset


def make_fake_df(symbol, n=300, base_price=50000):
    """Genera velas falsas para probar. NO datos reales."""
    np.random.seed(hash(symbol) % 2**32)
    closes = base_price + np.cumsum(np.random.randn(n) * base_price * 0.01)
    df = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='D'),
        'open':   closes + np.random.randn(n) * base_price * 0.002,
        'high':   closes + np.abs(np.random.randn(n)) * base_price * 0.005,
        'low':    closes - np.abs(np.random.randn(n)) * base_price * 0.005,
        'close':  closes,
        'volume': np.abs(np.random.randn(n)) * 1000,
    })
    return df


with open("runtime_config.json") as f:
    config = json.load(f)

print("=== TEST BLOQUE 3 - MULTI-ACTIVO ===\n")

# Estado vacio (sin posiciones)
state = {}
print(f"Activos habilitados: {multi_asset.get_enabled_assets(config)}")

# Generar dataframes falsos
dataframes = {}
for sym in multi_asset.get_enabled_assets(config):
    base = 80000 if "BTC" in sym else (2500 if "ETH" in sym else 150)
    dataframes[sym] = make_fake_df(sym, base_price=base)

print(f"\nDataframes generados: {list(dataframes.keys())}")

# Procesar todos los activos
results = multi_asset.process_all_assets(dataframes, state, config)

print("\n--- Resultados por activo ---")
for sym, r in results.items():
    print(f"\n{sym}:")
    print(f"  Signal:   {r['signal']}")
    print(f"  Price:    ${r['price']:,.2f}" if r['price'] else "  Price: N/A")
    print(f"  Mensaje:  {r['mensaje']}")
    print(f"  Position: {r['position']}")

# Verificar que cada activo proceso independientemente
print("\n--- Verificacion independencia ---")
assert len(results) == 3, "Deben procesarse 3 activos"
for sym in results:
    assert "signal" in results[sym], f"{sym} sin signal"
print("OK: los 3 activos se procesaron independientemente")

print("\n=== FIN TEST BLOQUE 3 ===")
