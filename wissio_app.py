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

# PASSO CRÍTICO: Configuração do banco de dados (Suporta SQLite e PostgreSQL/Supabase)
db_url = os.environ.get('DATABASE_URL')
# No Render, DATABASE_URL pode começar com postgres://, SQLAlchemy requer postgresql://
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

# Se DATABASE_URL não estiver presente, ou se USE_SQLITE for True, usa SQLite
if not db_url or os.environ.get('USE_SQLITE', 'false').lower() == 'true':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///wissio.db?check_same_thread=False'
else:
    SQLALCHEMY_DATABASE_URI = db_url

print(f"Banco de dados configurado: {SQLALCHEMY_DATABASE_URI[:30]}...")
sys.stdout.flush()

# Configuraçõesantes de importar Flask
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Criar app
app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'wissio-render-secret-key-2026-secure-32chars')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações de sessão - ESSENCIAIS para funcionamento
app.config['SESSION_COOKIE_SECURE'] = False  # Render usa HTTP durante build
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Evita problemas CORS
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas

# CSRF pode ser habilitado quando SMTP configurado
# Por enquanto, desabilitado para funcionamento estável
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
    try:
        db.session.remove()
    except Exception:
        pass


# Context processor - Injeta usuário logado e token CSRF em todos os templates
from flask_wtf.csrf import generate_csrf, validate_csrf

@app.context_processor
def inject_globals():
    user = None
    if 'usuario_id' in session:
        user = Usuario.query.get(session['usuario_id'])
    csrf_token_value = generate_csrf() if app.config.get('WTF_CSRF_ENABLED', True) else ''
    return {
        'tema_escuro': session.get('tema_escuro', False),
        'usuario': user,
        'csrf_token': csrf_token_value
    }


# Decoraor para CSRF em rotas AJAX
def csrf_protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
            if not token or not validate_csrf(token):
                return jsonify({'error': 'CSRF token inválido'}), 400
        return f(*args, **kwargs)
    return decorated


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
    session['email_verificado'] = user.email_verificado
    session.permanent = True
    
    print(f"DEBUG LOGIN: SUCESSO ID={user.id}")
    sys.stdout.flush()
    
    flash('Login realizado com sucesso!', 'success')
    if not user.onboarding_concluido:
        return redirect(url_for('onboarding_objetivos'))
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado.', 'info')
    return redirect(url_for('index'))


@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'GET':
        return render_template('esqueci_senha.html')
    
    email = request.form.get('email', '').strip().lower()
    user = Usuario.query.filter_by(email=email).first()
    
    if user:
        user.gerar_token_reset()
        token = user.token_reset_senha
        reset_url = url_for('redefinir_senha', token=token, _external=True)
        # Fallback para desenvolvimento / log se envio de e-mail falhar
        print(f"PASSWORD RESET LINK PARA {email}: {reset_url}")
        sys.stdout.flush()
        flash('Se o e-mail estiver cadastrado, você receberá instruções para redefinir sua senha.', 'info')
    else:
        flash('Se o e-mail estiver cadastrado, você receberá instruções para redefinir sua senha.', 'info')
        
    return redirect(url_for('login'))


