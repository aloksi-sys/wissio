from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    
    # Relacionamentos
    textos = db.relationship('Texto', backref='usuario', lazy=True)
    flashcards = db.relationship('Flashcard', backref='usuario', lazy=True)

class Texto(db.Model):
    __tablename__ = 'textos'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    conteudo_original = db.Column(db.Text, nullable=False)
    nivel = db.Column(db.String(10), nullable=False) # A1, A2, B1, B2, etc.
    ctest_conteudo = db.Column(db.Text, nullable=True) # Texto com as lacunas salvas
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    flashcards = db.relationship('Flashcard', backref='texto', lazy=True)

class Flashcard(db.Model):
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    palavra_alemao = db.Column(db.String(100), nullable=False)
    traducao = db.Column(db.String(100), nullable=True) # Pode ser preenchida/editada pelo aluno
    exemplo = db.Column(db.Text, nullable=True)
    revisado = db.Column(db.Boolean, default=False) # Para o progresso do aluno
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    texto_id = db.Column(db.Integer, db.ForeignKey('textos.id'), nullable=True)