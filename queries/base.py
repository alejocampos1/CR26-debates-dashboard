import pandas as pd


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
                AND original_timestamp >= TIMESTAMP '2026-01-09 18:00:00';
            """

    return pd.read_sql(query, conexion)
