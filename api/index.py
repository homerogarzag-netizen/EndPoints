import json
import time
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse, JSONResponse, HTMLResponse

from api.config import API_TITLE, API_VERSION
from api.models import (
    ExpectedMoveResponse,
    RegimeResponse,
    LevelsResponse,
    MarketSummaryResponse,
    HealthResponse
)
from api.db import get_latest_market_data, check_database_health, get_telemetry_stats
from api.telemetry import record_telemetry

DISCLAIMER = (
    "Disclaimer: AlphaQuant is an automated market data and quantitative modeling service "
    "provided strictly for educational, informational, and computational research purposes. "
    "None of the endpoints, metrics, or algorithmic outputs constitute financial, investment, "
    "legal, or trading advice. Trading options and financial instruments involves substantial "
    "risk of loss. Users and automated agents are solely responsible for their own trading decisions."
)

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "Microservicio de datos de mercado y opciones estructurados para consumo por Agentes de IA.\n\n"
        f"**Legal Disclaimer:**\n> {DISCLAIMER}"
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS abierto para agentes y clientes web sin restricciones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def vercel_path_normalizer(request: Request, call_next):
    """
    Normaliza la ruta ASGI en caso de que Vercel reescriba la petición a /api/index.py o /api/index.
    """
    path = request.scope.get("path", "")
    if path in ["/api/index.py", "/api/index", "/api"]:
        request.scope["path"] = "/"
    return await call_next(request)


LLMS_TXT_PATH = Path(__file__).resolve().parent.parent / "public" / "llms.txt"
DASHBOARD_HTML_PATH = Path(__file__).resolve().parent / "dashboard.html"
FALLBACK_DASHBOARD_PATH = Path(__file__).resolve().parent.parent / "public" / "dashboard.html"


@app.get("/dashboard", response_class=HTMLResponse, summary="Panel de control visual de telemetría y consola interactiva de pruebas")
@app.get("/api/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard():
    if DASHBOARD_HTML_PATH.exists():
        return HTMLResponse(content=DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))
    elif FALLBACK_DASHBOARD_PATH.exists():
        return HTMLResponse(content=FALLBACK_DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard file not found</h1>", status_code=404)


@app.get("/", summary="Ruta principal con metadatos y enlaces de descubrimiento")
@app.get("/api", include_in_schema=False)
@app.get("/api/index", include_in_schema=False)
@app.get("/api/index.py", include_in_schema=False)
async def root(request: Request, background_tasks: BackgroundTasks):
    start = time.perf_counter()
    duration_ms = (time.perf_counter() - start) * 1000
    
    background_tasks.add_task(
        record_telemetry,
        endpoint="/",
        method="GET",
        user_agent=request.headers.get("user-agent", ""),
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
        response_time_ms=duration_ms,
        status_code=200
    )

    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "status": "operational",
        "documentation": "/docs",
        "dashboard": "/dashboard",
        "llms_discovery": "/llms.txt",
        "endpoints": [
            "/v1/market/expected-move",
            "/v1/market/regime",
            "/v1/market/levels",
            "/v1/market/summary",
            "/v1/telemetry/stats"
        ],
        "disclaimer": DISCLAIMER
    }


@app.get("/llms.txt", response_class=PlainTextResponse, summary="Manifiesto llms.txt para motores de IA")
@app.get("/api/llms.txt", response_class=PlainTextResponse, include_in_schema=False)
async def get_llms_txt(request: Request, background_tasks: BackgroundTasks):
    start = time.perf_counter()
    content = ""
    if LLMS_TXT_PATH.exists():
        content = LLMS_TXT_PATH.read_text(encoding="utf-8")
    else:
        content = f"# {API_TITLE}\nEndpoints disponibles en /v1/market/summary"

    duration_ms = (time.perf_counter() - start) * 1000
    background_tasks.add_task(
        record_telemetry,
        endpoint="/llms.txt",
        method="GET",
        user_agent=request.headers.get("user-agent", ""),
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
        response_time_ms=duration_ms,
        status_code=200
    )

    return PlainTextResponse(content, media_type="text/plain")


@app.get("/health", response_model=HealthResponse, summary="Verificación de estado de la API")
@app.get("/api/health", response_model=HealthResponse, include_in_schema=False)
async def health():
    db_ok = await check_database_health()
    return HealthResponse(
        status="healthy" if db_ok else "degraded (mock active)",
        database_connected=db_ok,
        version=API_VERSION
    )


@app.get("/api/docs", include_in_schema=False)
async def redirect_api_docs():
    return RedirectResponse(url="/docs")


@app.get("/v1/telemetry/stats", summary="Métricas de telemetría y demanda de agentes en tiempo real")
@app.get("/api/v1/telemetry/stats", include_in_schema=False)
async def get_stats():
    return await get_telemetry_stats()


