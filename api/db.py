import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
import httpx
from api.config import SUPABASE_URL, SUPABASE_KEY, DEBUG

logger = logging.getLogger("db")

def to_ny_iso_timestamp(raw_ts: Optional[str]) -> str:
    """
    Convierte cualquier marca de tiempo (UTC de Supabase) a la hora oficial de 
    Nueva York (America/New_York / ET) manteniendo el estándar estricto ISO-8601 (offset -04:00 / -05:00).
    """
    if not raw_ts:
        return datetime.now(ZoneInfo("America/New_York")).isoformat()
    try:
        clean_ts = raw_ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ny_dt = dt.astimezone(ZoneInfo("America/New_York"))
        return ny_dt.isoformat()
    except Exception:
        return raw_ts

# Datos de respaldo para pruebas locales o cuando no hay registros aún
MOCK_MARKET_DATA = {
    "symbol": "SPX",
    "price": 5850.25,
    "expected_move": 25.50,
    "vix": 16.20,
    "trend_status": "bullish_expansion",
    "centroid": 5842.00,
    "target_close": 5865.00,
    "predicted_direction": "UP",
    "predicted_strength": 0.82,
    "created_at": datetime.now(ZoneInfo("America/New_York")).isoformat()
}

async def get_latest_market_data(symbol: str = "SPX") -> Dict[str, Any]:
    """
    Obtiene el registro más reciente de la tabla 'market_master' en Supabase para el símbolo especificado.
    Si Supabase no está configurado o falla temporalmente, devuelve datos de respaldo.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        if DEBUG:
            logger.info("Supabase no configurado, utilizando datos mock para desarrollo.")
        mock = MOCK_MARKET_DATA.copy()
        mock["symbol"] = symbol.upper()
        return mock

    clean_sym = (symbol or "SPX").strip().upper()
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json"
    }

    # 1. Intentar consultar la tabla maestra 'market_master'
    try:
        url_master = f"{SUPABASE_URL}/rest/v1/market_master"
        params_master = {
            "select": "*",
            "symbol": f"eq.{clean_sym}",
            "order": "timestamp.desc",
            "limit": 1
        }
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url_master, params=params_master, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0:
                    row = data[0]
                    raw_ts = row.get("timestamp")
                    ny_ts = to_ny_iso_timestamp(raw_ts)
                    return {
                        "symbol": row.get("symbol", clean_sym),
                        "price": float(row.get("spot_price", 0.0)),
                        "expected_move": float(row.get("expected_move", 0.0)),
                        "upper_bound": float(row.get("upper_band", 0.0)),
                        "lower_bound": float(row.get("lower_band", 0.0)),
                        "vix": float(row.get("vix", 0.0)),
                        "trend_status": str(row.get("trend_status", "neutral")),
                        "centroid": float(row.get("centroid", 0.0)) if row.get("centroid") is not None else float(row.get("spot_price", 0.0)),
                        "target_close": float(row.get("target_close", 0.0)) if row.get("target_close") is not None else float(row.get("spot_price", 0.0)),
                        "predicted_direction": str(row.get("predicted_direction", "NEUTRAL")),
                        "predicted_strength": float(row.get("predicted_strength", 50.0)),
                        "call_wall": float(row.get("call_wall", 0.0)) if row.get("call_wall") is not None else None,
                        "put_wall": float(row.get("put_wall", 0.0)) if row.get("put_wall") is not None else None,
                        "zero_gamma": float(row.get("zero_gamma", 0.0)) if row.get("zero_gamma") is not None else None,
                        "net_gex": float(row.get("net_gex", 0.0)) if row.get("net_gex") is not None else None,
                        "net_vanna": float(row.get("net_vanna", 0.0)) if row.get("net_vanna") is not None else None,
                        "put_call_ratio_vol": float(row.get("put_call_ratio_vol", 0.0)) if row.get("put_call_ratio_vol") is not None else None,
                        "put_call_ratio_oi": float(row.get("put_call_ratio_oi", 0.0)) if row.get("put_call_ratio_oi") is not None else None,
                        "created_at": ny_ts
                    }
    except Exception as exc:
        if DEBUG:
            logger.error(f"Excepción al conectar con market_master: {exc}")

    # 2. Fallback a 'market_logs' si clean_sym es SPX
    if clean_sym == "SPX":
        try:
            url_logs = f"{SUPABASE_URL}/rest/v1/market_logs"
            params_logs = {
                "select": "*",
                "order": "created_at.desc",
                "limit": 1
            }
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url_logs, params=params_logs, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        row = data[0]
                        raw_ts = row.get("created_at")
                        ny_ts = to_ny_iso_timestamp(raw_ts)
                        price = float(row.get("price", 0.0))
                        em = float(row.get("expected_move", 0.0))
                        return {
                            "symbol": "SPX",
                            "price": price,
                            "expected_move": em,
                            "upper_bound": round(price + em, 2),
                            "lower_bound": round(price - em, 2),
                            "vix": float(row.get("vix", 0.0)),
                            "trend_status": str(row.get("trend_status", "neutral")),
                            "centroid": float(row.get("centroid", 0.0)),
                            "target_close": float(row.get("target_close", 0.0)),
                            "predicted_direction": str(row.get("predicted_direction", "SIDEWAYS")),
                            "predicted_strength": float(row.get("predicted_strength", 0.0)),
                            "call_wall": None,
                            "put_wall": None,
                            "zero_gamma": None,
                            "net_gex": None,
                            "net_vanna": None,
                            "put_call_ratio_vol": None,
                            "put_call_ratio_oi": None,
                            "created_at": ny_ts
                        }
        except Exception as exc:
            if DEBUG:
                logger.error(f"Excepción al conectar con market_logs: {exc}")

    mock = MOCK_MARKET_DATA.copy()
    mock["symbol"] = clean_sym
    return mock

async def check_database_health() -> bool:
    """Verifica si las credenciales de Supabase están configuradas y responden."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/market_master"
        params = {"select": "id", "limit": 1}
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            return resp.status_code in [200, 206]
    except Exception:
        return False

