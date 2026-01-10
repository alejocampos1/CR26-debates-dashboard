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
    page_title="🇨🇷 Elecciones 2026 - Debate Presidencial",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DEBATE_ID = "CR26_PRES_TSE_D1"

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
        df_sent = pd.DataFrame()
        df_redes = pd.DataFrame()

# --------------------
# HERO – Atención y Riesgo
# --------------------
if not ranking:
    st.info("⏳ Aún no hay suficientes menciones. El debate comenzará pronto.")
else:
    df_rank = pd.DataFrame(
        ranking,
        columns=["candidate", "total", "pos", "neg", "balance"],
    )

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

        neutro = max(total - pos - neg, 0)

        with st.container():
            st.subheader(candidate)

            col1, col2, col3 = st.columns(3)
            col1.metric("Atención", total)
            col2.metric("Positivo", f"{(pos / total * 100):.1f}%")
            col3.metric("Negativo", f"{(neg / total * 100):.1f}%")

            # Lectura humana
            if neg / total > 0.4:
                st.warning("⚠️ Alta presión negativa")
            elif pos / total > 0.4:
                st.success("🟢 Conversación mayoritariamente favorable")
            else:
                st.info("🟡 Conversación mixta / indecisa")

            df_cand = df_sent[df_sent["candidate"] == candidate]

            if not df_cand.empty:
                chart_sent = (
                    alt.Chart(df_cand)
                    .mark_bar()
                    .encode(
                        x=alt.X("sentiment:N", title="Sentimiento"),
                        y=alt.Y("total:Q", title="Menciones"),
                        color=alt.Color(
                            "sentiment:N",
                            scale=alt.Scale(
                                domain=["positive", "neutral", "negative"],
                                range=["#2ecc71", "#bdc3c7", "#e74c3c"],
                            ),
                            legend=None,
                        ),
                        tooltip=["sentiment", "total"],
                    )
                    .properties(height=160)
                )

                st.altair_chart(chart_sent, use_container_width=True)

            st.markdown("---")

    # --------------------
    # Ranking por presión negativa
    # --------------------
    st.markdown("## ⚠️ Presión negativa comparativa")

    chart_riesgo = (
        alt.Chart(df_rank)
        .mark_bar()
        .encode(
            y=alt.Y("candidate:N", sort="-x", title="Candidato"),
            x=alt.X("neg:Q", title="Menciones negativas"),
            tooltip=["candidate", "neg", "total"],
        )
        .properties(height=30 * len(df_rank))
    )

    st.altair_chart(chart_riesgo, use_container_width=True)

    # --------------------
    # Distribución por red
    # --------------------
    st.markdown("## 🌐 Dónde ocurre la conversación")

    if not df_redes.empty:
        chart_redes = (
            alt.Chart(df_redes)
            .mark_bar()
            .encode(
                x=alt.X("platform:N", title=""),
                y=alt.Y("total:Q", title="Menciones"),
                color=alt.value("#3498db"),
            )
            .properties(height=240)
        )

        st.altair_chart(chart_redes, use_container_width=True)
