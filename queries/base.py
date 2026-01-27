import pandas as pd

fecha_inicio = pd.Timestamp("2026-01-26 17:30:00")
fecha_fin = pd.Timestamp("2026-01-26 22:00:00")

def obtener_menciones_base(conexion):
    query = """
        SELECT
            debate_id,
            candidate,
            platform,
            content_type,
            sentiment_label,
            sentiment_score,
            original_timestamp
        FROM ocdul_debates.mentions_raw
        WHERE
            is_valid = TRUE
            AND original_timestamp >= %(fecha_inicio)s
            AND original_timestamp <= %(fecha_fin)s
    """

    params = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }

    return pd.read_sql(query, conexion, params=params)
