# TrendGuard — Fase 7: Gestión de Riesgo Avanzada
*Fecha:* 7 de octubre de 2026
*Autores:* Jhonny + Claude (asistente técnico)
*Estado:* Diseño aprobado, pendiente implementación
*Lema:* JESUCRISTO NUESTRO SEÑOR

---

## 1. CONTEXTO

### Estado actual (cierre Fase 6)
- Bot corriendo en Docker en VPS AWS Frankfurt (63.177.89.167)
- Contenedores: trendguard-bot, trendguard-panel
- Estrategia: SMA200 + Donchian55 + Trailing 3 ATR + velas 1d
- Riesgo fijo: 2% por operación
- Modo: Demo (Binance Testnet)
- Panel: http://63.177.89.167:8501
- *Reportes Telegram cada 15 min: ARREGLADO Y CONFIRMADO el 7-oct-2026*
- Bug resuelto: price=None cuando no había señal, rompía el reporte

### Estado objetivo (cierre Fase 7)
- Protección de drawdown diario
- Riesgo configurable por activo
- Soporte multi-activo: BTC, ETH, SOL en paralelo
- Detección de correlación entre activos
- Todo configurable vía runtime_config.json
- Producción sigue corriendo sin interrupción

---

## 2. DECISIONES APROBADAS

### Bloque 1 — Protección contra Drawdown
- Límite diario: 3%
- Métrica: Equity (balance + PnL no realizado)
- Reset: 00:00 UTC
- Acción al disparar: OPCIÓN A (cerrar posición + no abrir más hoy)
- Notificación: Telegram obligatorio (inmediata + en cada reporte de 15 min)

### Bloque 2 — Riesgo dinámico
- Modo: 2% FIJO por operación
- Motivo: simple, predecible, fácil de explicar al cliente
- Futuro: revisar en Fase 9 si hay clientes con cuentas grandes

### Bloque 3 — Multi-activo
- Activos: BTC, ETH, SOL
- Modo: operación en paralelo (los 3 a la vez)
- Indicadores: cada activo con su propia SMA200, Donchian55, ATR
- State: un solo state.json con estructura por símbolo
- Config: cada activo se activa/desactiva desde runtime_config.json

### Bloque 4 — Correlación entre activos (sistema por tramos)
- > 0.85 → BLOQUEAR nueva entrada
- 0.70 a 0.85 → ABRIR con mitad de riesgo (1%)
- < 0.70 → ABRIR normal (2%)
- Ventana: 30 días de velas diarias
- Métrica: correlación de Pearson sobre retornos diarios

### Bloque 5 — Orden de implementación
1. Drawdown diario (más urgente)
2. Riesgo configurable (rápido)
3. Multi-activo (grande, requiere refactor)
4. Correlación (encima de multi-activo)

---

## 3. MODELO DE NEGOCIO

### Productos
| Producto | Precio | Incluye |
|---|---|---|
| TrendGuard Kit (DIY) | $249 pago único | Docker image privada + docs + guía. Código NO incluido. 15 días soporte email |
| TrendGuard Armado | $549 pago único + $29/mes | Setup completo (VPS, Docker, API, panel, dominio, SSL). Soporte 30 días |
| Licencia Revendedor | $3,500 pago único | Código fuente + derecho a revender. Sin soporte |
| Soporte Premium | $49/mes | Soporte prioritario + actualizaciones |

### 3 errores evitados
1. NO vender código fuente barato (se piratea)
2. NO vender solo con pago único (modelo muerto)
3. NO incluir soporte eterno sin cobro

### Responsabilidad legal
- TrendGuard es HERRAMIENTA, no servicio de inversión
- Cliente es el único responsable de sus decisiones y su dinero
- ToS y disclaimers obligatorios antes de vender
- NUNCA prometer rentabilidad

---

## 4. ARQUITECTURA TÉCNICA

### Estructura de archivos objetivo
trendguard/
- bot.py                    (motor principal multi-activo)
- config.py                 (NO TOCAR)
- indicators.py             (NO TOCAR)
- strategy.py               (extender, no romper)
- notifier.py               (NO TOCAR)
- risk_manager.py           (NUEVO - drawdown y correlación)
- multi_asset.py            (NUEVO - manejo BTC/ETH/SOL)
- runtime_config.json       (config editable)
- state.json                (estado persistido)
- docs/
  - fase7_design.md         (este archivo)
- panel/
  - app.py
  - requirements.txt
- Dockerfile
- docker-compose.yml
- .env

### Nuevos campos en runtime_config.json
{
  "assets": {
    "BTC/USDT": { "enabled": true,  "risk_per_trade": 0.02 },
    "ETH/USDT": { "enabled": true,  "risk_per_trade": 0.02 },
    "SOL/USDT": { "enabled": true,  "risk_per_trade": 0.02 }
  },
  "drawdown": {
    "max_daily_pct": 0.03,
    "reset_hour_utc": 0,
    "action": "close_and_stop"
  },
  "correlation": {
    "window_days": 30,
    "block_threshold": 0.85,
    "half_risk_threshold": 0.70
  }
}

