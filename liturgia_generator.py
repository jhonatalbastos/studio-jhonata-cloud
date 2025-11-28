from datetime import date
import re
import requests
import streamlit as st
from groq import Groq  # Cliente oficial Groq [web:86][web:91]

# API pública de liturgia diária [web:43]
API_LITURGIA = "https://api-liturgia-diaria.vercel.app/?date="


def limpar_versiculos(texto: str) -> str:
    """
    Remove números de versículos do Evangelho.
    Exemplos: '1Jesus', '2Viu também', etc.
    """
    if not texto:
        return ""

    t = texto.replace("\n", " ").strip()
    # Remove números colados no início das palavras (1Jesus, 20Quando...)
    t = re.sub(r"\b(\d{1,3})(?=[A-Za-zÁ-Úá-ú])", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def buscar_evangelho(data_obj: date):
    """Busca Evangelho do dia na API e devolve dados básicos (texto já limpo)."""
    data_str = data_obj.strftime("%Y-%m-%d")
    try:
        resp = requests.get(API_LITURGIA + data_str, timeout=10)
        resp.raise_for_status()
        dados = resp.json()

        today = dados.get("today", {})
        readings = today.get("readings", {})
        gospel = readings.get("gospel")

        if not gospel:
            return None

        referencia = today.get("entry_title", "").strip()
        titulo = gospel.get("head_title", "").strip() or gospel.get("title", "").strip()
        texto = gospel.get("text", "").strip()

        if not texto:
            return None

        texto_limpo = limpar_versiculos(texto)

        return {
            "referencia": referencia,
            "titulo": titulo,
            "texto": texto_limpo,
        }
    except Exception:
        return None


def get_groq_client() -> Groq:
    """Cria cliente do Groq usando a chave salva em st.secrets."""
    api_key = st.secrets.get("GROQ_API_KEY", None)
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada em Secrets do Streamlit.")
    return Groq(api_key=api_key)


def gerar_partes_com_groq(evangelho_texto: str, referencia: str, data_str: str):
    """
    Usa Groq para gerar Reflexão, Aplicação e Oração com base no Evangelho.
    Retorna um dicionário com os três textos.
    """
    client = get_groq_client()

    prompt_usuario = (
        "Você é um roteirista católico, escrevendo para vídeos curtos "
        "no estilo TikTok/Reels, em português do Brasil, com tom simples, devocional "
        "e acolhedor.\n\n"
        f"Evangelho do dia ({data_str}) - {referencia}:\n"
        f"{evangelho_texto}\n\n"
        "Com base neste Evangelho, gere três textos:\n"
        "1) REFLEXÃO: um parágrafo de 3 a 5 frases, com aproximadamente 20 a 30 segundos de leitura em voz alta. "
        "Ajude a pessoa a entender o que Jesus comunica com essa Palavra hoje.\n"
        "2) APLICAÇÃO: um parágrafo de 3 a 5 frases, também com cerca de 20 a 30 segundos, "
        "com sugestões bem práticas de como viver essa Palavra no dia a dia.\n"
        "3) ORAÇÃO: uma oração espontânea, em primeira pessoa, com 3 a 5 frases, também em torno de 20 a 30 segundos.\n\n"
        "Responda EXATAMENTE neste formato JSON, sem comentários e sem texto fora do JSON:\n"
        "{\n"
        '  \"reflexao\": \"...\",\n'
        '  \"aplicacao\": \"...\",\n'
        '  \"oracao\": \"...\"\n'
        "}\n"
    )

    chat = client.chat.completions.create(
        model="llama-3.1-70b-versatile",  # modelo recomendado pela Groq [web:82][web:94]
        messages=[
            {
                "role": "system",
                "content": (
                    "Você ajuda a criar roteiros católicos para vídeos verticais. "
                    "Sempre escreva em português do Brasil, de forma simples, calorosa e fiel ao espírito do Evangelho."
                ),
            },
            {"role": "user", "content": prompt_usuario},
        ],
        temperature=0.7,
        max_tokens=800,
    )

    content = chat.choices[0].message.content.strip()

    # Tenta interpretar a resposta como JSON
    import json

    try:
        dados = json.loads(content)
        reflexao = dados.get("reflexao", "").strip()
        aplicacao = dados.get("aplicacao", "").strip()
        oracao = dados.get("oracao", "").strip()
    except Exception:
        # Se por algum motivo não vier JSON perfeito, usa tudo como reflexão
        reflexao = content
        aplicacao = ""
        oracao = ""

    return {
        "reflexao": reflexao,
        "aplicacao": aplicacao,
        "oracao": oracao,
    }


def gerar_roteiro(data_obj: date, tipo: str = "Evangelho"):
    """
    Monta o roteiro em 4 partes:
      1) Hook + leitura completa com abertura e fechamento.
      2) Reflexão (gerada pela IA Groq).
      3) Aplicação (gerada pela IA Groq).
      4) Oração (gerada pela IA Groq).
    """
    ev = buscar_evangelho(data_obj)
    data_str = data_obj.strftime("%d/%m/%Y")

    if not ev:
        return {
            "data": data_str,
            "tipo": tipo,
            "referencia": "",
            "titulo": "",
            "texto_completo": "",
            "partes": []
        }

    referencia = ev["referencia"] or "Evangelho do dia"
    titulo_liturgico = ev["titulo"] or "Evangelho de Jesus Cristo"
    texto_evangelho = ev["texto"]

    # Parte 1 – Hook + leitura + CTA (aqui ainda é fixa, mas usando texto real)
    abertura = (
        f"Proclamação do Evangelho de Jesus Cristo, segundo São Lucas. "
        f"{referencia}. Glória a vós, Senhor!"
    )
    fechamento = "Palavra da Salvação. Glória a vós, Senhor!"

    hook_inicial = (
        "Talvez você esteja vivendo um momento confuso, sem entender muito bem "
        "o que Deus está fazendo na sua vida.
