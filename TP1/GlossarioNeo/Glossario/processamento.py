import re
import json
from unidecode import unidecode
import html

# 1) Ler o XML como texto
with open('TP1\\GlossarioNeo\\Glossario\\neologismos_glossario.xml', encoding='utf8') as f:
    raw = f.read()

# 2) Extrai o conteúdo que está entre os <text>...</text>
raw_lines = re.findall(r'<text[^>]*>(.*?)</text>', raw, re.DOTALL)

# 3) Limpa tags, decodifica termos, limpa acentos e espaços
clean_lines = []
for frag in raw_lines:
    txt = re.sub(r'<[^>]+>', '', frag)      # remove tags <b>s e <i>s
    txt = html.unescape(txt)                # converte &#34; em ' " '
    txt = unidecode(txt).strip()            # tira os acentos e os espaços
    if txt:
        clean_lines.append(txt)

# Corrige etiquetas [esp] incompletas ou mal formadas
clean_lines = [re.sub(r'\[esp?\.?\]?', '[esp]', line, flags=re.IGNORECASE) for line in clean_lines]

# 4) Junta o termo + substantivo (ex: 'abeta' + 's.f.') na mesma linha
#isto facilita a identificação do início de um novo conceito, graças ao substantivo ter sempre o mesmo formato s.[mf].
merged = []
i = 0
while i < len(clean_lines):
    if i + 1 < len(clean_lines) and re.match(r'^(s\.[mf]\.)$', clean_lines[i+1], re.IGNORECASE):
        merged.append(f"{clean_lines[i]} {clean_lines[i+1]}")
        i += 2
    else:
        merged.append(clean_lines[i])
        i += 1
lines = merged



# 5) Junta traduções inglês + marcador + espanhol em apenas 1 linha.
# Tive de fazer isto por causa do sydenham que apresentava as traduções ao longo de 3 linhas diferentes
entry_start_re = re.compile(r'^(.+?)\s+(s\.[mf]\.)$', re.IGNORECASE)
normalized = []
j = 0

while j < len(lines):
    if entry_start_re.match(lines[j]) and j + 1 < len(lines):
        normalized.append(lines[j])  # mantém termo + s.f./s.m.

        # verificamos se as próximas linhas têm traduções separadas
        buffer = [lines[j + 1]]
        k = j + 2
        # junta até 3 linhas seguintes, para tentar apanhar [ing] + [esp] separados
        while k < len(lines) and len(buffer) < 3:
            buffer.append(lines[k])
            combined = ' '.join(buffer)
            if '[ing]' in combined.lower() and '[esp]' in combined.lower():
                normalized.append(combined)
                j = k + 1
                break
            k += 1
        else:
            # se não encontrou [ing] e [esp], adiciona a linha normal e avança só 1
            normalized.append(lines[j + 1])
            j += 2
    else:
        normalized.append(lines[j])
        j += 1


lines = normalized



# Regex para identificar início de um conceito: termo + subtantivo
entry_start = re.compile(r'^(.+?)\s+(s\.[mf]\.)$', re.IGNORECASE)
entries = []
i = 0
n = len(lines)
#print(lines)


