import re
import json
from unidecode import unidecode
import html

# 1) Lê o XML inteiro como texto
with open('TP1\\GlossarioNeo\\Anexos\\neologismos_anexos.xml', encoding='utf8') as f:
    raw = f.read()

# 2) Filtra apenas o conteúdo das páginas 218 até 230
pages = re.findall(r'<page number="(\d+)".*?>(.*?)</page>', raw, re.DOTALL) #retorna tuplos (nr página, conteudo página)
filtered_pages = [content for num, content in pages if 218 <= int(num) <= 230] # agrupar o conteudo das diferentes páginas em uma lista, para retirar da forma de tuplos
filtered_raw = '\n'.join(filtered_pages) # agrupa os elementos da lista em apenas 1 elemento

# 3) Extrai o conteúdo que está entre os <text>...</text>
raw_lines = re.findall(r'<text[^>]*>(.*?)</text>', filtered_raw, re.DOTALL)
print(raw_lines)


# 4) Limpa tags, decodifica termos, limpa acentos e espaços
clean_lines = []
for frag in raw_lines:
    txt = re.sub(r'<[^>]+>', '', frag)      # remove tags <b>s e <i>s
    txt = html.unescape(txt)               # converte entidades como &#34; em "
    txt = unidecode(txt).strip()           # tira acentos e espaços
    if txt:
        clean_lines.append(txt)

print (clean_lines)

# 5) Parse da tabela
entries = []
i = 0
n = len(clean_lines)

# padrão para detectar o início de cada registro que é um número de 2 a 3 dígitos
row_re = re.compile(r'^\d{2,3}$')

# pula até o primeiro "01"
while i < n and not row_re.match(clean_lines[i].strip()):
    i += 1

while i < n:
    # 1) número da linha
    num = clean_lines[i].strip()
    if not row_re.match(num): #verifica se é um número, através do regex que se fez em cima
        break
    i += 1

    # 2) título: pode ocupar várias linhas até encontrar o próximo número (número da edição)
    title_parts = []
    while i < n and not re.match(r'^\d+$', clean_lines[i].strip()):
        title_parts.append(clean_lines[i].strip())
        i += 1
    title = ' '.join(title_parts)

    # 3) número da edição
    if i < n and re.match(r'^\d+$', clean_lines[i].strip()): #garante que é um número
        num_edic = clean_lines[i].strip()
        i += 1
    else:
        num_edic = ''

    # 4) mês da edição
    if i < n:
        mes_edic = clean_lines[i].strip()
    else:
        mes_edic = ''
    i += 1

    # 5) ano da edição
    if i < n:
        ano_edic = clean_lines[i].strip()
    else:
        ano_edic = ''
    i += 1

    entries.append({
        "Número": num,
        "Título do Artigo": title,
        "Número da Edição": num_edic,
        "Mês da Edição": mes_edic,
        "Ano da Edição": ano_edic
    })

# 6) Grava em JSON
with open('TP1\\GlossarioNeo\\Anexos\\anexos_pesquisa.json', 'w', encoding='utf8') as out:
    json.dump(entries, out, ensure_ascii=False, indent=2)

print(f"Processados {len(entries)} artigos e gerado 'anexos_pesquisa.json'.")