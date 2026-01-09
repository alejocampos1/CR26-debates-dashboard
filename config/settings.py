import os

CADENA_CONEXION_POSTGRES = os.getenv(
    "CADENA_CONEXION_POSTGRES",
    "postgresql://usuario:password@host:5432/base"
)