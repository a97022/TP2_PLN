import re
from unidecode import unidecode
import json

f = open("TP1\GlossarioMini\glossario_ministerio_saude.xml", "r", encoding="utf-8")
texto = f.read()


# ---------------- EXTRAÇAO DOS CONCEITOS E SIGLAS ------------------------

texto = re.sub(r"<image.+-11_1.+>", r"<b></b>", texto) # marcação fim das siglas
texto = re.sub(r"<image.+-107_1.+>", r"@-", texto)  # marcaçao do fim dos conceitos

texto = re.sub(r"<.+?>Categoria<.+\n<.+>([^:\n]+)<.+?>", r"\n@CAT\1\n", texto)    # casos em que categoria não tem dois pontos
texto = re.sub(r"<.+?>Categoria:.+\n<.+?>(.+)<.+", r"\n@CAT\1\n", texto)          # correção do caso "notificação de doenças" que tem a categoria a bold
texto = re.sub(r".+21\"><b>(.+)\n<.+21\"?><b>(.+)<.+", r"@-\1\2", texto)          # marcaçao termos que ocupam duas linhas
texto = re.sub(r".+13\"><b>(.+)\n<.+13\"?><b>(.+)<.+", r"@-\1\2", texto)          # Casos especifico do termo sisvan que está escrito com letra menor
texto = re.sub(r"<.+>[0-9]{1,3}<.+>", r"\n", texto)                               # eliminaçao das paginas
texto = re.sub(r"<[/]?i>", r"", texto)                                            # remover italicos para nao interferir na sinalizaçao de termos (equivalencia in vitro)
texto = re.sub(r"(.+)top=\"(233|240|250|247|246|238|257)\"(.+)", r"", texto)      # remove cabeçalhos das páginas com termos/conceitos (ex: ADJ Adjuvante farmacêutico Aids pediátrica)
texto = re.sub(r"(.+)font=\"21\"><b>(.+)</b>(.+)", r"\n@-\2\n", texto)            # sinaliza termos
texto = re.sub(r"<.+?>Categoria:.+\n<.+?>(.+)<.+", r"\n@CAT\1\n", texto)          # marca categorias, importante para distinguir das areas tematicas
texto = re.sub(r"<.+?>Categoria.+\n<.+?>:(.+)<.+", r"\n@CAT\1\n", texto)          # casos em que os dois pontos estão separados da palavra "Categoria" (ver termo CNS)

texto = re.sub(r"<.+?>(.+)-<.+\n", r"\1", texto)                                  # tratamento de palavras com hifens   
texto = re.sub(r"<.+?>(.+)<.+\n", r"\1\n", texto)                                 # tirar elementos html

texto = re.sub(r"[^A-Za-z]?\n+<.+font=\"24\"></text>\n*[^A-Za-z]?(.+)", r"\n@CAT\1\n", texto)  # termos com duas categorias, com símbolo estranho 
texto = re.sub(r"\n[A-Z]\n", r"\n", texto)                                        # cabeçalho

texto = re.sub(r"@CAT(.+)-\n+([^\s\n@<]+)\n", r"@CAT\1\2\n", texto)               # Correção da categoria Recuros Humanos em Saúde Pú-blica
texto = re.sub(r"@CAT(.+)\n+([^\s\n@<]+)\n", r"@CAT\1\2\n", texto)                # apanha e corrige outras categorias que nao cabem numa só linha
texto = re.sub(r"@CAT(.+)\n+@CAT\s+\n([^\n@<]+)\n", r"@CAT\1\n@CAT\2\n", texto) 
texto = re.sub(r"@CAT\s\n+<b>in vitro</b>", r"", texto)                           # remoçao do termo in vitro do cabeçalho da pag 83
texto = re.sub(r"\n+(<.+>)?\n+<b>(in vi.+)</b>", r"\2", texto)                    # correção dos restantes termos que usam "in vitro ou in vivo"
texto = re.sub(r"@CAT([^\n]+)([\n]?)\n([^A-ZÉÓÍ@\n<])", r"@CAT\1\3", texto)       # correção de categorias como atençao a saude
texto = re.sub(r"@CAT\s(.+)", r"@CAT\1", texto)                                   # remoção de espaços entre marca e categoria
texto = re.sub(r"Promoção\s*e\s*[\n]*Ed(.+)", r"Promoção e Ed\1", texto)
texto = re.sub(r"@CAT(.+),\s*\n(.+)", r"@CAT\1, \2", texto)                       # medicamentos, vacinas e insumos
texto = re.sub(r"@CAT(.+)\s?\n+Saúde\s?\n", r"@CAT\1Saúde\n", texto)              # Atencao a saude
texto = re.sub(r"<[^b].+[^b]>", r"", texto)                                       # eliminar todos elementos  HTML menos os bold
texto = re.sub(r"\n<b>(.+)</b>\n+@CAT", r"\n@-\1\n@CAT", texto)                   # correçao de termos com elementos a bold
texto = re.sub(r"@-(.+)[\n]*@-(.+)", r"@-\1\2", texto)                            # correção do termo Profae
texto = re.sub(r"@CAT \n+(.+)", r"@CAT\1\n", texto)                               # correcao de vigilancia em saude
texto = re.sub(r"@CAT(.+)Atenção\sà\sSaúde", r"@CAT\1\n@CATAtenção à Saúde\n", texto)



