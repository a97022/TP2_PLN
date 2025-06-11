import re
import json

# Caminho para o arquivo XML
doc_text_path = "TP1\\GlossarioNeo\\AbreviaturasSiglas\\Neologismos.xml"

# Ler o arquivo XML
with open(doc_text_path, 'r', encoding="utf-8") as file:
    xml_data = file.read()

# 1. Extrair apenas o conteúdo da página 10 usando regex
pagina_10_pattern = re.compile(
    r'<page number="10".*?>.*?</page>',
    re.DOTALL  # Permite que . corresponda a quebras de linha também
)

pagina_10_match = pagina_10_pattern.search(xml_data)
if not pagina_10_match:
    print("Página 10 não encontrada no arquivo XML.")
    exit()

pagina_10 = pagina_10_match.group(0)

# 2. Extrair todas as tags <text> da página 10
text_tags_pattern = re.compile(
    r'<text[^>]*>(.*?)</text>',
    re.DOTALL
)

# 3. Padrão para identificar siglas e significados
sigla_pattern = re.compile(
    r'^([A-Z0-9&][A-Z0-9\s&\.]+[A-Z0-9]|et\s+al\.)\s*[–\-:]\s*(.+)$',
    re.IGNORECASE | re.UNICODE
)

abreviaturas = {}

for text_tag in text_tags_pattern.finditer(pagina_10):
    conteudo = text_tag.group(1).strip()

    # Remover tags HTML/bold se existirem
    conteudo_limpo = re.sub(r'<[^>]+>', '', conteudo).strip()

    # Verificar se é uma linha de sigla
    match = sigla_pattern.match(conteudo_limpo)
    if match:
        sigla = match.group(1).strip()
        significado = match.group(2).strip()
        abreviaturas[sigla] = significado

# Ordenar as siglas alfabeticamente
abreviaturas_ordenadas = dict(sorted(abreviaturas.items()))

# Guardar em ficheiro JSON
output_path = "TP1\GlossarioNeo\AbreviaturasSiglas\Abreviaturas_page10.json"
with open(output_path, 'w', encoding='utf-8') as json_file:
    json.dump(abreviaturas_ordenadas, json_file, indent=2, ensure_ascii=False)

print(f"Ficheiro JSON guardado em: {output_path}")
print(f"Abreviaturas encontradas: {abreviaturas_ordenadas}")