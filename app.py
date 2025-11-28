import streamlit as st
from datetime import date
import re
import requests
from groq import Groq
import json

# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Studio Jhonata",
    layout="wide",
    initial_sidebar_state="expanded",
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
# Inicializar banco de personagens
# =========================
@st.cache_data
def inicializar_personagens():
    return {
        "Jesus": "homem de 33 anos, pele morena clara, cabelo castanho ondulado na altura dos ombros, barba bem aparada, olhos castanhos penetrantes e serenos, túnica branca tradicional com detalhes vermelhos, manto azul, expressão de autoridade amorosa, estilo renascentista clássico",
        "São Pedro": "homem robusto de 50 anos, pele bronzeada, cabelo curto grisalho, barba espessa, olhos determinados, túnica de pescador bege com remendos, mãos calejadas, postura forte, estilo realista bíblico",
        "São João": "jovem de 25 anos, magro, cabelo castanho longo liso, barba rala, olhos expressivos, túnica branca limpa, expressão contemplativa, estilo renascentista",
    }


# =========================
# Limpeza do texto bíblico
# =========================
def limpar_texto_evangelho(texto: str) -> str:
    if not texto:
        return ""
    texto_limpo = texto.replace("\n", " ").strip()
    texto_limpo = re.sub(r"\b(\d{1,3})(?=[A-Za-zÁ-Úá-ú])", "", texto_limpo)
    texto_limpo = re.sub(r"\s{2,}", " ", texto_limpo)
    return texto_limpo.strip()


# =========================
# Extrair referência bíblica
# =========================
def extrair_referencia_biblica(titulo: str):
    if not titulo:
        return None
    m = re.search(
        r"segundo\s+São\s+([A-Za-zÁ-Úá-ú]+)\s+(\d+),\s*([\d\-–]+)",
        titulo,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    evangelista = m.group(1).strip()
    capitulo = m.group(2).strip()
    versiculos_raw = m.group(3).strip()
    versiculos = versiculos_raw.replace("-", " a ").replace("–", " a ")
    return {"evangelista": evangelista, "capitulo": capitulo, "versiculos": versiculos}


def formatar_referencia_curta(ref_biblica):
    if not ref_biblica:
        return ""
    return f"{ref_biblica['evangelista']}, Cap. {ref_biblica['capitulo']}, {ref_biblica['versiculos']}"


# =========================
# ANÁLISE DE PERSONAGENS + BANCO
# =========================
def analisar_personagens_groq(texto_evangelho: str, banco_personagens: dict):
    client = inicializar_groq()
    
    system_prompt = """Você é especialista em análise bíblica. Analise o texto e identifique TODOS os personagens bíblicos mencionados.
    
    Formato EXATO da resposta:
    PERSONAGENS: nome1; nome2; nome3
    NOVOS: NomeNovo|descrição_detalhada_aparência_física_roupas_idade_estilo (apenas se não existir no banco)
    
    BANCO EXISTENTE: """ + "; ".join(banco_personagens.keys()) + """
    
    Exemplo:
    PERSONAGENS: Jesus; Pedro; fariseus
    NOVOS: Mulher Samaritana|mulher de 35 anos, pele morena, véu colorido, jarro d'água, expressão curiosa, túnica tradicional"""
    
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TEXTO: {texto_evangelho[:1500]}"}
            ],
            temperature=0.3,
            max_tokens=400,
        )
        
        resultado = resp.choices[0].message.content
        personagens_detectados = {}
        
        # Parse PERSONAGENS
        if m := re.search(r"PERSONAGENS:\s*(.+)", resultado):
            nomes = [n.strip() for n in m.group(1).split(";") if n.strip()]
            for nome in nomes:
                if nome in banco_personagens:
                    personagens_detectados[nome] = banco_personagens[nome]
        
        # Parse NOVOS
        if m := re.search(r"NOVOS:\s*(.+)", resultado):
            novos = m.group(1).strip()
            for novo in novos.split(","):
                if "|" in novo:
                    nome, desc = novo.split("|", 1)
                    personagens_detectados[nome.strip()] = desc.strip()
                    banco_personagens[nome.strip()] = desc.strip()
        
        return personagens_detectados
    except:
        return {}


