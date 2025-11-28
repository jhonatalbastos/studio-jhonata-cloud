from datetime import date
import re
import requests
import streamlit as st
from groq import Groq

# Carrega chave da API Groq dos Secrets do Streamlit
@st.cache_data
def carregar_chave_groq():
    if "GROQ_API_KEY" not in st.secrets:
        st.error("❌ Configure GROQ_API_KEY nas Secrets do Streamlit!")
        st.stop()
    return st.secrets["GROQ_API_KEY"]

GROQ_API_KEY = carregar_chave_groq()
client = Groq(api_key=GROQ_API_KEY)

def buscar_liturgia_do_dia(data_str=None):
    """Busca evangelho do dia via API litúrgica"""
    if data_str is None:
        data_str = date.today().strftime("%Y-%m-%d")
    
    url = f"https://api.liturgia.net.br/liturgia?data={data_str}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        dados = response.json()
        
        evangelho = None
        for leitura in dados.get("leituras", []):
            if "Evangelho" in leitura.get("titulo", "") or "evangelho" in leitura.get("titulo", "").lower():
                evangelho = leitura
                break
        
        if not evangelho:
            st.error("❌ Evangelho não encontrado para esta data")
            return None
            
        return {
            "titulo": evangelho.get("titulo", ""),
            "referencia": evangelho.get("referencia", ""),
            "texto": evangelho.get("texto", "")
        }
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar liturgia: {str(e)}")
        return None

def limpar_texto_evangelho(texto):
    """Remove números de versículos e limpa formatação"""
    # Remove números de versículo [1], [2], 1:, 2: etc.
    texto_limpo = re.sub(r'\[\d+\]', '', texto)
    texto_limpo = re.sub(r'\d+\s*[:\-]\s*', '', texto_limpo)
    texto_limpo = re.sub(r'\n\s*\n', '\n', texto_limpo)  # Remove linhas vazias extras
    return texto_limpo.strip()

def gerar_roteiro_com_groq(texto_evangelho, referencia):
    """Gera todo o roteiro usando Groq API"""
    
    texto_limpo = limpar_texto_evangelho(texto_evangelho)
    
    system_prompt = """Você é um criador de conteúdo católico para vídeos curtos (TikTok/Reels).
    
Crie um roteiro litúrgico em 5 partes perfeitas para vídeo vertical de 60-90 segundos:

HOOK: 1-2 frases impactantes (5-8 seg) que criem curiosidade sobre o Evangelho
LEITURA: "Proclamação do Evangelho de Jesus Cristo, segundo [evangelista]. [referência]. Glória a vós Senhor!" + texto limpo + "Palavra da Salvação. Glória a vós Senhor!"
REFLEXÃO: Meditação profunda (20-25 seg, 2-3 frases) conectando Evangelho com vida espiritual
APLICAÇÃO: "Evangelho na sua vida" - como aplicar HOJE (20-25 seg, prático e direto)
ORAÇÃO: Oração curta e sincera baseada no Evangelho (20-25 seg)

Formato EXATO:
HOOK: [texto]
LEITURA: [texto completo]
REFLEXÃO: [texto]
APLICAÇÃO: [texto]
ORAÇÃO: [texto]

Mantenha linguagem simples, devocional, acessível. Cada parte deve ter ~120-150 caracteres."""

    user_prompt = f"""Evangelho do dia - {referencia}

Texto: {texto_limpo}

Gere o roteiro completo no formato exato."""

    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        
        texto_gerado = resposta.choices[0].message.content
        
        # Extrai partes usando regex
        partes = {}
        secoes = ["HOOK", "LEITURA", "REFLEXÃO", "APLICAÇÃO", "ORAÇÃO"]
        
        for secao in secoes:
            pattern = rf"{secao}:\s*(.*?)(?={next((s for s in secoes if s != secao), 'FIM')}:|$)"
            match = re.search(pattern, texto_gerado, re.DOTALL | re.IGNORECASE)
            if match:
                partes[secao.lower()] = match.group(1).strip()
            else:
                partes[secao.lower()] = f"[Parte {secao} não gerada]"
        
        return partes
        
    except Exception as e:
        st.error(f"❌ Erro na geração com Groq: {str(e)}")
        return None

def exibir_roteiro(roteiro):
    """Exibe o roteiro formatado no Streamlit"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("## 📖 **ROTEIRO**")
        st.markdown("---")
        
    with col2:
        if roteiro:
            st.markdown("### 🎣 **HOOK**")
            st.markdown(f"**{roteiro.get('hook', '')}**")
            st.markdown("---")
            
            st.markdown("### 📖 **LEITURA**")
            st.markdown(roteiro.get('leitura', ''))
            st.markdown("---")
            
            st.markdown("### 💭 **REFLEXÃO**")
            st.markdown(roteiro.get('reflexão', ''))
            st.markdown("---")
            
            st.markdown("### 🌟 **APLICAÇÃO**")
            st.markdown(roteiro.get('aplicação', ''))
            st.markdown("---")
            
            st.markdown("### 🙏 **ORAÇÃO**")
            st.markdown(roteiro.get('oração', ''))
            
            # Botão para copiar
            st.markdown("---")
            if st.button("📋 Copiar todo o roteiro"):
                texto_completo = (
                    f"HOOK: {roteiro.get('hook', '')}\n\n"
                    f"LEITURA: {roteiro.get('leitura', '')}\n\n"
                    f"REFLEXÃO: {roteiro.get('reflexão', '')}\n\n"
                    f"APLICAÇÃO: {roteiro.get('aplicação', '')}\n\n"
                    f"ORAÇÃO: {roteiro.get('oração', '')}"
                )
                st.code(texto_completo)
        else:
            st.warning("⚠️ Nenhuma parte do roteiro foi gerada")

# Interface principal
def main():
    st.set_page_config(page_title="Studio Jhonata", layout="wide")
    st.title("✨ Studio Jhonata - Gerador Litúrgico IA")
    st.markdown("---")
    
    col_data, col_status = st.columns(2)
    
    with col_data:
        data_selecionada = st.date_input(
            "📅 Selecione a data:",
            value=date.today(),
            min_value=date(2023, 1, 1)
        )
    
    with col_status:
        st.markdown("**Status:** ✅ Groq API configurada")
    
    if st.button("🚀 Gerar Roteiro Completo", type="primary"):
        with st.spinner("🔍 Buscando liturgia..."):
            liturgia = buscar_liturgia_do_dia(data_selecionada.strftime("%Y-%m-%d"))
        
        if liturgia:
            st.success(f"✅ Evangelho encontrado: {liturgia['referencia']}")
            
            with st.spinner("🤖 Gerando com Groq..."):
                roteiro = gerar_roteiro_com_groq(
                    liturgia['texto'], 
                    liturgia['referencia']
                )
            
            exibir_roteiro(roteiro)
        else:
            st.error("Não foi possível gerar o roteiro")

if __name__ == "__main__":
    main()
