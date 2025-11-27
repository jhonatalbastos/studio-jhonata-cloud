def gerar_roteiro(data, tipo):
    return {
        "data": data.strftime("%d/%m/%Y"),
        "tipo": tipo,
        "cenas": ["Leitura", "Reflexão", "Aplicação", "Oração"]
    }
