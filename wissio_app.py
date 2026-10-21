"""
Aplicação Flask Wissio - Plataforma de Aprendizado de Alemão.
Versão ultra-robusta para Render deployment.
"""

import json
import sys
import os
import secrets
import random
from datetime import datetime, timedelta, timezone
from functools import wraps

# DEBUG: Check environment BEFORE any imports
print("=" * 60)
print("INICIALIZANDO WISSIO (Flask)")
print("=" * 60)
sys.stdout.flush()

# PASSO CRÍTICO: Limpar DATABASE_URL ANTES de qualquer importação
# Render injeta DATABASE_URL automaticamente com informações do Supabase
if 'DATABASE_URL' in os.environ:
    db_url_val = os.environ.get('DATABASE_URL', '')
    print(f"DATABASE_URL injetado pelo Render, removendo: {db_url_val[:60]}...")
    sys.stdout.flush()
    del os.environ['DATABASE_URL']

os.environ.pop('DATABASE_URL', None)

print(f"DATABASE_URL após limpeza: {os.environ.get('DATABASE_URL', 'NÃO EXISTE')}")
sys.stdout.flush()

# Configuraçõesantes de importar Flask
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Criar app
app = Flask(__name__)

# Configurações - SQLite forçado
# Usar chave secreta fixa para consistência entre requests
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'wissio-render-secret-key-2026-secure-32chars')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wissio.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações de sessão - ESSENCIAIS para funcionamento
app.config['SESSION_COOKIE_SECURE'] = False  # Render usa HTTP durante build
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Evita problemas CORS
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas

# CSRF desabilitado (problema com login)
app.config['WTF_CSRF_ENABLED'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = None

print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"WTF_CSRF_ENABLED: {app.config['WTF_CSRF_ENABLED']}")
sys.stdout.flush()

# Imports depois da configuração
from models import db, Usuario, Texto, Flashcard, ProgressoFlashcard, CTestSubmissao, EstatisticaDiaria, NivelCEFR, ObjetivoAprendizagem, RespostaFlashcard
from processador import processar_texto_alemao
from translation import translate_with_definition

# Inicializar SQLAlchemy
db.init_app(app)

# Close db session after request
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


# Context processor - MUITO SIMPLES sem queries
@app.context_processor
def inject_globals():
    """Injeta variáveis em todos os templates - SEM DATABASE QUERIES."""
    return {
        'tema_escuro': session.get('tema_escuro', False),
        'csrf_token': ''
    }


# Decorador para login required
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, faça login primeiro.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ========== ROTAS ==========

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    # Normalizar e-mail (case-insensitive)
    email = request.form.get('email', '').strip().lower()
    senha = request.form.get('senha', '')
    
    print(f"DEBUG LOGIN: Tentativa email='{email}'")
    sys.stdout.flush()
    
    if not email or not senha:
        flash('Por favor, preencha e-mail e senha.', 'warning')
        return redirect(url_for('login'))
    
    # Buscar usuário
    user = Usuario.query.filter_by(email=email).first()
    
    if not user:
        print(f"DEBUG LOGIN: Usuário NÃO encontrado")
        sys.stdout.flush()
        flash('Email ou senha inválidos.', 'danger')
        return redirect(url_for('login'))
    
    print(f"DEBUG LOGIN: Usuário encontrado ID={user.id}")
    sys.stdout.flush()
    
    # Verificar senha
    if not user.check_senha(senha):
        print(f"DEBUG LOGIN: SENHA INCORRETA")
        sys.stdout.flush()
        flash('Email ou senha inválidos.', 'danger')
        return redirect(url_for('login'))
    
    # Login OK - gravar sessão
    session['usuario_id'] = user.id
    session['usuario_nome'] = user.nome
    session.permanent = True
    
    print(f"DEBUG LOGIN: SUCESSO ID={user.id}")
    sys.stdout.flush()
    
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
    
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    senha = request.form.get('senha', '')
    confirmar_senha = request.form.get('confirmar_senha', '')
    
    print(f"DEBUG CADASTRO: nome={nome}, email={email}")
    sys.stdout.flush()
    
    if not nome or not email or not senha:
        flash('Por favor, preencha nome, e-mail e senha.', 'warning')
        return redirect(url_for('cadastro'))
    
    if senha != confirmar_senha:
        flash('As senhas não coincidem.', 'warning')
        return redirect(url_for('cadastro'))
    
    if Usuario.query.filter_by(email=email).first():
        flash('Email já cadastrado.', 'warning')
        return redirect(url_for('cadastro'))
    
    novo_usuario = Usuario(nome=nome, email=email)
    novo_usuario.set_senha(senha)
    db.session.add(novo_usuario)
    db.session.commit()
    
    print(f"DEBUG CADASTRO: USUÁRIO CRIADO ID={novo_usuario.id}")
    sys.stdout.flush()
    
    flash('Cadastro realizado com sucesso! Faça login.', 'success')
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    user = Usuario.query.get(session['usuario_id'])
    textos = Texto.query.filter_by(usuario_id=user.id).order_by(Texto.id.desc()).limit(3).all()
    total_textos = Texto.query.filter_by(usuario_id=user.id).count()
    total_flashcards = Flashcard.query.filter_by(usuario_id=user.id).count()
    
    return render_template('home.html',
                          usuario=user,
                          texto_recentes=textos,
                          total_textos=total_textos,
                          total_flashcards=total_flashcards)


