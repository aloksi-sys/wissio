import json
import sys
import random

import os, secrets
from datetime import datetime, date, timedelta, timezone
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from models import db, Usuario, Texto, Flashcard, ProgressoFlashcard, CTestSubmissao, EstatisticaDiaria, NivelCEFR, ObjetivoAprendizagem, RespostaFlashcard
from processador import processar_texto_alemao

# Import translation utility (now at project root)
from translation import translate_with_definition

app = Flask(__name__)

# Remove any external DATABASE_URL that Render may inject
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

# Debug: show DB URI after possible env removal
print('DEBUG: DB URI after env cleanup:', app.config.get('SQLALCHEMY_DATABASE_URI'))
sys.stdout.flush()

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Use a local SQLite database (ignore external DATABASE_URL)
_db_url = 'sqlite:///wissio.db'

app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações das extensões Flask
csrf = CSRFProtect(app)
csrf.init_app(app)

db.init_app(app)
migrate = Migrate(app, db)

# CSRF protection for API endpoints – require token via header (or skip for GET)
def csrf_protect(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not token or token != session.get('_csrf_token'):
                abort(400, description='Invalid CSRF token')
        return f(*args, **kwargs)
    return decorated

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# Helper for session
def get_current_user():
    if 'user_id' not in session:
        return None
    return Usuario.query.get(session['user_id'])

# ---------- ROTAS DE AUTENTICAÇÃO ----------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email')
    senha = request.form.get('senha')
    user = Usuario.query.filter_by(email=email).first()
    if not user or not user.verificar_senha(senha):
        flash('Email ou senha inválidos.', 'danger')
        return redirect(url_for('login'))
    session['user_id'] = user.id
    flash('Login realizado com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado.', 'info')
    return redirect(url_for('index'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'GET':
        return render_template('cadastro.html')
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    if Usuario.query.filter_by(email=email).first():
        flash('Email já cadastrado.', 'warning')
        return redirect(url_for('cadastro'))
    novo_usuario = Usuario(nome=nome, email=email)
    novo_usuario.definir_senha(senha)
    db.session.add(novo_usuario)
    db.session.commit()
    flash('Cadastro realizado com sucesso! Faça login.', 'success')
    return redirect(url_for('login'))

# ---------- ROTAS DE USUÁRIO ----------
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = Usuario.query.get(session['user_id'])
    # Obtém último progresso por texto
    textos = Texto.query.filter_by(usuario_id=user.id).order_by(Texto.id.desc()).all()
    texto_infos = []
    for texto in textos:
        ultimo_progresso = (
            db.session.query(ProgressoFlashcard)
            .join(Flashcard)
            .filter(Flashcard.texto_id == texto.id)
            .order_by(ProgressoFlashcard.data_ultimo_acesso.desc())
            .first()
        )
        texto_infos.append({
            'texto': texto,
            'ultimo_progresso': ultimo_progresso,
        })
    return render_template('home.html', user=user, texto_infos=texto_infos)

# ---------- ROTAS DE TEXTO ----------
@app.route('/texto/novo', methods=['GET', 'POST'])
@login_required
def novo_texto():
    if request.method == 'GET':
        return render_template('novo_texto.html')
    titulo = request.form.get('titulo')
    conteudo = request.form.get('conteudo')
    nivel = request.form.get('nivel_cefr')
    objetivo = request.form.get('objetivo_aprendizagem')
    idioma_origem = request.form.get('idioma_origem')
    idioma_destino = request.form.get('idioma_destino')
    usuario = get_current_user()
    # Processamento e criação de flashcards
    resultado = processar_texto_alemao(conteudo)
    texto_obj = Texto(
        titulo=titulo,
        conteudo_original=conteudo,
        nivel_cefr=NivelCEFR[nivel] if nivel in NivelCEFR.__members__ else None,
        objetivo_aprendizagem=ObjetivoAprendizagem[objetivo] if objetivo in ObjetivoAprendizagem.__members__ else None,
        idioma_origem=idioma_origem,
        idioma_destino=idioma_destino,
        usuario_id=usuario.id
    )
    db.session.add(texto_obj)
    db.session.flush()  # get texto_obj.id
    # Cria flashcards
    for card in resultado.get('flashcards', []):
        # Usa a nova lógica de tradução/definição
        traducao, definicao = translate_with_definition(card['palavra'], src='pt', tgt='en')
        fc = Flashcard(
            palavra_alemao=card['palavra'],
            traducao=traducao,
            tipo=card.get('tipo'),
            exemplo=card['exemplo'],
            alternativas=json.dumps({"definicao": definicao} if definicao else {}),
            usuario_id=usuario.id,
            texto_id=texto_obj.id
        )
        db.session.add(fc)
        db.session.flush()
        progresso = ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=fc.id)
        db.session.add(progresso)
    db.session.commit()
    flash('Texto e flashcards criados com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/texto/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def editar_texto(id):
    texto = Texto.query.get_or_404(id)
    if texto.usuario_id != session.get('user_id'):
        abort(403)
    if request.method == 'GET':
        return render_template('editar_texto.html', texto=texto)
    texto.titulo = request.form.get('titulo')
    texto.conteudo_original = request.form.get('conteudo')
    texto.nivel_cefr = NivelCEFR[request.form.get('nivel_cefr')]
    texto.objetivo_aprendizagem = ObjetivoAprendizagem[request.form.get('objetivo_aprendizagem')]
    db.session.commit()
    flash('Texto atualizado.', 'success')
    return redirect(url_for('home'))

# ---------- FLASHCARD ROTAS ----------
@app.route('/texto/<int:id>/flashcards', methods=['GET'])
@login_required
def flashcards_do_texto(id):
    texto = Texto.query.get_or_404(id)
    if texto.usuario_id != session.get('user_id'):
        abort(403)
    flashcards = Flashcard.query.filter_by(texto_id=id).all()
    return render_template('flashcards.html', texto=texto, flashcards=flashcards)

@app.route('/texto/<int:id>/flashcards/gerar', methods=['POST'])
@login_required
def gerar_flashcards_do_texto(id):
    """Gera flashcards para um texto já existente (ou completa os que faltam)."""
    usuario = get_current_user()
    texto = Texto.query.get_or_404(id)
    if texto.usuario_id != usuario.id:
        abort(403)
    # Processamento original para extrair palavras‑alemão, exemplos etc.
    resultado = processar_texto_alemao(texto.conteudo_original)
    candidatos = resultado.get('flashcards', [])
    ja_tem = {f.palavra_alemao.lower() for f in Flashcard.query.filter_by(texto_id=texto.id, usuario_id=usuario.id).all()}
    criados = 0
    novos = []
    for card in candidatos:
        if card['palavra'].lower() in ja_tem:
            continue
        # ----- NOVA LÓGICA DE TRADUÇÃO + DEFINIÇÃO -----
        traducao, definicao = translate_with_definition(card['palavra'], src='pt', tgt='en')
        fc = Flashcard(
            palavra_alemao=card['palavra'],
            traducao=traducao,
            tipo=card.get('tipo'),
            exemplo=card['exemplo'],
            alternativas=json.dumps({"definicao": definicao} if definicao else {}),
            usuario_id=usuario.id,
            texto_id=texto.id
        )
        db.session.add(fc)
        novos.append(fc)
        criados += 1
    db.session.flush()
    for fc in novos:
        db.session.add(ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=fc.id))
    db.session.commit()
    if criados:
        flash(f'{criados} novo(s) flashcard(s) gerados para "{texto.titulo}".', 'success')
    else:
        flash('Todos os flashcards deste texto já foram gerados.', 'info')
    return redirect(url_for('flashcards_do_texto', id=texto.id))

# ---------- ROTAS API ----------
@app.route('/api/dica-aleatoria', methods=['GET'])
def obter_dica_aleatoria():
    # Exemplo de endpoint simples que retorna um dado aleatório (pode ser usado pelo front‑end)
    dicas = [
        "Pratique todos os dias!",
        "Reveja palavras que errou.",
        "Use cartões de memória para revisão espaçada.",
    ]
    return jsonify({'dica': random.choice(dicas)})

print('FINAL DB URI:', app.config.get('SQLALCHEMY_DATABASE_URI'))
# app.run(host='0.0.0.0', port=5000, debug=False)
