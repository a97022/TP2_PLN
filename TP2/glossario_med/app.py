from flask import Flask, render_template, json, request, redirect, url_for
from markupsafe import Markup
import re
import urllib.parse

app = Flask(__name__)

# Carregar dados do JSON
with open('dados.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)


# Processar links nos textos
def processar_links(texto, origem=None):
    if not texto:
        return ""

    # Siglas (ex: FAPESP)
    for sigla, significado in dados['SIGLAS'].items():
        if origem:
            origem_url = urllib.parse.quote(origem) #para garantir que o nome do conceito (caso tenha espaços, acentos ou caracteres especiais) não cause problemas na URL
            link = f'<a href="/sigla/{sigla}?origem={origem_url}" class="tooltip" title="{significado}">{sigla}</a>'
        else:
            link = f'<a href="/sigla/{sigla}" class="tooltip" title="{significado}">{sigla}</a>'
        texto = re.sub(rf'\b{re.escape(sigla)}\b', link, texto)

    # Abreviaturas (ex: et al.)
    for abrev, significados in dados['ABREVS'].items():
        significado = ', '.join(significados)
        if origem:
            origem_url = urllib.parse.quote(origem)
            link = f'<a href="/abreviatura/{abrev}?origem={origem_url}" class="tooltip" title="{significado}">{abrev}</a>'
        else:
            link = f'<a href="/abreviatura/{abrev}" class="tooltip" title="{significado}">{abrev}</a>'
        texto = re.sub(rf'\b{re.escape(abrev)}\b', link, texto)

    return Markup(texto)


@app.route('/')
def index():
    # Calcular estatísticas para a página inicial
    stats = {
        'conceitos': len(dados['CONCEITOS']),
        'siglas': len(dados['SIGLAS']),
        'abreviaturas': len(dados['ABREVS']),
        'categorias': len(dados['CATEGORIAS']),
        'anexos': len(dados['ANEXOS'])
    }
    return render_template('index.html', stats=stats)


@app.route('/conceitos')
def listar_conceitos():
    q = request.args.get('q', '').strip()
    exata = request.args.get('exata') == 'true'
    conceitos = dados['CONCEITOS']
    if q:
        q_lower = q.lower()
        if exata:
            conceitos = {termo: info for termo, info in dados['CONCEITOS'].items() if termo.lower() == q_lower}
        else:
            conceitos = {termo: info for termo, info in dados['CONCEITOS'].items() if q_lower in termo.lower()}
    return render_template('conceitos.html', conceitos=conceitos, q=q, exata=exata)


@app.route('/conceito/<nome>')
def detalhe_conceito(nome):
    conceito = dados['CONCEITOS'].get(nome)
    if not conceito:
        return "Conceito não encontrado", 404

    # Processar definições (lidando com listas vazias)
    definicoes_processadas = []
    for definicao, fonte in conceito.get('definicoes', []):
        definicoes_processadas.append([processar_links(definicao, origem=nome), fonte])

    # Processar informações enciclopédicas
    info_enc = conceito.get('info_enc', '')
    info_enc_processada = processar_links(info_enc, origem=nome) if info_enc else ""

    return render_template('conceito.html',
                           nome=nome,
                           conceito=conceito,
                           definicoes_processadas=definicoes_processadas,
                           info_enc_processada=info_enc_processada,
                           categorias=dados['CATEGORIAS'],
                           dados=dados)


@app.route('/siglas')
def listar_siglas():
    q = request.args.get('q', '').strip()
    exata = request.args.get('exata') == 'true'
    if q:
        siglas_result = pesquisar_siglas(q, exata)
        siglas = {sigla: significado for sigla, significado, _ in siglas_result}
    else:
        siglas = dados['SIGLAS']
    return render_template('siglas.html', siglas=siglas, q=q, exata=exata)


# Rota para detalhe de sigla
@app.route('/sigla/<sigla>')
def detalhe_sigla(sigla):
    significado = dados['SIGLAS'].get(sigla)
    if not significado:
        return "Sigla não encontrada", 404
    return render_template('sigla.html', sigla=sigla, significado=significado)


@app.route('/abreviaturas')
def listar_abreviaturas():
    q = request.args.get('q', '').strip()
    exata = request.args.get('exata') == 'true'
    if q:
        q_lower = q.lower()
        if exata:
            abreviaturas = {abrev: significados for abrev, significados in dados['ABREVS'].items() if abrev.lower() == q_lower}
        else:
            abreviaturas = {abrev: significados for abrev, significados in dados['ABREVS'].items() if q_lower in abrev.lower()}
    else:
        abreviaturas = dados['ABREVS']
    return render_template('abreviaturas.html', abreviaturas=abreviaturas, q=q, exata=exata)


# Rota para detalhe de abreviatura
@app.route('/abreviatura/<abrev>')
def detalhe_abreviatura(abrev):
    significados = dados['ABREVS'].get(abrev)
    if not significados:
        return "Abreviatura não encontrada", 404
    return render_template('abreviatura.html', abrev=abrev, significados=significados)


# Rota para listar categorias
@app.route('/categorias')
def listar_categorias():
    q = request.args.get('q', '').strip()
    exata = request.args.get('exata') == 'true'
    campo = request.args.get('campo', 'categoria')
    if q:
        q_lower = q.lower()
        if campo == 'subcategoria':
            if exata:
                categorias = {nome: info for nome, info in dados['CATEGORIAS'].items() if any(sub.lower() == q_lower for sub in info.get('subcategorias', []))}
            else:
                categorias = {nome: info for nome, info in dados['CATEGORIAS'].items() if any(q_lower in sub.lower() for sub in info.get('subcategorias', []))}
        else:
            if exata:
                categorias = {nome: info for nome, info in dados['CATEGORIAS'].items() if nome.lower() == q_lower}
            else:
                categorias = {nome: info for nome, info in dados['CATEGORIAS'].items() if q_lower in nome.lower()}
    else:
        categorias = dados['CATEGORIAS']
    return render_template('categorias.html', categorias=categorias, q=q, exata=exata, campo=campo, dados=dados)


# Rota para detalhe de uma categoria
@app.route('/categoria/<path:nome>')
def detalhe_categoria(nome):
    # Decodificar o nome da categoria
    nome_decodificado = nome.strip('"')
    categoria = dados['CATEGORIAS'].get(nome_decodificado)

    if not categoria:
        return "Categoria não encontrada", 404

    # Construir lista de conceitos relacionados
    conceitos_relacionados = []
    for termo, info in dados['CONCEITOS'].items():
        if 'categoria_area' in info and nome_decodificado in info['categoria_area']:
            conceitos_relacionados.append(termo)

    return render_template('categoria.html',
                           nome=nome_decodificado,
                           categoria=categoria,
                           conceitos_relacionados=conceitos_relacionados)


@app.route('/anexos')
def listar_anexos():
    q = request.args.get('q', '').strip()
    exata = request.args.get('exata') == 'true'
    if q:
        q_lower = q.lower()
        if exata:
            anexos = [anexo for anexo in dados['ANEXOS'] if anexo['Título do Artigo'].lower() == q_lower]
        else:
            anexos = [anexo for anexo in dados['ANEXOS'] if q_lower in anexo['Título do Artigo'].lower()]
    else:
        anexos = dados['ANEXOS']
    return render_template('anexos.html', anexos=anexos, q=q, exata=exata)


# Funções auxiliares de pesquisa
def pesquisar_conceitos(query, exata=False):
    resultados = {}
    query_lower = query.lower()

    for termo, info in dados['CONCEITOS'].items():
        contextos = []
        termo_lower = termo.lower()

        # Pesquisa no próprio termo
        if exata:
            if query_lower == termo_lower:
                contextos.append("Termo exato")
            # Verifica se o termo contém a query como palavra completa
            elif query_lower in termo_lower.split():
                contextos.append("Termo contém palavra")
        else:
            if query_lower in termo_lower:
                contextos.append("Termo contém")

        # Pesquisa nas definições
        for definicao, fonte in info.get('definicoes', []):
            definicao_lower = definicao.lower()
            if exata:
                palavras = definicao_lower.split()
                if query_lower in palavras:
                    contextos.append(f"Definição: {definicao[:50]}...")
            else:
                if query_lower in definicao_lower:
                    contextos.append(f"Definição: {definicao[:50]}...")

        # Pesquisa nas traduções
        for lang, traducoes in info.get('traducoes', {}).items():
            for trad in traducoes:
                trad_lower = trad.lower()
                if exata:
                    if query_lower == trad_lower:
                        contextos.append(f"Tradução ({lang}) exata: {trad}")
                    elif query_lower in trad_lower.split():
                        contextos.append(f"Tradução ({lang}) contém palavra: {trad}")
                else:
                    if query_lower in trad_lower:
                        contextos.append(f"Tradução ({lang}): {trad}")

        # Se encontrou correspondências, adiciona ao resultado
        if contextos:
            resultados[termo] = {
                'info': info,
                'contextos': contextos
            }

    return resultados

def pesquisar_siglas(query, exata=False):
    resultados = []
    query_lower = query.lower()

    for sigla, significado in dados['SIGLAS'].items():
        sigla_lower = sigla.lower()
        significado_lower = significado.lower()

        if exata:
            # Verifica se a query é exatamente igual à sigla (case-insensitive)
            if query_lower == sigla_lower:
                resultados.append((sigla, significado, "Sigla exata"))
            # Verifica se a query é uma palavra completa no significado
            elif query_lower in significado_lower.split():
                resultados.append((sigla, significado, "Significado exato"))
        else:
            # Verifica se a query está contida na sigla
            if query_lower in sigla_lower:
                resultados.append((sigla, significado, "Sigla contém"))
            # Verifica se a query está contida no significado
            elif query_lower in significado_lower:
                resultados.append((sigla, significado, "Significado contém"))

    return resultados

def pesquisar_abreviaturas(query, exata=False):
    resultados = []
    for abrev, significados in dados['ABREVS'].items():
        if exata:
            if query == abrev:
                resultados.append((abrev, significados, "Abreviatura exata"))
        else:
            if query in abrev:
                resultados.append((abrev, significados, "Abreviatura contém"))
            else:
                for significado in significados:
                    if query in significado:
                        resultados.append((abrev, significados, f"Significado: {significado}"))
    return resultados


def pesquisar_categorias(query, exata=False):
    resultados = []
    for nome, info in dados['CATEGORIAS'].items():
        if exata:
            if query.lower() == nome.lower():
                resultados.append((nome, info, "Categoria exata"))
            else:
                for sub in info.get('subcategorias', []):
                    if query.lower() == sub.lower():
                        resultados.append((nome, info, f"Subcategoria: {sub}"))
        else:
            if query.lower() in nome.lower():
                resultados.append((nome, info, "Categoria contém"))
            elif query.lower() in info['definicao'].lower():
                resultados.append((nome, info, "Definição contém"))
            else:
                for sub in info.get('subcategorias', []):
                    if query.lower() in sub.lower():
                        resultados.append((nome, info, f"Subcategoria: {sub}"))
    return resultados


def pesquisar_anexos(query, exata=False):
    resultados = []
    for anexo in dados['ANEXOS']:
        titulo = anexo['Título do Artigo']
        if exata:
            if query.lower() == titulo.lower():
                resultados.append(anexo)
        else:
            if query.lower() in titulo.lower():
                resultados.append(anexo)
    return resultados


# Rota de pesquisa
@app.route('/pesquisar')
def pesquisar():
    query = request.args.get('q', '').strip().lower()
    tipo = request.args.get('tipo', 'tudo')
    exata = request.args.get('exata') == 'true'

    if not query:
        return redirect(url_for('index'))

    resultados = {
        'conceitos': {},
        'siglas': [],
        'abreviaturas': [],
        'categorias': [],
        'anexos': []
    }

    if tipo in ['tudo', 'conceitos']:
        resultados['conceitos'] = pesquisar_conceitos(query, exata)

    if tipo in ['tudo', 'siglas']:
        resultados['siglas'] = pesquisar_siglas(query, exata)

    if tipo in ['tudo', 'abreviaturas']:
        resultados['abreviaturas'] = pesquisar_abreviaturas(query, exata)

    if tipo in ['tudo', 'categorias']:
        resultados['categorias'] = pesquisar_categorias(query, exata)

    if tipo in ['tudo', 'anexos']:
        resultados['anexos'] = pesquisar_anexos(query, exata)

    return render_template('resultados_pesquisa.html',
                           query=query,
                           resultados=resultados,
                           tipo=tipo,
                           exata=exata)


if __name__ == '__main__':
    app.run(debug=True)