import json
import requests
from bs4 import BeautifulSoup

# Carregar JSON existente
with open('../../DMultilingue/glossario_final_completo.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Acessar a página
url = "https://hgis.org.br/abreviacoes-e-siglas-padronizadas-para-registros-do-prontuario/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Encontrar todos os grupos (accordions)
accordion_items = soup.select('.elementor-accordion-item')

for item in accordion_items:
    # Verificar se é o grupo de símbolos
    title = item.select_one('.elementor-accordion-title')
    if title and "Símbolos" in title.get_text(strip=True):
        print("Saltar grupo de símbolos")
        continue

    # Encontrar a tabela dentro do item
    table = item.select_one('table')
    if not table:
        continue

    # Processar cada linha da tabela (ignorando cabeçalhos)
    rows = table.select('tr:not(.FundoTabelaAzul)')
    for row in rows:
        cells = row.select('td')
        if len(cells) < 2:
            continue

        abbr = cells[0].get_text(strip=True)
        meaning = cells[1].get_text(strip=True)

        # Pular entradas vazias ou sem significado
        if not abbr or not meaning:
            continue

        # Remover asteriscos e espaços extras
        abbr = abbr.replace('*', '').strip()

        # Processar múltiplas siglas (ex: "ADA ou AEA")
        for single_abbr in [a.strip() for a in abbr.split(' ou ') if a.strip()]:
            # Classificar como SIGLA (todas maiúsculas) ou ABREV
            if single_abbr.isupper() or not any(c.islower() for c in single_abbr):
                target_dict = data["SIGLAS"]
                new_value = meaning
            else:
                target_dict = data["ABREVS"]
                new_value = [meaning]

            # Adicionar se não existir
            if single_abbr not in target_dict:
                target_dict[single_abbr] = new_value
                #print(f"adicionei {single_abbr} a {meaning}")

# Salvar JSON atualizado
with open('glossario_siglas_abrevs.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)