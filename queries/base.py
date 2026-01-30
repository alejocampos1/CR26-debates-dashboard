import psycopg2
import pandas as pd


def obtener_menciones_base(
    conexion,
    debate_id: str,
    fecha_inicio,
    fecha_fin
) -> pd.DataFrame:
    """
    Obtiene las menciones base (posts y comentarios) de un debate específico,
    filtradas correctamente por ventana temporal y validez.
    """

    query = """
    SELECT
        debate_id,
        candidate,
        platform,
        content_type,
        sentiment_label,
        sentiment_score,
        original_timestamp,
        created_at
    FROM ocdul_debates.mentions_raw
    WHERE
        debate_id = %(debate_id)s
        AND is_valid = TRUE
        AND original_timestamp >= %(fecha_inicio)s
        AND original_timestamp <= %(fecha_fin)s
        AND content_type IN ('post', 'comment')
    ORDER BY original_timestamp ASC
    """

    params = {
        "debate_id": debate_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }

    return pd.read_sql(query, conexion, params=params)
