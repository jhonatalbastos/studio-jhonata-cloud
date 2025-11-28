import streamlit as st
from datetime import date, timedelta
# from liturgia_generator import gerar_roteiro

st.set_page_config(page_title="Studio Jhonata", layout="wide")

st.markdown("""
# 🎬 Studio Jhonata Cloud
**Vídeos Litúrgicos Automáticos GRÁTIS**
""")

# Sidebar – configuração básica
st.sidebar.title("📅 Configurar")

col1, col2 = st.sidebar.columns(2)
data_inicio = col1.date_input("Data Início", date.today())
data_fim = col2.date_input("Data Fim", date.today() + timedelta(days=6))

tipo = st.sidebar.selectbox(
    "Tipo de leitura",
    ["Evangelho", "1ª Leitura", "Salmo", "2ª Leitura"]
)

# Botão principal (por enquanto só informativo)
if st.sidebar.button("🚀 Gerar Vídeos", type="primary"):
    st.sidebar.success("✅ Adicionado na fila!")
    st.success("Vídeos vão aparecer aqui em alguns minutos (próximo passo do projeto).")

st.markdown("---")

# Botão: Ver roteiro real de hoje
if st.button("👀 Ver roteiro de hoje"):
    with st.spinner("Buscando Evangelho de hoje..."):
        roteiro = gerar_roteiro(date.today(), tipo)

    if not roteiro.get("partes"):
        st.error("Não foi possível carregar a liturgia de hoje. Tente novamente mais tarde.")
    else:
        st.subheader(f"{roteiro['tipo']} - {roteiro['data']}")
        if roteiro.get("referencia"):
            st.write(f"Referência: {roteiro['referencia']}")
        if roteiro.get("titulo"):
            st.write(f"Título litúrgico: {roteiro['titulo']}")
        st.markdown("---")

        for parte in roteiro["partes"]:
            st.markdown(f"### {parte['nome']}")
            st.write(parte["texto"])
            st.caption(parte["titulo_3l"].replace("\n", " | "))
            st.markdown("---")
