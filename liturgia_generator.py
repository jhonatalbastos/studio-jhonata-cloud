from datetime import date
import requests

API_LITURGIA = "https://api-liturgia-diaria.vercel.app/?date="  # [web:43]

def buscar_evangelho(data_obj: date):
    """Busca Evangelho do dia na API."""
    data_str = data_obj.strftime("%Y-%m-%d")
    try:
        resp = requests.get(API_LITURGIA + data_str, timeout=10)
        resp.raise_for_status()
        dados = resp.json()

        # A API devolve uma lista de leituras; vamos achar a que é Evangelho.
        leituras = dados.get("leituras", [])
        evangelho = None
        for l in leituras:
            tipo = l.get("tipo", "").lower()
            if "evangelho" in tipo:
                evangelho = l
                break

        if not evangelho:
            return None

        return {
            "referencia": evangelho.get("referencia", "").strip(),
            "titulo": evangelho.get("titulo", "").strip(),
            "texto": evangelho.get("texto", "").strip(),
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

    # Para não pesar nem copiar o texto inteiro, usamos só um trecho inicial.
    trecho_leitura = ev["texto"][:400] + "..." if len(ev["texto"]) > 400 else ev["texto"]

    partes = [
        {
            "nome": "HOOK + LEITURA + CTA",
            "titulo_3l": f"EVANGELHO\n{data_str}\n{referencia}",
            "texto": (
                "Hoje a Igreja nos propõe este Evangelho. "
                "Escute com atenção este trecho: "
                f"{trecho_leitura} "
                "Fica comigo até o final para rezarmos juntos."
            )
        },
        {
            "nome": "REFLEXÃO",
            "titulo_3l": f"REFLEXÃO\n{data_str}\n{referencia}",
            "texto": (
                "Este Evangelho nos lembra que Deus fala conosco na realidade concreta da nossa vida. "
                "Qual palavra ou frase mais chamou sua atenção hoje?"
            )
        },
        {
            "nome": "APLICAÇÃO",
            "titulo_3l": f"APLICAÇÃO\n{data_str}\n{referencia}",
            "texto": (
                "Escolha uma atitude prática para viver esta Palavra hoje: "
                "perdoar alguém, escutar com mais paciência, ou oferecer sua dificuldade a Deus."
            )
        },
        {
            "nome": "ORAÇÃO",
            "titulo_3l": f"ORAÇÃO\n{data_str}\n{referencia}",
            "texto": (
                "Senhor Jesus, obrigado por tua Palavra neste Evangelho. "
                "Que ela transforme meus pensamentos, minhas palavras e minhas atitudes hoje. Amém."
            )
        },
    ]

    return {
        "data": data_str,
        "tipo": tipo,
        "referencia": referencia,
        "titulo": titulo_liturgico,
        "texto_completo": ev["texto"],
        "partes": partes
    }
