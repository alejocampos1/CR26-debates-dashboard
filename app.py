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

# --------------------
# Configuración general
# --------------------

# Configuración general

MIN_MENCIONES_HERO = 50

st.markdown(
    """
    <style>
    * {
        user-select: none;
        -webkit-user-select: none;
        -ms-user-select: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.set_page_config(
    page_title="🇨🇷 Elecciones 2026 - Debate Presidencial",
    layout="centered",
    initial_sidebar_state="collapsed",
)

ORDEN_SENTIMIENTO = ["Positivo", "Neutro", "Negativo"]

MAPA_REDES_UI = {
    "x": "X (Twitter)",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "tiktok": "TikTok",
}

MAPA_COLORES_REDES = {
    "X (Twitter)": "#14B7A6",
    "Facebook": "#1877F2",
    "Instagram": "#F15BCB",
    "TikTok": "#A056E6",
}

PALETA_NEUTRA = [
    "#1f77b4",  
    "#9467bd",  
    "#17becf",  
    "#ff7f0e",  
    "#8c564b",  
    "#e377c2",  
    "#7f7f7f",  
]


# Componentes de cálculo de porcentajes para el HERO
def badge_apoyo(valor):
    color = "#2ecc71" if valor >= 0 else "#e74c3c"
    signo = "+" if valor >= 0 else ""
    return f"""
    <div style="
        display:inline-block;
        padding:8px 16px;
        border-radius:8px;
        background-color:{color};
        color:white;
        font-size:28px;
        font-weight:700;
    ">
        {signo}{valor:.1f}%
    </div>
    """

# Auto-refresh (cada 60 segundos)
st_autorefresh(interval=60 * 1000, key="auto_refresh")


# Contexto del debate
DEBATE_ID = "CR26_PRES_TSE_D1"

MAPEO_SENTIMIENTO_UI = {
    "positive": "Positivo",
    "neutral": "Neutro",
    "negative": "Negativo",
}


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

# Mayor apoyo neto
with col1:
    st.markdown("### 🟢 Mayor apoyo neto")

    if mas_apoyo["candidate"] in MAPA_IMAGENES:
        st.image(
            MAPA_IMAGENES[mas_apoyo["candidate"]],
            width=120,
        )

    st.markdown(f"### {mas_apoyo['candidate']}")
    st.markdown(
        badge_apoyo(mas_apoyo["apoyo_neto_pct"]),
        unsafe_allow_html=True,
    )

# Mayor rechazo neto
with col2:
    st.markdown("### 🔴 Mayor rechazo neto")

    if mas_rechazo["candidate"] in MAPA_IMAGENES:
        st.image(
            MAPA_IMAGENES[mas_rechazo["candidate"]],
            width=120,
        )

    st.markdown(f"### {mas_rechazo['candidate']}")
    st.markdown(
        badge_apoyo(mas_rechazo["apoyo_neto_pct"]),
        unsafe_allow_html=True,
    )

st.markdown(" ")
st.caption(
    "*Apoyo neto = % positivas − % negativas"
)


st.markdown("---")

# --------------------
# Bloques por candidato
# --------------------
st.markdown("# Candidaturas")
st.markdown("#### Evolución de la conversación digital por candidato")
st.markdown("---")

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
st.markdown("## Evolución del debate en el tiempo")
st.markdown("#### Cantidad de menciones por candidato durante el debate")

if not df_tiempo.empty:
    fig_tiempo = px.line(
        df_tiempo,
        x="tiempo",
        y="total",
        color="candidate",
        color_discrete_sequence=PALETA_NEUTRA,
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

st.markdown("---")

# --------------------
# Distribución por red social
# --------------------
st.markdown("## Dónde ocurre la conversación")
st.markdown("#### Distribución por red social (Cantidad de menciones)")

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

    fig_redes.update_layout(
        height=300,
        margin=dict(t=20, b=40, l=20, r=20),
    )

    st.plotly_chart(fig_redes, use_container_width=True)
    
st.markdown("---")

col_footer_text, col_footer_logo = st.columns([5, 2])

with col_footer_text:
    st.markdown(
        """
        <div style="
            font-size:13px;
            color:#6c757d;
            line-height:1.5;
        ">
        <strong>Metodología y limitaciones:</strong><br>
        Este análisis monitorea conversaciones públicas en Facebook, X (Twitter), Instagram y TikTok,
        considerando el universo total de menciones digitales asociadas a cada candidatura y su entorno.
        A diferencia de los estudios de opinión tradicionales, no se basa en encuestas ni en opiniones
        declaradas, sino en comportamientos digitales observables (qué se comenta y qué se amplifica).
        Los resultados no constituyen una predicción electoral y están sujetos a sesgos propios de cada
        plataforma y de la composición demográfica de sus usuarios.
        <br><br>
        <strong>© 2026 – SoundCheck CR - Todos los derechos reservados.</strong>
        El contenido, visualizaciones y métricas presentadas en este tablero son propiedad intelectual
        de sus autores y no pueden ser reproducidos, redistribuidos ni utilizados sin autorización expresa.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_footer_logo:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.image(
        "assets/logo.png",
        use_container_width=True,
    )
