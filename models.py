from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import enum
import secrets

db = SQLAlchemy()

class NivelCEFR(enum.Enum):
    A1 = 'A1'
    A2 = 'A2'
    B1 = 'B1'
    B2 = 'B2'
    C1 = 'C1'
    C2 = 'C2'

class ObjetivoAprendizagem(enum.Enum):
    VIAJAR = 'viajar'
    ESTUDOS = 'estudos'
    TRABALHO = 'trabalho'
    CULTURA = 'cultura'
    OUTROS = 'outros'

# O banco armazena os "values" (ex.: 'A1', 'estudos', 'viajar') em vez dos "names".
# `values_callable` precisa receber a FUNÇÃO (o SQLAlchemy a chama passando a classe do enum).
def _valores_enum(enum_cls):
    return [m.value for m in enum_cls]

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    objetivo = db.Column(db.Enum(ObjetivoAprendizagem), nullable=True)
    nivel_atual = db.Column(db.Enum(NivelCEFR), default=NivelCEFR.A1)
    meta_diaria_minutos = db.Column(db.Integer, default=5)
    meta_semanal_textos = db.Column(db.Integer, default=3)
    meta_flashcards_iniciais = db.Column(db.Integer, default=20)
    onboarding_concluido = db.Column(db.Boolean, default=False)
    email_verificado = db.Column(db.Boolean, default=False)
    token_verificacao = db.Column(db.String(100), nullable=True)
    token_verificacao_expira = db.Column(db.DateTime, nullable=True)
    tema_escuro = db.Column(db.Boolean, default=False)  # Preferência de tema
    
    # Campos para recuperação de senha
    token_reset_senha = db.Column(db.String(100), nullable=True)
    token_reset_expira = db.Column(db.DateTime, nullable=True)
    
    # Campos adicionais para funcionalidades completas
    streak_dias = db.Column(db.Integer, default=0)  # Dia consecutivo de revisão
    ultima_data_revisao = db.Column(db.DateTime, nullable=True)  # Última data de revisão
    xp_total = db.Column(db.Integer, default=0)  # Total de XP ganho
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    textos = db.relationship('Texto', backref='usuario', lazy=True, cascade='all, delete-orphan')
    flashcards = db.relationship('Flashcard', backref='usuario', lazy=True, cascade='all, delete-orphan')
    progresso_flashcards = db.relationship('ProgressoFlashcard', backref='usuario', lazy=True, cascade='all, delete-orphan')
    ctest_submissoes = db.relationship('CTestSubmissao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    estatisticas_diarias = db.relationship('EstatisticaDiaria', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_senha(self, senha):
        # scrypt: KDF resistente a força bruta (equivalente ao bcrypt),
        # explicito para nao depender do default da versao do Werkzeug.
        self.senha_hash = generate_password_hash(senha, method='scrypt')
    
    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    
    def gerar_token_verificacao(self):
        self.token_verificacao = secrets.token_urlsafe(32)
        self.token_verificacao_expira = datetime.now(timezone.utc) + timedelta(hours=24)
        db.session.commit()
    
    def verificar_token(self, token):
        # Garante que a comparação de datas seja feita entre objetos "aware"
        if self.token_verificacao == token and self.token_verificacao_expira:
            exp = self.token_verificacao_expira
            # Se o valor armazenado no banco não tem informação de timezone, assume UTC
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) < exp
        return False

    def gerar_token_reset(self):
        self.token_reset_senha = secrets.token_urlsafe(32)
        self.token_reset_expira = datetime.now(timezone.utc) + timedelta(hours=2)
        db.session.commit()

    def verificar_token_reset(self, token):
        if self.token_reset_senha == token and self.token_reset_expira:
            exp = self.token_reset_expira
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) < exp
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'objetivo': self.objetivo.value if self.objetivo else None,
            'nivel_atual': self.nivel_atual.value if self.nivel_atual else 'A1',
            'meta_diaria_minutos': self.meta_diaria_minutos,
            'meta_semanal_textos': self.meta_semanal_textos,
            'meta_flashcards_iniciais': self.meta_flashcards_iniciais,
            'onboarding_concluido': self.onboarding_concluido,
            'email_verificado': self.email_verificado,
            'tema_escuro': self.tema_escuro,
        }

