import json

import os, secrets
from datetime import datetime, date, timedelta, timezone
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from models import db, Usuario, Texto, Flashcard, ProgressoFlashcard, CTestSubmissao, EstatisticaDiaria, NivelCEFR, ObjetivoAprendizagem, RespostaFlashcard
from processador import processar_texto_alemao

app = Flask(__name__)

# Configurações de segurança
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configuração do banco de dados
# Em produção (Render/Supabase) a variável DATABASE_URL contém a URI do Postgres.
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///wissio.db')
# Compatibilidade: SQLAlchemy exige o prefixo postgresql:// (Render entrega postgres://)
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

# Se o driver postgresql:// padrão falhar por falta de psycopg2, tenta usar pg8000 ou ajusta o esquema
try:
    import psycopg2
except ImportError:
    # Se o psycopg2 não existir no ambiente, troca o driver para postgresql+pg8000://
    if _db_url.startswith('postgresql://'):
        _db_url = _db_url.replace('postgresql://', 'postgresql+pg8000://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações de sessão seguras
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# CSRF Protection
csrf = CSRFProtect(app)

db.init_app(app)
migrate = Migrate(app, db)

# ============================================================
# GARANTIA DE SCHEMA
# ============================================================

def _mapa_colunas_pendentes():
    """
    Colunas que podem faltar em bancos criados antes de uma atualização do schema.
    `db.create_all()` só cria tabelas novas — não altera tabelas existentes.
    """
    sqlite = db.engine.dialect.name == 'sqlite'
    texto_json = 'TEXT' if sqlite else 'JSON'
    return {
        'usuarios': [
            ('email_verificado', 'BOOLEAN', '0'),
            ('token_verificacao', 'VARCHAR(100)', None),
            ('token_verificacao_expira', 'TIMESTAMP', None),
            ('tema_escuro', 'BOOLEAN', '0'),
        ],
        'flashcards': [
            ('traducao', 'VARCHAR(100)', None),
            ('tipo', 'VARCHAR(40)', None),
            ('alternativas', 'TEXT', None),
    ('ultima_resposta', 'TEXT', None),
    ('resposta_correta', 'BOOLEAN', None),
        ],
        'textos': [
            ('ctest_respostas', texto_json, None),
        ],
    }


def _garantir_colunas():
    """Adiciona colunas ausentes sem apagar dados (bancos locais antigos)."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(db.engine)
        tabelas_existentes = set(inspector.get_table_names())
    except Exception:
        return

    for tabela, colunas in _mapa_colunas_pendentes().items():
        if tabela not in tabelas_existentes:
            continue
        for nome, tipo, padrao in colunas:
            # Confirma a lista a cada ALTER: se um falhar e cair no rollback,
            # os anteriores já ficaram gravados (um COMMIT por alteração).
            try:
                existentes = {c['name'] for c in inspect(db.engine).get_columns(tabela)}
            except Exception:
                break
            if nome in existentes:
                continue
            sql = f'ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}'
            if padrao is not None:
                sql += f' DEFAULT {padrao}'
            try:
                db.session.execute(text(sql))
                db.session.commit()
            except Exception:
                db.session.rollback()


# Cria as tabelas que não existirem ainda e completa colunas faltantes
# (idempotente, funciona em SQLite e PostgreSQL)
with app.app_context():
    try:
        db.create_all()
        _garantir_colunas()
    except Exception as _e:
        # Nunca impede o app de subir: em produção é melhor uma página com erro
        # do que o serviço inteiro fora do ar.
        print('[AVISO] Falha ao preparar o schema do banco:', _e)

# Constantes de cores da bandeira alemã
CORES_ALEMA = {
    'preto': '#000000',
    'vermelho': '#FF0000', 
    'ouro': '#FFCC00',
    'ouro_escuro': '#E6B800'
}

# ============================================================
# DECORATORS & HELPERS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Faça login para acessar esta página.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def email_verificado_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login', next=request.url))
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario and not usuario.email_verificado:
            flash('Verifique seu e-mail antes de continuar.', 'warning')
            return redirect(url_for('verificar_email'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'usuario_id' in session:
        return Usuario.query.get(session['usuario_id'])
    return None


def _reconstruir_respostas_ctest(ctest_salvo, conteudo_original):
    """
    Recupera as palavras completas de cada lacuna a partir do texto original.
    Usado apenas para textos criados antes de gravarmos as respostas.
    Percorre o texto original na ordem (cursor) para não desalinhar.
    """
    def _norm(s):
        return ''.join(c for c in (s or '') if c.isalnum()).lower()

    prefixos = []
    for word in (ctest_salvo or '').split():
        if '____' in word:
            prefixos.append(_norm(word.split('____')[0]))

    orig_norm, orig_raw = [], []
    for w in (conteudo_original or '').split():
        n = _norm(w)
        if n:
            orig_norm.append(n)
            orig_raw.append(w)

    respostas, cursor = [], 0
    for prefixo in prefixos:
        encontrada = ''
        for j in range(cursor, len(orig_norm)):
            if not prefixo or orig_norm[j].startswith(prefixo):
                encontrada = orig_raw[j]
                cursor = j + 1
                break
        respostas.append(encontrada)
    return respostas

@app.context_processor
def inject_globals():
    """Injeta o usuário atual e o tema em todos os templates."""
    usuario = get_current_user()
    tema_escuro = session.get('tema_escuro')
    if tema_escuro is None and usuario is not None:
        tema_escuro = usuario.tema_escuro
    return {
        'usuario': usuario,
        'tema_escuro': bool(tema_escuro),
    }

def atualizar_estatistica_diaria(usuario_id, **kwargs):
    """Atualiza ou cria estatística do dia atual."""
    hoje = date.today()
    stat = EstatisticaDiaria.query.filter_by(usuario_id=usuario_id, data=hoje).first()
    if not stat:
        stat = EstatisticaDiaria(usuario_id=usuario_id, data=hoje)
        db.session.add(stat)
    for key, value in kwargs.items():
        if hasattr(stat, key):
            current = getattr(stat, key) or 0
            setattr(stat, key, current + value)
    db.session.commit()

def gerar_token_verificacao():
    return secrets.token_urlsafe(32)

# Dicas de alemão para exibição aleatória
DICAS_ALEMAO = [
    {"titulo": "Artigos Definidos", "conteudo": "No alemão, os artigos definidos mudam conforme o caso: der (masc.), die (fem.), das (neut.), die (pl.). Ex: der Mann, die Frau, das Kind."},
    {"titulo": "Casos Gramaticais", "conteudo": "O alemão tem 4 casos: Nominativo (sujeito), Acusativo (objeto direto), Dativo (objeto indireto) e Genitivo (posse). Eles alteram artigos e adjetivos."},
    {"titulo": "Verbos Separáveis", "conteudo": "Muitos verbos alemães têm prefixos separáveis: aufstehen (levantar) → ich stehe auf. O prefixo vai para o final da frase."},
    {"titulo": "Palavras Compostas", "conteudo": "O alemão forma palavras longas combinando substantivos: Hauptbahnhof (estação principal) = Haupt + Bahnhof. Útil para expandir vocabulário."},
    {"titulo": "Pronúncia: 'ei' vs 'ie'", "conteudo": "'ei' soa como 'ai' em 'pai' (Beispiel), 'ie' soa como 'i' longo em 'vila' (spielen). Regra: segunda vogal é pronunciada."},
    {"titulo": "Substantivos com Maiúscula", "conteudo": "No alemão, TODOS os substantivos começam com letra maiúscula: das Buch, die Tür, der Tisch. Isso ajuda a identificá-los nos textos."},
    {"titulo": "Plural Irregular", "conteudo": "O plural alemão tem várias formas: -e (der Tag → die Tage), -er (das Kind → die Kinder), -n/-en (die Frau → die Frauen), ou mudança de vogal (der Vater → die Väter)."},
    {"titulo": "Preposições com Caso", "conteudo": "Algumas preposições exigem caso específico: mit + Dativo (mit dem Auto), für + Acusativo (für dich), während + Genitivo (während der Woche)."},
    {"titulo": "Falsos Cognatos", "conteudo": "Cuidado: 'bekommen' = receber (não 'tornar-se'), 'aktuell' = atual (não 'atual'), 'eventuell' = possivelmente (não 'eventualmente')."},
    {"titulo": "Números 21-99", "conteudo": "No alemão, diz-se unidade + 'und' + dezena: 21 = einundzwanzig, 34 = vierunddreißig, 99 = neunundneunzig. Ordem inversa do português."},
]

# ============================================================
# ROTAS PÚBLICAS
# ============================================================

@app.route('/')
def home():
    usuario = get_current_user()
    return render_template('index.html', usuario=usuario)

# --- AUTENTICAÇÃO ---

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        # Validações
        erros = []
        if not nome:
            erros.append('Nome é obrigatório.')
        if not email or '@' not in email:
            erros.append('E-mail válido é obrigatório.')
        if len(senha) < 6:
            erros.append('Senha deve ter pelo menos 6 caracteres.')
        if senha != confirmar_senha:
            erros.append('As senhas não conferem.')
        
        if Usuario.query.filter_by(email=email).first():
            erros.append('Este e-mail já está cadastrado!')
        
        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('cadastro.html', nome=nome, email=email), 400
        
        novo_usuario = Usuario(nome=nome, email=email)
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        
        session['usuario_id'] = novo_usuario.id
        session['usuario_nome'] = novo_usuario.nome
        session.permanent = True
        flash('Conta criada com sucesso! Bem-vindo ao WISSIO.', 'success')
        return redirect(url_for('onboarding_objetivos'))
    
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_senha(senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            session['tema_escuro'] = usuario.tema_escuro
            session.permanent = True
            flash(f'Bem-vindo de volta, {usuario.nome}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('E-mail ou senha incorretos.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('home'))

# ============================================================
# VERIFICAÇÃO DE E-MAIL
# ============================================================

@app.route('/verificar-email')
@login_required
def verificar_email():
    usuario = get_current_user()
    if usuario.email_verificado:
        flash('Seu e-mail já está verificado!', 'success')
        return redirect(url_for('home'))
    return render_template('verificar_email.html', usuario=usuario)

@app.route('/verificar-email/enviar', methods=['POST'])
@login_required
def enviar_verificacao_email():
    usuario = get_current_user()
    if usuario.email_verificado:
        return jsonify({'success': True, 'link': None, 'message': 'Seu e-mail já está verificado.'})
    
    usuario.gerar_token_verificacao()
    
    # Modo demonstração: sem servidor de e-mail real, retornamos o link para a tela.
    link_verificacao = url_for('confirmar_email', token=usuario.token_verificacao)
    
    return jsonify({'success': True, 'link': link_verificacao, 'message': 'Link gerado!'})

@app.route('/confirmar-email/<token>')
def confirmar_email(token):
    try:
        usuario = Usuario.query.filter_by(token_verificacao=token).first()
        if usuario and usuario.verificar_token(token):
            usuario.email_verificado = True
            usuario.token_verificacao = None
            usuario.token_verificacao_expira = None
            db.session.commit()
            flash('E-mail verificado com sucesso! Bem-vindo ao WISSIO.', 'success')
            return redirect(url_for('home'))
    except Exception as e:
        print('Erro na confirmação de email:', e)
        db.session.rollback()
    flash('Token inválido ou expirado. Solicite um novo link.', 'danger')
    return redirect(url_for('verificar_email'))

# ============================================================
# TEMA ESCURO / CLARO
# ============================================================

@app.route('/toggle-tema', methods=['POST'])
@login_required
def toggle_tema():
    usuario = get_current_user()
    usuario.tema_escuro = not usuario.tema_escuro
    db.session.commit()
    session['tema_escuro'] = usuario.tema_escuro
    return jsonify({'success': True, 'tema_escuro': usuario.tema_escuro})

# ============================================================
# FLASHCARDS POR TEXTO
# ============================================================

@app.route('/texto/<int:id>/flashcards')
@login_required
def flashcards_do_texto(id):
    usuario = get_current_user()
    texto = Texto.query.get_or_404(id)
    
    if texto.usuario_id != usuario.id:
        abort(403)
    
    flashcards = Flashcard.query.filter_by(texto_id=texto.id, usuario_id=usuario.id).all()
    
    # Buscar progresso de cada flashcard
    cards_data = []
    for fc in flashcards:
        prog = ProgressoFlashcard.query.filter_by(usuario_id=usuario.id, flashcard_id=fc.id).first()
        if not prog:
            prog = ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=fc.id)
            db.session.add(prog)
        cards_data.append({'flashcard': fc, 'progresso': prog})
    
    db.session.commit()
    
    return render_template('flashcards_texto.html', texto=texto, cards_data=cards_data)


@app.route('/texto/<int:id>/flashcards/gerar', methods=['POST'])
@login_required
def gerar_flashcards_do_texto(id):
    """Gera flashcards para um texto já existente (ou completa os que faltam)."""
    usuario = get_current_user()
    texto = Texto.query.get_or_404(id)
    
    if texto.usuario_id != usuario.id:
        abort(403)
    
    resultado = processar_texto_alemao(texto.conteudo_original)
    candidatos = resultado.get('flashcards', [])
    
    ja_tem = {
        f.palavra_alemao.lower()
        for f in Flashcard.query.filter_by(texto_id=texto.id, usuario_id=usuario.id).all()
    }
    
    criados = 0
    novos = []
    for card in candidatos:
        if card['palavra'].lower() in ja_tem:
            continue
        fc = Flashcard(
            palavra_alemao=card['palavra'],
            traducao=card.get('traducao'),
            tipo=card.get('tipo'),
            exemplo=card['exemplo'],
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

# ============================================================
# DICAS DE ALEMÃO
# ============================================================

@app.route('/dicas-alemao')
@login_required
def dicas_alemao():
    import random
    dicas = random.sample(DICAS_ALEMAO, min(5, len(DICAS_ALEMAO)))
    return render_template('dicas_alemao.html', dicas=dicas)

@app.route('/api/dica-aleatoria')
@login_required
def api_dica_aleatoria():
    import random
    dica = random.choice(DICAS_ALEMAO)
    return jsonify(dica)

# ============================================================
# ONBOARDING
# ============================================================

@app.route('/onboarding/objetivos', methods=['GET', 'POST'])
@login_required
def onboarding_objetivos():
    usuario = get_current_user()
    if usuario.onboarding_concluido:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        objetivo = request.form.get('objetivo')
        if objetivo in [o.value for o in ObjetivoAprendizagem]:
            usuario.objetivo = ObjetivoAprendizagem(objetivo)
            # NÃO marca onboarding_concluido ainda - vai para o plano
            db.session.commit()
            flash('Objetivo definido! Vamos configurar seu plano de estudos.', 'success')
            return redirect(url_for('onboarding_plano'))
        else:
            flash('Selecione um objetivo válido.', 'danger')
    
    return render_template('onboarding_objetivos.html', objetivos=ObjetivoAprendizagem)

@app.route('/onboarding/plano', methods=['GET', 'POST'])
@login_required
def onboarding_plano():
    usuario = get_current_user()
    if not usuario.objetivo:
        return redirect(url_for('onboarding_objetivos'))
    # Só redireciona para home se JÁ tiver completado o onboarding (metas definidas)
    if usuario.onboarding_concluido:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            meta_diaria = int(request.form.get('meta_diaria_minutos', 5))
            meta_semanal = int(request.form.get('meta_semanal_textos', 3))
            meta_flashcards = int(request.form.get('meta_flashcards_iniciais', 20))
            nivel = request.form.get('nivel_atual', 'A1')
            
            usuario.meta_diaria_minutos = max(1, min(120, meta_diaria))
            usuario.meta_semanal_textos = max(1, min(20, meta_semanal))
            usuario.meta_flashcards_iniciais = max(5, min(100, meta_flashcards))
            usuario.nivel_atual = NivelCEFR(nivel) if nivel in [n.value for n in NivelCEFR] else NivelCEFR.A1
            usuario.onboarding_concluido = True  # Marca como concluído AQUI
            db.session.commit()
            
            flash('Plano de estudos configurado! Agora você pode começar.', 'success')
            return redirect(url_for('home'))
        except ValueError:
            flash('Valores inválidos. Tente novamente.', 'danger')
    
    return render_template('onboarding_plano.html', niveis=NivelCEFR, usuario=usuario)

# ============================================================
# TEXTOS
# ============================================================

@app.route('/textos')
@login_required
def lista_textos():
    usuario = get_current_user()
    
    # Filtros
    nivel_filtro = request.args.get('nivel')
    busca = request.args.get('busca', '').strip()
    categoria = request.args.get('categoria')
    
    query = Texto.query.filter_by(usuario_id=usuario.id)
    
    if nivel_filtro:
        query = query.filter(Texto.nivel == NivelCEFR(nivel_filtro))
    if categoria:
        query = query.filter(Texto.categoria == categoria)
    if busca:
        query = query.filter(
            db.or_(
                Texto.titulo.ilike(f'%{busca}%'),
                Texto.conteudo_original.ilike(f'%{busca}%')
            )
        )
    
    textos = query.order_by(Texto.created_at.desc()).all()
    
    # Categorias únicas do usuário
    categorias = db.session.query(Texto.categoria).filter_by(usuario_id=usuario.id).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]
    
    return render_template('textos.html', 
                         textos=textos, 
                         categorias=categorias,
                         niveis=NivelCEFR,
                         filtro_nivel=nivel_filtro,
                         filtro_categoria=categoria,
                         busca=busca)

@app.route('/novo-texto', methods=['GET', 'POST'])
@login_required
def novo_texto():
    usuario = get_current_user()
    
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()
        categoria = request.form.get('categoria', '').strip() or None
        
        if not titulo or not conteudo:
            flash('Título e conteúdo são obrigatórios.', 'danger')
            return render_template('novo_texto.html'), 400
        
        # Processamento inteligente com spaCy
        resultado = processar_texto_alemao(conteudo)
        
        # Estimar tempo de leitura (palavras / 200 palavras por minuto)
        palavras = len(conteudo.split())
        tempo_estimado = max(1, round(palavras / 200))
        
        # Salva o texto processado
        texto_obj = Texto(
            titulo=titulo,
            conteudo_original=conteudo,
            nivel=NivelCEFR(resultado['nivel']),
            ctest_conteudo=resultado['ctest'],
            ctest_respostas=resultado.get('ctest_respostas'),
            categoria=categoria,
            tempo_estimado_min=tempo_estimado,
            usuario_id=usuario.id
        )
        db.session.add(texto_obj)
        db.session.flush()
        
        # Gera e salva os Flashcards automáticos
        flashcards_objs = []
        for card in resultado['flashcards']:
            flashcard_obj = Flashcard(
                palavra_alemao=card['palavra'],
                traducao=card.get('traducao'),
                tipo=card.get('tipo'),
                exemplo=card['exemplo'],
                alternativas=json.dumps(card.get('alternativas') or []),
                usuario_id=usuario.id,
                texto_id=texto_obj.id
            )
            db.session.add(flashcard_obj)
            flashcards_objs.append(flashcard_obj)
        
        # Flush para obter IDs dos flashcards
        db.session.flush()
        
        # Cria registro de progresso FSRS para cada flashcard
        for flashcard_obj in flashcards_objs:
            progresso = ProgressoFlashcard(
                usuario_id=usuario.id,
                flashcard_id=flashcard_obj.id
            )
            db.session.add(progresso)
        
        db.session.commit()
        
        atualizar_estatistica_diaria(usuario.id, textos_lidos=1)
        
        flash('Texto processado com sucesso! Flashcards e C-Test gerados.', 'success')
        return redirect(url_for('ver_texto', id=texto_obj.id))
    
    return render_template('novo_texto.html')

@app.route('/texto/<int:id>')
@login_required
def ver_texto(id):
    usuario = get_current_user()
    texto = Texto.query.get_or_404(id)
    
    # IDOR protection
    if texto.usuario_id != usuario.id:
        abort(403)
    
    return render_template('ver_texto.html', texto=texto)

@app.route('/texto/<int:id>/ctest', methods=['POST'])
@login_required
def submeter_ctest(id):
    usuario = get_current_user()
    texto = Texto.query.get_or_404(id)
    
    if texto.usuario_id != usuario.id:
        abort(403)
    
    # Obter respostas do formulário
    respostas = {}
    for key, value in request.form.items():
        if key.startswith('gap_'):
            try:
                pos = int(key.replace('gap_', ''))
                respostas[pos] = value.strip()
            except ValueError:
                continue
    
    if not respostas:
        flash('Nenhuma resposta enviada.', 'warning')
        return redirect(url_for('ver_texto', id=id))
    
    # USA O C-TEST SALVO (não reprocessa) - fonte da verdade
    ctest_salvo = texto.ctest_conteudo

    # Prefixos (texto mostrado antes dos underscores) de cada lacuna, na ordem
    prefixos = []
    for word in ctest_salvo.split():
        if '____' in word:
            prefixos.append(word.split('____')[0] or '')

    total = len(prefixos)

    # Palavras completas esperadas: gravadas na criação do texto (mais confiável).
    # Para textos antigos, recaímos na reconstrução pelo texto original.
    respostas_salvas = texto.ctest_respostas
    if not respostas_salvas or not isinstance(respostas_salvas, list) or len(respostas_salvas) != total:
        respostas_salvas = _reconstruir_respostas_ctest(ctest_salvo, texto.conteudo_original)

    # Corrigir respostas usando o C-Test SALVO como referência
    def _normalizar(s):
        return ''.join(c for c in (s or '').lower() if c.isalnum())

    resultado_detalhado = {}
    acertos = 0

    for pos, resposta_usuario in respostas.items():
        # pos vem do template (1-based, sequencial nas lacunas encontradas)
        gap_idx = pos - 1
        if 0 <= gap_idx < total:
            esperada = respostas_salvas[gap_idx] or ''
            prefixo = (prefixos[gap_idx] or '').lower()
            resposta_norm = _normalizar(resposta_usuario)
            esperada_norm = _normalizar(esperada)
            prefixo_norm = _normalizar(prefixo)

            if not resposta_norm or not esperada_norm:
                correta = False
            elif resposta_norm == esperada_norm:
                # Usuário digitou a palavra completa
                correta = True
            elif prefixo_norm and esperada_norm.startswith(prefixo_norm) and resposta_norm == esperada_norm[len(prefixo_norm):]:
                # Usuário digitou apenas o complemento (2ª metade)
                correta = True
            elif prefixo_norm and _normalizar(prefixo + resposta_usuario) == esperada_norm:
                # Usuário digitou prefixo + complemento
                correta = True
            else:
                correta = False

            resultado_detalhado[pos] = {
                'correta': correta,
                'esperada': esperada,
                'usuario': resposta_usuario,
                'prefixo': prefixos[gap_idx]
            }
            if correta:
                acertos += 1

    percentual = round((acertos / total * 100) if total > 0 else 0, 1)
    xp_ganho = acertos * 5 + (10 if percentual >= 80 else 0)
    
    # Salvar submissão
    submissao = CTestSubmissao(
        usuario_id=usuario.id,
        texto_id=texto.id,
        respostas=respostas,
        resultado=resultado_detalhado,
        acertos=acertos,
        total=total,
        percentual=percentual,
        xp_ganho=xp_ganho
    )
    db.session.add(submissao)
    
    # Atualizar estatísticas
    atualizar_estatistica_diaria(usuario.id, ctests_completados=1, xp_ganho=xp_ganho)
    
    db.session.commit()
    
    flash(f'C-Test concluído! {acertos}/{total} acertos ({percentual}%) — +{xp_ganho} XP', 'success')
    return redirect(url_for('ver_texto', id=id))

# ============================================================
# FLASHCARDS
# ============================================================

@app.route('/flashcards')
@login_required
def flashcards():
    usuario = get_current_user()
    
    # Filtros opcionais (vindos do Painel de Flashcards):
    #   /flashcards?texto_id=7      -> só os cards de um texto
    #   /flashcards?ids=1,9,22      -> exatamente os cards marcados
    #   /flashcards?pendentes=1     -> só os que estão no devido hoje
    texto_id = request.args.get('texto_id', type=int)
    ids_param = (request.args.get('ids') or '').strip()
    somente_pendentes = request.args.get('pendentes') == '1'
    
    query = db.session.query(Flashcard, ProgressoFlashcard).outerjoin(
        ProgressoFlashcard, 
        db.and_(
            ProgressoFlashcard.flashcard_id == Flashcard.id,
            ProgressoFlashcard.usuario_id == usuario.id
        )
    ).filter(Flashcard.usuario_id == usuario.id)
    
    if ids_param:
        try:
            ids = [int(x) for x in ids_param.split(',') if x.strip()]
        except ValueError:
            ids = []
        if ids:
            query = query.filter(Flashcard.id.in_(ids))
        else:
            # Lista malformada -> não devolve tudo por engano
            return redirect(url_for('painel_flashcards'))
    elif texto_id:
        query = query.filter(Flashcard.texto_id == texto_id)
    
    if somente_pendentes:
        query = query.filter(
            db.or_(
                ProgressoFlashcard.id == None,          # ainda não estudado
                ProgressoFlashcard.next_review <= datetime.now(timezone.utc)
            )
        )
    
    flashcards_query = query.all()
    
    # Preparar dados para o template
    cards_data = []
    for fc, prog in flashcards_query:
        if not prog:
            prog = ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=fc.id)
            db.session.add(prog)
        cards_data.append({
            'flashcard': fc,
            'progresso': prog
        })
    
    db.session.commit()
    
    return render_template('flashcards.html', cards_data=cards_data, usuario=usuario)


@app.route('/painel-flashcards')
@login_required
def painel_flashcards():
    """Painel para escolher quais flashcards de cada texto serão revisados."""
    usuario = get_current_user()
    
    # Textos mais recentes primeiro, com a contagem de cards de cada um
    textos = Texto.query.filter_by(usuario_id=usuario.id).order_by(
        Texto.created_at.desc()).all()
    
    hoje = datetime.now(timezone.utc)
    total_cards = 0
    total_pendentes = 0
    painel = []
    
    for t in textos:
        cards = Flashcard.query.filter_by(texto_id=t.id, usuario_id=usuario.id).all()
        if not cards:
            painel.append({'texto': t, 'cards': [], 'pendentes': 0})
            continue
        
        ids = [c.id for c in cards]
        progressos = {
            p.flashcard_id: p for p in ProgressoFlashcard.query.filter(
                ProgressoFlashcard.usuario_id == usuario.id,
                ProgressoFlashcard.flashcard_id.in_(ids)
            ).all()
        }
        
        # Cartão pendente = nunca revisado OU vencido (próxima revisão <= agora)
        pendentes = 0
        for c in cards:
            p = progressos.get(c.id)
            if p is None or p.next_review is None or p.next_review <= hoje:
                pendentes += 1
        
        total_cards += len(cards)
        total_pendentes += pendentes
        painel.append({'texto': t, 'cards': cards, 'progressos': progressos, 'pendentes': pendentes})
    
    return render_template('painel_flashcards.html',
                           painel=painel,
                           total_cards=total_cards,
                           total_pendentes=total_pendentes)

@app.route('/flashcards/<int:id>/responder', methods=['POST'])
@csrf.exempt
@login_required
def responder_flashcard(id):
    usuario = get_current_user()
    flashcard = Flashcard.query.get_or_404(id)
    if flashcard.usuario_id != usuario.id:
        abort(403)
    resposta = request.form.get('resposta')
    correta = (resposta == flashcard.traducao)
    # persiste registro histórico
    registro = RespostaFlashcard(
        usuario_id=usuario.id,
        flashcard_id=flashcard.id,
        resposta_texto=resposta,
        correta=correta,
    )
    db.session.add(registro)
    db.session.commit()
    return jsonify({'correta': correta})

@login_required
@app.route('/flashcards/<int:id>/revisar', methods=['POST'])
def revisar_flashcard(id):
    usuario = get_current_user()
    flashcard = Flashcard.query.get_or_404(id)
    
    if flashcard.usuario_id != usuario.id:
        abort(403)
    
    facilidade = request.form.get('facilidade')  # 'again', 'hard', 'good', 'easy'
    
    progresso = ProgressoFlashcard.query.filter_by(
        usuario_id=usuario.id, 
        flashcard_id=flashcard.id
    ).first()
    
    if not progresso:
        progresso = ProgressoFlashcard(usuario_id=usuario.id, flashcard_id=flashcard.id)
        db.session.add(progresso)
    
    # Delegar lógica ao helper
    progresso = processar_revisao(progresso, facilidade)
    db.session.commit()
    atualizar_estatistica_diaria(usuario.id, flashcards_revisados=1, xp_ganho=5)
    return jsonify({'success': True, 'next_review': progresso.next_review.isoformat() if progresso.next_review else None})

      # Endereço `/flashcards/<int:id>/responder` antigo removido – histórico de respostas agora é armazenado na tabela `RespostaFlashcard`.
      # (mantido apenas para referência e evitar colisões de rota)

# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    usuario = get_current_user()
    
    # Estatísticas gerais
    total_textos = Texto.query.filter_by(usuario_id=usuario.id).count()
    total_flashcards = Flashcard.query.filter_by(usuario_id=usuario.id).count()
    total_ctests = CTestSubmissao.query.filter_by(usuario_id=usuario.id).count()
    
    # XP total
    xp_total = db.session.query(db.func.sum(CTestSubmissao.xp_ganho)).filter_by(usuario_id=usuario.id).scalar() or 0
    xp_total += db.session.query(db.func.sum(EstatisticaDiaria.xp_ganho)).filter_by(usuario_id=usuario.id).scalar() or 0
    
    # Dias consecutivos (streak)
    streak = calcular_streak(usuario.id)
    
    # Últimas 7 dias para gráfico
    dias_grafico = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        stat = EstatisticaDiaria.query.filter_by(usuario_id=usuario.id, data=d).first()
        dias_grafico.append({
            'data': d.strftime('%d/%m'),
            'xp': stat.xp_ganho if stat else 0,
            'textos': stat.textos_lidos if stat else 0,
            'flashcards': stat.flashcards_revisados if stat else 0,
        })
    
    # Próximas revisões
    proximas_revisoes = ProgressoFlashcard.query.filter(
        ProgressoFlashcard.usuario_id == usuario.id,
        ProgressoFlashcard.next_review != None,
        ProgressoFlashcard.next_review <= datetime.now(timezone.utc) + timedelta(days=1)
    ).order_by(ProgressoFlashcard.next_review).limit(10).all()
    
    return render_template('dashboard.html', 
                         usuario=usuario,
                         total_textos=total_textos,
                         total_flashcards=total_flashcards,
                         total_ctests=total_ctests,
                         xp_total=xp_total,
                         streak=streak,
                         dias_grafico=dias_grafico,
                         proximas_revisoes=proximas_revisoes)

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    usuario = get_current_user()
    
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'atualizar_perfil':
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip().lower()
            
            if not nome or not email:
                flash('Nome e e-mail são obrigatórios.', 'danger')
            elif Usuario.query.filter(Usuario.email == email, Usuario.id != usuario.id).first():
                flash('Este e-mail já está em uso.', 'danger')
            else:
                usuario.nome = nome
                usuario.email = email
                session['usuario_nome'] = nome
                db.session.commit()
                flash('Perfil atualizado com sucesso!', 'success')
        
        elif acao == 'alterar_senha':
            senha_atual = request.form.get('senha_atual')
            nova_senha = request.form.get('nova_senha')
            confirmar_senha = request.form.get('confirmar_senha')
            
            if not usuario.check_senha(senha_atual):
                flash('Senha atual incorreta.', 'danger')
            elif len(nova_senha) < 6:
                flash('Nova senha deve ter pelo menos 6 caracteres.', 'danger')
            elif nova_senha != confirmar_senha:
                flash('As senhas não conferem.', 'danger')
            else:
                usuario.set_senha(nova_senha)
                db.session.commit()
                flash('Senha alterada com sucesso!', 'success')
        
        elif acao == 'atualizar_metas':
            try:
                usuario.meta_diaria_minutos = int(request.form.get('meta_diaria_minutos', 5))
                usuario.meta_semanal_textos = int(request.form.get('meta_semanal_textos', 3))
                usuario.meta_flashcards_iniciais = int(request.form.get('meta_flashcards_iniciais', 20))
                db.session.commit()
                flash('Metas atualizadas!', 'success')
            except ValueError:
                flash('Valores inválidos.', 'danger')
        
        return redirect(url_for('perfil'))
    
    streak = calcular_streak(usuario.id)
    return render_template('perfil.html', usuario=usuario, niveis=NivelCEFR, objetivos=ObjetivoAprendizagem, streak=streak)

# ============================================================
# BIBLIOTECA PÚBLICA (textos de exemplo)
# ============================================================

@app.route('/biblioteca')
@login_required
def biblioteca():
    usuario = get_current_user()
    
    # Textos públicos (sem dono ou marcados como públicos) - por enquanto apenas do usuário
    # No futuro pode ter textos compartilhados
    nivel_filtro = request.args.get('nivel')
    busca = request.args.get('busca', '').strip()
    categoria = request.args.get('categoria')
    
    query = Texto.query.filter_by(usuario_id=usuario.id)
    
    if nivel_filtro:
        query = query.filter(Texto.nivel == NivelCEFR(nivel_filtro))
    if categoria:
        query = query.filter(Texto.categoria == categoria)
    if busca:
        query = query.filter(
            db.or_(
                Texto.titulo.ilike(f'%{busca}%'),
                Texto.conteudo_original.ilike(f'%{busca}%')
            )
        )
    
    textos = query.order_by(Texto.created_at.desc()).all()
    
    # Categorias únicas do usuário (usadas no filtro do template)
    categorias = db.session.query(Texto.categoria).filter_by(usuario_id=usuario.id).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]
    
    return render_template('biblioteca.html', 
                         textos=textos, 
                         categorias=categorias,
                         niveis=NivelCEFR,
                         filtro_nivel=nivel_filtro,
                         filtro_categoria=categoria,
                         busca=busca)

# ============================================================
# API / AJAX
# ============================================================

@app.route('/api/progresso')
@login_required
def api_progresso():
    usuario = get_current_user()
    
    # Dados para gráficos
    dias = 30
    dados = []
    for i in range(dias-1, -1, -1):
        d = date.today() - timedelta(days=i)
        stat = EstatisticaDiaria.query.filter_by(usuario_id=usuario.id, data=d).first()
        dados.append({
            'data': d.isoformat(),
            'xp': stat.xp_ganho if stat else 0,
            'textos': stat.textos_lidos if stat else 0,
            'flashcards': stat.flashcards_revisados if stat else 0,
            'ctests': stat.ctests_completados if stat else 0,
        })
    
    return jsonify(dados)

def calcular_streak(usuario_id):
    """Calcula dias consecutivos de atividade."""
    streak = 0
    hoje = date.today()
    for i in range(365):  # máximo 1 ano
        d = hoje - timedelta(days=i)
        stat = EstatisticaDiaria.query.filter_by(usuario_id=usuario_id, data=d).first()
        if stat and (stat.xp_ganho > 0 or stat.textos_lidos > 0 or stat.flashcards_revisados > 0 or stat.ctests_completados > 0):
            streak += 1
        else:
            if i == 0:  # hoje sem atividade, não quebra streak se ontem teve
                continue
            break
    return streak

# ============================================================
# PÁGINAS DE ERRO AMIGÁVEIS
# ============================================================

MENSAGENS_ERRO = {
    403: ('Acesso negado',
          'Este conteúdo pertence a outra conta. Verifique se você está logado com o usuário certo.'),
    404: ('Página não encontrada',
          'O endereço acessado não existe ou o conteúdo foi removido.'),
    500: ('Algo deu errado',
          'Ocorreu um erro inesperado no servidor. Tente novamente em alguns instantes.'),
}


def _render_erro(codigo):
    titulo, mensagem = MENSAGENS_ERRO.get(codigo, ('Erro', 'Não foi possível concluir sua solicitação.'))
    return render_template('erro.html', codigo=codigo, titulo=titulo, mensagem=mensagem), codigo


@app.errorhandler(403)
def erro_403(e):
    return _render_erro(403)


@app.errorhandler(404)
def erro_404(e):
    return _render_erro(404)


@app.errorhandler(500)
def erro_500(e):
    return _render_erro(500)

def processar_revisao(progresso, facilidade):
    """Aplica a lógica FSRS simplificada ao objeto ProgressoFlashcard.
    Retorna o objeto atualizado.
    """
    # Ensure defaults are set for transient objects
    if progresso.lapses is None:
        progresso.lapses = 0
    if progresso.stability is None:
        progresso.stability = 0.0
    if progresso.difficulty is None:
        progresso.difficulty = 5.0
    if progresso.reps is None:
        progresso.reps = 0
    if progresso.state is None:
        progresso.state = 0
    agora = datetime.now(timezone.utc)

    if facilidade == 'again':
        progresso.lapses += 1
        progresso.stability = 0.0
        progresso.difficulty = min(10, progresso.difficulty + 1)
        progresso.state = 1  # Learning
        progresso.next_review = agora + timedelta(minutes=10)
    elif facilidade == 'hard':
        progresso.difficulty = min(10, progresso.difficulty + 0.5)
        if progresso.state == 0:  # New
            progresso.stability = 0.5
            progresso.next_review = agora + timedelta(hours=6)
        elif progresso.state == 1:  # Learning
            progresso.stability *= 1.3
            progresso.next_review = agora + timedelta(days=progresso.stability)
        else:  # Review
            progresso.stability *= 1.2
            progresso.next_review = agora + timedelta(days=progresso.stability)
    elif facilidade == 'good':
        progresso.reps += 1
        if progresso.state == 0:  # New -> Review
            progresso.stability = 1.0
            progresso.state = 2
            progresso.next_review = agora + timedelta(days=1)
        elif progresso.state == 1:  # Learning -> Review
            progresso.stability = max(1.0, progresso.stability * 1.5)
            progresso.state = 2
            progresso.next_review = agora + timedelta(days=progresso.stability)
        else:  # Review
            progresso.stability *= 2.5
            progresso.next_review = agora + timedelta(days=progresso.stability)
    elif facilidade == 'easy':
        progresso.reps += 1
        progresso.difficulty = max(1, progresso.difficulty - 0.5)
        if progresso.state == 0:
            progresso.stability = 4.0
            progresso.state = 2
            progresso.next_review = agora + timedelta(days=4)
        else:
            progresso.stability *= 3.0
            progresso.next_review = agora + timedelta(days=progresso.stability)
    else:
        progresso.next_review = agora
    progresso.last_review = agora
    progresso.updated_at = agora
    return progresso


    app.run(debug=os.environ.get('FLASK_ENV') != 'production')