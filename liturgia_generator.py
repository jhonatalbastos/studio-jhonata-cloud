import streamlit as st
from datetime import date, timedelta
import re
import requests
from groq import Groq

# Configuração da página
st.set_page_config(
    page_title="Studio Jhonata", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cliente Groq lazy loading
_client = None

def inicializar_groq():
    global _client
    if _client is None:
        if "GROQ_API_KEY" not in st.secrets:
            st.error("❌ Configure GROQ_API_KEY nas Secrets do Streamlit!")
            st.stop()
        _client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return _client

def buscar_liturgia_do_dia(data_str=None):
    """Busca evangelho do dia via API litúrgica"""
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
        st.error("❌ Evangelho não encontrado para esta data")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao buscar liturgia: {str(e)}")
        return None

def limpar_texto_evangelho(texto):
    """Remove números de versículos e limpa formatação"""
    texto_limpo = re.sub(r'\[\d+\]', '', texto)
    texto_limpo = re.sub(r'\d+\s*[:\-]\s*', '', texto_limpo)
    texto_limpo = re.sub(r'\n\s*\n', '\n', texto_limpo)
    return texto_limpo.strip()

def gerar_roteiro_com_groq(texto_evangelho, referencia):
    """Gera todo o roteiro usando Groq API"""
    try:
        client = inicializar_groq()
        texto_limpo = limpar_texto_evangelho(texto_evangelho)
        
        system_prompt = """Você cria roteiros litúrgicos para vídeos TikTok/Reels católicos.

Formato EXATO com 5 partes separadas por título:
HOOK: 1-2 frases curtas criando curiosidade (5-8 seg)
LEITURA: "Proclamação do Evangelho de Jesus Cristo, segundo [evangelista]. [referência]. Glória a vós Senhor!" + texto limpo + "Palavra da Salvação. Glória a vós Senhor!"
REFLEXÃO: Meditação profunda (20-25 seg, 2-3 frases)
APLICAÇÃO: "Evangelho na sua vida" - como aplicar HOJE (20-25 seg)
ORAÇÃO: Oração curta e sincera (20-25 seg)

Responda APENAS no formato:
HOOK: [texto]
LEITURA: [texto]
REFLEXÃO: [texto]
APLICAÇÃO: [texto]
ORAÇÃO: [texto]"""

        user_prompt = f"""Evangelho do dia - {referencia}

Texto: {texto_limpo[:2000]}

Gere o roteiro completo no formato exato."""

        resposta = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        
        texto_gerado = resposta.choices[0].message.content
        
        # Parse das partes
        partes = {}
        secoes = ["HOOK", "LEITURA", "REFLEXÃO", "APLICAÇÃO", "ORAÇÃO"]
        
        for secao in secoes:
            pattern = rf"{secao}:\s*([^LEITURA:|^REFLEXÃO:|^APLICAÇÃO:|^ORAÇÃO:|^HOOK:]+?)(?=\n[A-Z]{4,}[:\n]|$)"
            match = re.search(pattern, texto_gerado, re.DOTALL | re.IGNORECASE)
            if match:
                partes[secao.lower()] = match.group(1).strip()
            else:
                partes[secao.lower()] = f"[Parte {secao} não gerada pela IA]"
        
        return partes
    except Exception as e:
        st.error(f"❌ Erro Groq: {str(e)}")
        return None

# === INTERFACE PRINCIPAL ===
st.title("✨ **Studio Jhonata** - Automação Litúrgica Completa")
st.markdown("---")

# Sidebar
st.sidebar.title("⚙️ Configurações")
st.sidebar.markdown("**✅ APIs Configuradas:**")
st.sidebar.success("• Groq (Roteiro IA)")
st.sidebar.success("• Liturgia.net.br")
st.sidebar.markdown("---")
st.sidebar.markdown("**Próximas:** gTTS, MoviePy, Imagens IA")

# Tabs
tab1, tab2, tab3 = st.tabs(["📖 Gerar Roteiro", "🎥 Fábrica Vídeo", "📊 Histórico"])

with tab1:
    st.header("🚀 Gerador de Roteiro IA Completo")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        data_selecionada = st.date_input(
            "📅 Data da liturgia:",
            value=date.today(),
            min_value=date(2023, 1, 1)
        )
    with col2:
        st.info("**Status:** ✅ Groq pronto")
    
    if st.button("🚀 Gerar Roteiro Completo", type="primary", use_container_width=True):
        with st.spinner("🔍 Buscando liturgia do dia..."):
            liturgia = buscar_liturgia_do_dia(data_selecionada.strftime("%Y-%m-%d"))
        
        if liturgia:
            st.success(f"✅ Evangelho encontrado: **{liturgia['referencia']}**")
            
            with st.spinner("🤖 Groq gerando roteiro personalizado..."):
                roteiro = gerar_roteiro_com_groq(liturgia['texto'], liturgia['referencia'])
            
            if roteiro:
                st.markdown("## 📖 **ROTEIRO PRONTO PARA GRAVAR**")
                st.markdown("---")
                
                # Layout em colunas
                col_hook_reflexao, col_leitura_app = st.columns(2)
                
                with col_hook_reflexao:
                    st.markdown("### 🎣 **HOOK** (5-8s)")
                    st.markdown(f"> **{roteiro.get('hook', '')}**")
                    st.markdown("---")
                    st.markdown("### 💭 **REFLEXÃO** (20-25s)")
                    st.markdown(roteiro.get('reflexão', ''))
                
                with col_leitura_app:
                    st.markdown("### 📖 **LEITURA COMPLETA**")
                    st.markdown(roteiro.get('leitura', ''))
                    st.markdown("---")
                    st.markdown("### 🌟 **APLICAÇÃO** (20-25s)")
                    st.markdown(roteiro.get('aplicação', ''))
                
                st.markdown("### 🙏 **ORAÇÃO FINAL** (20-25s)")
                st.markdown(roteiro.get('oração', ''))
                st.markdown("---")
                
                # Botões de ação
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📋 Copiar Todo Roteiro", use_container_width=True):
                        texto_completo = (
                            f"HOOK: {roteiro['hook']}\n\n"
                            f"LEITURA: {roteiro['leitura']}\n\n"
                            f"REFLEXÃO: {roteiro['reflexão']}\n\n"
                            f"APLICAÇÃO: {roteiro['aplicação']}\n\n"
                            f"ORAÇÃO: {roteiro['oração']}"
                        )
                        st.code(texto_completo)
                        st.success("✅ Copiado!")
                
                with col_btn2:
                    st.markdown("**👉 Próximo:** Fábrica de Vídeo")
                
                # Salvar histórico
                if 'historico' not in st.session_state:
                    st.session_state.historico = []
                st.session_state.historico.append({
                    'data': data_selecionada,
                    'referencia': liturgia['referencia'],
                    'roteiro': roteiro
                })
                st.balloons()

with tab2:
    st.header("🎥 Fábrica de Vídeo (Em Desenvolvimento)")
    st.info("🔄 **Próximas entregas:**\n• TTS com gTTS\n• Imagens IA\n• Vídeo vertical MoviePy\n• Subtítulos SRT\n• Export TikTok/Reels")
    st.button("🚧 Em breve!")

with tab3:
    st.header("📊 Histórico de Roteiros")
    if 'historico' in st.session_state and st.session_state.historico:
        for item in st.session_state.historico[-5:]:  # Últimos 5
            with st.expander(f"📅 {item['data'].strftime('%d/%m/%Y')} - {item['referencia']}"):
                st.markdown(f"**HOOK:** {item['roteiro']['hook']}")
                st.markdown(f"**Leitura:** {item['roteiro']['leitura'][:150]}...")
    else:
        st.info("📝 Gere roteiros na primeira aba para ver histórico")

# Footer
st.markdown("---")
st.markdown("**✨ Studio Jhonata - Evangelização Automatizada** | Feito com ❤️ para Deus")