@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    user = Usuario.query.filter_by(token_reset_senha=token).first()
    
    if not user or not user.verificar_token_reset(token):
        flash('Token de redefinição inválido ou expirado.', 'danger')
        return redirect(url_for('login'))
        
    if request.method == 'GET':
        return render_template('redefinir_senha.html', token=token)
        
    senha = request.form.get('senha', '')
    confirmar_senha = request.form.get('confirmar_senha', '')
    
    if not senha or senha != confirmar_senha:
        flash('As senhas não coincidem ou estão vazias.', 'warning')
        return redirect(url_for('redefinir_senha', token=token))
        
    user.set_senha(senha)
    user.token_reset_senha = None
    user.token_reset_expira = None
    db.session.commit()
    
    flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
    return redirect(url_for('login'))


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
    from datetime import date, timedelta
    
    user = Usuario.query.get(session['usuario_id'])
    textos = Texto.query.filter_by(usuario_id=user.id).order_by(Texto.id.desc()).all()
    
    # Calcular streak (dias consecutivos de revisão)
    streak = 0
    today = date.today()
    if user.ultima_data_revisao:
        last_rev = user.ultima_data_revisao.date() if hasattr(user.ultima_data_revisao, 'date') else user.ultima_data_revisao
        
        if last_rev == today:
            streak = user.streak_dias or 0
        elif last_rev == today - timedelta(days=1):
            streak = user.streak_dias or 0
    
    # Calcular totals
    total_textos = Texto.query.filter_by(usuario_id=user.id).count()
    total_flashcards = Flashcard.query.filter_by(usuario_id=user.id).count()
    
    # XP total
    xp_total = user.xp_total if hasattr(user, 'xp_total') else (total_textos * 50 + total_flashcards * 10)
    
    # Próximas revisões
    now = datetime.now(timezone.utc)
    proximas_revisoes = ProgressoFlashcard.query.filter(
        ProgressoFlashcard.usuario_id == user.id,
        ProgressoFlashcard.next_review != None,
        ProgressoFlashcard.next_review <= now + timedelta(days=7)
    ).order_by(ProgressoFlashcard.next_review).limit(10).all()
    
    # Dados do gráfico (últimos 7 dias)
    dias_grafico = []
    for i in range(7):
        day_data = type('DayData', (), {'xp': 10 + i, 'textos': 0, 'flashcards': 0, 'data': today - timedelta(days=6-i)})()
        dias_grafico.append(day_data)
    
    return render_template('dashboard.html',
                          usuario=user,
                          textos=textos,
                          total_textos=total_textos,
                          total_flashcards=total_flashcards,
                          streak=streak,
                          xp_total=xp_total,
                          proximas_revisoes=proximas_revisoes,
                          dias_grafico=dias_grafico)


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
    
    # Preparar dados para o template
    cards_data = []
    for fc in flashcards:
        try:
            alternativas = json.loads(fc.alternativas) if fc.alternativas else []
            alternativas_lista = list(alternativas.values()) if isinstance(alternativas, dict) else (alternativas if isinstance(alternativas, list) else [])
        except:
            alternativas_lista = []
        
        progresso = ProgressoFlashcard.query.filter_by(
            usuario_id=user.id, flashcard_id=fc.id
        ).first()
        
        cards_data.append({
            'flashcard': fc,
            'progresso': progresso,
            'alternativas': alternativas_lista
        })
    
    return render_template('flashcards.html', cards_data=cards_data)


@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    user = Usuario.query.get(session['usuario_id'])
    
    if request.method == 'POST':
        acao = request.form.get('acao', '')
        
        if acao == 'atualizar_perfil':
            user.nome = request.form.get('nome', '').strip()
            user.email = request.form.get('email', '').strip().lower()
            nivel = request.form.get('nivel_atual', 'A1')
            if nivel in NivelCEFR.__members__:
                user.nivel_atual = NivelCEFR[nivel]
            objetivo = request.form.get('objetivo', '')
            if objetivo in ObjetivoAprendizagem.__members__:
                user.objetivo = ObjetivoAprendizagem[objetivo]
            db.session.commit()
            flash('Perfil atualizado!', 'success')
            return redirect(url_for('perfil'))
        
        elif acao == 'atualizar_metas':
            user.meta_diaria_minutos = int(request.form.get('meta_diaria_minutos', 60))
            user.meta_semanal_textos = int(request.form.get('meta_semanal_textos', 3))
            user.meta_flashcards_iniciais = int(request.form.get('meta_flashcards_iniciais', 20))
            db.session.commit()
            flash('Metas atualizadas!', 'success')
            return redirect(url_for('perfil'))
        
        elif acao == 'alterar_senha':
            senha_atual = request.form.get('senha_atual', '')
            nova_senha = request.form.get('nova_senha', '')
            confirmar = request.form.get('confirmar_senha', '')
            
            if user.check_senha(senha_atual):
                if nova_senha and nova_senha == confirmar:
                    user.set_senha(nova_senha)
                    db.session.commit()
                    flash('Senha alterada com sucesso!', 'success')
                else:
                    flash('Nova senha e confirmação não coincidem.', 'warning')
            else:
                flash('Senha atual está incorreta.', 'danger')
            return redirect(url_for('perfil'))
    
    # Calcular streak para o template
    streak = user.streak_dias or 0
    
    # GET request
    return render_template('perfil.html', usuario=user,
                          streak=streak,
                          niveis=NivelCEFR, objetivos=ObjetivoAprendizagem)


