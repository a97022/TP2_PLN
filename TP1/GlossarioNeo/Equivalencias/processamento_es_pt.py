import re
import json

# Lê o conteúdo do XML
with open("TP1\\GlossarioNeo\\Equivalencias\\equivalencias_es_pt.xml", "r", encoding="utf-8") as file:
    xml_content = file.read()

# Expressão regular: extrai (top, left, content)
text_blocks = re.findall(r'<text top="(\d+)" left="(\d+)"[^>]*>(.*?)<\/text>', xml_content)

es_to_pt = {}
current_spanish_parts = []
current_portuguese_parts = []
collecting_portuguese = False

for top, left, content in text_blocks:
    top = int(top)
    left = int(left)
    content = re.sub(r"<.*?>", "", content).strip()

    # Ignora títulos e vazios
    if not content or content in ["ESPANHOL", "PORTUGUÊS", "3.4. Equivalências espanhol – português"]:
        continue

    if left < 431:
        if collecting_portuguese and current_spanish_parts and current_portuguese_parts:
            # Salva par anterior
            full_spanish = " ".join(current_spanish_parts).strip()
            full_portuguese = " ".join(current_portuguese_parts).strip()
            es_to_pt[full_spanish] = full_portuguese

            # Reset
            current_spanish_parts = []
            current_portuguese_parts = []
            collecting_portuguese = False

        current_spanish_parts.append(content)

    elif left >= 431:
        current_portuguese_parts.append(content)
        collecting_portuguese = True

# Último par
if current_spanish_parts and current_portuguese_parts:
    full_spanish = " ".join(current_spanish_parts).strip()
    full_portuguese = " ".join(current_portuguese_parts).strip()
    es_to_pt[full_spanish] = full_portuguese

# Salva JSON
with open("TP1\\GlossarioNeo\\Equivalencias\\es_pt.json", "w", encoding="utf-8") as json_file:
    json.dump(es_to_pt, json_file, ensure_ascii=False, indent=2)

print(f"{len(es_to_pt)} pares extraídos com sucesso.")


