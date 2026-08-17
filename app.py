from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Usuario, Texto, Flashcard
from processador import processar_texto_alemao

app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave_secreta_wissio_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wissio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

# --- AUTENTICAÇÃO ---
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado!')
            return redirect(url_for('cadastro'))

        novo_usuario = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(novo_usuario)
        db.session.commit()

        session['usuario_id'] = novo_usuario.id
        session['usuario_nome'] = novo_usuario.nome
        return redirect(url_for('home'))

    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.senha == senha:
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            return redirect(url_for('home'))
        else:
            flash('E-mail ou senha incorretos.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- MÓDULO INTELIGENTE DE TEXTOS E C-TEST ---

@app.route('/textos')
def lista_textos():
    if 'usuario_id' not in session:
        flash('Faça login para ver seus textos.')
        return redirect(url_for('login'))
        
    textos = Texto.query.filter_by(usuario_id=session['usuario_id']).all()
    return render_template('textos.html', textos=textos)

@app.route('/novo-texto', methods=['GET', 'POST'])
def novo_texto():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']

        # Processamento inteligente com o spaCy em alemão!
        resultado = processar_texto_alemao(conteudo)

        # Salva o texto processado no banco
        texto_obj = Texto(
            titulo=titulo,
            conteudo_original=conteudo,
            nivel=resultado['nivel'],
            ctest_conteudo=resultado['ctest'],
            usuario_id=session['usuario_id']
        )
        db.session.add(texto_obj)
        db.session.commit()

        # Gera e salva os Flashcards automáticos
        for card in resultado['flashcards']:
            flashcard_obj = Flashcard(
                palavra_alemao=card['palavra'],
                exemplo=card['exemplo'],
                usuario_id=session['usuario_id'],
                texto_id=texto_obj.id
            )
            db.session.add(flashcard_obj)
        
        db.session.commit()

        return redirect(url_for('ver_texto', id=texto_obj.id))

    return render_template('novo_texto.html')

@app.route('/texto/<int:id>')
def ver_texto(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    texto = Texto.query.get_or_404(id)
    return render_template('ver_texto.html', texto=texto)

@app.route('/flashcards')
def flashcards():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    meus_flashcards = Flashcard.query.filter_by(usuario_id=session['usuario_id']).all()
    return render_template('flashcards.html', flashcards=meus_flashcards)

if __name__ == '__main__':
    app.run(debug=True)