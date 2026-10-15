import time
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse

from api.config import API_TITLE, API_VERSION
from api.models import (
    ExpectedMoveResponse,
    RegimeResponse,
    LevelsResponse,
    MarketSummaryResponse,
    HealthResponse
)
from api.db import get_latest_market_data, check_database_health
from api.telemetry import record_telemetry

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="Microservicio de datos de mercado y opciones estructurados para consumo por Agentes de IA.",
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


@app.get("/", summary="Ruta principal con metadatos y enlaces de descubrimiento")
@app.get("/api", summary="Ruta principal con prefijo /api")
@app.get("/api/index", summary="Ruta principal /api/index")
@app.get("/api/index.py", summary="Ruta principal /api/index.py")
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
        "llms_discovery": "/llms.txt",
        "endpoints": [
            "/v1/market/expected-move",
            "/v1/market/regime",
            "/v1/market/levels",
            "/v1/market/summary"
        ]
    }


@app.get("/llms.txt", response_class=PlainTextResponse, summary="Manifiesto llms.txt para motores de IA")
@app.get("/api/llms.txt", response_class=PlainTextResponse)
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
@app.get("/api/health", response_model=HealthResponse)
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
