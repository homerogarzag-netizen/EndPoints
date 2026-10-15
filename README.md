# AlphaQuant - Market Intelligence API for AI Agents 🚀

Microservicio en Python diseñado para ejecutarse como función **Serverless en Vercel**, entregando datos estructurados de opciones, volatilidad y niveles cuantitativos de mercado directamente a **Agentes de IA**, LLMs y sistemas algorítmicos.

---

## ⚡ Estructura del Proyecto

```text
.
├── api/
│   ├── __init__.py
│   ├── index.py           # Entrypoint FastAPI (CORS, rutas y background tasks)
│   ├── config.py          # Variables de entorno y ajustes
│   ├── db.py              # Conexión asíncrona a Supabase (market_logs)
│   ├── models.py          # Modelos Pydantic optimizados para tokens
│   └── telemetry.py       # Sonda de demanda no bloqueante (telemetria_sonda)
├── public/
│   └── llms.txt           # Especificación estándar para indexación de Agentes
├── .env.example           # Plantilla de variables de entorno
├── requirements.txt       # Dependencias mínimas de producción
├── schema.sql             # Script SQL para tablas de Supabase
├── vercel.json            # Configuración de rutas para Vercel Serverless
└── README.md
```

---

## 🛠️ Paso 1: Configurar Supabase

1. Abre tu panel en [Supabase](https://supabase.com) e ingresa al **SQL Editor**.
2. Copia y ejecuta el contenido de [`schema.sql`](./schema.sql).
   - Crea la tabla de telemetría `telemetria_sonda` con sus índices analíticos.
   - Crea (si no existe) la tabla `market_logs` y agrega un registro de prueba.
3. Copia tu **Project URL** y tu **Anon / Service Key** desde *Project Settings -> API*.

---

## 💻 Paso 2: Ejecución y Pruebas Locales

1. Activa tu entorno virtual e instala dependencias:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configura tu archivo `.env`:
   ```bash
   cp .env.example .env
   # Edita .env con tus credenciales de Supabase
   ```
   *(Nota: Si no configuras las variables inmediatamente, la API iniciará en modo mock con datos simulados sin romperse).*

3. Inicia el servidor de desarrollo:
   ```bash
   uvicorn api.index:app --reload --port 8000
   ```

4. Explora las rutas en tu navegador:
   - **Documentación Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Manifiesto para Agentes:** [http://localhost:8000/llms.txt](http://localhost:8000/llms.txt)
   - **Expected Move:** [http://localhost:8000/v1/market/expected-move](http://localhost:8000/v1/market/expected-move)
   - **Régimen de Mercado:** [http://localhost:8000/v1/market/regime](http://localhost:8000/v1/market/regime)
   - **Niveles Cuantitativos:** [http://localhost:8000/v1/market/levels](http://localhost:8000/v1/market/levels)
   - **Resumen Completo:** [http://localhost:8000/v1/market/summary](http://localhost:8000/v1/market/summary)

---

## ☁️ Paso 3: Despliegue en Vercel

### Opción A: Vercel CLI (Más rápido)
```bash
npm i -g vercel
vercel
```
Durante el asistente de Vercel, agrega las variables de entorno `SUPABASE_URL` y `SUPABASE_KEY`.

### Opción B: Repositorio en GitHub
1. Sube este proyecto a tu repositorio de GitHub.
2. Ve a [Vercel Dashboard](https://vercel.com/new), importa el repositorio.
3. En la sección **Environment Variables**, añade:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
4. Presiona **Deploy**. Vercel detectará automáticamente `vercel.json` y la carpeta `api/`.

---

## 📡 Paso 4: La Estrategia del Sondeo de Demanda

Una vez desplegada tu API:

1. **Registra tus endpoints en el ecosistema:**
   - Publica un servidor MCP o añade tu API en directorios como Smithery.ai, Glama.ai o mcp.so.
   - Publica un post o issue en foros y repositorios de agentes de trading (como trading-agents, CrewAI, LangChain).
2. **Monitorea `telemetria_sonda` en Supabase:**
   - Ejecuta consultas como:
     ```sql
     -- ¿Qué endpoint es el más consultado?
     SELECT endpoint, count(*) as peticiones 
     FROM telemetria_sonda 
     GROUP BY endpoint 
     ORDER BY peticiones DESC;

     -- ¿Qué tipo de clientes nos llaman?
     SELECT caller_type, count(*) as total 
     FROM telemetria_sonda 
     GROUP BY caller_type;
     ```
3. **Pivote y Monetización:**
   - El endpoint con más volumen de llamadas de `ai_agent` y `python_client` es tu producto estrella para empaquetar con claves API de pago (mediante Zuplo, Unkey o Stripe).

---

## ⚖️ Legal Disclaimer

> **Disclaimer:** AlphaQuant is an automated market data and quantitative modeling service provided strictly for educational, informational, and computational research purposes. None of the endpoints, metrics, or algorithmic outputs constitute financial, investment, legal, or trading advice. Trading options and financial instruments involves substantial risk of loss. Users and automated agents are solely responsible for their own trading decisions.