@app.route('/onboarding_objetivos', methods=['GET', 'POST'])
@login_required
def onboarding_objetivos():
    usuario = get_current_user()
    
    if request.method == 'POST':
        objetivo = request.form.get('objetivo', '')
        if objetivo in ObjetivoAprendizagem.__members__:
            usuario.objetivo = ObjetivoAprendizagem[objetivo]
            db.session.commit()
            flash('Objetivo salvo! Continue para seu plano de estudos.', 'success')
            return redirect(url_for('onboarding_plano'))
        flash('Objetivo inválido.', 'danger')
        return redirect(url_for('onboarding_objetivos'))
    
    return render_template('onboarding_objetivos.html', objetivos=ObjetivoAprendizagem)


@app.route('/onboarding_plano', methods=['GET', 'POST'])
@login_required
def onboarding_plano():
    usuario = get_current_user()
    
    if request.method == 'POST':
        try:
            usuario.meta_diaria_minutos = int(request.form.get('meta_diaria_minutos', 60))
            usuario.meta_semanal_textos = int(request.form.get('meta_semanal_textos', 3))
            usuario.meta_flashcards_iniciais = int(request.form.get('meta_flashcards_iniciais', 20))
            nivel = request.form.get('nivel_atual', 'A1')
            if nivel in NivelCEFR.__members__:
                usuario.nivel_atual = NivelCEFR[nivel]
            usuario.onboarding_concluido = True
            db.session.commit()
            flash('Plano de estudos criado com sucesso! Agora é só começar.', 'success')
            session.pop('_onboarding_complete', None)
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Erro ao salvar plano: {str(e)}', 'danger')
            return redirect(url_for('onboarding_plano'))
    
    return render_template('onboarding_plano.html', 
                          usuario=usuario,
                          niveis=NivelCEFR)


@app.route('/dicas-alemao')
def dicas_alemao():
    dicas = [
        {'titulo': 'Aprenda as Preposições', 'conteudo': 'As preposições em alemão: in, an, auf, bei, für, mit. Use-as corretamente para expressar localização, tempo e relações.', 'categoria': 'gramatica'},
        {'titulo': 'Declínios de Artigos', 'conteudo': 'O alemão tem artigos definidos e indefinidos que mudam conforme o gênero, número e caso.', 'categoria': 'vocabulario'},
        {'titulo': 'Verbos Essenciais', 'conteudo': 'sein (ser/estar), haben (ter), werden (futuro), können (poder), müssen (dever).', 'categoria': 'verbo'},
        {'titulo': 'Acentuação Gráfica', 'conteudo': 'O trema (ä, ö, ü) indica modificação da vogal. O eszeleto (ß) substitui "ss".', 'categoria': 'pronuncia'},
        {'titulo': 'Conjunções', 'conteudo': 'Und, oder, aber, denn, weil, obwohl conectam ideias e mudam o verbo para o fim.', 'categoria': 'gramatica'},
    ]
    return render_template('dicas_alemao.html', dicas=dicas, total_dicas=len(dicas))


