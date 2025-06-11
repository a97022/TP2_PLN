
import re
import json

# Lê o conteúdo do XML
with open("TP1\\GlossarioNeo\\Equivalencias\\equivalencias_ing_pt.xml", "r", encoding="utf-8") as file:
    xml_content = file.read()

# Expressão regular para capturar todas as linhas de texto
text_regex = re.findall(r'<text top="\d+" left="(\d+)"[^>]*>(.*?)<\/text>', xml_content) #extrai posição horizontal (left) e conteudo textual <text></text>
print(f"text_regex:{text_regex}")

# Armazenar as linhas agrupadas por posição horizontal
eng_to_pt = {}  # Dicionário para armazenar pares inglês-português
current_english = "" # Linha atual em inglês
is_reading_portuguese = False # Flag para saber se estamos a ler o lado português
portuguese_lines = [] # Lista de linhas em português

for left, content in text_regex: #percorre cada linha capturada com a expressão regex anterior
    left = int(left)
    content = re.sub(r"<.*?>", "", content).strip()  # Remove tags HTML internas
    print(f"left: {left}, content: {content}")
    # Ignora linhas vazias ou linhas que são cabeçalhos/títulos
    if not content or content.upper() in ["INGLÊS", "PORTUGUÊS"] or "Equivalências" in content:
        continue

    if left == 128:
        # Verifica se a linha contém ambos os idiomas (com 2 ou + espaços consecutivos)
        if re.search(r"\s{2,}", content):
            parts = re.split(r"\s{2,}", content)
            if len(parts) >= 2:
                eng, pt = parts[0].strip(), parts[1].strip()
                eng_to_pt[eng] = pt
                current_english = ""
                portuguese_lines = []
                is_reading_portuguese = False
                continue  # já foi tratado, passa à próxima linha

        # Caso normal (só inglês)
        if current_english and portuguese_lines:
            eng_to_pt[current_english] = " ".join(portuguese_lines).strip()
        current_english = content
        portuguese_lines = []
        is_reading_portuguese = False

    elif left == 473: #traduções correspondentes em portugues
        portuguese_lines.append(content)
        is_reading_portuguese = True

    elif left > 473 and is_reading_portuguese:
        # Continuação da tradução em português
        portuguese_lines.append(content)

# No fim do loop, adiciona a última entrada válida pq já nao há mais entradas inglesas
if current_english and portuguese_lines:
    eng_to_pt[current_english] = " ".join(portuguese_lines).strip()

# Salva em JSON
with open("TP1\\GlossarioNeo\\Equivalencias\\ing_pt.json", "w", encoding="utf-8") as json_file:
    json.dump(eng_to_pt, json_file, ensure_ascii=False, indent=2)