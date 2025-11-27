from datetime import date

def gerar_roteiro(data_obj: date, tipo: str = "Evangelho"):
    data_str = data_obj.strftime("%d/%m/%Y")

    referencia = "Mc 16, 15-20"
    titulo_liturgico = "Proclamação do Evangelho de Jesus Cristo segundo Marcos"

    partes = [
        {
            "nome": "HOOK + LEITURA + CTA",
            "titulo_3l": f"EVANGELHO\n{data_str}\n{referencia}",
            "texto": (
                "Hoje o Evangelho traz uma mensagem muito forte para a sua vida. "
                "Fica comigo até o final deste vídeo para rezarmos juntos."
            )
        },
        {
            "nome": "REFLEXÃO",
            "titulo_3l": f"REFLEXÃO\n{data_str}\n{referencia}",
            "texto": (
                "Este Evangelho nos lembra que cada um de nós é enviado por Deus ao mundo. "
                "Você não está onde está por acaso."
            )
        },
        {
            "nome": "APLICAÇÃO",
            "titulo_3l": f"APLICAÇÃO\n{data_str}\n{referencia}",
            "texto": (
                "Pensa em uma pessoa hoje para quem você pode levar uma palavra de esperança, "
                "uma mensagem, uma ligação ou um simples gesto de carinho."
            )
        },
        {
            "nome": "ORAÇÃO",
            "titulo_3l": f"ORAÇÃO\n{data_str}\n{referencia}",
            "texto": (
                "Senhor Jesus, obrigado por tua Palavra. "
                "Ajuda-me a ser sinal do teu amor onde eu estiver hoje. Amém."
            )
        },
    ]

    return {
        "data": data_str,
        "tipo": tipo,
        "referencia": referencia,
        "titulo": titulo_liturgico,
        "texto_completo": "",
        "partes": partes
    }