async def get_telemetry_stats() -> Dict[str, Any]:
    """Obtiene métricas resumidas de la sonda para análisis de demanda."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"total_requests": 0, "by_endpoint": {}, "by_caller": {}}
    
    url = f"{SUPABASE_URL}/rest/v1/telemetria_sonda"
    params = {
        "select": "id,endpoint,caller_type,user_agent,response_time_ms,created_at",
        "order": "created_at.desc",
        "limit": 500
    }
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                rows = resp.json()
                by_endpoint: Dict[str, int] = {}
                by_caller: Dict[str, int] = {}
                total_latency = 0.0
                count = len(rows)

                for r in rows:
                    ep = r.get("endpoint", "unknown")
                    ct = r.get("caller_type", "unknown")
                    by_endpoint[ep] = by_endpoint.get(ep, 0) + 1
                    by_caller[ct] = by_caller.get(ct, 0) + 1
                    total_latency += float(r.get("response_time_ms") or 0.0)

                avg_latency = round(total_latency / count, 2) if count > 0 else 0.0

                recent_calls = []
                for r in rows[:15]:
                    call_copy = dict(r)
                    call_copy["created_at"] = to_ny_iso_timestamp(r.get("created_at"))
                    recent_calls.append(call_copy)

                return {
                    "sample_size": count,
                    "avg_response_time_ms": avg_latency,
                    "demand_by_endpoint": dict(sorted(by_endpoint.items(), key=lambda x: x[1], reverse=True)),
                    "demand_by_caller_type": dict(sorted(by_caller.items(), key=lambda x: x[1], reverse=True)),
                    "recent_calls": recent_calls
                }
    except Exception as exc:
        if DEBUG:
            logger.error(f"Error calculando métricas de telemetría: {exc}")
    
    return {"sample_size": 0, "demand_by_endpoint": {}, "demand_by_caller_type": {}, "recent_calls": []}


async def record_feedback(
    category: str = "ticker_request",
    ticker: Optional[str] = None,
    comment: Optional[str] = None,
    contact_email: Optional[str] = None,
    user_agent: Optional[str] = None,
    client_ip: Optional[str] = None
) -> Optional[int]:
    """
    Registra una sugerencia o voto de ticker en Supabase.
    No bloqueante y tolerante a fallos.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        import hashlib
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16] if client_ip else None
        clean_ticker = ticker.strip().upper() if ticker else None

        payload = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "ticker": clean_ticker,
            "comment": comment.strip() if comment else None,
            "contact_email": contact_email.strip() if contact_email else None,
            "user_agent": user_agent[:255] if user_agent else None,
            "ip_hash": ip_hash
        }

        url = f"{SUPABASE_URL}/rest/v1/feedback_clientes"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in [200, 201]:
                res_data = resp.json()
                if isinstance(res_data, list) and len(res_data) > 0:
                    return res_data[0].get("id")
    except Exception as exc:
        if DEBUG:
            logger.warning(f"Error registrando feedback: {exc}")
    return None


async def get_feedback_summary() -> Dict[str, Any]:
    """
    Obtiene el resumen de sugerencias y ranking de tickers solicitados.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"total_feedback": 0, "top_tickers": {}, "recent_feedback": []}

    url = f"{SUPABASE_URL}/rest/v1/feedback_clientes"
    params = {
        "select": "id,created_at,category,ticker,comment,contact_email",
        "order": "created_at.desc",
        "limit": 200
    }
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                rows = resp.json()
                ticker_counts: Dict[str, int] = {}
                for r in rows:
                    t = r.get("ticker")
                    if t:
                        t = t.strip().upper()
                        ticker_counts[t] = ticker_counts.get(t, 0) + 1

                recent = []
                for r in rows[:15]:
                    c_copy = dict(r)
                    c_copy["created_at"] = to_ny_iso_timestamp(r.get("created_at"))
                    em = c_copy.get("contact_email")
                    if em and "@" in em:
                        parts = em.split("@")
                        c_copy["contact_email"] = f"{parts[0][:2]}***@{parts[1]}"
                    recent.append(c_copy)

                return {
                    "total_feedback": len(rows),
                    "top_tickers": dict(sorted(ticker_counts.items(), key=lambda x: x[1], reverse=True)),
                    "recent_feedback": recent
                }
    except Exception as exc:
        if DEBUG:
            logger.error(f"Error obteniendo resumen de feedback: {exc}")

    return {"total_feedback": 0, "top_tickers": {}, "recent_feedback": []}