# =========================
# APIs Liturgia
# =========================
def buscar_liturgia_api1(data_str: str):
    url = f"https://api-liturgia-diaria.vercel.app/?date={data_str}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
        today = dados.get("today", {})
        readings = today.get("readings", {})
        gospel = readings.get("gospel")
        if not gospel:
            return None
        referencia_liturgica = today.get("entry_title", "").strip() or "Evangelho do dia"
        titulo = (gospel.get("head_title", "") or gospel.get("title", "") or "Evangelho de Jesus Cristo").strip()
        texto = gospel.get("text", "").strip()
        if not texto:
            return None
        texto_limpo = limpar_texto_evangelho(texto)
        ref_biblica = extrair_referencia_biblica(titulo)
        return {
            "fonte": "api-liturgia-diaria.vercel.app",
            "titulo": titulo,
            "referencia_liturgica": referencia_liturgica,
            "texto": texto_limpo,
            "ref_biblica": ref_biblica,
        }
    except:
        return None


def buscar_liturgia_api2(data_str: str):
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
        if not texto:
            return None
        texto_limpo = limpar_texto_evangelho(texto)
        return {
            "fonte": "liturgia.up.railway.app",
            "titulo": "Evangelho do dia",
            "referencia_liturgica": "Evangelho do dia",
            "texto": texto_limpo,
            "ref_biblica": None,
        }
    except:
        return None


def obter_evangelho_com_fallback(data_str: str):
    ev = buscar_liturgia_api1(data_str)
    if ev:
        st.info("📡 Usando api-liturgia-diaria.vercel.app")
        return ev
    ev = buscar_liturgia_api2(data_str)
    if ev:
        st.info("📡 Usando liturgia.up.railway.app")
        return ev
    st.error("❌ Não foi possível obter o Evangelho")
    return None


# =========================
# Roteiro + Prompts Visuais
# =========================
def gerar_roteiro_com_prompts_groq(texto_evangelho: str, referencia_liturgica: str, personagens: dict):
    client = inicializar_groq()
    texto_limpo = limpar_texto_evangelho(texto_evangelho)
    
    personagens_str = json.dumps(personagens, ensure_ascii=False)
    
    system_prompt = f"""Crie roteiro + 5 prompts visuais CATÓLICOS para vídeo devocional.

PERSONAGENS FIXOS: {personagens_str}

IMPORTANTE:
- 4 PARTES EXATAS: HOOK, REFLEXÃO, APLICAÇÃO, ORAÇÃO
- 5 PROMPTS VISUAIS: um para cada parte + GERAL
- USE SEMPRE as descrições exatas dos personagens
- Estilo: artístico renascentista católico, luz divina, cores quentes

Formato EXATO:
HOOK: [texto 5-8s]
PROMPT_HOOK: [prompt visual com personagens fixos]
REFLEXÃO: [texto 20-25s]  
PROMPT_REFLEXÃO: [prompt visual com personagens fixos]
APLICAÇÃO: [texto 20-25s]
PROMPT_APLICACAO: [prompt visual com personagens fixos]  
ORAÇÃO: [texto 20-25s]
PROMPT_ORACAO: [prompt visual com personagens fixos]
PROMPT_GERAL: [prompt para thumbnail/capa]"""
    
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, 
                     {"role": "user", "content": f"Evangelho: {referencia_liturgica}\n\n{texto_limpo[:2000]}"}],
            temperature=0.7,
            max_tokens=1200,
        )
        
        texto_gerado = resp.choices[0].message.content
        partes = {}
        secoes = ["HOOK", "REFLEXÃO", "APLICAÇÃO", "ORAÇÃO"]
        
        for secao in secoes:
            # Texto da seção
            padrao_texto = rf"{secao}:\s*(.*?)(?=\n[A-ZÁÉÍÓÚÃÕÇ]{{3,}}:\s*|\nPROMPT|$)"
            match_texto = re.search(padrao_texto, texto_gerado, re.DOTALL | re.IGNORECASE)
            if match_texto:
                partes[secao.lower()] = match_texto.group(1).strip()
            
            # Prompt da seção
            padrao_prompt = rf"PROMPT_{secao}:\s*(.*?)(?=\n[A-ZÁÉÍÓÚÃÕÇ]{{3,}}:\s*|$)"
            match_prompt = re.search(padrao_prompt, texto_gerado, re.DOTALL | re.IGNORECASE)
            if match_prompt:
                partes[f"prompt_{secao.lower()}"] = match_prompt.group(1).strip()
        
        # Prompt geral
        m = re.search(r"PROMPT_GERAL:\s*(.+)", texto_gerado, re.DOTALL | re.IGNORECASE)
        if m:
            partes["prompt_geral"] = m.group(1).strip()
            
        return partes
    except Exception as e:
        st.error(f"❌ Erro Groq: {e}")
        return None


