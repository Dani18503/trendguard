"""
TrendGuard - Bot Test (Fase 7, Bloque 3.4)
Loop multi-activo integrado: descarga BTC/ETH/SOL + procesa + drawdown + Telegram.
NO ejecuta ordenes reales. NO toca produccion.
"""

import json
import os
import time
from datetime import datetime, timezone

import ccxt
from dotenv import load_dotenv

import multi_asset
import risk_manager as rm
import notifier


CONFIG_FILE = "runtime_config.json"
STATE_FILE = "state.json"
load_dotenv("/home/ubuntu/trendguard/.env")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def log(msg):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def get_equity(exchange):
    """Equity total = balance libre + PnL de posiciones (simplificado)."""
    try:
        bal = exchange.fetch_balance()
        free = bal['USDT']['free']
        return float(free)
    except Exception as e:
        log(f"  [!] Error leyendo balance: {e}")
        log(f"  [!] Usando equity simulado para test: $5000.00")
        return 5000.0


def build_report(results, equity, dd_state, max_dd):
    now = datetime.now(timezone.utc).strftime("%H:%M")
    lines = [
        "\U0001F4CA Reporte TrendGuard MULTI-ACTIVO",
        f"\U0001F550 Hora UTC: {now}",
        f"\U0001F4B0 Equity: ${equity:,.2f}",
        f"\U0001F6E1\uFE0F Drawdown: {dd_state.get('drawdown_pct', 0):.2%} / Limite {max_dd:.2%}",
        "",
    ]
    for sym, r in results.items():
        pos = r.get('position') or 'none'
        price = r.get('price')
        price_txt = f"${price:,.2f}" if price else "N/A"
        emoji = "\U0001F7E2" if r['signal'] == 'buy' else ("\U0001F534" if r['signal'] == 'sell' else "\u26AA")
        lines.append(f"{emoji} {sym.split(':')[0]}: {r['signal'].upper()} @ {price_txt} | pos: {pos}")
    return "\n".join(lines)


# === EJECUCION ===
log("=== TrendGuard Multi-Activo Test (Fase 7, Bloque 3.4) ===")

config = load_json(CONFIG_FILE)
state = load_json(STATE_FILE)

# Migrar state si es necesario
state, migrated = multi_asset.migrate_state_to_multi(state, config)
if migrated:
    log("State migrado a multi-activo")
    save_json(state, STATE_FILE)

# Crear exchange
exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_SECRET"),
    "options": {"defaultType": "future"},
    "enableRateLimit": True,
})
exchange.set_sandbox_mode(True)
log(f"Exchange: {exchange.id} (sandbox)")

enabled = multi_asset.get_enabled_assets(config)
log(f"Activos habilitados: {enabled}")
max_dd = config["drawdown"]["max_daily_pct"]
log(f"Drawdown maximo: {max_dd:.2%}")
log("")

# Descargar velas de los 3 activos
log("--- Descargando velas ---")
dataframes = multi_asset.fetch_all_assets(exchange, config, timeframe="1d", limit=300)
for sym, df in dataframes.items():
    log(f"  {sym}: {len(df)} velas | ${df['close'].iloc[-1]:,.2f}")

# Equity actual
equity = get_equity(exchange)
if equity is None:
    log("No se pudo leer equity. Abortando.")
    exit(1)
log(f"Equity actual: ${equity:,.2f}")
log("")

# Drawdown
dd_state = rm.reset_drawdown_if_new_day(state.get("drawdown", {}), equity)
state["drawdown"] = dd_state

triggered, pct = rm.check_daily_drawdown(equity, dd_state["day_start_equity"], max_dd)
dd_state["drawdown_pct"] = pct
state["drawdown"] = dd_state

log(f"Drawdown dia: {pct:.4%} | Trigger: {triggered} | Ya disparado: {dd_state.get('triggered_today')}")
log("")

if triggered and not dd_state.get("triggered_today"):
    dd_state["triggered_today"] = True
    log("!!! DRAWDOWN DISPARADO - reportando a Telegram")
    notifier.send_telegram_message(
        "\U0001F6A8 DRAWDOWN DIARIO\n"
        f"Equity: ${equity:,.2f}\n"
        f"Caida: {pct:.2%}\n"
        "Modo simulacion"
    )

# Procesar los 3 activos
log("--- Procesando senales ---")
results = multi_asset.process_all_assets(dataframes, state, config)

for sym, r in results.items():
    price_txt = f"${r['price']:,.2f}" if r['price'] else "N/A"
    log(f"  {sym}: {r['signal']} @ {price_txt}")
    log(f"      -> {r['mensaje']}")

# Enviar reporte consolidado
report = build_report(results, equity, dd_state, max_dd)
log("")
log("--- Enviando reporte a Telegram ---")
notifier.send_telegram_message(report)
log("Reporte enviado.")

# Guardar state
save_json(state, STATE_FILE)
log("")
log("=== FIN TEST BLOQUE 3.4 ===")
print(json.dumps(state, indent=2))
