import os

CADENA_CONEXION_POSTGRES = os.getenv(
    "CADENA_CONEXION_POSTGRES",
    "postgresql://usuario:password@host:5432/base"
)

ESQUEMA_DB = os.getenv("ESQUEMA_DB", "ocdul_debates")

CANDIDATOS_DEBATE = [
    "Eliécer Feinzaig",
    "Claudia Dobles",
    "Fabricio Alvarado",
    "Ana Virginia Calzada",
    "Natalia Díaz",
    "José Aguilar Berrocal",
    "Ariel Robles",
    "Juan Carlos Hidalgo",
]