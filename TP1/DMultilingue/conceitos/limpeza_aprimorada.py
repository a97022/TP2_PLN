import re
import json
import logging
import sys
import os
from typing import List, Dict, Any

AREAS = [
    "Conceptes generals","Epidemiologia","Etiopatogènia",
    "Diagnòstic","Clínica","Prevenció","Tractament",
    "Principis actius","Entorn social"
]
AREA_RE = r'|'.join(a.upper() for a in AREAS)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extrair_nota_completa(bloco: str) -> List[str]:
    """
    Extrai todas as notas de um bloco de texto.
    Uma nota começa com 'Nota:' e termina no próximo conceito ou no fim do bloco.
    """
    notas = []
    
    # Procura pelo início da nota
    inicio_nota = re.search(r'<text[^>]*font="9"[^>]*>Nota:', bloco)
    if not inicio_nota:
        return notas
    
    # Procura pelo próximo conceito ou fim do bloco
    proximo_conceito = re.search(r'<text font="1">\d+</text><text font="6"><b>', bloco[inicio_nota.end():])
    fim_nota = inicio_nota.end() + (proximo_conceito.start() if proximo_conceito else len(bloco[inicio_nota.end():]))
    
    # Extrai o texto da nota
    texto_nota = bloco[inicio_nota.end():fim_nota]
    
    # Remove tags HTML e espaços extras
    texto_nota = re.sub(r'<[^>]+>', ' ', texto_nota)
    texto_nota = re.sub(r'\s+', ' ', texto_nota).strip()
    
    # Remove o prefixo "Nota:" se existir
    texto_nota = re.sub(r'^Nota:\s*', '', texto_nota)
    
    # Encontra as posições das notas numeradas
    # Procura por números seguidos de ponto e espaço, mas não quando fazem parte de outras palavras
    posicoes = []
    for match in re.finditer(r'(?<!\w)(\d+)\.\s', texto_nota):
        # Verifica se o número não faz parte de uma palavra (como COVID-19)
        if not re.search(r'\w-\d+', texto_nota[max(0, match.start()-10):match.end()]):
            # Verifica se não é parte de uma definição ou outro texto
            if not re.search(r'que es troba|que constitueix|que s\'uneix', texto_nota[max(0, match.start()-50):match.end()]):
                posicoes.append(match.start())
    
    # Se não houver notas numeradas, retorna o texto completo como uma única nota
    if not posicoes:
        if texto_nota:
            # Remove qualquer texto que pareça ser de outro conceito
            texto_nota = re.sub(r'que es troba.*$', '', texto_nota)
            texto_nota = re.sub(r'que constitueix.*$', '', texto_nota)
            texto_nota = re.sub(r'que s\'uneix.*$', '', texto_nota)
            notas.append(texto_nota.strip())
        return notas
    
    # Adiciona o início do texto como primeira posição
    posicoes.insert(0, 0)
    
    # Adiciona o fim do texto como última posição
    posicoes.append(len(texto_nota))
    
    # Separa as notas
    for i in range(len(posicoes) - 1):
        nota = texto_nota[posicoes[i]:posicoes[i+1]].strip()
        if nota:
            # Remove qualquer texto que pareça ser de outro conceito
            nota = re.sub(r'que es troba.*$', '', nota)
            nota = re.sub(r'que constitueix.*$', '', nota)
            nota = re.sub(r'que s\'uneix.*$', '', nota)
            notas.append(nota.strip())
    
    return notas

def parse_concept(block: str, id_str: str, problemas: List[Dict[str, Any]]) -> Dict[str, Any]:
    c = {
        "id": int(id_str),
        "denominacao_catala": None,
        "categoria_lexica": None,
        "sinonimos_complementares": [],
        "traducao": {},
        "cas": None,
        "area_tematica": None,
        "definicao": None,
        "nota": []
    }
    problemas_c = []

    # 1) Denominação (bold em font=6)
    m_den = re.search(r'<text[^>]*font="6"[^>]*><b>([^<]+)</b>', block)
    if m_den:
        c["denominacao_catala"] = m_den.group(1).strip()
    else:
        problemas_c.append("denominacao_catala")

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
    if not c["categoria_lexica"]:
        problemas_c.append("categoria_lexica")

    # 3) Sinonimos complementares
    c["sinonimos_complementares"] = [
        s.strip() for s in re.findall(
            r'sin\. compl\.\s*</text>.*?<text[^>]*font="6"[^>]*><b>([^<]+)</b>',
            block, re.IGNORECASE|re.DOTALL)
    ]

    # 4) Traduções + categoria
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
    
    # Procura por definições que começam com "veg." e capturam o termo de referência
    veg_def = re.search(r'<text[^>]*font="1"[^>]*>\s*veg\.\s*</text>\s*<text[^>]*font="6"[^>]*><b>([^<]+)</b></text>', snippet)
    if veg_def:
        defs.append(f"veg. {veg_def.group(1)}")
    else:
        # Se não encontrar "veg.", procura por outras definições normalmente
        for d in re.findall(r'<text[^>]*font="1"[^>]*>\s*([^<;][^<]*)</text>', snippet):
            d = d.strip()
            if d:
                defs.append(d)
    
    if defs:
        c["definicao"] = " ".join(defs)
    else:
        problemas_c.append("definicao")

    # 8) Nota completa
    c["nota"] = extrair_nota_completa(block)

    # Reportar problemas deste conceito
    if problemas_c:
        problemas.append({"id": c["id"], "campos_faltando": problemas_c})

    return c


def main(xml_path=None, json_path=None, relatorio_path=None):
    if not xml_path:
        xml_path = "limpeza_Conceitos_limpo.xml"
    if not json_path:
        json_path = "limpeza_conceitos_aprimorado.json"
    if not relatorio_path:
        relatorio_path = "relatorio_problemas.json"

    if not os.path.exists(xml_path):
        logging.error(f"Arquivo XML não encontrado: {xml_path}")
        sys.exit(1)

    logging.info(f"Lendo arquivo: {xml_path}")
    xml = open(xml_path, encoding="utf-8").read()
    xml = re.sub(r'(?s)^.*?(?=<text)', "", xml)
    blocks = re.split(r'<text[^>]*>\s*(\d+)\s*</text>', xml)[1:]
    conceitos = []
    problemas = []
    for i in range(0, len(blocks), 2):
        id_str, bloco = blocks[i], blocks[i+1]
        c = parse_concept(bloco, id_str, problemas)
        conceitos.append(c)

    logging.info(f"Total de conceitos extraídos: {len(conceitos)}")
    logging.info(f"Total de conceitos com problemas: {len(problemas)}")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(conceitos, f, ensure_ascii=False, indent=2)
    logging.info(f"JSON salvo em: {json_path}")

    with open(relatorio_path, "w", encoding="utf-8") as f:
        json.dump(problemas, f, ensure_ascii=False, indent=2)
    logging.info(f"Relatório de problemas salvo em: {relatorio_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Limpeza e extração aprimorada de conceitos do dicionário.")
    parser.add_argument('--xml', help='Caminho do XML de entrada')
    parser.add_argument('--json', help='Caminho do JSON de saída')
    parser.add_argument('--relatorio', help='Caminho do relatório de problemas')
    args = parser.parse_args()
    main(args.xml, args.json, args.relatorio) 