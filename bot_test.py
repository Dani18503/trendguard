"""
TrendGuard - Bot Test (Fase 7, Dia 3.3)
Test integral Bloque 1: drawdown + cierre + reset diario UTC.
NO ejecuta ordenes reales. NO conecta a Binance.
"""

import json
from datetime import datetime, timezone

import risk_manager as rm
import notifier


CONFIG_FILE = "runtime_config.json"
STATE_FILE = "state.json"


def load_config(path=CONFIG_FILE):
    with open(path, "r") as f:
        return json.load(f)


def load_state(path=STATE_FILE):
    with open(path, "r") as f:
        return json.load(f)


def save_state(state, path=STATE_FILE):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def log(msg):
    print(f"[{msg}]")


def today_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def check_day_reset(state, current_equity, simulated_day=None):
    """
    Tarea 1.3: al arrancar, detecta si cambio el dia UTC.
    Si cambio -> reset day_start_equity + triggered_today=False.
    """
    day = simulated_day if simulated_day else today_utc()
    dd = state.get("drawdown", {})

    if dd.get("date_utc") != day:
        log(f"  >> NUEVO DIA detectado ({day}). Reseteando drawdown.")
        state["drawdown"] = {
            "date_utc": day,
            "day_start_equity": current_equity,
            "triggered_today": False,
        }
    else:
        log(f"  >> Mismo dia ({day}). Manteniendo day_start_equity=${dd.get('day_start_equity'):,.2f}")

    return state


def build_drawdown_alert(equity, day_start, pct, max_dd):
    return (
        "\U0001F6A8 DRAWDOWN DIARIO DISPARADO\n"
        "\U0001F4C9 Equity inicio: $" + f"{day_start:,.2f}" + "\n"
        "\U0001F4C9 Equity actual: $" + f"{equity:,.2f}" + "\n"
        "\U0001F4C9 Caida: " + f"{pct:.2%}" + " | Limite: " + f"{max_dd:.2%}" + "\n"
        "\U0001F9EA MODO SIMULACION"
    )


def build_close_alert(info):
    e = "\U0001F4B0" if info["pnl"] >= 0 else "\U0001F4C9"
    return (
        "\U0001F512 POSICION CERRADA POR DRAWDOWN\n"
        "\U0001F4CA " + info["position"].upper() + " | Cant: " + f"{info['cantidad']:.6f}" + "\n"
        "\U0001F4B5 Entrada: $" + f"{info['entry_price']:,.2f}" + "\n"
        "\U0001F4B5 Cierre:  $" + f"{info['close_price']:,.2f}" + "\n"
        + e + " P&L: " + f"{info['pnl']:+,.2f}" + " USDT\n"
        "\U0001F9EA MODO SIMULACION"
    )


def simulate_close(state, close_price):
    pos = state.get("current_position")
    if pos is None:
        return None
    entry = state.get("entry_price", 0.0)
    cant = state.get("cantidad", 0.0)
    pnl = (close_price - entry) * cant if pos == "long" else (entry - close_price) * cant
    info = {"position": pos, "entry_price": entry, "close_price": close_price,
            "cantidad": cant, "pnl": pnl}
    state["current_position"] = None
    state["entry_price"] = 0.0
    state["max_price"] = 0.0
    state["min_price"] = 0.0
    state["cantidad"] = 0.0
    return info


def run_cycle(state, equity, price, max_dd, day):
    state = check_day_reset(state, equity, simulated_day=day)
    dd = state["drawdown"]
    trig, pct = rm.check_daily_drawdown(equity, dd["day_start_equity"], max_dd)

    log(f"  Equity: ${equity:,.2f} | DD: {pct:.4%} | Trigger: {trig} | Already: {dd['triggered_today']}")

    if trig and not dd["triggered_today"]:
        dd["triggered_today"] = True
        log("  !!! DRAWDOWN DISPARADO - enviando alertas")
        notifier.send_telegram_message(build_drawdown_alert(equity, dd["day_start_equity"], pct, max_dd))
        info = simulate_close(state, price)
        if info:
            log(f"  Cierre {info['position']} @ ${info['close_price']:,.2f} | P&L: {info['pnl']:+,.2f}")
            notifier.send_telegram_message(build_close_alert(info))

    if dd["triggered_today"]:
        log("  ESTADO: BLOQUEADO")
    else:
        log("  ESTADO: NORMAL")
    return state


# === EJECUCION ===
log("=== TEST INTEGRAL BLOQUE 1 (Fase 7) ===")
config = load_config()
state = load_state()
max_dd = config["drawdown"]["max_daily_pct"]

# Reset inicial para el test
state["current_position"] = "long"
state["entry_price"] = 85935.6
state["max_price"] = 85935.6
state["min_price"] = 85935.6
state["cantidad"] = 0.0886
state["drawdown"] = {}
save_state(state)

log(f"Posicion inicial: {state['current_position']} @ ${state['entry_price']:,.2f} | cant {state['cantidad']}")
log(f"Drawdown maximo: {max_dd:.2%}")

# ---------- DIA 1 ----------
log("")
log("========== DIA 1: 2026-10-08 ==========")
day1 = [
    (5000.00, 85935.60),
    (4980.00, 85600.00),
    (4950.00, 85100.00),
    (4900.00, 84300.00),
    (4850.00, 83550.00),  # dispara
    (4800.00, 82600.00),  # bloqueado
    (4700.00, 80900.00),  # bloqueado
]
for eq, px in day1:
    log(f"--- Ciclo D1 ---")
    state = run_cycle(state, eq, px, max_dd, day="2026-10-08")
save_state(state)
log(f"State D1: pos={state['current_position']} | triggered={state['drawdown']['triggered_today']}")

# ---------- DIA 2 ----------
log("")
log("========== DIA 2: 2026-10-09 (NUEVO DIA) ==========")
day2 = [
    (4700.00, 80900.00),  # nuevo dia -> reset, opera normal
    (4680.00, 80600.00),
    (4690.00, 80750.00),
]
for eq, px in day2:
    log(f"--- Ciclo D2 ---")
    state = run_cycle(state, eq, px, max_dd, day="2026-10-09")
save_state(state)
log(f"State D2: pos={state['current_position']} | triggered={state['drawdown']['triggered_today']}")

log("")
log("=== STATE FINAL ===")
print(json.dumps(state, indent=2))
log("=== FIN TEST INTEGRAL ===")
