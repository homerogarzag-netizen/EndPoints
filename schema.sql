-- =========================================================================
-- Schema SQL: Sonda de Telemetría y Tabla de Mercado para Agentes de IA
-- Ejecuta este script en el editor SQL de Supabase (SQL Editor).
-- =========================================================================

-- 1. Tabla de Telemetría (Sonda de demanda para Agentes)
CREATE TABLE IF NOT EXISTS public.telemetria_sonda (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    endpoint TEXT NOT NULL,
    method TEXT DEFAULT 'GET',
    user_agent TEXT,
    caller_type TEXT,                -- 'ai_agent', 'python_client', 'mcp_client', 'browser', 'unknown'
    query_params JSONB DEFAULT '{}'::jsonb,
    ip_hash TEXT,
    status_code INTEGER DEFAULT 200,
    response_time_ms NUMERIC(8, 2)
);

-- Índices para consultas analíticas rápidas de demanda
CREATE INDEX IF NOT EXISTS idx_telemetria_created_at ON public.telemetria_sonda (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_telemetria_endpoint ON public.telemetria_sonda (endpoint);
CREATE INDEX IF NOT EXISTS idx_telemetria_caller_type ON public.telemetria_sonda (caller_type);

-- Habilitar RLS (Row Level Security) y permitir inserciones de la API
ALTER TABLE public.telemetria_sonda ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir insercion anonima a telemetria"
    ON public.telemetria_sonda
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Permitir lectura a servicio"
    ON public.telemetria_sonda
    FOR SELECT
    USING (true);


-- 2. Estructura de referencia para 'market_logs' (si aún no la tienes creada)
CREATE TABLE IF NOT EXISTS public.market_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    symbol TEXT DEFAULT 'SPX',
    price NUMERIC(12, 4) NOT NULL,
    expected_move NUMERIC(12, 4) NOT NULL,
    vix NUMERIC(8, 2) NOT NULL,
    trend_status TEXT NOT NULL,              -- e.g. 'bullish', 'bearish', 'neutral', 'compression'
    centroid NUMERIC(12, 4) NOT NULL,
    target_close NUMERIC(12, 4) NOT NULL,
    predicted_direction TEXT NOT NULL,       -- e.g. 'UP', 'DOWN', 'SIDEWAYS'
    predicted_strength NUMERIC(5, 2) NOT NULL -- e.g. 0.85 (0.0 to 1.0)
);

CREATE INDEX IF NOT EXISTS idx_market_logs_created_at ON public.market_logs (created_at DESC);

-- Habilitar RLS en market_logs y permitir lectura pública
ALTER TABLE public.market_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir lectura publica a market_logs"
    ON public.market_logs
    FOR SELECT
    USING (true);

-- 3. Fila de prueba inicial (por si quieres probar inmediatamente)
INSERT INTO public.market_logs (
    symbol, price, expected_move, vix, trend_status, centroid, target_close, predicted_direction, predicted_strength
) VALUES (
    'SPX', 5845.20, 24.50, 15.80, 'bullish_expansion', 5838.00, 5860.00, 'UP', 0.78
) ON CONFLICT DO NOTHING;
