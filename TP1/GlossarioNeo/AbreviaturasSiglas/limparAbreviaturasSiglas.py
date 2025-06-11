import re
import json

# Caminho para o arquivo XML
doc_text_path = "TP1\\GlossarioNeo\\AbreviaturasSiglas\\Neologismos.xml"

# Ler o arquivo XML
with open(doc_text_path, 'r', encoding="utf-8") as file:
    xml_data = file.read()

# 1. Extrair apenas o conteúdo da página 86
pagina_86_pattern = re.compile(
    r'<page number="86".*?>.*?</page>',
    re.DOTALL  # Permite que . corresponda a quebras de linha também, para consiguir capturar várias linhas de conteúdo entre <page> e </page>
)

pagina_86_match = pagina_86_pattern.search(xml_data)
if not pagina_86_match:
    print("Página 86 não encontrada no arquivo XML.")
    exit()

pagina_86 = pagina_86_match.group(0)

# 2. Extrair todas as tags <text> da página 86
text_tags_pattern = re.compile(
    r'<text top="(\d+)" left="(\d+)"[^>]*>(.*?)</text>',
    re.DOTALL
)

# 3. Processar as tags para encontrar abreviaturas e significados
abreviaturas = {}
current_top = None
abreviatura = None

for match in text_tags_pattern.finditer(pagina_86): #percorre todas as tags <text> da página 86
    top = match.group(1)
    left = match.group(2)
    content = re.sub(r'<[^>]+>', '', match.group(3)).strip()

    # Se estiver na coluna da esquerda (left="128" ou próximo)
    if left == "128" and content and not content.isspace():
        current_top = top
        abreviatura = content #sigla está em left == "128"
    # Se estiver na coluna da direita (left="234" ou próximo) e tivermos uma abreviatura no mesmo top
    elif (left == "181" or left == "234") and current_top == top and abreviatura: #top igual se está na mesma linha, pq a sigla e o significado tem o mesmo top, apenas left diferente
        if content and not content.isspace(): #se a sigla já estiver guardada, guarda o par no dicionario #not content.isspace() - verifica se nao esta vazio
            abreviaturas[abreviatura] = content
            abreviatura = None

# Ordenar as abreviaturas alfabeticamente
abreviaturas_ordenadas = dict(sorted(abreviaturas.items()))

# Guardar em ficheiro JSON
output_path = "TP1\GlossarioNeo\AbreviaturasSiglas\Abreviaturas_page86.json"
with open(output_path, 'w', encoding='utf-8') as json_file:
    json.dump(abreviaturas_ordenadas, json_file, indent=2, ensure_ascii=False)

print(f"Ficheiro JSON guardado em: {output_path}")
#print(f"Abreviaturas encontradas: {json.dumps(abreviaturas_ordenadas, indent=2, ensure_ascii=False)}")