def montar_leitura_com_formula(texto_evangelho: str, ref_biblica):
    if ref_biblica:
        abertura = (
            f"Proclamação do Evangelho de Jesus Cristo, segundo São "
            f"{ref_biblica['evangelista']}, "
            f"Capítulo {ref_biblica['capitulo']}, "
            f"versículos {ref_biblica['versiculos']}. "
            "Glória a vós, Senhor!"
        )
    else:
        abertura = "Proclamação do Evangelho de Jesus Cristo, segundo São Lucas. Glória a vós, Senhor!"
    fechamento = "Palavra da Salvação. Glória a vós, Senhor!"
    return f"{abertura} {texto_evangelho} {fechamento}"


# =========================
# Interface Principal
# =========================
st.title("✨ Studio Jhonata - Automação Litúrgica")
st.markdown("---")

# Sidebar
st.sidebar.title("⚙️ Configurações")
st.sidebar.info("1️⃣ api-liturgia-diaria\n2️⃣ liturgia.railway\n3️⃣ Groq fallback")
st.sidebar.success("✅ Groq ativo")

# Inicializar banco personagens
if "personagens_biblicos" not in st.session_state:
    st.session_state.personagens_biblicos = inicializar_personagens()

tab1, tab2, tab3, tab4 = st.tabs(["📖 Gerar Roteiro", "🎨 Personagens", "🎥 Fábrica Vídeo", "📊 Histórico"])