@app.route('/dashboard')
@login_required
def dashboard():
    user = Usuario.query.get(session['usuario_id'])
    textos = Texto.query.filter_by(usuario_id=user.id).order_by(Texto.id.desc()).all()
    return render_template('dashboard.html', usuario=user, textos=textos)


@app.route('/biblioteca')
@login_required
def biblioteca():
    user = Usuario.query.get(session['usuario_id'])
    textos = Texto.query.filter_by(usuario_id=user.id).all()
    return render_template('textos.html', textos=textos)


@app.route('/flashcards')
@login_required
def flashcards():
    user = Usuario.query.get(session['usuario_id'])
    flashcards = Flashcard.query.filter_by(usuario_id=user.id).all()
    return render_template('flashcards.html', flashcards=flashcards)


@app.route('/perfil')
@login_required
def perfil():
    user = Usuario.query.get(session['usuario_id'])
    return render_template('perfil.html', usuario=user)


@app.route('/dicas-alemao')
def dicas_alemao():
    return render_template('dicas_alemao.html')


@app.route('/verificar-email')
@login_required
def verificar_email():
    return render_template('verificar_email.html')


@app.route('/textos')
@login_required
def lista_textos():
    user = Usuario.query.get(session['usuario_id'])
    textos = Texto.query.filter_by(usuario_id=user.id).order_by(Texto.id.desc()).all()
    return render_template('textos.html', textos=textos)


@app.route('/novo-texto', methods=['GET'])
@login_required
def novo_texto_page():
    return render_template('novo_texto.html')


@app.route('/texto/novo', methods=['GET', 'POST'])
@login_required
def novo_texto():
    if request.method == 'GET':
        return render_template('novo_texto.html')
    
    titulo = request.form.get('titulo', '').strip()
    conteudo = request.form.get('conteudo', '').strip()
    nivel_val = request.form.get('nivel_cefr', 'A1')
    categoria = request.form.get('categoria', '').strip()
    usuario = get_current_user()
    
    resultado = processar_texto_alemao(conteudo)
    
    nivel_enum = NivelCEFR[nivel_val] if nivel_val in NivelCEFR.__members__ else NivelCEFR.A1
    texto_obj = Texto(
        titulo=titulo,
        conteudo_original=conteudo,
        nivel=nivel_enum,
        categoria=categoria or None,
        usuario_id=usuario.id
    )
    db.session.add(texto_obj)
    db.session.flush()
    
    flashcards_criados = 0
    for card in resultado.get('flashcards', []):
        traducao, definicao = translate_with_definition(card['palavra'], src='pt', tgt='en')
        fc = Flashcard(
            palavra_alemao=card['palavra'],
            traducao=traducao,
            tipo=card.get('tipo'),
            exemplo=card.get('exemplo'),
            alternativas=json.dumps({"definicao": definicao} if definicao else {}),
            usuario_id=usuario.id,
            texto_id=texto_obj.id
        )
        db.session.add(fc)
        flashcards_criados += 1
        progresso = ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=fc.id)
        db.session.add(progresso)
    
    db.session.commit()
    flash(f'Texto criado com {flashcards_criados} flashcards!', 'success')
    return redirect(url_for('home'))


