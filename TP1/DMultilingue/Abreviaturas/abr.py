import re
import json


doc_text_path = "TP1\DMultilingue\Abreviaturas\Abreviaturas.txt"

with open(doc_text_path, 'r', encoding='utf-8') as f:
    doc = f.read()

# Remover linha com números e linha com "Abreviacions"
doc = re.sub(r'^.*\d+.*\n?', '', doc, flags=re.MULTILINE)
linhas = [linha.strip() for linha in doc.splitlines() if linha.strip() and "Abreviacions" not in linha]

# Secções (esperadas e em ordem de entrada)
secao1 = "Categories lèxiques"
secao2 = "Indicadors de llengua"
secao3 = "Altres codis"
secao4 = "Remissions"

# Obter só as linhas que não são títulos de secções
linhas_sem_seccoes = [linha for linha in linhas if linha not in {secao1, secao2, secao3, secao4}]

# pares (abreviação, descrição)
pares = [(linhas_sem_seccoes[i], linhas_sem_seccoes[i + 1]) for i in range(0, len(linhas_sem_seccoes), 2)]

resultado = {
    secao1: {},
    secao2: {},
    secao3: {},
    secao4: {}
}

# Distribuir os primeiros 21 pares (12+9) de forma intercalada
for i in range(22):
    abrev, desc = pares[i]
    if i % 2 == 0:
        destino = secao1
    else:
        destino = secao2

    if abrev == "pt":
        if "pt" not in resultado[secao2]:
            resultado[secao2]["pt"] = []
        resultado[secao2]["pt"].append(desc)
    else:
        resultado[destino][abrev] = desc

# A partir do par 21, alternar entre Altres codis e Remissions
for j, (abrev, desc) in enumerate(pares[22:]):
    destino = secao3 if j % 2 == 0 else secao4
    resultado[destino][abrev] = desc

with open("TP1\DMultilingue\Abreviaturas\Abreviacoes.json", "w", encoding="utf-8") as f_out:
    json.dump(resultado, f_out, ensure_ascii=False, indent=4)
