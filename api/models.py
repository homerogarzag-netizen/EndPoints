from typing import Optional
from pydantic import BaseModel, Field

class ExpectedMoveResponse(BaseModel):
    symbol: str = Field(..., description="Ticker subyacente (ej. SPX)")
    price: float = Field(..., description="Último precio spot registrado")
    expected_move: float = Field(..., description="Recorrido esperado calculado")
    upper_bound: float = Field(..., description="Banda superior esperada (precio + expected_move)")
    lower_bound: float = Field(..., description="Banda inferior esperada (precio - expected_move)")
    timestamp: str = Field(..., description="Marca temporal oficial del mercado de Nueva York (America/New_York / ET, ISO-8601 con offset)")

class RegimeResponse(BaseModel):
    symbol: str = Field(..., description="Ticker subyacente (ej. SPX)")
    vix: float = Field(..., description="Nivel actual del índice de volatilidad VIX")
    trend_status: str = Field(..., description="Estado de régimen de tendencia (ej. bullish_expansion, compression)")
    predicted_direction: str = Field(..., description="Sesgo direccional previsto (UP, DOWN, SIDEWAYS)")
    predicted_strength: float = Field(..., description="Confianza o fuerza de la predicción (0.0 a 1.0)")
    timestamp: str = Field(..., description="Marca temporal oficial del mercado de Nueva York (America/New_York / ET, ISO-8601 con offset)")

class LevelsResponse(BaseModel):
    symbol: str = Field(..., description="Ticker subyacente (ej. SPX)")
    price: float = Field(..., description="Último precio spot registrado")
    centroid: float = Field(..., description="Nivel del centroide o punto de equilibrio medio")
    target_close: float = Field(..., description="Precio objetivo estimado para el cierre de sesión")
    deviation_from_centroid: float = Field(..., description="Desviación actual respecto al centroide (precio - centroide)")
    distance_to_target: float = Field(..., description="Distancia restante al precio objetivo (target_close - precio)")
    timestamp: str = Field(..., description="Marca temporal oficial del mercado de Nueva York (America/New_York / ET, ISO-8601 con offset)")

class MarketSummaryResponse(BaseModel):
    symbol: str = Field(..., description="Ticker subyacente (ej. SPX)")
    price: float = Field(..., description="Último precio spot registrado")
    expected_move: float = Field(..., description="Recorrido esperado")
    upper_bound: float = Field(..., description="Límite superior esperado")
    lower_bound: float = Field(..., description="Límite inferior esperado")
    vix: float = Field(..., description="Nivel del índice de volatilidad VIX")
    trend_status: str = Field(..., description="Régimen o estado de tendencia")
    predicted_direction: str = Field(..., description="Dirección estimada")
    predicted_strength: float = Field(..., description="Fuerza estimada (0.0 - 1.0)")
    centroid: float = Field(..., description="Centroide")
    target_close: float = Field(..., description="Precio de cierre proyectado")
    deviation_from_centroid: float = Field(..., description="Desviación respecto al centroide")
    distance_to_target: float = Field(..., description="Distancia hacia el objetivo de cierre")
    timestamp: str = Field(..., description="Marca temporal oficial del mercado de Nueva York (America/New_York / ET, ISO-8601 con offset)")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Estado del servicio (healthy / degraded)")
    database_connected: bool = Field(..., description="Indica si Supabase está configurado y responde")
    version: str = Field(..., description="Versión de la API")