### Estructura de state.json objetivo
{
  "BTC/USDT": {
    "current_position": "long",
    "entry_price": 85935.60,
    "max_price": 86500.00,
    "min_price": null,
    "cantidad": 0.0886
  },
  "ETH/USDT": { "current_position": null },
  "SOL/USDT": { "current_position": null },
  "drawdown": {
    "date_utc": "2026-10-07",
    "day_start_equity": 5000.0,
    "triggered_today": false
  }
}

### Comportamiento del motor (cada ciclo de 60 seg)
1. Leer equity actual de Binance
2. Chequear drawdown → si > 3%, cerrar todo y no operar más hoy
3. Para cada activo habilitado:
   a. Descargar velas (1d, limit 300)
   b. Calcular indicadores
   c. Evaluar estrategia
   d. Si hay señal entrada:
      - Chequear correlación con posiciones abiertas
      - >0.85 bloquear / 0.70-0.85 half risk / <0.70 normal
      - Ejecutar orden
   e. Si hay señal cierre → cerrar posición
4. Cada 15 min → reporte Telegram con TODOS los activos
5. Cada 60 seg → guardar state.json

---

## 5. PLAN DE IMPLEMENTACIÓN

### Semana 1 (8-14 oct) — Drawdown
- Día 1 (8 oct): crear estructura, risk_manager.py skeleton, extender runtime_config
- Día 2 (9 oct): implementar chequeo drawdown diario
- Día 3 (10 oct): implementar cierre automático + bloqueo
- Día 4 (11 oct): testing drawdown en contenedor test
- Día 5 (12 oct): refactor state.json multi-activo
- Día 6-7 (13-14 oct): descanso / buffer bugs

### Semana 2 (15-21 oct) — Multi-activo
- Día 1: refactor bot.py multi-activo
- Día 2: refactor strategy.py multi-activo
- Día 3: testing multi-activo
- Día 4: implementar cálculo correlación
- Día 5: implementar bloqueo/half-risk
- Día 6-7: testing integral

### Semana 3 (22-28 oct) — Despliegue
- Día 1-3: despliegue producción + monitoreo
- Día 4-5: ajustes según comportamiento
- Día 6-7: buffer bugs

### Semana 4 (29 oct - 4 nov) — Inicio Fase 8
- Licencias
- Panel multi-usuario
- Documentación técnica
- Preparación comercial

### 5-15 nov — Cierre
- Fase 8 completa
- Fase 9 (legal, branding)
- LANZAMIENTO: 15 de noviembre de 2026

---

## 6. CRITERIOS DE ACEPTACIÓN

- Drawdown 3% se dispara correctamente al caer equity 3% en el día
- Al disparar, cierra posición y no abre más hasta reset 00:00 UTC
- Notificación Telegram al disparar
- Los 3 activos operan independientemente
- Cada activo con su SMA200, Donchian55, ATR propios
- state.json mantiene los 3 estados separados
- Correlación calculada con 30 días de velas diarias
- Bloqueo por correlación > 0.85 funciona
- Half risk por correlación 0.70-0.85 funciona
- Reportes Telegram cada 15 min incluyen los 3 activos
- Producción no se cae durante el despliegue
- Bot se recupera automáticamente si Binance falla

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Prob | Impacto | Mitigación |
|---|---|---|---|
| Bug en producción | Media | Alto | Desarrollar en contenedor test, deploy tras 24h prueba |
| Correlación mal calculada | Baja | Medio | Unit tests con datos históricos |
| Drawdown falso positivo | Media | Alto | Log claro + alerta Telegram + override manual |
| 3 activos abren a la vez (6% riesgo) | Media | Alto | Drawdown 3% protege automáticamente |
| Cliente rompe config | Alta | Medio | Validación de runtime_config.json al arrancar |

---

## 8. LO QUE NO SE TOCA (CONGELADO)

- config.py
- indicators.py
- notifier.py
- Lógica SMA200 + Donchian55
- trendguard-bot en producción (sigue corriendo sin interrupción)

---

## 9. PRÓXIMOS PASOS

1. 8 oct (mañana): crear risk_manager.py, multi_asset.py
2. 9 oct: implementar drawdown diario
3. Cada avance: probar en contenedor test, NO tocar producción
4. Cierre Fase 7: documentar + pasar a Fase 8

---

## 10. COMPROMISO

*Lema:* JESUCRISTO NUESTRO SEÑOR
*Fecha objetivo lanzamiento:* 15 de noviembre de 2026
*Principio rector:* Producto sólido > producto rápido

---

Documento redactado 7-oct-2026. Próxima revisión: 8-oct-2026 al iniciar implementación.