while i < n:
    # Encontra início de um conceito
    m = entry_start.match(lines[i])
    if not m:
        i += 1
        continue
    termo = m.group(1).strip()
    genero = m.group(2).lower().strip()
    i += 1

    # 5) Extrai a tradução inglesa e espanhola, mesmo que venham separadas em várias linhas
    full_trans = ''  # vai guardar as traduções
    max_lookahead = 3  # quantas linhas à frente vamos tentar “colar” até encontrar “[ing]”
    found = False  # flag para indicar se já encontramos o bloco de tradução

    for offset in range(max_lookahead):
        # evita ultrapassar o final da lista
        if i + offset >= n:
            break

        # constrói um “fragmento” que junta a linha atual até a linha i+offset
        fragment = ' '.join(lines[i:i + offset + 1])

        # procura o marcador [ing] (de forma case‑insensitive)
        if '[ing]' in fragment.lower():
            full_trans = fragment.strip()  # guarda o texto completo até aqui
            i += offset + 1  # avança o cursor para logo depois do bloco encontrado
            found = True  # sinaliza que encontramos o fragmento
            break  # sai do for

    # se não achou nenhum “[ing]” dentro de até max_lookahead linhas, dá erro
    if not found:
        raise ValueError(
            f"Esperado linha com tradução contendo [ing] para termo '{termo}', "
            f"mas obtido: '{lines[i] if i < n else 'FIM DO ARQUIVO'}'"
        )


    # 1) Extrai sigla inline de full_trans, se houver
    sigla_inline = ''
    sigla_match = re.search(r'\bSigla\s*:\s*(\w+)', full_trans, re.IGNORECASE)
    if sigla_match:
        sigla_inline = sigla_match.group(1).strip()
        # remove “Sigla: XXX” de full_trans para não poluir a descrição
        full_trans = re.sub(r'\bSigla\s*:\s*\w+', '', full_trans, flags=re.IGNORECASE).strip()

    # 2) Extrai sigla em linha separada, se vier numa linha própria
    sigla_next = ''
    if i < n and re.match(r'^\s*Sigla\s*:\s*', lines[i], re.IGNORECASE):
        parts = lines[i].split(':', 1)
        candidate = parts[1].strip()
        if candidate:
            # Sigla veio na mesma linha: "Sigla: ABC"
            sigla_next = candidate
            i += 1
        elif i + 1 < n:
            # Sigla veio na linha seguinte:
            # linha atual = "Sigla:", próxima = "AVCI"
            sigla_next = lines[i + 1].strip()
            i += 2
        else:
            # só tinha "Sigla:" no fim do arquivo…
            i += 1

    # 3) Escolhe a sigla que existir (prioridade para inline)
    sigla = sigla_inline or sigla_next


    # DExtrai tradução inglês + espanhol do texto restante já sem aSigla
    m2 = re.match(
        r'^(.+?)\s*\[ing\];?\s*(.+?)\s*\[esp\]\s*(.*)$',
        full_trans,
        re.IGNORECASE
    )
    if m2:
        termo_ing = m2.group(1).strip()
        termo_esp = m2.group(2).strip()
        # tudo após [esp] vira início da descrição
        desc_parts = [m2.group(3).strip()] if m2.group(3).strip() else []
    else:
        # fallback: não havia [esp], tudo depois de [ing] é termo_esp
        m2 = re.match(r'^(.+?)\s*\[ing\];?\s*(.+)$', full_trans, re.IGNORECASE)
        if not m2:
            raise ValueError(f"Formato inesperado para traduções: '{full_trans}'")
        termo_ing = m2.group(1).strip()
        termo_esp = m2.group(2).strip()
        desc_parts = []

    # continua o loop de descrição a partir de desc_parts inicial
    while i < n and not lines[i].lower().startswith('inf. encicl') \
            and not lines[i].startswith(('“', '"')) \
            and not entry_start.match(lines[i]):
        desc_parts.append(lines[i])
        i += 1
    descricao = ' '.join(desc_parts).strip()

    # Informação enciclopédia
    info_enc = ''
    if i < n and lines[i].lower().startswith('inf. encicl'):
        info_enc = re.sub(r'(?i)^inf\. encicl\.:?\s*', '', lines[i]); i += 1
        while i < n and not lines[i].startswith(('“','"')) and not entry_start.match(lines[i]):
            info_enc += ' ' + lines[i]; i += 1
        info_enc = info_enc.strip()

    # --- Alteração: captura citação apenas até '(' indicando número ---
    citacao = ''
    nr_artigos = []
    if i < n and lines[i].startswith(('“','"')):
        citacao = lines[i]; i += 1
        # agrupa até ver linha começando por '('
        while i < n and not lines[i].startswith('(') and not entry_start.match(lines[i]):
            citacao += ' ' + lines[i]; i += 1
        if i < n and lines[i].startswith('('):
            nums = re.findall(r'\d+', lines[i]); nr_artigos = [int(x) for x in nums]; i += 1

    entries.append({
        "Termo": termo,
        "Substantivo": genero,
        "Termo ing": termo_ing,
        "Termo esp": termo_esp,
        "Sigla": sigla,
        "Descricao": descricao,
        "Informacao Enciclopedia": info_enc,
        "citacao": citacao,
        "nr_artigos": nr_artigos
    })

# Grava em JSON
with open('TP1\\GlossarioNeo\\Glossario\\glossario.json', 'w', encoding='utf8') as out:
    json.dump(entries, out, ensure_ascii=False, indent=2)

print(f"Processados {len(entries)} termos e gerado 'glossario.json'.")

