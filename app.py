import time
import streamlit as st
import pandas as pd

from config.settings import CADENA_CONEXION_POSTGRES
from db.connection import obtener_conexion
from queries.base import obtener_menciones_base


st.set_page_config(
    page_title="Debate Presidencial – Monitoreo en Tiempo Real",
    layout="wide",
)

st.title("📊 Debate Presidencial – Conversación Digital")

REFRESH_SEGUNDOS = 30


def cargar_datos():
    with obtener_conexion(CADENA_CONEXION_POSTGRES) as conn:
        return obtener_menciones_base(conn)


placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            df = cargar_datos()

            if df.empty:
                st.info(
                    "⏳ El sistema está activo, pero aún no hay menciones recolectadas."
                )
            else:
                total = len(df)
                st.metric("Total de menciones válidas", total)

                conteo = (
                    df.groupby("candidate")
                    .size()
                    .reset_index(name="menciones")
                )

                st.subheader("Menciones por candidato")
                st.dataframe(conteo, use_container_width=True)

        except Exception as e:
            st.error("Error al consultar la base de datos")
            st.exception(e)

    time.sleep(REFRESH_SEGUNDOS)
    st.experimental_rerun()