@app.route('/texto/<int:id>/flashcards', methods=['GET'])
@login_required
def flashcards_do_texto(id):
    texto = Texto.query.get_or_404(id)
    if texto.usuario_id != session.get('usuario_id'):
        abort(403)
    
    flashcards = Flashcard.query.filter_by(texto_id=id, usuario_id=session['usuario_id']).all()
    user = Usuario.query.get(session['usuario_id'])
    
    cards_data = []
    for fc in flashcards:
        try:
            alternativas = json.loads(fc.alternativas) if fc.alternativas else {}
        except:
            alternativas = {}
        
        progresso = ProgressoFlashcard.query.filter_by(
            usuario_id=user.id, flashcard_id=fc.id
        ).first()
        
        cards_data.append({
            'flashcard': fc,
            'progresso': progresso,
            'alternativas': list(alternativas.values()) if alternativas else []
        })
    
    return render_template('flashcards.html', cards_data=cards_data, texto=texto, modo_texto= texto)


@app.route('/flashcards/<int:fc_id>/responder', methods=['POST'])
@login_required
def responder_flashcard(fc_id):
    usuario = get_current_user()
    flashcard = Flashcard.query.get_or_404(fc_id)
    if flashcard.usuario_id != usuario.id:
        abort(403)
    
    resposta = request.form.get('resposta', '')
    correta = (resposta == (flashcard.traducao or ''))
    
    progresso = ProgressoFlashcard.query.filter_by(
        usuario_id=usuario.id, flashcard_id=fc_id
    ).first()
    
    if progresso:
        if correta:
            progresso.stability = min(progresso.stability + 15, 365)
            progresso.difficulty = max(progresso.difficulty - 0.5, 1)
            progresso.reps += 1
        else:
            progresso.stability = max(progresso.stability * 0.5, 1)
            progresso.difficulty = min(progresso.difficulty + 1, 10)
            progresso.lapses += 1
            progresso.reps = 0
        progresso.next_review = datetime.now(timezone.utc) + timedelta(days=int(progresso.stability))
    
    db.session.commit()
    return jsonify({'correct': correta})


@app.route('/flashcards/<int:fc_id>/revisar', methods=['POST'])
@login_required
def revisar_flashcard(fc_id):
    usuario = get_current_user()
    flashcard = Flashcard.query.get_or_404(fc_id)
    if flashcard.usuario_id != usuario.id:
        abort(403)
    
    facilidade = request.form.get('facilidade', 'good')
    
    progresso = ProgressoFlashcard.query.filter_by(
        usuario_id=usuario.id, flashcard_id=fc_id
    ).first()
    
    if progresso:
        if facilidade == 'again':
            progresso.difficulty = min(progresso.difficulty + 1, 10)
            progresso.reps = 0
            progresso.lapses += 1
        else:
            progresso.reps += 1
            progresso.difficulty = max(progresso.difficulty - 0.5, 1)
            if facilidade == 'easy':
                progresso.stability = min(progresso.stability + 30, 365)
            elif facilidade == 'good':
                progresso.stability = min(progresso.stability + 15, 365)
            elif facilidade == 'hard':
                progresso.stability = max(progresso.stability + 5, 1)
        progresso.next_review = datetime.now(timezone.utc) + timedelta(days=int(progresso.stability))
    
    db.session.commit()
    return jsonify({'success': True, 'facilidade': facilidade})


