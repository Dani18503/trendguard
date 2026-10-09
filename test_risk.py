"""Test Bloque 2 - Riesgo configurable."""
import json
import risk_manager as rm
import strategy

with open("runtime_config.json") as f:
    config = json.load(f)

print("=== TEST BLOQUE 2 - RIESGO CONFIGURABLE ===\n")

# 1. Validacion de valores
print("--- Validacion de valores ---")
for v in [-0.5, 0, 0.0005, 0.001, 0.01, 0.02, 0.05, 0.10, 0.50, None, "abc"]:
    result = rm.validate_risk_pct(v)
    print(f"  {str(v):>8} -> {result:.4f} ({result*100:.2f}%)")

# 2. Leer desde config
print("\n--- Lectura desde runtime_config.json ---")
risk_global = rm.load_risk_from_config(config)
print(f"  Global: {risk_global:.4f} ({risk_global*100:.2f}%)")

risk_btc = rm.load_risk_from_config(config, asset="BTC/USDT:USDT")
print(f"  BTC:    {risk_btc:.4f} ({risk_btc*100:.2f}%)")

# 3. Calcular tamano de posicion con distintos riesgos
print("\n--- Calculo de tamano de posicion ---")
balance = 5000.0
entry = 85935.60
stop_loss = 83500.00

for risk in [0.005, 0.01, 0.02, 0.03]:
    size = strategy.calculate_position_size(balance, risk, entry, stop_loss)
    loss_at_stop = size * (entry - stop_loss)
    print(f"  Riesgo {risk*100:>4.1f}% -> size {size:.6f} BTC | perdida en stop: ${loss_at_stop:,.2f}")

print("\n=== FIN TEST BLOQUE 2 ===")
