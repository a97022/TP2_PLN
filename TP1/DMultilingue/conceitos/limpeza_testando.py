import re
import json

AREAS = [
    "Conceptes generals","Epidemiologia","Etiopatogènia",
    "Diagnòstic","Clínica","Prevenció","Tractament",
    "Principis actius","Entorn social"
]
AREA_RE = r'|'.join(a.upper() for a in AREAS)

import re

AREAS = [
    "Conceptes generals","Epidemiologia","Etiopatogènia",
    "Diagnòstic","Clínica","Prevenció","Tractament",
    "Principis actius","Entorn social"
]
AREA_RE = r'|'.join(a.upper() for a in AREAS)

def parse_concept(block):
    c = {
        "id": None,
        "denominacao_catala": None,
        "categoria_lexica": None,
        "sinonimos_complementares": [],
        "traducao": {},
        "cas": None,
        "area_tematica": None,
        "definicao": None,
        "nota": []
    }

    # 1) Denominação (bold em font=6)
    m_den = re.search(r'<text[^>]*font="6"[^>]*><b>([^<]+)</b>', block)
    if m_den:
        c["denominacao_catala"] = m_den.group(1).strip()

    # 2) Categoria gramatical (italic em font=7 junto ao bold)
    if m_den:
        pre, post = block[:m_den.start()], block[m_den.end():]
        m_cat = re.search(r'<text[^>]*font="7"[^>]*><i>\s*([^<]+)\s*</i>', pre[::-1])
        if m_cat:
            c["categoria_lexica"] = m_cat.group(1)[::-1].strip()
        else:
            m_cat = re.search(r'<text[^>]*font="7"[^>]*><i>\s*([^<]+)\s*</i>', post)
            if m_cat:
                c["categoria_lexica"] = m_cat.group(1).strip()

    # 3) Sinonimos complementares
    c["sinonimos_complementares"] = [
        s.strip() for s in re.findall(
            r'sin\. compl\.\s*</text>.*?<text[^>]*font="6"[^>]*><b>([^<]+)</b>',
            block, re.IGNORECASE|re.DOTALL)
    ]

    # 4) Traduções + categoria (aceita qualquer font para o termo, e captura a tag <i> seguinte)
    trad_re = re.compile(
        r'<text[^>]*font="7"[^>]*><i>\s*'
          r'(oc|eu|gl|es|en|fr|pt(?: \[PT\]|\s\[BR\])?|nl|ar)\s*'
        r'</i>\s*</text>\s*'
        r'<text[^>]*font="\d+"[^>]*>\s*([^<;]+?)\s*</text>\s*'
        r'(?:<text[^>]*font="7"[^>]*><i>\s*([^<]+?)\s*</i></text>)?',
        re.IGNORECASE|re.DOTALL
    )
    for code, term, cat in trad_re.findall(block):
        key = code.split()[0].lower()
        txt = term.strip()
        if cat:
            txt += " " + cat.strip()
        c["traducao"].setdefault(key, []).append(txt)

    # 5) CAS
    m_cas = re.search(
        r'<text[^>]*font="7"[^>]*><i>\s*CAS\s*</i>.*?'
        r'<text[^>]*font="1"[^>]*>\s*([^<]+?)\s*</text>',
        block, re.IGNORECASE|re.DOTALL
    )
    if m_cas:
        c["cas"] = m_cas.group(1).strip()

    # 6) Área temática + primeiro fragmento de definição
    defs = []
    m_area = re.search(
        rf'<text[^>]*font="1"[^>]*>\s*({AREA_RE})\.\s*(.*?)</text>',
        block, re.DOTALL
    )
    if m_area:
        c["area_tematica"] = m_area.group(1).capitalize()
        first_def = m_area.group(2).strip()
        if first_def:
            defs.append(first_def)
        start = m_area.end()
    elif m_cas:
        start = m_cas.end()
    else:
        start = m_den.end() if m_den else 0

    # 7) Resto da definição (font=1 até notes)
    m_note = re.search(r'<text[^>]*font="9"[^>]*>', block)
    end = m_note.start() if m_note else len(block)
    snippet = block[start:end]
    # texto em font=1, não iniciando com ponto-e-vírgula
    for d in re.findall(r'<text[^>]*font="1"[^>]*>\s*([^<;][^<]*)</text>', snippet):
        d = d.strip()
        if d:
            defs.append(d)
    if defs:
        c["definicao"] = " ".join(defs)

    # 8) Notas (font=9)
    c["nota"] = [n.strip() for n in
        re.findall(r'<text[^>]*font="9"[^>]*>\s*([^<]+?)</text>', block)]

    return c



# ————— texto completo e divisão em blocos —————
xml = open("TP1\DMultilingue\conceitos\limpeza_Conceitos_limpo.xml", encoding="utf-8").read()
# remove tudo antes do primeiro <text
xml = re.sub(r'(?s)^.*?(?=<text)', "", xml)

blocks = re.split(r'<text[^>]*>\s*(\d+)\s*</text>', xml)[1:]
# re.split devolve: [id1, bloco1, id2, bloco2, …]
conceitos = []
for i in range(0, len(blocks), 2):
    id_str, bloco = blocks[i], blocks[i+1]
    c = parse_concept(bloco)
    c["id"] = int(id_str)
    conceitos.append(c)

# grava o JSON
with open("TP1\DMultilingue\conceitos\limpeza_conceitos_testando.json", "w", encoding="utf-8") as f:
    json.dump(conceitos, f, ensure_ascii=False, indent=2)
