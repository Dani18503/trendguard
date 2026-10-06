import streamlit as st
import os
from pathlib import Path
import docker

ENV_FILE = Path("/home/ubuntu/trendguard/.env")
BOT_CONTAINER = os.getenv("BOT_CONTAINER", "trendguard-bot")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "trendguard")

st.set_page_config(page_title="TrendGuard Panel", page_icon="📈", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 TrendGuard — Acceso")
    st.caption("Proyecto: JESUCRISTO NUESTRO SEÑOR")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Entrar", use_container_width=True):
        if pwd == PANEL_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

try:
    client = docker.from_env()
    docker_ok = True
except Exception as e:
    docker_ok = False
    docker_error = str(e)

def get_status():
    if not docker_ok:
        return "no_docker"
    try:
        c = client.containers.get(BOT_CONTAINER)
        return c.status
    except docker.errors.NotFound:
        return "not_found"

def read_env():
    cfg = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg

def write_env_key(key, value):
    if not ENV_FILE.exists():
        ENV_FILE.write_text(f"{key}={value}\n")
        return
    lines = ENV_FILE.read_text().splitlines()
    found = False
    out = []
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out) + "\n")

def do_action(action):
    if not docker_ok:
        return False, docker_error
    try:
        c = client.containers.get(BOT_CONTAINER)
        if action == "start":
            c.start()
        elif action == "stop":
            c.stop(timeout=30)
        elif action == "restart":
            c.restart(timeout=30)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def tail_logs(lines=100):
    if not docker_ok:
        return "Docker no disponible"
    try:
        c = client.containers.get(BOT_CONTAINER)
        return c.logs(tail=lines).decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error leyendo logs: {e}"

st.title("📈 TrendGuard — Panel de Control")
st.caption("Proyecto: JESUCRISTO NUESTRO SEÑOR")

status = get_status()
cfg = read_env()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Estado Bot", status.upper())
col2.metric("Par", cfg.get("SYMBOL", "-"))
col3.metric("Riesgo", cfg.get("RISK_PER_TRADE", "-"))
col4.metric("Temporalidad", cfg.get("TIMEFRAME", "-"))

st.divider()
st.subheader("🎛️ Control del Bot")
c1, c2, c3 = st.columns(3)
if c1.button("▶️ Iniciar", use_container_width=True):
    ok, msg = do_action("start")
    st.success("Bot iniciado") if ok else st.error(f"Error: {msg}")
    st.rerun()
if c2.button("⏹️ Detener", use_container_width=True):
    ok, msg = do_action("stop")
    st.warning("Bot detenido") if ok else st.error(f"Error: {msg}")
    st.rerun()
if c3.button("🔄 Reiniciar", use_container_width=True):
    ok, msg = do_action("restart")
    st.info("Bot reiniciado") if ok else st.error(f"Error: {msg}")
    st.rerun()

st.divider()
st.subheader("⚙️ Configuración de Estrategia")
with st.form("cfg_form"):
    symbol = st.text_input("Par (SYMBOL)", value=cfg.get("SYMBOL", "BTC/USDT:USDT"))
    risk = st.text_input("Riesgo por trade (RISK_PER_TRADE, ej 0.01 = 1%)", value=cfg.get("RISK_PER_TRADE", "0.01"))
    tf = st.selectbox("Temporalidad (TIMEFRAME)", ["15m", "1h", "4h", "1d"], index=["15m","1h","4h","1d"].index(cfg.get("TIMEFRAME", "15m")) if cfg.get("TIMEFRAME", "15m") in ["15m","1h","4h","1d"] else 0)
    lev = st.text_input("Apalancamiento (LEVERAGE)", value=cfg.get("LEVERAGE", "3"))
    if st.form_submit_button("💾 Guardar y reiniciar bot"):
        write_env_key("SYMBOL", symbol)
        write_env_key("RISK_PER_TRADE", risk)
        write_env_key("TIMEFRAME", tf)
        write_env_key("LEVERAGE", lev)
        ok, msg = do_action("restart")
        st.success("Configuración aplicada y bot reiniciado.") if ok else st.error(f"Guardado, pero error reiniciando: {msg}")
        st.rerun()

st.divider()
st.subheader("🔑 API Keys y Telegram")
with st.form("keys_form"):
    ak = st.text_input("BINANCE_API_KEY", type="password", placeholder="(dejar en blanco para mantener)")
    asec = st.text_input("BINANCE_API_SECRET", type="password", placeholder="(dejar en blanco para mantener)")
    ttok = st.text_input("TELEGRAM_BOT_TOKEN", type="password", placeholder="(dejar en blanco para mantener)")
    tchat = st.text_input("TELEGRAM_CHAT_ID", placeholder="(dejar en blanco para mantener)")
    if st.form_submit_button("💾 Guardar Keys y reiniciar"):
        if ak: write_env_key("BINANCE_API_KEY", ak)
        if asec: write_env_key("BINANCE_API_SECRET", asec)
        if ttok: write_env_key("TELEGRAM_BOT_TOKEN", ttok)
        if tchat: write_env_key("TELEGRAM_CHAT_ID", tchat)
        ok, msg = do_action("restart")
        st.success("Keys actualizadas y bot reiniciado.") if ok else st.error(f"Guardado, error reiniciando: {msg}")
        st.rerun()

st.divider()
st.subheader("📜 Últimos logs del bot")
if st.button("🔄 Refrescar logs"):
    st.rerun()
st.code(tail_logs(100), language="log")

with st.expander("⚠️ Zona de peligro"):
    if st.button("🗑️ Reiniciar state.json (borra posición actual)"):
        state = Path("/home/ubuntu/trendguard/state.json")
        if state.exists():
            state.write_text('{"current_position": null, "entry_price": 0.0, "max_price": 0.0, "min_price": 0.0, "cantidad": 0.0}')
            st.warning("state.json reiniciado. Reinicia el bot.")
        else:
            st.info("state.json no existe.")
