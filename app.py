import streamlit as st
from datetime import date
import re
import requests
from groq import Groq

# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Studio Jhonata",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Groq - cliente lazy
# =========================
_client = None

def inicializar_groq():
    global _client
    if _client is None:
        if "GROQ_API_KEY" not in st.secrets:
            st.error("❌ Configure GROQ_API_KEY em Settings → Secrets no Streamlit Cloud.")
            st.stop()
        _client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return _client

# =========================
# Limpeza do texto bíblico
# =========================
def limpar_texto_evangelho(texto: str) -> str:
    """Remove números de versículos e espaços extras do texto do Evangelho."""
    texto_limpo = re.sub(r"\[\d+\]", "", texto)              # remove [1], [2]...
    texto_limpo = re.sub(r"\d+\s*[:\-]\s*", "", texto_limpo) # remove 1:1, 2-3...
    texto_limpo = re.sub(r"\n\s*\n", "\n", texto_limpo)      # junta linhas vazias
    return texto_limpo.strip()

# =========================
# API 1 – api-liturgia-diaria.vercel.app
# =========================
def buscar_liturgia_api1(data_str: str):
    """
    Usa API_LITURGIA_DIARIA (sagradaliturgia.com.br) via Vercel.
    GET https://api-liturgia-diaria.vercel.app/today
    ou /date/AAAA-MM-DD.
    Estrutura vista no JSON anexado. [attached_file:1]
    """
    # A API aceita /today ou /date/AAAA-MM-DD – vamos usar /date para qualquer data.
    url = f"https://api-liturgia-diaria.vercel.app/date/{data_str}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        dados = resp.json()

        today = dados.get("today") or dados  # segurança
        readings = today.get("readings", {})
        gospel = readings.get("gospel", {})

        texto = gospel.get("text", "")
        titulo_head = gospel.get("head_title", "") or gospel.get("title", "")
        referencia = titulo_head if titulo_head else "Evangelho do dia"

        if not texto:
            return None

        return {
            "fonte": "api-liturgia-diaria.vercel.app",
            "titulo": titulo_head,
            "referencia": referencia,
            "texto": texto,
        }
    except Exception:
        return None

# =========================
# API 2 – Railway (Dancrf /liturgia-diaria)
# =========================
def buscar_liturgia_api2(data_str: str):
    # API alternativa de liturgia diária. [web:56][web:92]
    url = f"https://liturgia.up.railway.app/v2/{data_str}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        dados = resp.json()

        lit = dados.get("liturgia", {})
        ev = lit.get("evangelho") or lit.get("evangelho_do_dia") or {}
        if not ev:
            return None

        texto = ev.get("texto", "") or ev.get("conteudo", "")
        ref = ev.get("referencia", "") or ev.get("ref", "")
        titulo = ev.get("titulo", "") or ev.get("titulo_evangelho", "")

        if not texto:
            return None

        referencia = ref or titulo or "Evangelho do dia"

        return {
            "fonte": "liturgia.up.railway.app",
            "titulo": titulo,
            "referencia": referencia,
            "texto": texto,
        }
    except Exception:
        return None

# =========================
# Fallback – Groq gera Evangelho INTEIRO
# =========================
def gerar_evangelho_com_groq(data_str: str):
    """
    Quando nenhuma API de liturgia responde, pede ao Groq para gerar
    UM texto completo de Evangelho para a liturgia católica daquele dia.
    """
    client = inicializar_groq()

    system_prompt = (
        "Você é um teólogo e liturgista católico.\n"
        "Para a data informada, gere UMA proposta de Evangelho do dia, "
        "EM TEXTO COMPLETO, como se fosse lido na Missa, sem números de versículos.\n\n"
        "Responda APENAS neste formato, em português do Brasil:\n"
        "REFERENCIA: Evangelho de Jesus Cristo segundo São ... [capítulo, versículos]\n"
        "TEXTO: [texto completo do Evangelho, pronto para ser lido em voz alta, sem números de versículos]\n"
    )

    user_prompt = (
        f"Data litúrgica: {data_str}.\n\n"
        "Gere uma referência e o texto COMPLETO de um Evangelho apropriado para esse dia, "
        "seguindo o formato acima, sem comentários adicionais."
    )

    try:
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        conteudo = resp.choices[0].message.content

        ref_match = re.search(r"REFERENCIA:\s*(.+)", conteudo)
        texto_match = re.search(r"TEXTO:\s*(.+)", conteudo, flags=re.DOTALL)

        referencia = ref_match.group(1).strip() if ref_match else "Evangelho do dia"
        texto = texto_match.group(1).strip() if texto_match else conteudo

        return {
            "fonte": "groq-fallback",
            "titulo": "Evangelho do dia (gerado por IA)",
            "referencia": referencia,
            "texto": texto,
        }
    except Exception as e:
        st.error(f"❌ Falha também no fallback do Groq para gerar o Evangelho: {e}")
        return None

