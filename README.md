# AlphaQuant - Market Intelligence API for AI Agents 🚀

[![Production API](https://img.shields.io/badge/Production%20API-Online-success?style=for-the-badge&logo=vercel)](https://end-points.vercel.app/)
[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-Ops%20Monitor-10b981?style=for-the-badge&logo=speedtest)](https://end-points.vercel.app/dashboard)
[![Swagger Docs](https://img.shields.io/badge/Swagger-OpenAPI%20Docs-blue?style=for-the-badge&logo=swagger)](https://end-points.vercel.app/docs)
[![Smithery Registry](https://img.shields.io/badge/Smithery-MCP%20Server-orange?style=for-the-badge)](https://smithery.ai/servers/@homero-garza-g/alphaquant)
[![Agent Protocol](https://img.shields.io/badge/LLMs.txt-Agent%20Ready-purple?style=for-the-badge)](https://end-points.vercel.app/llms.txt)

AlphaQuant es un microservicio de alta velocidad y baja latencia diseñado específicamente para **Agentes de IA (Claude, GPT, Cursor, LangChain)** y traders algorítmicos. Entrega datos cuantitativos estructurados derivados del mercado de opciones del **S&P 500 (SPX 0DTE)**: recorrido esperado (Expected Move), régimen de volatilidad (VIX), sesgo direccional y niveles de reversión a la media.

Todas las marcas temporales se entregan formateadas bajo el estándar **ISO-8601 con offset oficial de Nueva York (`America/New_York` / ET)**.

---

## ⚡ Quickstart en 30 Segundos (Zero Setup)

La API pública se encuentra en producción y lista para ser consumida inmediatamente sin llaves de acceso en fase pública:

### 1. Consulta Rápida vía cURL
```bash
curl -s "https://end-points.vercel.app/v1/market/summary" | jq
```

### 2. Integración en Python
```python
import requests

url = "https://end-points.vercel.app/v1/market/summary"
response = requests.get(url, headers={"User-Agent": "QuantBot/1.0"}).json()

print(f"SPX Spot: {response['price']}")
print(f"Rango 0DTE: [{response['lower_bound']} - {response['upper_bound']}] (±{response['expected_move']})")
print(f"Régimen: {response['trend_status']} | Sesgo: {response['predicted_direction']} ({response['predicted_strength']}%)")
print(f"Objetivo de Cierre: {response['target_close']} | Centroide: {response['centroid']}")
print(f"Hora Mercado NY: {response['timestamp']}")
```

### 3. Integración en TypeScript / Node.js
```typescript
const res = await fetch("https://end-points.vercel.app/v1/market/summary");
const data = await res.json();
console.log(`Expected Move SPX: ±${data.expected_move} | Cierre Proyectado: ${data.target_close}`);
```

---

## 🤖 Conexión a Agentes de IA vía MCP (Model Context Protocol)

AlphaQuant está verificado en **Smithery.ai** y expone un endpoint Streamable HTTP compatible con el protocolo MCP.

### Instalación en 1 Clic con Smithery CLI:
```bash
# Para Claude Desktop
npx -y @smithery/cli install @homero-garza-g/alphaquant --client claude

# Para Cursor
npx -y @smithery/cli install @homero-garza-g/alphaquant --client cursor
```

### Configuración Manual en Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "alphaquant": {
      "command": "python3",
      "args": ["-c", "import urllib.request, sys; exec(urllib.request.urlopen('https://raw.githubusercontent.com/homerogarzag-netizen/EndPoints/main/mcp_server.py').read().decode('utf-8'))"]
    }
  }
}
```

### Herramientas MCP Disponibles para Agentes:
- `get_market_summary`: Resumen cuantitativo consolidado completo (precio spot, Expected Move, bandas, VIX, tendencia, centroide y objetivo).
- `get_expected_move`: Recorrido esperado de la sesión y límites superior/inferior.
- `get_market_regime`: Régimen de volatilidad, VIX y sesgo direccional pronosticado.
- `get_reversion_levels`: Centroide cuantitativo y precio objetivo de cierre.
- `submit_feedback_or_request`: Permite al agente solicitar nuevos activos (QQQ, SPY, NVDA) o nuevas métricas algorítmicas.

---

## 📡 Endpoints Públicos

| Endpoint | Descripción | Formato |
| :--- | :--- | :---: |
| `GET /v1/market/summary` | Resumen cuantitativo completo de la sesión en un solo payload compacto | JSON |
| `GET /v1/market/expected-move` | Precio spot, Expected Move (0DTE) y bandas de volatilidad superior/inferior | JSON |
| `GET /v1/market/regime` | Nivel actual de VIX, régimen de tendencia y sesgo pronosticado | JSON |
| `GET /v1/market/levels` | Centroide de reversión a la media y precio objetivo proyectado de cierre | JSON |
| `POST /v1/feedback` | Buzón para solicitar nuevos activos (QQQ, SPY, NVDA) o sugerir métricas | JSON |
| `GET /v1/feedback` | Ranking de demanda y activos más solicitados por la comunidad | JSON |
| `GET /v1/telemetry/stats` | Métricas públicas agregadas de consumo y demanda | JSON |
| `GET /llms.txt` | Manifiesto estándar para motores de IA y LLMs | Texto Plano |
| `GET /docs` | Especificación interactiva Swagger / OpenAPI | UI |

---

## 🗳️ Soporte de Activos & Solicitud de Tickers

- **Activo Base Activo:** `SPX` (S&P 500 Index 0DTE).
- **Sondeo de Nuevos Activos:** Todos los endpoints soportan el parámetro `?symbol=...` (ej. `?symbol=QQQ` o `?symbol=NVDA`). Si consultas un activo aún no integrado, el sistema registra automáticamente tu consulta como un **voto de demanda** para acelerar su lanzamiento en el roadmap.
- **Votación Visual:** Puedes votar directamente por activos como **QQQ, SPY, NVDA, IWM, TSLA y BTC** desde el panel web interactivo en **[/dashboard](https://end-points.vercel.app/dashboard)**.

---

## 📊 Monitor de Telemetría & Consola Web

Accede al panel de control en tiempo real para inspeccionar el estado del sistema, el reloj de Wall Street (ET), las métricas de consumo y probar cada endpoint interactivamente en 1 clic:

👉 **[https://end-points.vercel.app/dashboard](https://end-points.vercel.app/dashboard)**

---

## ⚖️ Legal Disclaimer

> **Disclaimer:** AlphaQuant is an automated market data and quantitative modeling service provided strictly for educational, informational, and computational research purposes. None of the endpoints, metrics, or algorithmic outputs constitute financial, investment, legal, or trading advice. Trading options and financial instruments involves substantial risk of loss. Users and automated agents are solely responsible for their own trading decisions.