@app.get(
    "/v1/market/expected-move",
    response_model=ExpectedMoveResponse,
    summary="Rango de volatilidad y recorrido esperado (Expected Move)"
)
@app.get("/api/v1/market/expected-move", response_model=ExpectedMoveResponse, include_in_schema=False)
async def get_expected_move(request: Request, background_tasks: BackgroundTasks):
    start = time.perf_counter()
    data = await get_latest_market_data()

    price = data["price"]
    em = data["expected_move"]
    upper = round(price + em, 2)
    lower = round(price - em, 2)

    duration_ms = (time.perf_counter() - start) * 1000
    background_tasks.add_task(
        record_telemetry,
        endpoint="/v1/market/expected-move",
        method="GET",
        user_agent=request.headers.get("user-agent", ""),
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
        response_time_ms=duration_ms,
        status_code=200
    )

    return ExpectedMoveResponse(
        symbol=data.get("symbol", "SPX"),
        price=price,
        expected_move=em,
        upper_bound=upper,
        lower_bound=lower,
        timestamp=data.get("created_at")
    )


@app.get(
    "/v1/market/regime",
    response_model=RegimeResponse,
    summary="Régimen de mercado, VIX y sesgo direccional pronosticado"
)
@app.get("/api/v1/market/regime", response_model=RegimeResponse, include_in_schema=False)
async def get_regime(request: Request, background_tasks: BackgroundTasks):
    start = time.perf_counter()
    data = await get_latest_market_data()

    duration_ms = (time.perf_counter() - start) * 1000
    background_tasks.add_task(
        record_telemetry,
        endpoint="/v1/market/regime",
        method="GET",
        user_agent=request.headers.get("user-agent", ""),
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
        response_time_ms=duration_ms,
        status_code=200
    )

    return RegimeResponse(
        symbol=data.get("symbol", "SPX"),
        vix=data["vix"],
        trend_status=data["trend_status"],
        predicted_direction=data["predicted_direction"],
        predicted_strength=data["predicted_strength"],
        timestamp=data.get("created_at")
    )


@app.get(
    "/v1/market/levels",
    response_model=LevelsResponse,
    summary="Niveles objetivo de cierre y centroide de reversión"
)
@app.get("/api/v1/market/levels", response_model=LevelsResponse, include_in_schema=False)
async def get_levels(request: Request, background_tasks: BackgroundTasks):
    start = time.perf_counter()
    data = await get_latest_market_data()

    price = data["price"]
    centroid = data["centroid"]
    target_close = data["target_close"]
    deviation = round(price - centroid, 2)
    dist_target = round(target_close - price, 2)

    duration_ms = (time.perf_counter() - start) * 1000
    background_tasks.add_task(
        record_telemetry,
        endpoint="/v1/market/levels",
        method="GET",
        user_agent=request.headers.get("user-agent", ""),
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
        response_time_ms=duration_ms,
        status_code=200
    )

    return LevelsResponse(
        symbol=data.get("symbol", "SPX"),
        price=price,
        centroid=centroid,
        target_close=target_close,
        deviation_from_centroid=deviation,
        distance_to_target=dist_target,
        timestamp=data.get("created_at")
    )


@app.get(
    "/v1/market/summary",
    response_model=MarketSummaryResponse,
    summary="Resumen consolidado de la sesión en un solo payload compacto"
)
@app.get("/api/v1/market/summary", response_model=MarketSummaryResponse, include_in_schema=False)
async def get_summary(request: Request, background_tasks: BackgroundTasks):
    start = time.perf_counter()
    data = await get_latest_market_data()

    price = data["price"]
    em = data["expected_move"]
    centroid = data["centroid"]
    target_close = data["target_close"]

    duration_ms = (time.perf_counter() - start) * 1000
    background_tasks.add_task(
        record_telemetry,
        endpoint="/v1/market/summary",
        method="GET",
        user_agent=request.headers.get("user-agent", ""),
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
        response_time_ms=duration_ms,
        status_code=200
    )

    return MarketSummaryResponse(
        symbol=data.get("symbol", "SPX"),
        price=price,
        expected_move=em,
        upper_bound=round(price + em, 2),
        lower_bound=round(price - em, 2),
        vix=data["vix"],
        trend_status=data["trend_status"],
        predicted_direction=data["predicted_direction"],
        predicted_strength=data["predicted_strength"],
        centroid=centroid,
        target_close=target_close,
        deviation_from_centroid=round(price - centroid, 2),
        distance_to_target=round(target_close - price, 2),
        timestamp=data.get("created_at")
    )


