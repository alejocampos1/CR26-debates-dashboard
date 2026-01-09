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
        WHERE is_valid = true
    """

    return pd.read_sql(query, conexion)
