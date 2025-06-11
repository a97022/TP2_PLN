import re
from unidecode import unidecode
import json

f = open("TP1\GlossarioMini\glossario_ministerio_saude cut.xml", "r", encoding="utf-8")
texto = f.read()

# ------------------ EXTRAÇAO DAS DEFINIÇOES DAS AREAS TEMATICAS ------------------------

texto = re.sub(r".+21\"><b>(.+)\n<.+21\"?><b>(.+)<.+", r"\n@-\1\2", texto)          # marcaçao termos que ocupam duas linhas
texto = re.sub(r"<.+>[0-9]{1,3}<.+>", r"\n", texto)                               # eliminaçao das paginas
texto = re.sub(r"<[/]?i>", r"", texto)                                            # remover italicos para nao interferir na sinalizaçao de termos (equivalencia in vitro)
texto = re.sub(r"(.+)font=\"21\"><b>(.+)</b>(.+)", r"\n@-\2\n", texto)            # sinaliza termos

texto = re.sub(r"<.+?>(.+)-<.+\n", r"\1", texto)                                  # tratamento de palavras com hifens   
texto = re.sub(r"<.+?>(.+)<.+\n", r"\1\n", texto)                                 # tirar elementos html
texto = re.sub(r"\n[A-Z]\n", r"\n", texto)                                        # cabeçalho
texto = re.sub(r"<.+>", r"", texto)  
texto = re.sub(r"[\n]{3,}[^@]", r"", texto)  
texto = re.sub(r"@-", r"\n@-", texto)  

file_out = open("TP1\GlossarioMini\glossario_ministerio_saude_outcut.xml", "w", encoding="utf-8")
file_out.write(texto)
file_out.close()


# -------------------- AREAS TEMATICAS ----------------------

areas = re.findall(r'@-(.+)\n([^@]+)\n?', texto)   # apanha termos com 1 categoria


areas_dict = {elem[0].replace("\n", ""): elem[1].replace("\n", "") for elem in areas}


areas_dict = dict(sorted(areas_dict.items(), key=lambda item: unidecode(item[0].lower())))

print("areas: " + str(len(areas_dict)))

file_out = open("TP1\GlossarioMini\Areas.json", "w", encoding="UTF-8")
json.dump(areas_dict, file_out, indent=4, ensure_ascii=False)
file_out.close()
