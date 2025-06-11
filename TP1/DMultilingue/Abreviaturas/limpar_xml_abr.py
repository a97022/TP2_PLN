import re
from unidecode import unidecode
import json

#pdftohtml -f 29 -l 29 -xml multi_covid.pdf abreviaturas.xml 

doc_text_path ="DMultilingue\DM_abreviaturas.xml" 
doc_t = open(doc_text_path,'r', encoding="utf-8")

doc = doc_t.read()

doc = re.sub(r"<text\stop.*?>",r"<text>",doc) # limpar dados
doc = re.sub(r'.+page.+\n?',"",doc)
doc = re.sub(r'<\?xml.*?\?>\s*<!DOCTYPE pdf2xml[^>]*>\s*', '', doc, flags=re.DOTALL) # Remover cabeçalho XML e DTD
doc = re.sub(r'<fontspec[^>]*/>', '', doc) # Remover todas as tags <fontspec ... />
doc = re.sub(r'</?pdf2xml[^>]*>', '', doc) # Remover todas as tags <pdf2xml ... />
doc = re.sub(r'\n\s*\n', '\n', doc) # Limpar espaços em branco extra
doc = re.sub(r'<text[^>]*>.*\d+.*</text>\n?', '', doc) #remover todas as linhas que contenham numeros (numero da pagina, titulo do dicionario e quarter 50)

# Guardar num novo ficheiro
with open("DMultilingue\Abreviaturas_limpo.xml", "w", encoding="utf-8") as f_out:
    f_out.write(doc)

