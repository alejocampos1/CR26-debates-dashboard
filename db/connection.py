from contextlib import contextmanager
import psycopg2


@contextmanager
def obtener_conexion(cadena_conexion: str):
    conn = psycopg2.connect(cadena_conexion)
    try:
        yield conn
    finally:
        conn.close()
