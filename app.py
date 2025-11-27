import streamlit as st
from datetime import date, timedelta
import json
import os

st.set_page_config(page_title="Studio Jhonata", layout="wide")

st.markdown("""
# 🎬 Studio Jhonata Cloud
**Vídeos Litúrgicos Automáticos GRÁTIS**
""")

# Sidebar simples
st.sidebar.title("📅 Configurar")
data_inicio = st.sidebar.date_input("Data Início", date.today())
data_fim = st.sidebar.date_input("Data Fim", date.today() + timedelta(days=6))
tipo = st.sidebar.selectbox("Tipo", ["Evangelho", "1ª Leitura", "Salmo", "2ª Leitura"])

# Botão principal
if st.sidebar.button("🚀 Gerar Vídeos", type="primary"):
    st.sidebar.success("✅ Adicionado na fila!")
    st.success("Vídeos vão aparecer aqui em alguns minutos!")

# Preview
if st.button("👀 Ver roteiro de hoje"):
    st.write("**EVANGELHO**")
    st.write("01/12/2025")
    st.write("Mc 16:15-20")
    st.write("• Leitura do dia")
    st.write("• Reflexão") 
    st.write("• Aplicação")
    st.write("• Oração")
