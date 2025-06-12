import json
import re
import requests
from bs4 import BeautifulSoup

# Carregar o JSON existente
with open('../Siglas_Abreviacoes/glossario_siglas_abrevs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# URLs para cada grupo de letras
urls = [
    "https://www.health.harvard.edu/a-through-c",
    "https://www.health.harvard.edu/d-through-i",
    "https://www.health.harvard.edu/j-through-p",
    "https://www.health.harvard.edu/q-through-z"]

for url in urls:
    print(f"A processsar: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        container = soup.select_one('div.content-repository-content')

        if not container:
            print("Container principal não encontrado")
            continue

        # Encontrar todos os elementos de parágrafo que contêm termos
        for p in container.find_all('p'):
            # Verificar se o parágrafo contém um termo em negrito
            if p.strong:
                term_text = p.strong.get_text(strip=True)

                # Extrair o termo (remover os dois pontos finais)
                term = term_text.rstrip(':').strip()
                normalized_term = term.lower()

                # Extrair definição (texto após o termo)
                definition = p.get_text().replace(term_text, '', 1).strip()

                if not definition:
                    continue

                #print(f"  → Termo encontrado: {term}")

                # Procurar termo nas traduções do JSON
                for concept, details in data["CONCEITOS"].items():
                    en_translations = details["traducoes"].get("en", [])
                    #print(f"en_translations:{en_translations}")

                    # Transformar a lista de traduções em texto JSON simulado
                    translations_text = json.dumps(en_translations, indent=2)
                    #print(f"translations_text:{translations_text}")

                    # Aplicar a regex no texto
                    matches = re.findall(r'((?:(?:\w{2,}-?(?:\'\w*)?|\d-?(?:\'\w*)?)\s?)+)', translations_text)
                    #print(f"matches:{matches}")

                    # Extrair os termos encontrados pela regex
                    normalized_translations = [m.strip().lower() for m in matches]
                    #print(f"normalized_translations:{normalized_translations}")

                    for termo in normalized_translations:
                        #if normalized_term == "arrhythmia":
                            #print(f"normalized_term: {normalized_term}")
                            #print(f"termo: {termo}")
                        if termo == normalized_term:
                            #print(f"normalized_term: {normalized_term}")
                            #print(f"A adicionar definição para: {concept}")
                            details["definicoes"].append([definition, "Harvard"])


    except Exception as e:
        print(f"Erro ao processar {url}: {str(e)}")

# Salvar o JSON atualizado
with open('glossario_final.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Processo concluído! Glossário atualizado.")