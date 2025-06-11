import re
from unidecode import unidecode

doc_text_path = "TP1\DMultilingue\conceitos\conceitos.xml"
doc_t = open(doc_text_path, 'r', encoding="utf-8")
doc = doc_t.read()

# Limpeza geral de cabeçalhos, marcas e estrutura
doc = re.sub(r'.+page.+\n?', "", doc)
doc = re.sub(r'<\?xml.*?\?>\s*<!DOCTYPE pdf2xml[^>]*>\s*', '', doc, flags=re.DOTALL)
doc = re.sub(r'<fontspec[^>]*/>', '', doc)
doc = re.sub(r'</?pdf2xml[^>]*>', '', doc)
doc = re.sub(r'\n\s*\n', '\n', doc)
doc = re.sub(r'<page number[\w\W]+?<text>\d+</text>\n', "", doc)
doc = re.sub(r"</page>\n", "", doc)

# Simplificar tag <text> para manter só a fonte
doc = re.sub(r'<text[^>]*?font="([^"]+)"[^>]*?>(.*?)</text>', r'<text font="\1">\2</text>', doc)

# Remover tags <text> com conteúdo vazio ou espaços
doc = re.sub(r'<text font="\d+">[\s\u00A0]*</text>\n?', '', doc)

# Remover <text> com apenas pontuação (ex: ; , . … ! ? etc.)
doc = re.sub(r'<text font="\d+">[;.,…!?]+\s*</text>\n?', '', doc)

# Remover <text><b> </b></text> e <text><i> </i></text> (tags bold/italic vazias)
doc = re.sub(r'<text font="\d+"><[bi]>\s*</[bi]></text>\n?', '', doc)

# Remover textos com números de página (em font 0 ou outras variantes)
doc = re.sub(r'<text font="0">.*?\d+.*?</text>\n?', '', doc)

# Remover a letra indicadora do dicionário, como <text font="15">A</text>
doc = re.sub(r'<text font="15">[A-ZÀ-ÿ]</text>\n?', '', doc)

# Remover o cabeçalho com "QUADERNS 50"
doc = re.sub(r'<text font="3"><b>QUADERNS 50\s*</b></text>\n?', '', doc)

# Remover o subtítulo "DICCIONARI MULTILINGÜE DE LA COVID-19"
doc = re.sub(r'<text font="4">\s*DICCIONARI MULTILINGÜE DE LA COVID-19\s*</text>\n?', '', doc)


# Guardar ficheiro limpo
with open("TP1\DMultilingue\conceitos\limpeza_Conceitos_limpo.xml", "w", encoding="utf-8") as f_out:
    f_out.write(doc)