file_out = open("TP1\GlossarioMini\glossario_ministerio_saude_out.xml", "w", encoding="utf-8")
file_out.write(texto)
file_out.close()

# -------------------- CONCEITOS ----------------------

conceitos1 = re.findall(r'@-([^@]+)@CAT(.+)[\n]*([^@]+)', texto)   # apanha termos com 1 categoria
conceitos2 = re.findall(r'@-([^@]+)@CAT([^@]+)@CAT(.+)[\n]*([^@]+)', texto)   # apanha termos com 2 categorias
conceitos3 = re.findall(r'@-([^@]+)@CAT([^@]+)@CAT([^@]+)@CAT(.+)[\n]*([^@]+)', texto)   # apanha termos com 3 categorias
conceitos4 = re.findall(r'@-(.+)[\n]+Ver([^@]+)', texto)


conceitos_dict = {conceitos1[i][0].replace("\n", ""): {"Categoria": [conceitos1[i][j].replace("\n", "") for j in range(1, len(conceitos1[i])-1)], 
                                     "Descrição": conceitos1[i][len(conceitos1[i])-1].replace("\n", "")} 
                  for i in range(0, len(conceitos1))}


for i in range(0, len(conceitos2)):
    conceitos_dict[conceitos2[i][0].replace("\n", "")] = {"Categoria": [conceitos2[i][j].strip().replace("\n", "") for j in range(1, len(conceitos2[i])-1)], 
                                                        "Descrição": conceitos2[i][len(conceitos2[i])-1].strip().replace("\n", "")} 


for i in range(0, len(conceitos3)):
    conceitos_dict[conceitos3[i][0].replace("\n", "")] = {"Categoria": [conceitos3[i][j].strip().replace("\n", "") for j in range(1, len(conceitos3[i])-1)], 
                                        "Descrição": conceitos3[i][len(conceitos3[i])-1].strip().replace("\n", "")} 


for i in range(0, len(conceitos4)):
    conceitos_dict[conceitos4[i][0].replace("\n", "")] = {"Descrição": "Ver " + conceitos4[i][1].strip().replace("\n", "")} 


conceitos_dict = dict(sorted(conceitos_dict.items(), key=lambda item: unidecode(item[0].lower())))

print("conceitos: " + str(len(conceitos_dict)))

file_out = open("TP1\GlossarioMini\conceitos.json", "w", encoding="UTF-8")
json.dump(conceitos_dict, file_out, indent=4, ensure_ascii=False)
file_out.close()


# ------------------ SIGLAS ----------------------

siglas = re.findall(r"<b>(.+)\s–\s?</b>\n([^<]*)", texto)
siglas2 = re.findall(r"<b>(.+)</b>\n[\s]?–([^<]*)", texto)

siglas_dict = {siglas[i][0].replace("\n", "") : siglas[i][1].replace("\n", "") for i in range(0, len(siglas))}

for i in range(0, len(siglas2)):
    siglas_dict[siglas2[i][0].replace("\n", "")] = siglas2[i][1].replace("\n", "")

siglas_dict = dict(sorted(siglas_dict.items(), key=lambda item: unidecode(item[0].lower())))

print("siglas: " + str(len(siglas_dict)))

file_out = open("TP1\GlossarioMini\siglas.json", "w", encoding="UTF-8")
json.dump(siglas_dict, file_out, indent=4, ensure_ascii=False)
file_out.close()




# NOTA foi colocado um @ após o termo (e respetiva definição de zalcitabina)
#print(conceitos)



letras = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'X', 'Z', 'W']
print("CONCEITOS")
for letra in letras:
    i = 0
    for conceito in conceitos_dict:
        if unidecode(conceito.lower()).startswith(letra.lower()):
            i += 1
    print(letra + str(i))

print("SIGLAS")
for letra in letras:
    i = 0
    for sigla in siglas_dict:
        if unidecode(sigla.lower()).startswith(letra.lower()):
            i += 1
    print(letra + str(i))


