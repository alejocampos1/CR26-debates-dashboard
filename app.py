import streamlit as st
from db.connection import obtener_conexion
from queries.debate_metrics import obtener_ranking_sentimiento

# --------------------
# Configuración general
# --------------------
st.set_page_config(
    page_title="Debate CR26",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DEBATE_ID = "CR26_PRES_TSE_D1"

# Conexión DB
conexion = obtener_conexion()

# Datos
ranking = obtener_ranking_sentimiento(conexion, DEBATE_ID)

if not ranking:
    st.warning("Aún no hay suficientes menciones para mostrar resultados.")
    st.stop()

mejor = ranking[0]
peor = ranking[-1]


# HERO: Mejores / Peores
st.markdown("## 🔥 Pulso del Debate")

st.markdown("### 🟢 Mejor sentimiento")
st.metric(
    label=mejor[0],
    value=f"{mejor[4]:.2f}",
    delta=f"{mejor[1]} menciones"
)

st.markdown("---")

st.markdown("### 🔴 Peor sentimiento")
st.metric(
    label=peor[0],
    value=f"{peor[4]:.2f}",
    delta=f"{peor[1]} menciones"
)

st.markdown("---")


# Bloques por candidato
st.markdown("## 📊 Candidatos")

for c in ranking:
    candidate, total, pos, neg, balance = c

    with st.container():
        st.subheader(candidate)
        col1, col2, col3 = st.columns(3)

        col1.metric("Menciones", total)
        col2.metric("Positivas", pos)
        col3.metric("Negativas", neg)

        st.progress(min(max((balance + 1) / 2, 0), 1))
        st.caption(f"Balance de sentimiento: {balance:.2f}")

        st.markdown("---")
