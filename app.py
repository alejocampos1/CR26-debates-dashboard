import streamlit as st
import pandas as pd
import plotly.express as px

from streamlit_autorefresh import st_autorefresh
from config.settings import CADENA_CONEXION_POSTGRES
from db.connection import obtener_conexion
from queries.debate_metrics import (
    obtener_ranking_sentimiento,
    obtener_sentimiento_por_candidato,
    obtener_menciones_por_red,
    obtener_volumen_temporal_por_candidato
)

MIN_MENCIONES_HERO = 50

# --------------------
# Configuración general
# --------------------
st.set_page_config(
    page_title="🇨🇷 Elecciones 2026 - Debate Presidencial",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --------------------
# Auto-refresh (cada 60 segundos)
# --------------------
st_autorefresh(interval=60 * 1000, key="auto_refresh")

DEBATE_ID = "CR26_PRES_TSE_D1"

MAPEO_SENTIMIENTO_UI = {
    "positive": "Positivo",
    "neutral": "Neutro",
    "negative": "Negativo",
}

ORDEN_SENTIMIENTO = ["Positivo", "Neutro", "Negativo"]

RUTA_IMAGENES = "assets/candidatos"

MAPA_IMAGENES = {
    "Natalia Díaz": f"{RUTA_IMAGENES}/Natalia_Diaz.png",
    "Boris Molina": f"{RUTA_IMAGENES}/Boris_Molina.png",
    "Fernando Zamora": f"{RUTA_IMAGENES}/Fernando_Zamora.png",
    "Walter Hernandez": f"{RUTA_IMAGENES}/Walter_Hernandez.png",
    "Luz Mary Alpízar": f"{RUTA_IMAGENES}/Luz_Mary_Alpizar.png",
}

MAPA_PARTIDOS = {
    "Natalia Díaz": "Partido Unidos Podemos",
    "Luz Mary Alpízar": "Partido Progreso Social Democrático",
    "Boris Molina": "Partido Unión Costarricense Democrática",
    "Fernando Zamora": "Partido Nueva Generación",
    "Walter Hernandez": "Partido Justicia Social Costarricense",
}

MAPA_REDES_UI = {
    "x": "X (Twitter)",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "tiktok": "TikTok",
}

MAPA_COLORES_REDES = {
    "X (Twitter)": "#19FFE8",
    "Facebook": "#1877F2",
    "Instagram": "#AF30E1",
    "TikTok": "#D12A2A",
}

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
    sentimientos = obtener_sentimiento_por_candidato(conexion, DEBATE_ID)
    redes = obtener_menciones_por_red(conexion, DEBATE_ID)
    volumen_temporal = obtener_volumen_temporal_por_candidato(
        conexion,
        DEBATE_ID,
        intervalo_minutos=15,
    )

# DataFrames
if ranking:
    df_rank = pd.DataFrame(
        ranking,
        columns=["candidate", "total", "pos", "neg", "balance"],
    )
else:
    df_rank = pd.DataFrame()

if sentimientos:
    df_sent = pd.DataFrame(
        sentimientos,
        columns=["candidate", "sentiment", "total"],
    )
else:
    df_sent = pd.DataFrame()

if redes:
    df_redes = pd.DataFrame(
        redes,
        columns=["platform", "total"],
    )
else:
    df_redes = pd.DataFrame()

if not df_redes.empty:
    df_redes["platform_ui"] = (
        df_redes["platform"]
        .str.lower()
        .map(MAPA_REDES_UI)
        .fillna(df_redes["platform"].str.capitalize())
    )

if volumen_temporal:
    df_tiempo = pd.DataFrame(
        volumen_temporal,
        columns=["tiempo", "candidate", "total"],
    )
else:
    df_tiempo = pd.DataFrame()

# --------------------
# HERO – Apoyo / Rechazo neto (porcentual)
# --------------------
if df_rank.empty:
    st.info("⏳ Aún no hay suficientes menciones. El debate comenzará pronto.")
    st.stop()

df_hero = df_rank[df_rank["total"] >= MIN_MENCIONES_HERO].copy()

if df_hero.empty:
    st.info("⏳ Aún no hay volumen suficiente para destacar apoyos o rechazos.")
    st.stop()

# Índice neto en porcentaje
df_hero["apoyo_neto_pct"] = (
    (df_hero["pos"] - df_hero["neg"]) / df_hero["total"]
) * 100

mas_apoyo = df_hero.sort_values(
    ["apoyo_neto_pct", "total"],
    ascending=[False, False],
).iloc[0]

mas_rechazo = df_hero.sort_values(
    ["apoyo_neto_pct", "total"],
    ascending=[True, False],
).iloc[0]

col1, col2 = st.columns(2)

col1.metric(
    label="🟢  Mayor apoyo neto",
    value=mas_apoyo["candidate"],
    delta=f'{mas_apoyo["apoyo_neto_pct"]:+.1f}%',
)

col2.metric(
    label="🔴  Mayor rechazo neto",
    value=mas_rechazo["candidate"],
    delta=f'{mas_rechazo["apoyo_neto_pct"]:+.1f}%',
)

st.caption(
    "Apoyo neto = % positivas − % negativas (solo candidaturas con volumen relevante)"
)

st.markdown("---")

# --------------------
# Bloques por candidato
# --------------------
st.markdown("## Candidaturas")

for _, fila in df_rank.iterrows():
    candidate = fila["candidate"]
    total = fila["total"]
    pos = fila["pos"]
    neg = fila["neg"]
    neu = max(total - pos - neg, 0)

    with st.container():
        col_img, col_title = st.columns([1, 4])

        with col_img:
            if candidate in MAPA_IMAGENES:
                st.image(
                    MAPA_IMAGENES[candidate],
                    use_container_width=True,
                )

        with col_title:
            st.subheader(candidate)
            
            partido = MAPA_PARTIDOS.get(candidate)
            if partido:
                st.caption(partido)

        st.markdown(
            f" ### {int(total):,} menciones",
        )

        col1, col2 = st.columns(2)
        col1.metric("Positivo", f"{(pos / total) * 100:.1f}%")
        col2.metric("Negativo", f"{(neg / total) * 100:.1f}%")

        if neg / total > 0.4:
            st.error("⚠️  Alta presión negativa")
        elif pos / total > 0.4:
            st.success("🟢  Conversación mayoritariamente favorable")
        else:
            st.info("🟡  Conversación mixta / indecisa")
            
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
                x="sentimiento_es",
                y="total",
                color="sentimiento_es",
                category_orders={
                    "sentimiento_es": ORDEN_SENTIMIENTO
                },
                color_discrete_map={
                    "Positivo": "#2ecc71",
                    "Neutro": "#bdc3c7",
                    "Negativo": "#e74c3c",
                },
                labels={
                    "sentimiento_es": "Sentimiento",
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
# Evolución del debate en el tiempo
# --------------------        
st.markdown("## ⏱️ Evolución del debate en el tiempo")

if not df_tiempo.empty:
    fig_tiempo = px.line(
        df_tiempo,
        x="tiempo",
        y="total",
        color="candidate",
        labels={
            "tiempo": "Tiempo",
            "total": "Menciones",
            "candidate": "Candidato",
        },
    )

    fig_tiempo.update_layout(
        height=380,
        margin=dict(t=20, b=40, l=20, r=20),
        legend_title_text="",
    )

    st.plotly_chart(fig_tiempo, use_container_width=True)
else:
    st.info("⏳ Aún no hay datos temporales suficientes.")

# --------------------
# Distribución por red social
# --------------------
st.markdown("## 🌐 Dónde ocurre la conversación")

if not df_redes.empty:
    fig_redes = px.bar(
        df_redes,
        x="platform_ui",
        y="total",
        color="platform_ui",
        color_discrete_map=MAPA_COLORES_REDES,
        labels={
            "platform_ui": "Red social",
            "total": "Menciones",
        },
    )

    fig_redes.update_traces(marker_color="#3498db")
    fig_redes.update_layout(
        height=300,
        margin=dict(t=20, b=40, l=20, r=20),
    )

    st.plotly_chart(fig_redes, use_container_width=True)
