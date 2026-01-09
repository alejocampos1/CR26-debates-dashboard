def obtener_ranking_sentimiento(conexion, debate_id: str):
    query = """
    WITH base AS (
        SELECT
            candidate,
            COUNT(*) AS total_menciones,
            SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positivas,
            SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negativas
        FROM mentions_raw
        WHERE debate_id = %(debate_id)s
          AND is_valid = TRUE
        GROUP BY candidate
    ),
    filtrado AS (
        SELECT *,
               (positivas - negativas)::float / total_menciones AS balance_sentimiento
        FROM base
        WHERE total_menciones >= 50
    )
    SELECT *
    FROM filtrado
    ORDER BY balance_sentimiento DESC;
    """
    with conexion.cursor() as cur:
        cur.execute(query, {"debate_id": debate_id})
        return cur.fetchall()
