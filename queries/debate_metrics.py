import pandas as pd
from config.settings import CANDIDATOS_DEBATE

# =========================
# Ventana temporal del debate
# =========================
FECHA_INICIO = pd.Timestamp("2026-01-29 18:30:00")
FECHA_FIN = pd.Timestamp("2026-01-29 22:00:00")


# =========================
# Ranking de sentimiento
# =========================
def obtener_ranking_sentimiento(conexion, debate_id: str, candidatos: list[str]):
    query = """
    WITH base AS (
        SELECT
            candidate,
            COUNT(*) AS total_menciones,
            SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positivas,
            SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negativas
        FROM ocdul_debates.mentions_raw
        WHERE
            debate_id = %(debate_id)s
            AND is_valid = TRUE
            AND candidate = ANY(%(candidatos)s)
            AND original_timestamp >= %(fecha_inicio)s
            AND original_timestamp <= %(fecha_fin)s
        GROUP BY candidate
    )
    SELECT
        candidate,
        total_menciones,
        positivas,
        negativas,
        (positivas - negativas)::float / NULLIF(total_menciones, 0) AS balance_sentimiento
    FROM base
    ORDER BY total_menciones DESC;
    """

    with conexion.cursor() as cur:
        cur.execute(
            query,
            {
                "debate_id": debate_id,
                "candidatos": candidatos,
                "fecha_inicio": FECHA_INICIO,
                "fecha_fin": FECHA_FIN,
            },
        )
        return cur.fetchall()


# =========================
# Sentimiento por candidato
# =========================
def obtener_sentimiento_por_candidato(conexion, debate_id: str, candidatos: list[str]):
    query = """
    SELECT
        candidate,
        sentiment_label,
        COUNT(*) AS total
    FROM ocdul_debates.mentions_raw
    WHERE
        debate_id = %(debate_id)s
        AND is_valid = TRUE
        AND candidate = ANY(%(candidatos)s)
        AND original_timestamp >= %(fecha_inicio)s
        AND original_timestamp <= %(fecha_fin)s
    GROUP BY candidate, sentiment_label;
    """

    with conexion.cursor() as cur:
        cur.execute(
            query,
            {
                "debate_id": debate_id,
                "candidatos": candidatos,
                "fecha_inicio": FECHA_INICIO,
                "fecha_fin": FECHA_FIN,
            },
        )
        return cur.fetchall()


# =========================
# Menciones por red y tipo
# =========================
def obtener_menciones_por_red(conexion, debate_id: str, candidatos: list[str]):
    query = """
    SELECT
        platform,
        content_type,
        COUNT(*) AS total
    FROM ocdul_debates.mentions_raw
    WHERE
        debate_id = %(debate_id)s
        AND is_valid = TRUE
        AND candidate = ANY(%(candidatos)s)
        AND original_timestamp >= %(fecha_inicio)s
        AND original_timestamp <= %(fecha_fin)s
    GROUP BY platform, content_type
    ORDER BY total DESC;
    """

    with conexion.cursor() as cur:
        cur.execute(
            query,
            {
                "debate_id": debate_id,
                "candidatos": candidatos,
                "fecha_inicio": FECHA_INICIO,
                "fecha_fin": FECHA_FIN,
            },
        )
        return cur.fetchall()


# =========================
# Volumen temporal por candidato
# =========================
def obtener_volumen_temporal_por_candidato(
    conexion,
    debate_id: str,
    candidatos: list[str],
    intervalo_minutos: int = 15,
):
    query = """
    SELECT
        to_timestamp(
            floor(
                extract(epoch from original_timestamp)
                / (%(intervalo)s * 60)
            ) * (%(intervalo)s * 60)
        ) AS tiempo,
        candidate,
        COUNT(*) AS total
    FROM ocdul_debates.mentions_raw
    WHERE
        debate_id = %(debate_id)s
        AND is_valid = TRUE
        AND candidate = ANY(%(candidatos)s)
        AND original_timestamp >= %(fecha_inicio)s
        AND original_timestamp <= %(fecha_fin)s
    GROUP BY 1, 2
    ORDER BY 1 ASC;
    """

    with conexion.cursor() as cursor:
        cursor.execute(
            query,
            {
                "debate_id": debate_id,
                "candidatos": candidatos,
                "intervalo": intervalo_minutos,
                "fecha_inicio": FECHA_INICIO,
                "fecha_fin": FECHA_FIN,
            },
        )
        return cursor.fetchall()


# =========================
# Sentimiento en vivo vs general
# =========================
def obtener_sentimiento_en_vivo_vs_general(
    conexion, debate_id: str, candidatos: list[str]
):
    query = """
        -- EN VIVO
        SELECT
            candidate,
            'En vivo' AS fuente,
            sentiment_label,
            COUNT(*) AS total
        FROM ocdul_debates.mentions_raw
        WHERE
            debate_id = %(debate_id)s
            AND is_valid = TRUE
            AND candidate = ANY(%(candidatos)s)
            AND content_type = 'live_comment'
            AND original_timestamp >= %(fecha_inicio)s
            AND original_timestamp <= %(fecha_fin)s
        GROUP BY candidate, sentiment_label

        UNION ALL

        -- GENERAL (SIN LIVE)
        SELECT
            candidate,
            'General' AS fuente,
            sentiment_label,
            COUNT(*) AS total
        FROM ocdul_debates.mentions_raw
        WHERE
            debate_id = %(debate_id)s
            AND is_valid = TRUE
            AND candidate = ANY(%(candidatos)s)
            AND content_type <> 'live_comment'
            AND original_timestamp >= %(fecha_inicio)s
            AND original_timestamp <= %(fecha_fin)s
        GROUP BY candidate, sentiment_label;
    """

    with conexion.cursor() as cur:
        cur.execute(
            query,
            {
                "debate_id": debate_id,
                "candidatos": candidatos,
                "fecha_inicio": FECHA_INICIO,
                "fecha_fin": FECHA_FIN,
            },
        )
        return cur.fetchall()
