from datetime import date
import re
import requests
import streamlit as st
from groq import Groq

# Cliente Groq lazy loading
_client = None

def inicializar_groq():
    global _client
    if _client is None:
        if "GROQ_API_KEY" not in st.secrets:
            st.error("❌ Configure GROQ_API_KEY nas Secrets!")
            st.stop()
        _client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return _client

def buscar_liturgia_do_dia(data_str=None):
    if data_str is None:
        data_str = date.today().strftime("%Y-%m-%d")
    
    url = f"https://api.liturgia.net.br/liturgia?data={data_str}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        dados = response.json()
        
        for leitura in dados.get("leituras", []):
            if "Evangelho" in leitura.get("titulo", "") or "evangelho" in leitura.get("titulo", "").lower():
                return {
                    "titulo": leitura.get("titulo", ""),
                    "referencia": leitura.get("referencia", ""),
                    "texto": leitura.get("texto", "")
                }
        st.error("❌ Evangelho não encontrado")
        return None
    except Exception as e:
        st.error(f"❌ Erro liturgia: {str(e)}")
        return None

def limpar_texto_evangelho(texto):
    texto_limpo = re.sub(r'\[\d+\]', '', texto)
    texto_limpo = re.sub(r'\d+\s*[:\-]\s*', '', texto_limpo)
    texto_limpo = re.sub(r'\n\s*\n', '\n', texto_limpo)
    return texto_limpo.strip()

def gerar_roteiro_com_groq(texto_evangelho, referencia):
    client = inicializar_groq()
    texto_limpo = limpar_texto_evangelho(texto_evangelho)
    
    system_prompt = """Você cria roteiros litúrgicos para vídeos TikTok/Reels.

Formato EXATO com 5 partes:
HOOK: [1-2 frases curtas criando curiosidade]
LEITURA: [Proclamação completa + texto + Palavra da Salvação]
REFLEXÃO: [Meditação 20-25s]
APLICAÇÃO: [Como aplicar hoje 20-25s]
ORAÇÃO: [Oração curta 20-25s]"""

    user_prompt = f"Evangelho ({referencia}):\n{texto_limpo}\n\nGere no formato exato."

    try:
        resposta = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        texto_gerado = resposta.choices[0].message.content
        partes = {}
        secoes = ["HOOK", "LEITURA", "REFLEXÃO", "APLICAÇÃO", "ORAÇÃO"]
        
        for secao in secoes:
            pattern = rf"{secao}:\s*([^\n]+(?:\n(?![A-Z]+:)[^\n]*)*)"
            match = re.search(pattern, texto_gerado, re.DOTALL | re.IGNORECASE)
            partes[secao.lower()] = match.group(1).strip() if match else f"[Parte {secao} faltando]"
        
        return partes
    except Exception as e:
        st.error(f"❌ Groq erro: {str(e)}")
        return None

# INTERFACE PRINCIPAL - CÓDIGO AUTÔNOMO
st.set_page_config(page_title="Studio Jhonata", layout="wide")
st.title("✨ Studio Jhonata - Gerador Litúrgico IA")
st.markdown("---")

col1, col2 = st.columns([2, 1])
with col1:
    data_selecionada = st.date_input("📅 Data:", value=date.today())
with col2:
    st.markdown("**Status:** ✅ Groq OK")

if st.button("🚀 Gerar Roteiro Completo", type="primary"):
    with st.spinner("🔍 Buscando liturgia..."):
        liturgia = buscar_liturgia_do_dia(data_selecionada.strftime("%Y-%m-%d"))
    
    if liturgia:
        st.success(f"✅ {liturgia['referencia']}")
        with st.spinner("🤖 Groq gerando..."):
            roteiro = gerar_roteiro_com_groq(liturgia['texto'], liturgia['referencia'])
        
        if roteiro:
            st.markdown("## 📖 **ROTEIRO COMPLETO**")
            st.markdown("---")
            
            st.markdown("### 🎣 **HOOK**")
            st.markdown(f"**{roteiro['hook']}**")
            
            st.markdown("### 📖 **LEITURA**")
            st.markdown(roteiro['leitura'])
            
            st.markdown("### 💭 **REFLEXÃO**")
            st.markdown(roteiro['reflexão'])
            
            st.markdown("### 🌟 **APLICAÇÃO**")
            st.markdown(roteiro['aplicação'])
            
            st.markdown("### 🙏 **ORAÇÃO**")
            st.markdown(roteiro['oração'])
            
            if st.button("📋 Copiar tudo"):
                st.code(f"""HOOK: {roteiro['hook']}
LEITURA: {roteiro['leitura']}
REFLEXÃO: {roteiro['reflexão']}
APLICAÇÃO: {roteiro['aplicação']}
ORAÇÃO: {roteiro['oração']}""")
    else:
        st.error("❌ Falha na geração")
