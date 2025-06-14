import xml.etree.ElementTree as ET
import json
import re
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def processar_conceitos():
    try:
        # Verificar se o arquivo existe
        xml_path = 'conceitos.xml'
        if not os.path.exists(xml_path):
            logger.error(f"Arquivo {xml_path} não encontrado!")
            return
        
        logger.info(f"Lendo arquivo {xml_path}...")
        # Ler o arquivo XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        logger.info("Processando conceitos...")
        conceitos = []
        id_atual = 1
        
        # Processar cada conceito
        for conceito in root.findall('.//conceito'):
            try:
                novo_conceito = {
                    "id": id_atual,
                    "denominacao_catala": conceito.find('denominacao_catala').text if conceito.find('denominacao_catala') is not None else "",
                    "categoria_lexica": conceito.find('categoria_lexica').text if conceito.find('categoria_lexica') is not None else "",
                    "sinonimos_complementares": [],
                    "traducao": {},
                    "cas": None,
                    "area_tematica": None,
                    "definicao": "",
                    "nota": []
                }
                
                # Processar sinônimos
                sinonimos = conceito.find('sinonimos_complementares')
                if sinonimos is not None:
                    for sinonimo in sinonimos.findall('sinonimo'):
                        if sinonimo.text:
                            novo_conceito["sinonimos_complementares"].append(sinonimo.text)
                
                # Processar traduções
                traducoes = conceito.find('traducoes')
                if traducoes is not None:
                    for traducao in traducoes.findall('traducao'):
                        idioma = traducao.get('idioma')
                        if idioma and traducao.text:
                            if idioma not in novo_conceito["traducao"]:
                                novo_conceito["traducao"][idioma] = []
                            novo_conceito["traducao"][idioma].append(traducao.text)
                
                # Processar CAS
                cas = conceito.find('cas')
                if cas is not None and cas.text:
                    novo_conceito["cas"] = cas.text
                
                # Processar área temática
                area = conceito.find('area_tematica')
                if area is not None and area.text:
                    novo_conceito["area_tematica"] = area.text
                
                # Processar definição
                definicao = conceito.find('definicao')
                if definicao is not None and definicao.text:
                    novo_conceito["definicao"] = definicao.text
                
                # Processar notas
                notas = conceito.find('notas')
                if notas is not None:
                    for nota in notas.findall('nota'):
                        if nota.text:
                            novo_conceito["nota"].append(nota.text)
                
                conceitos.append(novo_conceito)
                id_atual += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar conceito {id_atual}: {str(e)}")
                continue
        
        logger.info(f"Total de conceitos processados: {len(conceitos)}")
        
        # Salvar o resultado em um arquivo JSON
        output_file = 'conceitos_processados.json'
        logger.info(f"Salvando resultado em {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conceitos, f, ensure_ascii=False, indent=2)
        
        logger.info("Processamento concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o processamento: {str(e)}")

if __name__ == "__main__":
    processar_conceitos() 