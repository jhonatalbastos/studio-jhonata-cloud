import requests
from datetime import date

API_LITURGIA = "https://api-liturgia-diaria.vercel.app/?date="  # API pública [web:39]

def buscar_evangelho(data_obj: date):
    data_str = data_obj.strftime("%Y-%m-%d")
    try:
        resp = requests.get(API_LITURGIA + data_str, timeout=10)
        resp.raise_for_status()
        dados = resp.json()

        evangelho = next(
            (l for l in dados.get("leituras", []) if "Evangelho" in l.get("tipo","")),
            None
        )
        if not evangelho:
            return None

        return {
            "referencia": evangelho.get("referencia", "").strip(),
            "titulo": evangelho.get("titulo", "").strip(),
            "texto": evangelho.get("texto", "").strip()
        }
    except Exception:
        return None

def gerar_roteiro(data_obj: date, tipo: str = "Evangelho"):
    ev = buscar_evangelho(data_obj)
    if not ev:
        return {
            "data": data_obj.strftime("%d/%m/%Y"),
            "tipo": tipo,
            "referencia": "",
            "partes": []
        }

    data_str = data_obj.strftime("%d/%m/%Y")

    partes = [
        {
            "nome": "HOOK + LEITURA + CTA",
            "titulo_3l": f"EVANGELHO\n{data_str}\n{ev['referencia']}",
            "texto": (
                "Você sabia que a Palavra de hoje fala diretamente com você? "
                f"Escute este trecho: {ev['texto'][:300]}... "
                "Fique comigo até o final para uma oração especial."
            )
        },
        {
            "nome": "REFLEXÃO",
            "titulo_3l": f"REFLEXÃO\n{data_str}\n{ev['referencia']}",
            "texto": (
                "Neste Evangelho, Jesus nos convida a rever nossas atitudes à luz do amor de Deus. "
                "Que parte desta Palavra mais te toca hoje?"
            )
        },
        {
            "nome": "APLICAÇÃO",
            "titulo_3l": f"APLICAÇÃO\n{data_str}\n{ev['referencia']}",
            "texto": (
                "Pense em uma situação concreta do seu dia de hoje em que você pode viver esta Palavra. "
                "Talvez seja numa conversa, numa decisão difícil ou num gesto de perdão."
            )
        },
        {
            "nome": "ORAÇÃO",
            "titulo_3l": f"ORAÇÃO\n{data_str}\n{ev['referencia']}",
            "texto": (
                "Senhor Jesus, obrigado por tua Palavra. "
                "Ajuda-me a colocá-la em prática hoje. Amém."
            )
        },
    ]

    return {
        "data": data_str,
        "tipo": tipo,
        "referencia": ev["referencia"],
        "titulo": ev["titulo"],
        "texto_completo": ev["texto"],
        "partes": partes
    }
