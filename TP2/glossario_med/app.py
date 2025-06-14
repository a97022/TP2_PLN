from flask import Flask, render_template, json, request, redirect, url_for
from markupsafe import Markup
import re
import urllib.parse
import os

app = Flask(__name__)

# Carregar dados do JSON
def carregar_dados():
    #with open('TP2_PLN/TP2/glossario_med/dados.json', 'r', encoding='utf-8') as f:
    with open('dados.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_dados(dados):
    #with open('TP2_PLN/TP2/glossario_med/dados.json', 'w', encoding='utf-8') as f:
    with open('dados.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Carregar dados iniciais
dados = carregar_dados()

# Processar links nos textos
def processar_links(texto, origem=None):
    if not texto:
        return ""

    # Conceitos
    for termo, info in dados['CONCEITOS'].items():
        if origem and termo != origem:  # Não criar link para o próprio termo
            origem_url = urllib.parse.quote(origem)
            link = f'<a href="/conceito/{termo}?origem={origem_url}">{termo}</a>'
        else:
            link = f'<a href="/conceito/{termo}">{termo}</a>'
        texto = re.sub(rf'\b{re.escape(termo)}\b(?=\s|$)', link, texto, flags=re.IGNORECASE)

    # Siglas (ex: FAPESP)
    for sigla, significado in dados['SIGLAS'].items():
        if origem:
            origem_url = urllib.parse.quote(origem) #para garantir que o nome do conceito (caso tenha espaços, acentos ou caracteres especiais) não cause problemas na URL
            link = f'<a href="/sigla/{sigla}?origem={origem_url}" class="tooltip" title="{significado}">{sigla}</a>'
        else:
            link = f'<a href="/sigla/{sigla}" class="tooltip" title="{significado}">{sigla}</a>'
        texto = re.sub(rf'\b{re.escape(sigla)}\b(?=\s|$)', link, texto, flags=re.IGNORECASE) #Assegura que a sigla seja seguida por espaço ou fim de linha, para evitar capturas parciais.

    # Abreviaturas (ex: et al.)
    for abrev, significados in dados['ABREVS'].items():
        significado = ', '.join(significados)
        if origem:
            origem_url = urllib.parse.quote(origem)
            link = f'<a href="/abreviatura/{abrev}?origem={origem_url}" class="tooltip" title="{significado}">{abrev}</a>'
        else:
            link = f'<a href="/abreviatura/{abrev}" class="tooltip" title="{significado}">{abrev}</a>'
        texto = re.sub(rf'\b{re.escape(abrev)}\b(?=\s|$)', link, texto, flags=re.IGNORECASE)

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
        q_lower = q.lower()
        if exata:
            siglas = {sigla: significado for sigla, significado in dados['SIGLAS'].items() if sigla.lower() == q_lower}
        else:
            siglas = {sigla: significado for sigla, significado in dados['SIGLAS'].items() if q_lower in sigla.lower()}
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
@app.route('/abreviatura/<path:abrev>')
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


@app.route('/siglas/adicionar', methods=['GET', 'POST'])
def adicionar_sigla():
    if request.method == 'POST':
        sigla = request.form['sigla'].strip().upper()
        significado = request.form['significado'].strip()
        
        if not sigla or not significado:
            return redirect(url_for('adicionar_sigla', erro='Todos os campos são obrigatórios.'))
        
        if sigla in dados['SIGLAS']:
            return redirect(url_for('adicionar_sigla', erro='Esta sigla já existe.'))
        
        dados['SIGLAS'][sigla] = significado
        salvar_dados(dados)
        return redirect(url_for('listar_siglas', sucesso='Sigla adicionada com sucesso!'))
    
    erro = request.args.get('erro')
    return render_template('editar_sigla.html', erro=erro)

@app.route('/siglas/editar/<sigla>', methods=['GET', 'POST'])
def editar_sigla(sigla):
    if sigla not in dados['SIGLAS']:
        return redirect(url_for('listar_siglas', erro='Sigla não encontrada.'))
    
    if request.method == 'POST':
        significado = request.form['significado'].strip()
        
        if not significado:
            return redirect(url_for('editar_sigla', sigla=sigla, erro='O significado é obrigatório.'))
        
        dados['SIGLAS'][sigla] = significado
        salvar_dados(dados)
        return redirect(url_for('listar_siglas', sucesso='Sigla atualizada com sucesso!'))
    
    erro = request.args.get('erro')
    return render_template('editar_sigla.html', sigla=sigla, significado=dados['SIGLAS'][sigla], erro=erro)

@app.route('/siglas/eliminar/<sigla>', methods=['POST'])
def eliminar_sigla(sigla):
    if sigla in dados['SIGLAS']:
        del dados['SIGLAS'][sigla]
        salvar_dados(dados)
        return redirect(url_for('listar_siglas', sucesso='Sigla eliminada com sucesso!'))
    return redirect(url_for('listar_siglas', erro='Sigla não encontrada.'))

@app.route('/abreviaturas/adicionar', methods=['GET', 'POST'])
def adicionar_abreviatura():
    if request.method == 'POST':
        abrev = request.form['abrev'].strip()
        significados = [s.strip() for s in request.form['significados'].split('\n') if s.strip()]
        if not abrev or not significados:
            return redirect(url_for('adicionar_abreviatura', erro='Todos os campos são obrigatórios.'))
        if abrev in dados['ABREVS']:
            return redirect(url_for('adicionar_abreviatura', erro='Esta abreviatura já existe.'))
        dados['ABREVS'][abrev] = significados
        salvar_dados(dados)
        return redirect(url_for('listar_abreviaturas', sucesso='Abreviatura adicionada com sucesso!'))
    erro = request.args.get('erro')
    return render_template('editar_abreviatura.html', erro=erro)

@app.route('/abreviaturas/editar/<abrev>', methods=['GET', 'POST'])
def editar_abreviatura(abrev):
    if abrev not in dados['ABREVS']:
        return redirect(url_for('listar_abreviaturas', erro='Abreviatura não encontrada.'))
    if request.method == 'POST':
        significados = [s.strip() for s in request.form['significados'].split('\n') if s.strip()]
        if not significados:
            return redirect(url_for('editar_abreviatura', abrev=abrev, erro='O significado é obrigatório.'))
        dados['ABREVS'][abrev] = significados
        salvar_dados(dados)
        return redirect(url_for('listar_abreviaturas', sucesso='Abreviatura atualizada com sucesso!'))
    erro = request.args.get('erro')
    return render_template('editar_abreviatura.html', abrev=abrev, significados=dados['ABREVS'][abrev], erro=erro)

@app.route('/abreviaturas/eliminar/<abrev>', methods=['POST'])
def eliminar_abreviatura(abrev):
    if abrev in dados['ABREVS']:
        del dados['ABREVS'][abrev]
        salvar_dados(dados)
        return redirect(url_for('listar_abreviaturas', sucesso='Abreviatura eliminada com sucesso!'))
    return redirect(url_for('listar_abreviaturas', erro='Abreviatura não encontrada.'))

@app.route('/conceitos/adicionar', methods=['GET', 'POST'])
def adicionar_conceito():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        definicao = request.form['definicao'].strip()
        info_enc = request.form.get('info_enc', '').strip()
        categoria_lexica = request.form.get('categoria_lexica', '').strip()
        sigla = request.form.get('sigla', '').strip()
        cas = request.form.get('cas', '').strip()
        sinonimos_pt = [s.strip() for s in request.form.get('sinonimos_pt', '').split(',') if s.strip()]
        sinonimos_en = [s.strip() for s in request.form.get('sinonimos_en', '').split(',') if s.strip()]
        sinonimos_es = [s.strip() for s in request.form.get('sinonimos_es', '').split(',') if s.strip()]
        traducoes_ar = [t.strip() for t in request.form.get('traducoes_ar', '').split(',') if t.strip()]
        traducoes_ca = [t.strip() for t in request.form.get('traducoes_ca', '').split(',') if t.strip()]
        traducoes_en = [t.strip() for t in request.form.get('traducoes_en', '').split(',') if t.strip()]
        traducoes_es = [t.strip() for t in request.form.get('traducoes_es', '').split(',') if t.strip()]
        traducoes_eu = [t.strip() for t in request.form.get('traducoes_eu', '').split(',') if t.strip()]
        traducoes_fr = [t.strip() for t in request.form.get('traducoes_fr', '').split(',') if t.strip()]
        traducoes_gl = [t.strip() for t in request.form.get('traducoes_gl', '').split(',') if t.strip()]
        traducoes_nl = [t.strip() for t in request.form.get('traducoes_nl', '').split(',') if t.strip()]
        traducoes_oc = [t.strip() for t in request.form.get('traducoes_oc', '').split(',') if t.strip()]
        categoria_area = [c.strip() for c in request.form.get('categoria_area', '').split(',') if c.strip()]
        artigos_input = [a.strip() for a in request.form.get('artigos', '').split(',') if a.strip()]

        # Validar artigos relacionados
        anexos_validos = {anexo['Número'] for anexo in dados['ANEXOS']}
        artigos_validos = [artigo for artigo in artigos_input if artigo in anexos_validos]
        
        if not definicao:
            return redirect(url_for('adicionar_conceito', erro='A definição é obrigatória.'))
        if not nome:
            return redirect(url_for('adicionar_conceito', erro='O nome do conceito é obrigatório.'))
        if nome in dados['CONCEITOS']:
            return redirect(url_for('adicionar_conceito', erro='Este conceito já existe.'))

        # Construir o conceito na ordem desejada
        novo_conceito = {
            'CAS': cas,
            'artigos': artigos_validos,
            'categoria_area': categoria_area,
            'categoria_lexica': [c.strip() for c in categoria_lexica.split(',') if c.strip()] if categoria_lexica else [],
            'definicoes': [[definicao, 'Utilizador']],
            'info_enc': info_enc,
            'sigla': sigla,
            'sinonimos': {
                'pt': sinonimos_pt,
                'en': sinonimos_en,
                'es': sinonimos_es
            },
            'traducoes': {
                'ar': traducoes_ar,
                'ca': traducoes_ca,
                'en': traducoes_en,
                'es': traducoes_es,
                'eu': traducoes_eu,
                'fr': traducoes_fr,
                'gl': traducoes_gl,
                'nl': traducoes_nl,
                'oc': traducoes_oc
            },
        }

        dados['CONCEITOS'][nome] = novo_conceito
        salvar_dados(dados)
        return redirect(url_for('listar_conceitos', sucesso='Conceito adicionado com sucesso!'))
    erro = request.args.get('erro')
    return render_template('editar_conceito.html', erro=erro)

@app.route('/conceitos/editar/<nome>', methods=['GET', 'POST'])
def editar_conceito(nome):
    conceito = dados['CONCEITOS'].get(nome)
    if not conceito:
        return redirect(url_for('listar_conceitos', erro='Conceito não encontrado.'))
    if request.method == 'POST':
        definicao = request.form['definicao'].strip()
        info_enc = request.form.get('info_enc', '').strip()
        categoria_lexica_input = request.form.get('categoria_lexica', '').strip()
        sigla = request.form.get('sigla', '').strip()
        cas = request.form.get('cas', '').strip()
        sinonimos_pt_input = [s.strip() for s in request.form.get('sinonimos_pt', '').split(',') if s.strip()]
        sinonimos_en_input = [s.strip() for s in request.form.get('sinonimos_en', '').split(',') if s.strip()]
        sinonimos_es_input = [s.strip() for s in request.form.get('sinonimos_es', '').split(',') if s.strip()]
        traducoes_ar = [t.strip() for t in request.form.get('traducoes_ar', '').split(',') if t.strip()]
        traducoes_ca = [t.strip() for t in request.form.get('traducoes_ca', '').split(',') if t.strip()]
        traducoes_en = [t.strip() for t in request.form.get('traducoes_en', '').split(',') if t.strip()]
        traducoes_es = [t.strip() for t in request.form.get('traducoes_es', '').split(',') if t.strip()]
        traducoes_eu = [t.strip() for t in request.form.get('traducoes_eu', '').split(',') if t.strip()]
        traducoes_fr = [t.strip() for t in request.form.get('traducoes_fr', '').split(',') if t.strip()]
        traducoes_gl = [t.strip() for t in request.form.get('traducoes_gl', '').split(',') if t.strip()]
        traducoes_nl = [t.strip() for t in request.form.get('traducoes_nl', '').split(',') if t.strip()]
        traducoes_oc = [t.strip() for t in request.form.get('traducoes_oc', '').split(',') if t.strip()]
        categoria_area = [c.strip() for c in request.form.get('categoria_area', '').split(',') if c.strip()]
        artigos_input = [a.strip() for a in request.form.get('artigos', '').split(',') if a.strip()]

        # Validar artigos relacionados
        anexos_validos = {anexo['Número'] for anexo in dados['ANEXOS']}
        artigos_validos = [artigo for artigo in artigos_input if artigo in anexos_validos]
        
        if not definicao:
            return redirect(url_for('editar_conceito', nome=nome, erro='A definição é obrigatória.'))
        
        # Atualiza a primeira definição. Se não houver, cria uma nova.
        if conceito.get('definicoes'):
            conceito['definicoes'][0][0] = definicao
        else:
            conceito['definicoes'] = [[definicao, 'Utilizador']]

        # Atualizar os campos na ordem correta
        conceito_atualizado = {
            'CAS': cas,
            'artigos': artigos_validos,
            'categoria_area': categoria_area,
            'categoria_lexica': [c.strip() for c in categoria_lexica_input.split(',') if c.strip()] if categoria_lexica_input else [],
            'definicoes': conceito['definicoes'],
            'info_enc': info_enc,
            'sigla': sigla,
            'sinonimos': {
                'pt': sinonimos_pt_input,
                'en': sinonimos_en_input,
                'es': sinonimos_es_input
            },
            'traducoes': {
                'ar': traducoes_ar,
                'ca': traducoes_ca,
                'en': traducoes_en,
                'es': traducoes_es,
                'eu': traducoes_eu,
                'fr': traducoes_fr,
                'gl': traducoes_gl,
                'nl': traducoes_nl,
                'oc': traducoes_oc
            },
        }
        
        # Atualiza o conceito existente com o dicionário na ordem desejada
        dados['CONCEITOS'][nome] = conceito_atualizado

        salvar_dados(dados)
        return redirect(url_for('listar_conceitos', sucesso='Conceito atualizado com sucesso!'))
    erro = request.args.get('erro')
    return render_template('editar_conceito.html', nome=nome,
        definicao=conceito['definicoes'][0][0] if conceito.get('definicoes') and conceito['definicoes'] else '',
        info_enc=conceito.get('info_enc', ''),
        categoria_lexica=','.join(conceito.get('categoria_lexica', [])),
        sigla=conceito.get('sigla', ''),
        cas=conceito.get('CAS', ''),
        sinonimos_pt=','.join(conceito.get('sinonimos', {}).get('pt', [])),
        sinonimos_en=','.join(conceito.get('sinonimos', {}).get('en', [])),
        sinonimos_es=','.join(conceito.get('sinonimos', {}).get('es', [])),
        traducoes_ar=','.join(conceito.get('traducoes', {}).get('ar', [])),
        traducoes_ca=','.join(conceito.get('traducoes', {}).get('ca', [])),
        traducoes_en=','.join(conceito.get('traducoes', {}).get('en', [])),
        traducoes_es=','.join(conceito.get('traducoes', {}).get('es', [])),
        traducoes_eu=','.join(conceito.get('traducoes', {}).get('eu', [])),
        traducoes_fr=','.join(conceito.get('traducoes', {}).get('fr', [])),
        traducoes_gl=','.join(conceito.get('traducoes', {}).get('gl', [])),
        traducoes_nl=','.join(conceito.get('traducoes', {}).get('nl', [])),
        traducoes_oc=','.join(conceito.get('traducoes', {}).get('oc', [])),
        categoria_area=','.join(conceito.get('categoria_area', [])),
        artigos=','.join(conceito.get('artigos', [])),
        erro=erro)

@app.route('/conceitos/eliminar/<nome>', methods=['POST'])
def eliminar_conceito(nome):
    if nome in dados['CONCEITOS']:
        del dados['CONCEITOS'][nome]
        salvar_dados(dados)
        return redirect(url_for('listar_conceitos', sucesso='Conceito eliminado com sucesso!'))
    return redirect(url_for('listar_conceitos', erro='Conceito não encontrado.'))

@app.route('/anexos/adicionar', methods=['GET', 'POST'])
def adicionar_anexo():
    if request.method == 'POST':
        numero = request.form['numero'].strip()
        titulo = request.form['titulo'].strip()
        numero_edicao = request.form['numero_edicao'].strip()
        mes_edicao = request.form['mes_edicao'].strip()
        ano_edicao = request.form['ano_edicao'].strip()
        
        if not all([numero, titulo, numero_edicao, mes_edicao, ano_edicao]):
            return redirect(url_for('adicionar_anexo', erro='Todos os campos são obrigatórios.'))
        
        # Verificar se o número já existe
        if any(anexo['Número'] == numero for anexo in dados['ANEXOS']):
            return redirect(url_for('adicionar_anexo', erro='Este número de anexo já existe.'))
        
        novo_anexo = {
            'Número': numero,
            'Título do Artigo': titulo,
            'Número da Edição': numero_edicao,
            'Mês da Edição': mes_edicao,
            'Ano da Edição': ano_edicao
        }
        
        dados['ANEXOS'].append(novo_anexo)
        salvar_dados(dados)
        return redirect(url_for('listar_anexos', sucesso='Anexo adicionado com sucesso!'))
    
    erro = request.args.get('erro')
    return render_template('editar_anexo.html', erro=erro)

@app.route('/anexos/editar/<numero>', methods=['GET', 'POST'])
def editar_anexo(numero):
    anexo = next((a for a in dados['ANEXOS'] if a['Número'] == numero), None)
    if not anexo:
        return redirect(url_for('listar_anexos', erro='Anexo não encontrado.'))
    
    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        numero_edicao = request.form['numero_edicao'].strip()
        mes_edicao = request.form['mes_edicao'].strip()
        ano_edicao = request.form['ano_edicao'].strip()
        
        if not all([titulo, numero_edicao, mes_edicao, ano_edicao]):
            return redirect(url_for('editar_anexo', numero=numero, erro='Todos os campos são obrigatórios.'))
        
        anexo['Título do Artigo'] = titulo
        anexo['Número da Edição'] = numero_edicao
        anexo['Mês da Edição'] = mes_edicao
        anexo['Ano da Edição'] = ano_edicao
        
        salvar_dados(dados)
        return redirect(url_for('listar_anexos', sucesso='Anexo atualizado com sucesso!'))
    
    erro = request.args.get('erro')
    return render_template('editar_anexo.html', anexo=anexo, erro=erro)

@app.route('/anexos/eliminar/<numero>', methods=['POST'])
def eliminar_anexo(numero):
    anexo = next((a for a in dados['ANEXOS'] if a['Número'] == numero), None)
    if anexo:
        dados['ANEXOS'].remove(anexo)
        salvar_dados(dados)
        return redirect(url_for('listar_anexos', sucesso='Anexo eliminado com sucesso!'))
    return redirect(url_for('listar_anexos', erro='Anexo não encontrado.'))

@app.route('/categorias/adicionar', methods=['GET', 'POST'])
def adicionar_categoria():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        definicao = request.form['definicao'].strip()
        subcategorias = [s.strip() for s in request.form['subcategorias'].split('\n') if s.strip()]
        
        if not nome or not definicao:
            return redirect(url_for('adicionar_categoria', erro='Nome e definição são obrigatórios.'))
        
        if nome in dados['CATEGORIAS']:
            return redirect(url_for('adicionar_categoria', erro='Esta categoria já existe.'))
        
        dados['CATEGORIAS'][nome] = {
            'definicao': definicao,
            'subcategorias': subcategorias
        }
        
        salvar_dados(dados)
        return redirect(url_for('listar_categorias', sucesso='Categoria adicionada com sucesso!'))
    
    erro = request.args.get('erro')
    return render_template('editar_categoria.html', erro=erro)

@app.route('/categorias/editar/<nome>', methods=['GET', 'POST'])
def editar_categoria(nome):
    categoria = dados['CATEGORIAS'].get(nome)
    if not categoria:
        return redirect(url_for('listar_categorias', erro='Categoria não encontrada.'))
    
    if request.method == 'POST':
        definicao = request.form['definicao'].strip()
        subcategorias = [s.strip() for s in request.form['subcategorias'].split('\n') if s.strip()]
        
        if not definicao:
            return redirect(url_for('editar_categoria', nome=nome, erro='A definição é obrigatória.'))
        
        categoria['definicao'] = definicao
        categoria['subcategorias'] = subcategorias
        
        salvar_dados(dados)
        return redirect(url_for('listar_categorias', sucesso='Categoria atualizada com sucesso!'))
    
    erro = request.args.get('erro')
    return render_template('editar_categoria.html', categoria={'nome': nome, **categoria}, erro=erro)

@app.route('/categorias/eliminar/<nome>', methods=['POST'])
def eliminar_categoria(nome):
    if nome in dados['CATEGORIAS']:
        del dados['CATEGORIAS'][nome]
        salvar_dados(dados)
        return redirect(url_for('listar_categorias', sucesso='Categoria eliminada com sucesso!'))
    return redirect(url_for('listar_categorias', erro='Categoria não encontrada.'))

if __name__ == '__main__':
    app.run(debug=True)