# =========================
# Função unificada de liturgia (com 2 APIs + Groq)
# =========================
def obter_evangelho_com_fallback(data_str: str):
    """
    Ordem:
    1) api-liturgia-diaria.vercel.app
    2) liturgia.up.railway.app
    3) Groq gera Evangelho inteiro
    """
    ev = buscar_liturgia_api1(data_str)
    if ev:
        st.info("📡 Usando liturgia de api-liturgia-diaria.vercel.app")
        return ev

    ev = buscar_liturgia_api2(data_str)
    if ev:
        st.info("📡 Usando liturgia de liturgia.up.railway.app")
        return ev

    st.warning("⚠️ Nenhuma API de liturgia respondeu. Gerando Evangelho completo via Groq.")
    ev = gerar_evangelho_com_groq(data_str)
    if ev:
        return ev

    st.error("❌ Não foi possível obter o Evangelho, nem pelas APIs nem pelo Groq.")
    return None

# =========================
# Roteiro com Groq (Hook + 4 partes)
# =========================
def gerar_roteiro_com_groq(texto_evangelho: str, referencia: str):
    """Gera HOOK, Leitura, Reflexão, Aplicação e Oração usando Groq."""
    try:
        client = inicializar_groq()
        texto_limpo = limpar_texto_evangelho(texto_evangelho)

        system_prompt = (
            "Você cria roteiros católicos para vídeos curtos (TikTok/Reels) em português do Brasil.\n\n"
            "Sempre responda EXATAMENTE neste formato, com 5 partes, cada uma iniciando com o título em maiúsculas:\n"
            "HOOK: uma ou duas frases curtas (5-8 segundos) que criem curiosidade sobre o Evangelho.\n"
            "LEITURA: 'Proclamação do Evangelho de Jesus Cristo, segundo [evangelista]. [referência]. Glória a vós, Senhor!' "
            "+ o texto limpo do Evangelho adaptado para leitura em vídeo + 'Palavra da Salvação. Glória a vós, Senhor!'.\n"
            "REFLEXÃO: meditação devocional de 20-25 segundos (2-3 frases) conectando o Evangelho com a vida espiritual.\n"
            "APLICAÇÃO: 'Evangelho na sua vida hoje' em 20-25 segundos, bem prática.\n"
            "ORAÇÃO: oração curta (20-25 segundos), simples e sincera, inspirada no Evangelho.\n\n"
            "Formato exato da resposta (sem comentários adicionais):\n"
            "HOOK: ...\n"
            "LEITURA: ...\n"
            "REFLEXÃO: ...\n"
            "APLICAÇÃO: ...\n"
            "ORAÇÃO: ..."
        )

        user_prompt = (
            f"Evangelho do dia: {referencia}\n\n"
            f"Texto (sem números de versículos):\n{texto_limpo[:2000]}\n\n"
            "Gere o roteiro completo no formato exato pedido."
        )

        resposta = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )

        texto_gerado = resposta.choices[0].message.content

        partes = {}
        secoes = ["HOOK", "LEITURA", "REFLEXÃO", "APLICAÇÃO", "ORAÇÃO"]
        for secao in secoes:
            padrao = rf"{secao}:\s*(.*?)(?=\n[A-ZÁÉÍÓÚÃÕÇ]{3,}:\s*|$)"
            match = re.search(padrao, texto_gerado, flags=re.DOTALL)
            if match:
                partes[secao.lower()] = match.group(1).strip()
            else:
                partes[secao.lower()] = f"[Parte {secao} não foi gerada pela IA]"

        return partes

    except Exception as e:
        st.error(f"❌ Erro ao gerar roteiro com Groq: {e}")
        return None

# =========================
# Interface principal
# =========================
st.title("✨ Studio Jhonata - Automação Litúrgica")
st.markdown("---")

st.sidebar.title("⚙️ Configurações")
st.sidebar.markdown("**APIs de liturgia (ordem de uso):**")
st.sidebar.info("1️⃣ api-liturgia-diaria.vercel.app\n2️⃣ liturgia.up.railway.app\n3️⃣ Fallback: Groq gera Evangelho inteiro")
st.sidebar.markdown("---")
st.sidebar.success("✅ Groq ativo para roteiro e fallback")