class Texto(db.Model):
    __tablename__ = 'textos'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    conteudo_original = db.Column(db.Text, nullable=False)
    nivel = db.Column(db.Enum(NivelCEFR), nullable=False)
    ctest_conteudo = db.Column(db.Text, nullable=True)
    # Palavras completas de cada lacuna do C-Test, na ordem (fonte da verdade da correção)
    ctest_respostas = db.Column(db.JSON, nullable=True)
    categoria = db.Column(db.String(50), nullable=True)
    tempo_estimado_min = db.Column(db.Integer, nullable=True)
    imagem_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    flashcards = db.relationship('Flashcard', backref='texto', lazy=True, cascade='all, delete-orphan')
    ctest_submissoes = db.relationship('CTestSubmissao', backref='texto', lazy=True, cascade='all, delete-orphan')

class Flashcard(db.Model):
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    palavra_alemao = db.Column(db.String(100), nullable=False)
    traducao = db.Column(db.String(100), nullable=True)
    # Classe gramatical (Substantivo, Verbo, Adjetivo...) — exibida no verso do cartão
    tipo = db.Column(db.String(40), nullable=True)
    exemplo = db.Column(db.Text, nullable=True)
    # Lista JSON de quatro opções (uma correta)
    alternativas = db.Column(db.Text, nullable=True)
    # Armazena a última alternativa escolhida pelo usuário (texto)
    ultima_resposta = db.Column(db.Text, nullable=True)
    # Flag indicando se a última resposta foi correta
    resposta_correta = db.Column(db.Boolean, nullable=True)
    imagem_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    texto_id = db.Column(db.Integer, db.ForeignKey('textos.id'), nullable=True)
    progresso = db.relationship('ProgressoFlashcard', backref='flashcard', lazy=True, cascade='all, delete-orphan')

class RespostaFlashcard(db.Model):
    __tablename__ = 'respostas_flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=False)
    resposta_texto = db.Column(db.Text, nullable=True)
    correta = db.Column(db.Boolean, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='respostas_flashcards')
    flashcard = db.relationship('Flashcard', backref='respostas_flashcards')

class ProgressoFlashcard(db.Model):
    """Implementação simplificada do algoritmo FSRS para repetição espaçada"""
    __tablename__ = 'progresso_flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=False)
    
    # Parâmetros FSRS simplificados
    stability = db.Column(db.Float, default=0.0)  # Estabilidade da memória (dias)
    difficulty = db.Column(db.Float, default=5.0)  # Dificuldade do cartão (1-10)
    reps = db.Column(db.Integer, default=0)  # Número de revisões bem-sucedidas
    lapses = db.Column(db.Integer, default=0)  # Número de esquecimentos
    state = db.Column(db.Integer, default=0)  # 0=New, 1=Learning, 2=Review, 3=Relearning
    
    last_review = db.Column(db.DateTime, nullable=True)
    next_review = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    @property
    def state_label(self):
        return {0: 'Novo', 1: 'Aprendendo', 2: 'Revisão', 3: 'Reaprender'}.get(self.state, 'Novo')
    
    @property
    def pendente(self):
        """True quando nunca foi estudado ou quando a revisão já venceu."""
        if self.next_review is None:
            return True
        rev = self.next_review
        now = datetime.now(timezone.utc)
        if rev.tzinfo is None:
            rev = rev.replace(tzinfo=timezone.utc)
        return rev <= now
    
    __table_args__ = (db.UniqueConstraint('usuario_id', 'flashcard_id', name='uq_usuario_flashcard'),)

class CTestSubmissao(db.Model):
    __tablename__ = 'ctest_submissoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    texto_id = db.Column(db.Integer, db.ForeignKey('textos.id'), nullable=False)
    respostas = db.Column(db.JSON, nullable=False)  # {posicao: resposta_usuario}
    resultado = db.Column(db.JSON, nullable=False)  # {posicao: {correta: bool, esperada: str, usuario: str}}
    acertos = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    percentual = db.Column(db.Float, default=0.0)
    xp_ganho = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class TranslationCache(db.Model):
    __tablename__ = 'translation_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    src_text = db.Column(db.Text, nullable=False, unique=True)
    src_lang = db.Column(db.String(5), nullable=False)
    tgt_lang = db.Column(db.String(5), nullable=False)
    translated = db.Column(db.Text, nullable=False)
    definition = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'src_text': self.src_text,
            'src_lang': self.src_lang,
            'tgt_lang': self.tgt_lang,
            'translated': self.translated,
            'definition': self.definition,
        }


class EstatisticaDiaria(db.Model):
    __tablename__ = 'estatisticas_diarias'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    textos_lidos = db.Column(db.Integer, default=0)
    flashcards_revisados = db.Column(db.Integer, default=0)
    ctests_completados = db.Column(db.Integer, default=0)
    xp_ganho = db.Column(db.Integer, default=0)
    tempo_estudo_min = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (db.UniqueConstraint('usuario_id', 'data', name='uq_usuario_data'),)