@app.route('/toggle-tema', methods=['POST'])
@login_required
def toggle_tema():
    usuario = get_current_user()
    if usuario:
        usuario.tema_escuro = not usuario.tema_escuro
        db.session.commit()
        session['tema_escuro'] = usuario.tema_escuro
        return jsonify({'success': True, 'tema_escuro': usuario.tema_escuro})
    return jsonify({'success': False}), 400


@app.route('/texto/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def editar_texto(id):
    texto = Texto.query.get_or_404(id)
    if texto.usuario_id != session.get('usuario_id'):
        abort(403)
    if request.method == 'GET':
        return render_template('editar_texto.html', texto=texto)
    texto.titulo = request.form.get('titulo', '').strip()
    texto.conteudo_original = request.form.get('conteudo', '').strip()
    nivel_val = request.form.get('nivel_cefr')
    if nivel_val and nivel_val in NivelCEFR.__members__:
        texto.nivel = NivelCEFR[nivel_val]
    db.session.commit()
    flash('Texto atualizado.', 'success')
    return redirect(url_for('lista_textos'))


@app.route('/ver-texto/<int:id>')
@login_required
def ver_texto(id):
    texto = Texto.query.get_or_404(id)
    if texto.usuario_id != session.get('usuario_id'):
        abort(403)
    return render_template('ver_texto.html', texto=texto)


@app.route('/painel-flashcards')
@login_required
def painel_flashcards():
    user = Usuario.query.get(session['usuario_id'])
    flashcards = Flashcard.query.filter_by(usuario_id=user.id).all()
    return render_template('painel_flashcards.html', flashcards=flashcards)


@app.route('/api/dica-aleatoria', methods=['GET'])
def obter_dica_aleatoria():
    dicas = [
        "Pratique todos os dias!",
        "Revise palavras que errou.",
        "Use cartões de memória para revisão espaçada.",
        "Comece pelos flashcards mais fáceis.",
        "Leia textos simples em alemão diariamente."
    ]
    return jsonify({'dica': random.choice(dicas)})


# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return render_template('erro.html', error=str(error)), 400

@app.errorhandler(403)
def forbidden(error):
    return render_template('erro.html', error='Acesso negado'), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('erro.html', error='Página não encontrada'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('erro.html', error='Erro interno do servidor'), 500


# Helper function
def get_current_user():
    if 'usuario_id' not in session:
        return None
    return Usuario.query.get(session['usuario_id'])


# ========== INICIALIZAÇÃO DO BANCO ==========
print("=" * 60)
print("INICIALIZANDO BANCO...")
sys.stdout.flush()

with app.app_context():
    print("Criando tabelas...")
    sys.stdout.flush()
    db.create_all()
    print("Tabelas criadas com sucesso!")
    sys.stdout.flush()
    
    # Criar admin se não existir
    admin = Usuario.query.filter_by(email='admin@wissio.com').first()
    if not admin:
        print("Criando admin de teste...")
        sys.stdout.flush()
        admin = Usuario(nome='Admin Wissio', email='admin@wissio.com')
        admin.set_senha('admin123')
        db.session.add(admin)
        db.session.commit()
        print(f"Admin criado: ID={admin.id}")
        sys.stdout.flush()
    else:
        print(f"Admin existe: ID={admin.id}")
        sys.stdout.flush()
    
    # Testar senha
    pwd_ok = admin.check_senha('admin123')
    print(f"Teste senha admin: {pwd_ok}")
    sys.stdout.flush()
    
    if not pwd_ok:
        print("ERRO CRÍTICO: Verificação de senha do admin falhou!")
        sys.exit(1)
    
    count = Usuario.query.count()
    print(f"Database OK: {count} usuarios")
    sys.stdout.flush()

print("=" * 60)
print("INICIALIZAÇÃO CONCLUÍDA!")
print("=" * 60)
sys.stdout.flush()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)