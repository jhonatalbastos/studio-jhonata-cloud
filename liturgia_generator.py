from datetime import date
import requests

API_LITURGIA = "https://api-liturgia-diaria.vercel.app/?date="  # [web:43]

def buscar_evangelho(data_obj: date):
    """Busca Evangelho do dia na API e devolve dados básicos."""
    data_str = data_obj.strftime("%Y-%m-%d")
    try:
        resp = requests.get(API_LITURGIA + data_str, timeout=10)
        resp.raise_for_status()
        dados = resp.json()

        # A estrutura real vem em today -> readings -> gospel
        today = dados.get("today", {})
        readings = today.get("readings", {})
        gospel = readings.get("gospel")

        if not gospel:
            return None

        # Monta campos que vamos usar
        referencia = today.get("entry_title", "").strip()
        titulo = gospel.get("head_title", "").strip() or gospel.get("title", "").strip()
        texto = gospel.get("text", "").strip()

        if not texto:
            return None

        return {
            "referencia": referencia,
            "titulo": titulo,
            "texto": texto,
        }
    except Exception:
        return None

def gerar_roteiro(data_obj: date, tipo: str = "Evangelho"):
    """Monta o roteiro em 4 partes usando o Evangelho real do dia."""
    ev = buscar_evangelho(data_obj)
    data_str = data_obj.strftime("%d/%m/%Y")

    if not ev:
        # Se a API falhar, volta um roteiro vazio para o app mostrar erro.
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

    # Usa só um trecho inicial para não ficar enorme nem copiar tudo.
    texto = ev["texto"]
    trecho_leitura = texto[:400] + "..." if len(texto) > 400 else texto

    partes = [
        {
            "nome": "HOOK + LEITURA + CTA",
            "titulo_3l": f"EVANGELHO\n{data_str}\n{referencia}",
            "texto": (
                "Hoje a Igreja nos dá este Evangelho. "
                "Escute com atenção este trecho: "
                f"{trecho_leitura} "
                "Fica comigo até o final para rezarmos juntos."
            )
        },
        {
            "nome": "REFLEXÃO",
            "titulo_3l": f"REFLEXÃO\n{data_str}\n{referencia}",
            "texto": (
                "Este Evangelho mostra como Jesus olha para o coração e não só para aquilo que aparece. "
                "O que essa Palavra revela sobre a sua vida hoje?"
            )
        },
        {
            "nome": "APLICAÇÃO",
            "titulo_3l": f"APLICAÇÃO\n{data_str}\n{referencia}",
            "texto": (
                "Pensa em uma atitude concreta para hoje: "
                "ser mais generoso, ajudar alguém em necessidade ou oferecer a Deus aquilo que você tem e é."
            )
        },
        {
            "nome": "ORAÇÃO",
            "titulo_3l": f"ORAÇÃO\n{data_str}\n{referencia}",
            "texto": (
                "Senhor Jesus, obrigado por esta Palavra. "
                "Ensina-me a oferecer a ti, com amor, tudo o que eu sou e o que eu tenho. Amém."
            )
        },
    ]

    return {
        "data": data_str,
        "tipo": tipo,
        "referencia": referencia,
        "titulo": titulo_liturgico,
        "texto_completo": texto,
        "partes": partes
    }