@app.route('/debug-info')
def debug_info():
    """Endpoint de diagnóstico para Render."""
    try:
        import sys
        import os
        import platform
        
        info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "working_directory": os.getcwd(),
            "session": dict(session),
            "database_uri": str(app.config.get('SQLALCHEMY_DATABASE_URI')),
            "csrf_enabled": app.config.get('WTF_CSRF_ENABLED'),
            "routes": [rule.rule for rule in app.url_map.iter_rules() if 'painel' in str(rule) or 'dicas' in str(rule)]
        }
        
        try:
            usuarios_count = Usuario.query.count()
            textos_count = Texto.query.count()
            info["db_status"] = "OK"
            info["usuarios_count"] = usuarios_count
            info["textos_count"] = textos_count
        except Exception as db_err:
            info["db_status"] = f"ERRO: {str(db_err)}"
            
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/verificar-email', methods=['GET', 'POST'])
@login_required
def verificar_email():
    user = Usuario.query.get(session['usuario_id'])
    
    if request.method == 'POST':
        # Verificação instantânea por clique no botão
        user.email_verificado = True
        user.token_verificacao = None
        user.token_verificacao_expira = None
        db.session.commit()
        session['email_verificado'] = True
        flash('E-mail verificado com sucesso! Bem-vindo ao WISSIO.', 'success')
        return redirect(url_for('home'))
        
    # Se já estiver verificado, garante que a sessão reflete isso
    if user.email_verificado:
        session['email_verificado'] = True
        
    return render_template('verificar_email.html', user=user)


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
        # Traduzir do alemão para o português
        traducao, definicao = translate_with_definition(card['palavra'], src='de', tgt='pt')
        
        # Construir alternativas como lista para o quiz (4 opções)
        opcoes = []
        if traducao:
            opcoes.append(traducao)
        
        # Adicionar outras palavras do texto como distratores
        palavras_outros = [f['palavra'] for f in resultado.get('flashcards', []) 
                          if f['palavra'].lower() != card['palavra'].lower()]
        palavras_outros = [p for p in palavras_outros if p not in opcoes][:3]
        opcoes.extend(palavras_outros)
        
        # Limitar a 4 opções e embaralhar
        random.shuffle(opcoes)
        opcoes = opcoes[:4]
        
        # Salvar alternativas como JSON (lista de strings)
        alternativas_json = json.dumps(opcoes)
        
        fc = Flashcard(
            palavra_alemao=card['palavra'],
            traducao=traducao,
            tipo=card.get('tipo'),
            exemplo=card.get('exemplo'),
            alternativas=alternativas_json,
            usuario_id=usuario.id,
            texto_id=texto_obj.id
        )
        db.session.add(fc)
        db.session.flush()  # Flush para obter o ID
        flashcards_criados += 1
        progresso = ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=fc.id, stability=1.0, difficulty=5.0, next_review=datetime.now(timezone.utc))
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
        # Alternativas já é uma lista JSON (de opções de múltipla escolha)
        try:
            alternativas = json.loads(fc.alternativas) if fc.alternativas else []
            if not isinstance(alternativas, list):
                alternativas = []
        except:
            alternativas = []
        
        progresso = ProgressoFlashcard.query.filter_by(
            usuario_id=user.id, flashcard_id=fc.id
        ).first()
        
        cards_data.append({
            'flashcard': fc,
            'progresso': progresso,
            'alternativas': alternativas
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
    
    # Gerar conteúdo C-Test se não existir (remover futuramente quando processador salvar)
    if not texto.ctest_conteudo:
        palavras = (texto.conteudo_original or '').split()
        palavras_ctest = []
        respostas_ctest = []
        contador = 0
        for p in palavras:
            if len(p) > 3:
                contador += 1
                if contador % 2 == 0:
                    metade = len(p) // 2
                    palavras_ctest.append(p[:metade] + "____")
                    respostas_ctest.append(p)
                else:
                    palavras_ctest.append(p)
            else:
                palavras_ctest.append(p)
        texto.ctest_conteudo = " ".join(palavras_ctest)
        texto.ctest_respostas = respostas_ctest
        db.session.commit()
    
    return render_template('ver_texto.html', texto=texto)


@app.route('/submeter_ctest', methods=['POST'])
@login_required
def submeter_ctest():
    """
    Endpoint para submissão do C-Test.
    Recebe o ID do texto via formulario e corriger as respostas.
    """
    try:
        from models import CTestSubmissao
        
        # Obter ID do texto - pode vir de 'id' ou do path
        texto_id = request.form.get('id') or request.view_args.get('id')
        
        if not texto_id:
            flash('Texto não especificado.', 'danger')
            return redirect(url_for('biblioteca'))
        
        texto = Texto.query.get_or_404(int(texto_id))
        if texto.usuario_id != session.get('usuario_id'):
            abort(403)
        
        # Coletar respostas do formulario
        respostas_usuario = {}
        for key, value in request.form.items():
            if key.startswith('gap_'):
                gap_num = int(key.replace('gap_', ''))
                respostas_usuario[gap_num] = value.strip()
        
        # Obter respostas corretas do banco
        respostas_corretas = texto.ctest_respostas or []
        
        # Calcular resultado
        resultado = {}
        acertos = 0
        total = len(respostas_corretas)
        
        for i, resposta_correta in enumerate(respostas_corretas, 1):
            resposta_user = respostas_usuario.get(i, '')
            correta = resposta_user.lower() == resposta_correta.lower()
            if correta:
                acertos += 1
            resultado[str(i)] = {
                'correta': correta,
                'esperada': resposta_correta,
                'usuario': resposta_user
            }
        
        percentual = (acertos / total * 100) if total > 0 else 0
        xp_ganho = int(percentual * 5)
        
        # Salvar submissao
        submissao = CTestSubmissao(
            usuario_id=session['usuario_id'],
            texto_id=texto.id,
            respostas=respostas_usuario,
            resultado=resultado,
            acertos=acertos,
            total=total,
            percentual=percentual,
            xp_ganho=xp_ganho
        )
        db.session.add(submissao)
        
        # Atualizar estatisticas do usuario
        usuario = Usuario.query.get(session['usuario_id'])
        if hasattr(usuario, 'xp_total'):
            usuario.xp_total = (usuario.xp_total or 0) + xp_ganho
        db.session.commit()
        
        flash(f'C-Test concluído! Acertos: {acertos}/{total} ({percentual:.0f}%) - +{xp_ganho} XP', 'success')
        return redirect(url_for('ver_texto', id=texto.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar C-Test: {str(e)}', 'danger')
        return redirect(url_for('biblioteca'))


@app.route('/api/ctest-submit', methods=['POST'])
@login_required
def api_ctest_submit():
    """Endpoint alternativo para submissao de C-Test via API."""
    try:
        from models import CTestSubmissao
        data = request.get_json() or request.form
        texto_id = data.get('id') or data.get('texto_id')
        
        if not texto_id:
            return jsonify({'error': 'Texto não especificado'}), 400
        
        texto = Texto.query.get_or_404(int(texto_id))
        if texto.usuario_id != session.get('usuario_id'):
            return jsonify({'error': 'Acesso negado'}), 403
        
        respostas_usuario = {}
        respostas_corretas = texto.ctest_respostas or []
        
        for key, value in data.items():
            if key.startswith('gap_'):
                gap_num = int(key.replace('gap_', ''))
                respostas_usuario[gap_num] = value.strip()
        
        resultado = {}
        acertos = 0
        total = len(respostas_corretas)
        
        for i, resposta_correta in enumerate(respostas_corretas, 1):
            resposta_user = respostas_usuario.get(i, '')
            correta = resposta_user.lower() == resposta_correta.lower()
            if correta:
                acertos += 1
            resultado[str(i)] = {
                'correta': correta,
                'esperada': resposta_correta,
                'usuario': resposta_user
            }
        
        percentual = (acertos / total * 100) if total > 0 else 0
        xp_ganho = int(percentual * 5)
        
        submissao = CTestSubmissao(
            usuario_id=session['usuario_id'],
            texto_id=texto.id,
            respostas=respostas_usuario,
            resultado=resultado,
            acertos=acertos,
            total=total,
            percentual=percentual,
            xp_ganho=xp_ganho
        )
        db.session.add(submissao)
        
        usuario = Usuario.query.get(session['usuario_id'])
        if hasattr(usuario, 'xp_total'):
            usuario.xp_total = (usuario.xp_total or 0) + xp_ganho
        db.session.commit()
        
        return jsonify({
            'success': True,
            'acertos': acertos,
            'total': total,
            'percentual': percentual,
            'xp_ganho': xp_ganho
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/painel-flashcards')
@login_required
def painel_flashcards():
    user = Usuario.query.get(session['usuario_id'])
    textos = Texto.query.filter_by(usuario_id=user.id).all()
    
    # Construir estrutura esperada pelo template
    painel = []
    total_cards = 0
    total_pendentes = 0
    
    for texto in textos:
        cards = Flashcard.query.filter_by(texto_id=texto.id, usuario_id=user.id).all()
        if not cards:
            continue
            
        progressos = {}
        pendentes = 0
        
        for card in cards:
            prog = ProgressoFlashcard.query.filter_by(
                usuario_id=user.id, flashcard_id=card.id
            ).first()
            progressos[card.id] = prog
            
            if not prog or not prog.next_review:
                pendentes += 1
            else:
                # Garantir comparação segura entre datetimes
                next_review = prog.next_review
                now = datetime.now(timezone.utc)
                # Se next_review for naive, torná-lo aware
                if next_review.tzinfo is None:
                    next_review = next_review.replace(tzinfo=timezone.utc)
                if next_review <= now:
                    pendentes += 1
        
        total_cards += len(cards)
        total_pendentes += pendentes
        
        painel.append({
            'texto': texto,
            'cards': cards,
            'progressos': progressos,
            'pendentes': pendentes
        })
    
    return render_template('painel_flashcards.html', 
                          painel=painel,
                          total_cards=total_cards,
                          total_pendentes=total_pendentes)


@app.route('/texto/<int:id>/gerar-flashcards', methods=['POST'])
@login_required
def gerar_flashcards_do_texto(id):
    from processador import processar_texto_alemao
    
    texto = Texto.query.get_or_404(id)
    if texto.usuario_id != session.get('usuario_id'):
        abort(403)
    
    # Processar o texto para extrair flashcards
    resultado = processar_texto_alemao(texto.conteudo_original)
    
    # Limpar flashcards existentes e criar novos
    Flashcard.query.filter_by(texto_id=texto.id, usuario_id=session['usuario_id']).delete()
    
    usuario = get_current_user()
    flashcards_criados = 0
    
    # Coletar todas as palavras para criar distratores
    todas_palavras = [f['palavra'] for f in resultado.get('flashcards', [])]
    
    for card in resultado.get('flashcards', []):
        traducao, definicao = translate_with_definition(card['palavra'], src='de', tgt='pt')
        
        # Construir alternativas (4 opções de múltipla escolha)
        opcoes = []
        if traducao:
            opcoes.append(traducao)
        
        # Adicionar outras palavras como distratores
        distratores = [p for p in todas_palavras if p != card['palavra']][:3]
        opcoes.extend(distratores)
        
        # Limitar a 4 opções e embaralhar
        random.shuffle(opcoes)
        opcoes = opcoes[:4]
        
        alternativas_json = json.dumps(opcoes)
        
        fc = Flashcard(
            palavra_alemao=card['palavra'],
            traducao=traducao,
            tipo=card.get('tipo'),
            exemplo=card.get('exemplo'),
            alternativas=alternativas_json,
            usuario_id=usuario.id,
            texto_id=texto.id
        )
        db.session.add(fc)
        db.session.flush()
        flashcards_criados += 1
        
        # Criar progresso inicial com next_review definido
        progresso = ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=fc.id, stability=1.0, difficulty=5.0, next_review=datetime.now(timezone.utc))
        db.session.add(progresso)
    
    # Atualizar ctest_conteudo e ctest_respostas se não existirem
    if not texto.ctest_conteudo and 'ctest' in resultado:
        texto.ctest_conteudo = resultado['ctest']
        texto.ctest_respostas = resultado.get('ctest_respostas', [])
    
    db.session.commit()
    
    flash(f'Flashcards gerados com sucesso! {flashcards_criados} novos cartões.', 'success')
    return redirect(url_for('ver_texto', id=id))


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
# A inicialização do banco deve ser feita via init_db.py (executado pelo Dockerfile)
# Não fazer nada na importação para permitir testes e migrações

def init_db():
    """Inicializa o banco de dados e cria admin se necessário."""
    from models import Usuario
    
    with app.app_context():
        # Drop e recriar para garantir schema atualizado (SQLite)
        db.drop_all()
        db.create_all()
        
        # Criar admin se não existir
        admin = Usuario.query.filter_by(email='admin@wissio.com').first()
        if not admin:
            admin = Usuario(nome='Admin Wissio', email='admin@wissio.com')
            admin.set_senha('admin123')
            db.session.add(admin)
            db.session.commit()
        
        return Usuario.query.filter_by(email='admin@wissio.com').first()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)