import streamlit as st
import pandas as pd
import altair as alt

from config.settings import CADENA_CONEXION_POSTGRES
from db.connection import obtener_conexion
from queries.debate_metrics import (
    obtener_ranking_sentimiento,
    obtener_sentimiento_por_candidato,
    obtener_menciones_por_red,
)

# --------------------
# Configuración general
# --------------------
st.set_page_config(
    page_title="Debate CR26",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DEBATE_ID = "CR26_PRES_TSE_D1"

# Generar conexión a la base de datos

with obtener_conexion(
    cadena_conexion=CADENA_CONEXION_POSTGRES,
    esquema=ESQUEMA_DB,
) as conexion:
    
    ranking = obtener_ranking_sentimiento(conexion, DEBATE_ID)

    if not ranking:
        st.warning("Aún no hay suficientes menciones para mostrar resultados.")
        st.stop()


    ranking = sorted(ranking, key=lambda x: x[4], reverse=True)

    mejor = ranking[0]
    peor = ranking[-1]

# Garantizar orden correcto por balance de sentimiento
ranking = sorted(ranking, key=lambda x: x[4], reverse=True)

mejor = ranking[0]
peor = ranking[-1]

# --------------------
# HERO: Pulso del debate
# --------------------
st.markdown("## 🔥 Pulso del Debate")

st.markdown("### 🟢 Mejor sentimiento")
st.metric(
    label=mejor[0],
    value=f"{mejor[4]:.2f}",
    delta=f"{mejor[1]} menciones",
)

st.markdown("---")

st.markdown("### 🔴 Peor sentimiento")
st.metric(
    label=peor[0],
    value=f"{peor[4]:.2f}",
    delta=f"{peor[1]} menciones",
)

st.markdown("---")

# --------------------
# Datos de sentimiento por candidato (UNA sola query)
# --------------------
sentimientos = obtener_sentimiento_por_candidato(conexion, DEBATE_ID)
df_sent = pd.DataFrame(
    sentimientos,
    columns=["candidate", "sentiment", "total"],
)

# --------------------
# Bloques por candidato
# --------------------
st.markdown("## 📊 Candidatos")

for candidate, total, pos, neg, balance in ranking:
    with st.container():
        st.subheader(candidate)

        col1, col2, col3 = st.columns(3)
        col1.metric("Menciones", total)
        col2.metric("Positivas", pos)
        col3.metric("Negativas", neg)

        # Barra de sentimiento normalizada (-1 a 1 → 0 a 1)
        progreso = min(max((balance + 1) / 2, 0), 1)
        st.progress(progreso)
        st.caption(f"Balance de sentimiento: {balance:.2f}")

        # Gráfico de sentimiento por candidato
        df_cand = df_sent[df_sent["candidate"] == candidate]

        if not df_cand.empty:
            chart_sent = (
                alt.Chart(df_cand)
                .mark_bar()
                .encode(
                    x=alt.X("sentiment:N", title=""),
                    y=alt.Y("total:Q", title=""),
                    color=alt.Color(
                        "sentiment:N",
                        scale=alt.Scale(
                            domain=["positive", "neutral", "negative"],
                            range=["#2ecc71", "#bdc3c7", "#e74c3c"],
                        ),
                        legend=None,
                    ),
                )
                .properties(height=180)
            )

            st.altair_chart(chart_sent, use_container_width=True)

        st.markdown("---")

# --------------------
# Ranking emocional (comparativo)
# --------------------
st.markdown("## 🧠 Ranking emocional")

df_rank = pd.DataFrame(
    ranking,
    columns=["candidate", "total", "pos", "neg", "balance"],
)

chart_rank = (
    alt.Chart(df_rank)
    .mark_bar()
    .encode(
        y=alt.Y("candidate:N", sort="-x", title=""),
        x=alt.X("balance:Q", title="Balance de sentimiento"),
        color=alt.condition(
            alt.datum.balance > 0,
            alt.value("#2ecc71"),
            alt.value("#e74c3c"),
        ),
        tooltip=["candidate", "balance", "total"],
    )
    .properties(height=30 * len(df_rank))
)

st.altair_chart(chart_rank, use_container_width=True)

# --------------------
# Dónde ocurre el debate
# --------------------
st.markdown("## 🌐 Dónde ocurre el debate")

redes = obtener_menciones_por_red(conexion, DEBATE_ID)
df_redes = pd.DataFrame(redes, columns=["platform", "total"])

chart_redes = (
    alt.Chart(df_redes)
    .mark_bar()
    .encode(
        x=alt.X("platform:N", title=""),
        y=alt.Y("total:Q", title="Menciones"),
        color=alt.value("#3498db"),
    )
    .properties(height=250)
)

st.altair_chart(chart_redes, use_container_width=True)
