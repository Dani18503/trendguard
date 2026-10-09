"""
TrendGuard - Risk Manager (Fase 7)
Maneja proteccion de drawdown diario y correlacion entre activos.

NO ESTA CONECTADO AL BOT TODAVIA.
Skeleton creado: 8-oct-2026
"""

from datetime import datetime, timezone
import pandas as pd
import numpy as np


# ============================================================
# BLOQUE 1: DRAWDOWN DIARIO
# ============================================================

def get_today_utc():
    """Retorna la fecha UTC actual como string YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def check_daily_drawdown(current_equity, day_start_equity, max_daily_pct=0.03):
    """
    Verifica si se supero el drawdown diario maximo.

    Args:
        current_equity: equity actual (balance libre + valor posiciones)
        day_start_equity: equity al inicio del dia UTC
        max_daily_pct: maximo drawdown permitido (0.03 = 3%)

    Returns:
        (triggered: bool, drawdown_pct: float)
    """
    if day_start_equity is None or day_start_equity <= 0:
        return False, 0.0

    drawdown_pct = (day_start_equity - current_equity) / day_start_equity
    triggered = drawdown_pct >= max_daily_pct
    return triggered, drawdown_pct


def reset_drawdown_if_new_day(drawdown_state, current_equity):
    """
    Resetea el estado del drawdown si:
      1. Cambio el dia UTC
      2. El day_start_equity es absurdo (>50% de diferencia = state viejo/migracion/deposito)

    Returns:
        dict actualizado
    """
    today = get_today_utc()

    # Caso 1: cambio de dia
    if drawdown_state.get("date_utc") != today:
        return {
            "date_utc": today,
            "day_start_equity": current_equity,
            "triggered_today": False
        }

    # Caso 2: day_start_equity absurdo (guardado viejo o equity cambio drasticamente)
    day_start = drawdown_state.get("day_start_equity", 0)
    if day_start > 0:
        diff_pct = abs(day_start - current_equity) / day_start
        if diff_pct > 0.50:
            print(f"[!] Salvaguarda: day_start_equity=${day_start:,.2f} muy lejos del actual ${current_equity:,.2f} ({diff_pct:.1%}). Reseteando.")
            return {
                "date_utc": today,
                "day_start_equity": current_equity,
                "triggered_today": False
            }

    return drawdown_state


# ============================================================
# BLOQUE 4: CORRELACION ENTRE ACTIVOS
# ============================================================

def calculate_correlation(returns_a, returns_b, window_days=30):
    """
    Correlacion de Pearson entre dos series de retornos.

    Returns:
        float entre -1 y 1 (0.0 si no hay datos suficientes)
    """
    if returns_a is None or returns_b is None:
        return 0.0
    if len(returns_a) < 2 or len(returns_b) < 2:
        return 0.0

    a = returns_a.tail(window_days) if hasattr(returns_a, 'tail') else returns_a[-window_days:]
    b = returns_b.tail(window_days) if hasattr(returns_b, 'tail') else returns_b[-window_days:]

    if isinstance(a, pd.Series) and isinstance(b, pd.Series):
        aligned = pd.concat([a, b], axis=1, join='inner')
        if len(aligned) < 2:
            return 0.0
        corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
    else:
        corr = np.corrcoef(a, b)[0, 1]

    if corr is None or pd.isna(corr):
        return 0.0
    return float(corr)


def get_correlation_action(corr, block_threshold=0.85, half_risk_threshold=0.70):
    """
    Determina la accion segun la correlacion.

    Returns:
        "block" | "half_risk" | "normal"
    """
    if corr > block_threshold:
        return "block"
    elif corr >= half_risk_threshold:
        return "half_risk"
    else:
        return "normal"


# ============================================================
# TEST AISLADO
# ============================================================

if __name__ == "__main__":
    print("=== Test risk_manager.py ===\n")

    # Test drawdown
    print("-- Drawdown --")
    for eq, expected in [(10000, False), (9700, False), (9700, False), (9600, True)]:
        trig, pct = check_daily_drawdown(eq, 10000, 0.03)
        print(f"  equity=${eq}: triggered={trig}, pct={pct:.4%}")

    # Test reset dia
    print("\n-- Reset dia --")
    state = {"date_utc": "2026-10-07", "day_start_equity": 5000, "triggered_today": True}
    new_state = reset_drawdown_if_new_day(state, 4800)
    print(f"  estado viejo: {state}")
    print(f"  estado nuevo: {new_state}")

    # Test correlacion
    print("\n-- Correlacion --")
    np.random.seed(42)
    a = pd.Series(np.random.randn(60))
    b = a * 0.95 + np.random.randn(60) * 0.05  # muy correlacionado
    c = pd.Series(np.random.randn(60))          # independiente

    corr_ab = calculate_correlation(a, b)
    corr_ac = calculate_correlation(a, c)
    print(f"  BTC-ETH (esperado > 0.85): {corr_ab:.4f} -> {get_correlation_action(corr_ab)}")
    print(f"  BTC-SOL (esperado < 0.70): {corr_ac:.4f} -> {get_correlation_action(corr_ac)}")

    print("\n=== FIN TEST ===")


# ============================================================
# BLOQUE 2: VALIDACION DE RIESGO
# ============================================================

def validate_risk_pct(value, min_pct=0.001, max_pct=0.10, default=0.02):
    """
    Valida y normaliza el riesgo por operacion.

    Args:
        value: valor a validar (float, str, None)
        min_pct: minimo permitido (0.001 = 0.1%)
        max_pct: maximo permitido (0.10 = 10%)
        default: valor por defecto si falla la validacion

    Returns:
        float: valor validado y clampeado
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default

    if v != v:  # NaN
        return default

    if v < min_pct:
        return min_pct
    if v > max_pct:
        return max_pct
    return v


def load_risk_from_config(config, asset=None):
    """
    Lee el riesgo desde runtime_config.json.

    Prioridad:
      1. config['assets'][asset]['risk_per_trade'] si asset especificado
      2. config['risk_per_trade'] global
      3. default 0.02
    """
    if asset and 'assets' in config:
        asset_conf = config['assets'].get(asset, {})
        if 'risk_per_trade' in asset_conf:
            return validate_risk_pct(asset_conf['risk_per_trade'])

    if 'risk_per_trade' in config:
        return validate_risk_pct(config['risk_per_trade'])

    return validate_risk_pct(None)