tab1, tab2, tab3 = st.tabs(["📖 Gerar Roteiro", "🎥 Fábrica de Vídeo", "📊 Histórico"])

# --------- TAB 1: GERAR ROTEIRO ----------
with tab1:
    st.header("🚀 Gerador de Roteiro Litúrgico com IA")

    col1, col2 = st.columns([2, 1])
    with col1:
        data_selecionada = st.date_input(
            "📅 Selecione a data da liturgia:",
            value=date.today(),
            min_value=date(2023, 1, 1),
        )
    with col2:
        st.info("Status: ✅ pronto para gerar")

    if st.button("🚀 Gerar Roteiro Completo", type="primary", use_container_width=True):
        data_str = data_selecionada.strftime("%Y-%m-%d")

        with st.spinner("🔍 Buscando/gerando Evangelho do dia..."):
            liturgia = obter_evangelho_com_fallback(data_str)

        if not liturgia:
            st.stop()

        st.success(f"✅ Evangelho utilizado: **{liturgia['referencia']}** ({liturgia['fonte']})")

        with st.spinner("🤖 Gerando roteiro com Groq..."):
            roteiro = gerar_roteiro_com_groq(liturgia["texto"], liturgia["referencia"])

        if not roteiro:
            st.stop()

        st.markdown("## 📖 Roteiro pronto para gravar")
        st.markdown("---")

        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.markdown("### 🎣 HOOK (5–8s)")
            st.markdown(f"> **{roteiro.get('hook', '')}**")
            st.markdown("---")

            st.markdown("### 💭 REFLEXÃO (20–25s)")
            st.markdown(roteiro.get("reflexão", ""))

        with col_dir:
            st.markdown("### 📖 LEITURA")
            st.markdown(roteiro.get("leitura", ""))
            st.markdown("---")

            st.markdown("### 🌟 APLICAÇÃO (20–25s)")
            st.markdown(roteiro.get("aplicação", ""))

        st.markdown("### 🙏 ORAÇÃO (20–25s)")
        st.markdown(roteiro.get("oração", ""))
        st.markdown("---")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("📋 Copiar roteiro completo", use_container_width=True):
                texto_completo = (
                    f"HOOK: {roteiro['hook']}\n\n"
                    f"LEITURA: {roteiro['leitura']}\n\n"
                    f"REFLEXÃO: {roteiro['reflexão']}\n\n"
                    f"APLICAÇÃO: {roteiro['aplicação']}\n\n"
                    f"ORAÇÃO: {roteiro['oração']}"
                )
                st.code(texto_completo)
        with col_b2:
            st.markdown("**👉 Depois: usar na Fábrica de Vídeo**")

        if "historico" not in st.session_state:
            st.session_state["historico"] = []
        st.session_state["historico"].append(
            {
                "data": data_selecionada,
                "referencia": liturgia["referencia"],
                "fonte": liturgia["fonte"],
                "roteiro": roteiro,
            }
        )

# --------- TAB 2: FÁBRICA DE VÍDEO ----------
with tab2:
    st.header("🎥 Fábrica de Vídeo (Em desenvolvimento)")
    st.info(
        "Aqui virão as próximas etapas:\n"
        "- Geração de áudio com gTTS\n"
        "- Geração de imagens de fundo\n"
        "- Montagem do vídeo vertical (MoviePy)\n"
        "- Geração de legendas SRT\n"
        "- Export para TikTok / Reels"
    )
    st.button("🚧 Em breve", use_container_width=True)

# --------- TAB 3: HISTÓRICO ----------
with tab3:
    st.header("📊 Histórico de roteiros nesta sessão")

    historico = st.session_state.get("historico", [])
    if not historico:
        st.info("Nenhum roteiro gerado ainda nesta sessão.")
    else:
        for item in reversed(historico[-10:]):
            with st.expander(
                f"📅 {item['data'].strftime('%d/%m/%Y')} - {item['referencia']} ({item['fonte']})"
            ):
                r = item["roteiro"]
                st.markdown(f"**HOOK:** {r['hook']}")
                st.markdown(f"**Leitura (início):** {r['leitura'][:200]}...")
                st.markdown(f"**Reflexão (início):** {r['reflexão'][:200]}...")

st.markdown("---")
st.markdown("Feito com ❤️ para a evangelização - Studio Jhonata")