MCP_TOOLS_METADATA = [
    {
        "name": "get_market_summary",
        "description": "Obtiene el resumen cuantitativo completo de SPX en un solo payload: precio spot, Expected Move (0DTE), bandas de volatilidad, VIX, tendencia, centroide y precio objetivo de cierre.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "name": "get_expected_move",
        "description": "Obtiene el rango de volatilidad y recorrido esperado para la sesión (0DTE/SPX), incluyendo el límite superior (upper_bound) y límite inferior (lower_bound).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "name": "get_market_regime",
        "description": "Obtiene el nivel de VIX, régimen de tendencia actual y sesgo direccional pronosticado con porcentaje de confianza.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "name": "get_reversion_levels",
        "description": "Obtiene los niveles cuantitativos de reversión a la media: centroide de equilibrio, precio objetivo de cierre (target_close) y desviaciones.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    }
]


@app.api_route("/mcp", methods=["GET", "POST"], summary="Endpoint HTTP Streamable para el protocolo MCP (Smithery / Agentes)")
@app.api_route("/api/mcp", methods=["GET", "POST"], include_in_schema=False)
async def mcp_streamable_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint Streamable HTTP compatible con el protocolo MCP (Model Context Protocol).
    Permite registrar la API directamente en Smithery.ai y pasarelas de agentes.
    """
    if request.method == "GET":
        return {
            "status": "ready",
            "protocol": "mcp",
            "version": "2024-11-05",
            "server": "AlphaQuant-MCP",
            "tools": [t["name"] for t in MCP_TOOLS_METADATA]
        }

    start = time.perf_counter()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        )

    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    duration_ms = (time.perf_counter() - start) * 1000
    background_tasks.add_task(
        record_telemetry,
        endpoint=f"/mcp?method={method}",
        method="POST",
        user_agent=request.headers.get("user-agent", ""),
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
        response_time_ms=duration_ms,
        status_code=200
    )

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "AlphaQuant-MCP",
                    "version": "1.0.0",
                    "description": "Real-time quantitative options analytics, SPX 0DTE Expected Move, VIX volatility regimes, and mean-reversion levels for autonomous trading agents."
                },
                "instructions": (
                    "AlphaQuant provides real-time quantitative options metrics for SPX. "
                    "Use get_market_summary for a consolidated snapshot, get_expected_move for intraday/0DTE volatility boundaries, "
                    "get_market_regime for trend and direction confidence, and get_reversion_levels for centroid and close targets. "
                    "All data is for research and computational purposes."
                )
            }
        }

    elif method in ["notifications/initialized", "initialized"]:
        return JSONResponse(status_code=200, content={})

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS_METADATA
            }
        }

    elif method == "resources/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}}

    elif method == "prompts/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "prompts": [
                    {
                        "name": "analyze_spx_market_conditions",
                        "description": "Analiza el estado cuantitativo actual del mercado SPX (Expected Move, VIX, sesgo y reversión).",
                        "arguments": []
                    },
                    {
                        "name": "check_0dte_expected_move",
                        "description": "Evalúa el rango esperado 0DTE y bandas superior e inferior para la sesión.",
                        "arguments": []
                    }
                ]
            }
        }

    elif method == "prompts/get":
        prompt_name = params.get("name", "analyze_spx_market_conditions")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "description": f"Instrucción para {prompt_name}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Ejecuta el análisis de {prompt_name} llamando a la herramienta get_market_summary y entrega un reporte cuantitativo conciso."
                        }
                    }
                ]
            }
        }

    elif method == "ai.smithery/events/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"events": []}}

    elif method == "tools/call":
        tool_name = params.get("name")
        data = await get_latest_market_data()

        if tool_name == "get_market_summary":
            price = data["price"]
            em = data["expected_move"]
            res = {
                "symbol": data.get("symbol", "SPX"),
                "price": price,
                "expected_move": em,
                "upper_bound": round(price + em, 2),
                "lower_bound": round(price - em, 2),
                "vix": data["vix"],
                "trend_status": data["trend_status"],
                "predicted_direction": data["predicted_direction"],
                "predicted_strength": data["predicted_strength"],
                "centroid": data["centroid"],
                "target_close": data["target_close"],
                "deviation_from_centroid": round(price - data["centroid"], 2),
                "distance_to_target": round(data["target_close"] - price, 2),
                "timestamp": data.get("created_at")
            }
        elif tool_name == "get_expected_move":
            price = data["price"]
            em = data["expected_move"]
            res = {
                "symbol": data.get("symbol", "SPX"),
                "price": price,
                "expected_move": em,
                "upper_bound": round(price + em, 2),
                "lower_bound": round(price - em, 2),
                "timestamp": data.get("created_at")
            }
        elif tool_name == "get_market_regime":
            res = {
                "symbol": data.get("symbol", "SPX"),
                "vix": data["vix"],
                "trend_status": data["trend_status"],
                "predicted_direction": data["predicted_direction"],
                "predicted_strength": data["predicted_strength"],
                "timestamp": data.get("created_at")
            }
        elif tool_name == "get_reversion_levels":
            price = data["price"]
            res = {
                "symbol": data.get("symbol", "SPX"),
                "price": price,
                "centroid": data["centroid"],
                "target_close": data["target_close"],
                "deviation_from_centroid": round(price - data["centroid"], 2),
                "distance_to_target": round(data["target_close"] - price, 2),
                "timestamp": data.get("created_at")
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Herramienta desconocida: {tool_name}"}
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(res, indent=2, ensure_ascii=False)
                    }
                ]
            }
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Método no soportado: {method}"}
        }
