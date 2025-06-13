from flask import Flask, render_template, json, request
from markupsafe import Markup

app = Flask(__name__)

# Carregar dados do JSON
with open('dados.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)


# Processar links nos textos
def processar_links(texto):
    if not texto:
        return ""

    # Siglas (ex: FAPESP)
    for sigla, significado in dados['SIGLAS'].items():
        texto = texto.replace(sigla, f'<a href="/sigla/{sigla}" class="tooltip" title="{significado}">{sigla}</a>')

    # Abreviaturas (ex: et al.)
    for abrev, significados in dados['ABREVS'].items():
        if abrev in texto:
            significado = ', '.join(significados)
            texto = texto.replace(abrev,
                                  f'<a href="/abreviatura/{abrev}" class="tooltip" title="{significado}">{abrev}</a>')

    return Markup(texto)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/conceitos')
def listar_conceitos():
    conceitos = dados['CONCEITOS']
    return render_template('conceitos.html', conceitos=conceitos)


@app.route('/conceito/<nome>')
def detalhe_conceito(nome):
    conceito = dados['CONCEITOS'].get(nome)
    if not conceito:
        return "Conceito não encontrado", 404

    # Processar informações com links
    conceito['definicoes_processadas'] = [
        [processar_links(definicao), fonte]
        for definicao, fonte in conceito['definicoes']
    ]
    conceito['info_enc_processada'] = processar_links(conceito['info_enc'])

    return render_template('conceito.html',
                           nome=nome,
                           conceito=conceito,
                           categorias=dados['CATEGORIAS'])


@app.route('/siglas')
def listar_siglas():
    siglas = dados['SIGLAS']
    return render_template('siglas.html', siglas=siglas)


@app.route('/sigla/<sigla>')
def detalhe_sigla(sigla):
    significado = dados['SIGLAS'].get(sigla)
    if not significado:
        return "Sigla não encontrada", 404
    return render_template('sigla.html', sigla=sigla, significado=significado)


@app.route('/abreviaturas')
def listar_abreviaturas():
    abreviaturas = dados['ABREVS']
    return render_template('abreviaturas.html', abreviaturas=abreviaturas)


@app.route('/abreviatura/<abrev>')
def detalhe_abreviatura(abrev):
    significados = dados['ABREVS'].get(abrev)
    if not significados:
        return "Abreviatura não encontrada", 404
    return render_template('abreviatura.html', abrev=abrev, significados=significados)


@app.route('/categorias')
def listar_categorias():
    categorias = dados['CATEGORIAS']
    return render_template('categorias.html', categorias=categorias)


@app.route('/categoria/<nome>')
def detalhe_categoria(nome):
    categoria = dados['CATEGORIAS'].get(nome)
    if not categoria:
        return "Categoria não encontrada", 404
    return render_template('categoria.html', nome=nome, categoria=categoria)


@app.route('/anexos')
def listar_anexos():
    anexos = dados['ANEXOS']
    return render_template('anexos.html', anexos=anexos)


if __name__ == '__main__':
    app.run(debug=True)