import streamlit as st
import pandas as pd
import plotly.express as px

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
    page_title="🇨🇷 Elecciones 2026 - Debate Presidencial",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DEBATE_ID = "CR26_PRES_TSE_D1"

MAPEO_SENTIMIENTO_UI = {
    "positive": "Positivo",
    "neutral": "Neutro",
    "negative": "Negativo",
}

ORDEN_SENTIMIENTO = ["Positivo", "Neutro", "Negativo"]

# --------------------
# Encabezado
# --------------------
st.markdown("# 🇨🇷 Elecciones 2026 – Debate Presidencial")
st.caption("Monitoreo en tiempo real del debate")
st.markdown("---")

# --------------------
# Carga de datos
# --------------------
with obtener_conexion(
    cadena_conexion=CADENA_CONEXION_POSTGRES,
) as conexion:

    ranking = obtener_ranking_sentimiento(conexion, DEBATE_ID)

    if ranking:
        df_rank = pd.DataFrame(
            ranking,
            columns=["candidate", "total", "pos", "neg", "balance"],
        )

        sentimientos = obtener_sentimiento_por_candidato(conexion, DEBATE_ID)
        df_sent = pd.DataFrame(
            sentimientos,
            columns=["candidate", "sentiment", "total"],
        )

        redes = obtener_menciones_por_red(conexion, DEBATE_ID)
        df_redes = pd.DataFrame(
            redes,
            columns=["platform", "total"],
        )
    else:
        df_rank = pd.DataFrame()
        df_sent = pd.DataFrame()
        df_redes = pd.DataFrame()

# --------------------
# HERO – Morbo controlado
# --------------------
if df_rank.empty:
    st.info("⏳ Aún no hay suficientes menciones. El debate comenzará pronto.")
    st.stop()

df_rank["pct_pos"] = df_rank["pos"] / df_rank["total"]
df_rank["pct_neg"] = df_rank["neg"] / df_rank["total"]

mejor_positivo = df_rank.sort_values(
    ["pct_pos", "total"],
    ascending=[False, False],
).iloc[0]

peor_negativo = df_rank.sort_values(
    ["pct_neg", "total"],
    ascending=[False, False],
).iloc[0]

col1, col2 = st.columns(2)

col1.metric(
    label="🟢 Mejor imagen positiva",
    value=mejor_positivo["candidate"],
    delta=f'{mejor_positivo["pct_pos"]*100:.1f}% positivas',
)

col2.metric(
    label="🔴 Mayor rechazo",
    value=peor_negativo["candidate"],
    delta=f'{peor_negativo["pct_neg"]*100:.1f}% negativas',
)

st.markdown("---")

# --------------------
# Bloques por candidato
# --------------------
st.markdown("## 🧑‍💼 Candidatos")

for _, fila in df_rank.iterrows():
    candidate = fila["candidate"]
    total = fila["total"]
    pos = fila["pos"]
    neg = fila["neg"]
    neu = max(total - pos - neg, 0)

    with st.container():
        st.subheader(candidate)

        col1, col2, col3 = st.columns(3)
        col1.metric("Atención", int(total))
        col2.metric("Positivo", f"{(pos/total)*100:.1f}%")
        col3.metric("Negativo", f"{(neg/total)*100:.1f}%")

        if neg / total > 0.4:
            st.error("⚠️ Alta presión negativa")
        elif pos / total > 0.4:
            st.success("🟢 Conversación mayoritariamente favorable")
        else:
            st.info("🟡 Conversación mixta / indecisa")

        df_cand = df_sent[df_sent["candidate"] == candidate].copy()

        df_cand["sentimiento_es"] = (
            df_cand["sentiment"]
            .map(MAPEO_SENTIMIENTO_UI)
        )

        df_cand["sentimiento_es"] = pd.Categorical(
            df_cand["sentimiento_es"],
            categories=ORDEN_SENTIMIENTO,
            ordered=True,
        )

        if not df_cand.empty:
            fig_sent = px.bar(
                df_cand,
                x="sentiment",
                y="total",
                color="sentiment",
                color_discrete_map={
                    "positive": "#2ecc71",
                    "neutral": "#bdc3c7",
                    "negative": "#e74c3c",
                },
                labels={
                    "sentiment": "Sentimiento",
                    "total": "Menciones",
                },
            )

            fig_sent.update_layout(
                height=260,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
            )

            st.plotly_chart(fig_sent, use_container_width=True)

        st.markdown("---")

# --------------------
# Ranking por presión negativa
# --------------------
st.markdown("## ⚠️ Presión negativa comparativa")

fig_riesgo = px.bar(
    df_rank.sort_values("neg", ascending=True),
    x="neg",
    y="candidate",
    orientation="h",
    labels={
        "neg": "Menciones negativas",
        "candidate": "Candidato",
    },
)

fig_riesgo.update_traces(marker_color="#e74c3c")
fig_riesgo.update_layout(
    height=60 * len(df_rank),
    margin=dict(t=20, b=20, l=40, r=20),
)

st.plotly_chart(fig_riesgo, use_container_width=True)

# --------------------
# Distribución por red social
# --------------------
st.markdown("## 🌐 Dónde ocurre la conversación")

if not df_redes.empty:
    fig_redes = px.bar(
        df_redes,
        x="platform",
        y="total",
        labels={
            "platform": "Red social",
            "total": "Menciones",
        },
    )

    fig_redes.update_traces(marker_color="#3498db")
    fig_redes.update_layout(
        height=300,
        margin=dict(t=20, b=40, l=20, r=20),
    )

    st.plotly_chart(fig_redes, use_container_width=True)