# TAB 1: ROTEIRO
with tab1:
    st.header("🚀 Gerador de Roteiro + Imagens")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        data_selecionada = st.date_input("📅 Data liturgia:", value=date.today(), min_value=date(2023, 1, 1))
    with col2:
        st.info("✅ Pronto")
    
    if st.button("🚀 Gerar Roteiro Completo", type="primary"):
        data_str = data_selecionada.strftime("%Y-%m-%d")
        with st.spinner("🔍 Buscando Evangelho..."):
            liturgia = obter_evangelho_com_fallback(data_str)
        if not liturgia:
            st.stop()
        
        st.success(f"✅ {liturgia['referencia_liturgica']} ({liturgia['fonte']})")
        
        # Análise personagens
        with st.spinner("🤖 Analisando personagens..."):
            personagens_detectados = analisar_personagens_groq(liturgia["texto"], st.session_state.personagens_biblicos)
        
        # Gerar roteiro + prompts
        with st.spinner("✨ Gerando roteiro e prompts visuais..."):
            roteiro = gerar_roteiro_com_prompts_groq(
                liturgia["texto"], liturgia["referencia_liturgica"], 
                {**st.session_state.personagens_biblicos, **personagens_detectados}
            )
        
        if not roteiro:
            st.stop()
        
        leitura_montada = montar_leitura_com_formula(liturgia["texto"], liturgia.get("ref_biblica"))
        ref_curta = formatar_referencia_curta(liturgia.get("ref_biblica"))
        
        st.markdown("## 📖 Roteiro pronto")
        if ref_curta:
            st.markdown(f"**Leitura:** {ref_curta}")
        st.markdown("---")
        
        # PERSONAGENS DETECTADOS
        if personagens_detectados:
            st.markdown("### 👥 Personagens nesta leitura")
            for nome, desc in personagens_detectados.items():
                st.markdown(f"**{nome}:** {desc}")
            st.markdown("---")
        
        # ROTEIRO + PROMPTS
        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.markdown("### 🎣 HOOK")
            st.markdown(roteiro.get("hook", ""))
            st.markdown("**📸 Prompt:**")
            st.code(roteiro.get("prompt_hook", ""))
            
            st.markdown("### 💭 REFLEXÃO")
            st.markdown(roteiro.get("reflexão", ""))
            st.markdown("**📸 Prompt:**")
            st.code(roteiro.get("prompt_reflexão", ""))
        
        with col_dir:
            st.markdown("### 📖 LEITURA")
            st.markdown(leitura_montada)
            
            st.markdown("### 🌟 APLICAÇÃO")
            st.markdown(roteiro.get("aplicação", ""))
            st.markdown("**📸 Prompt:**")
            st.code(roteiro.get("prompt_aplicação", ""))
        
        st.markdown("### 🙏 ORAÇÃO")
        st.markdown(roteiro.get("oração", ""))
        st.markdown("**📸 Prompt:**")
        st.code(roteiro.get("prompt_oracao", ""))
        
        st.markdown("### 🖼️ THUMBNAIL")
        st.code(roteiro.get("prompt_geral", ""))
        st.markdown("---")

# TAB 2: GERENCIAR PERSONAGENS
with tab2:
    st.header("🎨 Banco de Personagens Bíblicos")
    
    banco = st.session_state.personagens_biblicos.copy()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📋 Todos os personagens")
        for i, (nome, desc) in enumerate(banco.items()):
            with st.expander(f"✏️ {nome}"):
                novo_nome = st.text_input(f"Nome {i}", value=nome, key=f"nome_{i}")
                nova_desc = st.text_area(f"Descrição {i}", value=desc, height=100, key=f"desc_{i}")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"💾 Salvar", key=f"salvar_{i}"):
                        if novo_nome and nova_desc:
                            if novo_nome in st.session_state.personagens_biblicos and novo_nome != nome:
                                del st.session_state.personagens_biblicos[novo_nome]
                            st.session_state.personagens_biblicos[novo_nome] = nova_desc
                            st.rerun()
                with col_b:
                    if st.button(f"🗑️ Apagar", key=f"apagar_{i}"):
                        del st.session_state.personagens_biblicos[nome]
                        st.rerun()
    
    with col2:
        st.markdown("### ➕ Novo Personagem")
        novo_nome = st.text_input("Nome do personagem", key="novo_nome")
        nova_desc = st.text_area("Descrição detalhada (aparência, roupas, idade, estilo)", height=120, key="nova_desc")
        if st.button("➕ Adicionar") and novo_nome and nova_desc:
            st.session_state.personagens_biblicos[novo_nome] = nova_desc
            st.rerun()

# TAB 3 e 4 (placeholder)
with tab3:
    st.header("🎥 Fábrica de Vídeo")
    st.info("Em desenvolvimento: áudio gTTS + MoviePy")

with tab4:
    st.header("📊 Histórico")
    st.info("Em breve")

st.markdown("---")
st.markdown("Feito com ❤️ para evangelização - Studio Jhonata")
