import streamlit as st
from datetime import date, timedelta
import os

# Configuração da página
st.set_page_config(
    page_title="Studio Jhonata", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("✨ **Studio Jhonata** - Automação Litúrgica")
st.markdown("---")

# Sidebar com configurações
st.sidebar.title("⚙️ Configurações")
st.sidebar.markdown("**APIs Configuradas:**")
st.sidebar.success("✅ Groq (Roteiro)")
st.sidebar.info("📅 Liturgia do dia")
st.sidebar.markdown("---")

# Tabs principais
tab1, tab2, tab3 = st.tabs(["📖 Gerar Roteiro", "🎥 Fábrica de Vídeo", "📊 Histórico"])

with tab1:
    st.header("🚀 Gerador de Roteiro Litúrgico")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        data_selecionada = st.date_input(
            "📅 Selecione a data:",
            value=date.today(),
            min_value=date(2023, 1, 1)
        )
    with col2:
        if st.button("🔄 Atualizar", key="atualizar"):
            st.rerun()
    
    if st.button("🚀 Gerar Roteiro Completo", type="primary"):
        with st.spinner("🔍 Buscando liturgia..."):
            liturgia = buscar_liturgia_do_dia(data_selecionada.strftime("%Y-%m-%d"))
        
        if liturgia:
            st.success(f"✅ Evangelho: {liturgia['referencia']}")
            
            with st.spinner("🤖 Groq gerando roteiro..."):
                roteiro = gerar_roteiro_com_groq(
                    liturgia['texto'], 
                    liturgia['referencia']
                )
            
            if roteiro:
                st.markdown("## 📖 **ROTEIRO PRONTO**")
                st.markdown("---")
                
                col_roteiro1, col_roteiro2 = st.columns(2)
                
                with col_roteiro1:
                    st.markdown("### 🎣 **HOOK**")
                    st.markdown(f"**{roteiro['hook']}**")
                    st.markdown("---")
                    
                    st.markdown("### 💭 **REFLEXÃO**")
                    st.markdown(roteiro['reflexão'])
                
                with col_roteiro2:
                    st.markdown("### 📖 **LEITURA**")
                    st.markdown(roteiro['leitura'])
                    st.markdown("---")
                    
                    st.markdown("### 🌟 **APLICAÇÃO**")
                    st.markdown(roteiro['aplicação'])
                
                st.markdown("### 🙏 **ORAÇÃO**")
                st.markdown(roteiro['oração'])
                
                # Botões de ação
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("📋 Copiar Roteiro"):
                        st.code(f"""HOOK: {roteiro['hook']}
LEITURA: {roteiro['leitura']}
REFLEXÃO: {roteiro['reflexão']}
APLICAÇÃO: {roteiro['aplicação']}
ORAÇÃO: {roteiro['oração']}""")
                
                with col_btn2:
                    st.markdown("**[Próximo: Fábrica de Vídeo]** 👈")
                
                # Salvar no histórico
                if 'historico_roteiros' not in st.session_state:
                    st.session_state.historico_roteiros = []
                
                st.session_state.historico_roteiros.append({
                    'data': data_selecionada.strftime("%d/%m/%Y"),
                    'referencia': liturgia['referencia'],
                    'roteiro': roteiro
                })
                st.success("✅ Salvo no histórico!")

with tab2:
    st.header("🎥 Fábrica de Vídeo (Em Desenvolvimento)")
    st.info("🔄 Próximas funcionalidades:\n• TTS com gTTS\n• Geração de imagens\n• Vídeo vertical com MoviePy\n• Subtítulos SRT")
    
    if st.button("🚧 Preparar próximo vídeo"):
        st.balloons()

with tab3:
    st.header("📊 Histórico de Roteiros")
    
    if 'historico_roteiros' in st.session_state and st.session_state.historico_roteiros:
        for i, item in enumerate(st.session_state.historico_roteiros[-10:], 1):  # Últimos 10
            with st.expander(f"📅 {item['data']} - {item['referencia']}"):
                st.markdown(f"**HOOK:** {item['roteiro']['hook']}")
                st.markdown(f"**Leitura:** {item['roteiro']['leitura'][:100]}...")
    else:
        st.info("📝 Gere seu primeiro roteiro na aba 'Gerar Roteiro'")

# Footer
st.markdown("---")
st.markdown("**Made with ❤️ para a evangelização** | Studio Jhonata")

# FUNÇÕES DO liturgia_generator EMBUTIDAS (código autônomo)
def inicializar_groq():
    if "GROQ_API_KEY" not in st.secrets:
        st.error("❌ Configure GROQ_API_KEY nas Secrets!")
        st.stop()
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

def buscar_liturgia_do_dia(data_str=None):
    from datetime import date
    import requests
    
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
        return None
    except:
        return None

def limpar_texto_evangelho(texto):
    import re
    texto_limpo = re.sub(r'\[\d+\]', '', texto)
    texto_limpo = re.sub(r'\d+\s*[:\-]\s*', '', texto_limpo)
    texto_limpo = re.sub(r'\n\s*\n', '\n', texto_limpo)
    return texto_limpo.strip()

def gerar_roteiro_com_groq(texto_evangelho, referencia):
    try:
        from groq import Groq
        import re
        
        client = inicializar_groq()
        texto_limpo = limpar_texto_evangelho(texto_evangelho)
        
        system_prompt = """Crie roteiro litúrgico TikTok/Reels em 5 partes:
HOOK: [1-2 frases curiosidade]
LEITURA: [Proclamação + texto + Palavra da Salvação]
REFLEXÃO: [Meditação 20s]
APLICAÇÃO: [Aplicação prática 20s]
ORAÇÃO: [Oração curta 20s]"""

        user_prompt = f"Evangelho ({referencia}):\n{texto_limpo}\n\nFormato exato."

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
            partes[secao.lower()] = match.group(1).strip() if match else "[Parte faltando]"
        
        return partes
    except Exception as e:
        st.error(f"❌ Erro Groq: {str(e)}")
        return None
