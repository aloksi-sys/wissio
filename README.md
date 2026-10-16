# WISSIO - Deutsche Plattform

Plataforma digital para aprendizagem de alemão com textos contextualizados, flashcards inteligentes (FSRS), exercícios C-Test e acompanhamento de progresso.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Cost](https://img.shields.io/badge/Cost-R$0-brightgreen.svg)

## Funcionalidades Implementadas

### Autenticação & Onboarding
- Cadastro e login seguro com hash de senha (bcrypt via Werkzeug)
- Proteção CSRF em todos os formulários
- Onboarding em 2 etapas: definição de objetivo + plano de estudos personalizado
- Sessões seguras (HttpOnly, SameSite, expiração configurável)

### Textos & Processamento NLP
- Inserção de textos em alemão com título e categoria
- Classificação automática de nível CEFR (A1–C1) via heurística de tamanho médio de palavra (spaCy)
- Extração automática de flashcards (substantivos e verbos lematizados + frase de exemplo)
- Geração de C-Test (lacunas em cada 2ª palavra > 3 chars)
- Estimativa de tempo de leitura

### Flashcards & Repetição Espaçada (FSRS)
- Revisão gamificada: múltipla escolha + completar lacuna
- Algoritmo FSRS simplificado (stability, difficulty, reps, lapses, state)
- 4 botões de avaliação: Novamente / Difícil / Bom / Fácil
- Persistência de progresso por usuário + flashcard
- XP e estatísticas diárias

### C-Test Interativo
- Preenchimento de lacunas com inputs inline
- Correção flexível (case-insensitive, match de raiz)
- Feedback imediato com acertos/erros e XP
- Histórico de submissões salvo

### Dashboard & Progresso
- Cards de estatísticas: textos, flashcards, streak (dias consecutivos), XP total
- Gráfico semanal (Chart.js): XP, textos lidos, flashcards revisados
- Próximas revisões pendentes (próximas 24h)
- Ações rápidas para navegação

### Perfil & Configurações
- Edição de nome, e-mail, nível CEFR, objetivo
- Alteração de senha com verificação da atual
- Ajuste de metas diárias/semanais
- Zona de perigo (exclusão de conta - a implementar)

### Biblioteca
- Listagem de textos do usuário com cards visuais
- Busca por título/conteúdo
- Filtros por nível CEFR e categoria
- Estados vazios e loading

### Segurança
- Senhas hasheadas (nunca em texto puro)
- SECRET_KEY via variável de ambiente
- CSRF Protection (Flask-WTF)
- IDOR protection (verificação de ownership em todas rotas)
- Cookies seguros em produção
- Validação de entrada server-side
- Debug mode desabilitado em produção

## Stack Tecnológica

| Camada | Tecnologia |
|--------|------------|
| Backend | Flask 3.1, Python 3.10+ |
| ORM | SQLAlchemy 2.0 + Flask-SQLAlchemy |
| Migrações | Flask-Migrate (Alembic) |
| NLP | spaCy 3.8 + `de_core_news_sm` |
| Auth | Sessões Flask + Werkzeug Security |
| CSRF | Flask-WTF |
| Frontend | Bootstrap 5.3, Chart.js, JS Vanilla |
| Deploy | Gunicorn, Render (web) + Supabase (DB) |

## Instalação Local

### Pré-requisitos
- Python 3.10+
- Git

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/aloksi-sys/wissio.git
cd wissio

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instale dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com seus valores (SECRET_KEY, DATABASE_URL)

# 5. Inicialize o banco
python -m flask db upgrade
# Ou para criar do zero: python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 6. Execute
python app.py
# Acesse http://localhost:5000
```

### Variáveis de Ambiente (.env)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `FLASK_ENV` | Ambiente (`development` ou `production`) | `development` |
| `SECRET_KEY` | Chave secreta para sessões/CSRF (32+ chars aleatórios) | `sua-chave-secreta-aqui` |
| `DATABASE_URL` | URI do banco (SQLite local ou PostgreSQL) | `sqlite:///wissio.db` |

## Deploy Gratuito (Custo Zero)

### Arquitetura
```
┌─────────────┐     HTTPS      ┌─────────────┐
│  Usuário    │ ──────────────▶ │   Render    │
│  (Browser)  │ ◀────────────── │  (Web App)  │
└─────────────┘                 └──────┬──────┘
                                       │
                                       │ PostgreSQL (SSL)
                                       ▼
                                ┌─────────────┐
                                │  Supabase   │
                                │ (PostgreSQL)│
                                │  Free Tier  │
                                └─────────────┘
```

### 1. Supabase (Banco de Dados)
1. Acesse https://supabase.com e crie conta gratuita
2. New Project → escolha região próxima → anote a senha do banco
3. Vá em Settings → Database → Connection pooling → **Transaction** mode
4. Copie a **Connection String (URI)**:  
   `postgresql://postgres:[SUA_SENHA]@db.[PROJECT].supabase.co:5432/postgres`
5. (Opcional) Em SQL Editor, rode: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`

### 2. Render (Hospedagem Web)
1. Acesse https://render.com e crie conta gratuita
2. New → Web Service → Conecte seu repositório GitHub
3. Configure:
   - **Name**: `wissio`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python -m flask db upgrade`
   - **Start Command**: `gunicorn app:app`
4. Environment Variables (Settings → Environment):
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = *Generate* (botão Generate do Render)
   - `DATABASE_URL` = *cole a URI do Supabase*
5. Create Web Service → aguarde build e deploy

### 3. Validação Pós-Deploy
- Acesse a URL pública: `https://wissio.onrender.com`
- Teste: Cadastro → Onboarding → Inserir Texto → Flashcards → C-Test → Dashboard
- Verifique se dados persistem após novo deploy (push no GitHub)

## Limitações dos Planos Gratuitos

| Serviço | Limite | Impacto |
|---------|--------|---------|
| Render Web | Spin-down após 15min inativo | Cold start ~30s na primeira requisição |
| Render Web | 100 GB/mês bandwidth | Suficiente para uso moderado |
| Supabase | 500 MB database | ~50k textos/flashcards |
| Supabase | Pausa após 7 dias inativo | Reativar manual no painel |
| Supabase | 2 GB bandwidth/mês | Suficiente para texto |

## Estrutura do Projeto

```
wissio/
├── app.py                 # Aplicação Flask principal
├── models.py              # Modelos SQLAlchemy
├── processador.py         # NLP com spaCy (alemão)
├── requirements.txt       # Dependências Python
├── render.yaml            # Config deploy Render
├── .env.example           # Template variáveis ambiente
├── migrations/            # Migrações Alembic
├── instance/              # SQLite local (ignorado no git)
├── templates/             # Templates Jinja2
│   ├── base.html
│   ├── index.html
│   ├── cadastro.html
│   ├── login.html
│   ├── onboarding_objetivos.html
│   ├── onboarding_plano.html
│   ├── textos.html
│   ├── novo_texto.html
│   ├── ver_texto.html
│   ├── flashcards.html
│   ├── dashboard.html
│   ├── perfil.html
│   └── biblioteca.html
└── static/                # (Opcional) CSS/JS/imagens locais
```

## Testes

```bash
# Instalar pytest
pip install pytest pytest-cov

# Executar testes (quando implementados)
pytest tests/ -v --cov=app --cov=models --cov=processador
```

### Cenários de Teste Cobertos (Manuais)
- [x] Cadastro válido e inválido (e-mail duplicado, senha curta, senhas diferentes)
- [x] Login válido e inválido
- [x] Logout limpa sessão
- [x] Proteção de rotas privadas (redirect para login)
- [x] Isolamento de dados entre usuários (IDOR)
- [x] Inserção de texto com processamento NLP
- [x] Geração de flashcards e C-Test
- [x] Visualização de texto (abas Original / C-Test)
- [x] Submissão e correção de C-Test
- [x] Revisão de flashcards com FSRS
- [x] Persistência de progresso (recarregar página)
- [x] Dashboard com estatísticas
- [x] Perfil: editar dados, alterar senha, metas
- [x] Biblioteca com busca e filtros
- [x] CSRF tokens em todos forms
- [x] Layout responsivo (mobile/tablet/desktop)

## Desenvolvimento

### Adicionar Nova Migração
```bash
# Após alterar models.py
python -m flask db migrate -m "Descrição da mudança"
python -m flask db upgrade
```

### Processador Linguístico
O arquivo `processador.py` usa spaCy (`de_core_news_sm`) para:
- Tokenização e lematização
- POS tagging (substantivos, verbos)
- Classificação heurística CEFR (tamanho médio de palavra)
- Geração de C-Test (lacunas em palavras alternadas)

Fallback: se modelo não carregar, usa split simples.

### Estilos CSS
Usa Bootstrap 5.3 via CDN + CSS customizado nos templates. Cores WISSIO:
- Primária: `#0d6efd` (Bootstrap primary)
- Sucesso: `#198754`
- Aviso: `#ffc107`
- Perigo: `#dc3545`
- Info: `#0dcaf0`

## Documentação do Projeto Original

Baseado no trabalho acadêmico: **WISSIO DEUTSCHE PLATTFORM**  
Curso: Técnico em Informática Integrado ao Ensino Médio  
Instituição: CEMI - Gama/DF, 2026

Referências teóricas:
- C-Test: Eckes & Grotjahn (2006), McKay et al. (2021)
- Repetição espaçada: Kim & Webb (2023)
- Leitura extensiva: Sangers et al. (2025), Zhu et al. (2024)
- Memorização visual: Zhang, Sala & Gobet (2025)

## Roadmap / Melhorias Futuras

- [ ] Recuperação de senha por e-mail
- [ ] Compartilhamento de textos entre usuários
- [ ] Textos públicos da comunidade
- [ ] Modo offline (Service Worker + IndexedDB)
- [ ] Exportação Anki (.apkg)
- [ ] TTS (Text-to-Speech) para pronúncia
- [ ] Gamificação: conquistas, níveis, leaderboard
- [ ] API REST para clientes móveis
- [ ] Testes automatizados (pytest + coverage > 80%)
- [ ] CI/CD (GitHub Actions)

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## Créditos

Desenvolvido por alunos do CEMI-Gama como projeto final de Téc. Informática.  
Orientação: Prof. Esp. Regimilton Luiz Rodrigues de Souza.

---

**Deploy URL (exemplo):** https://wissio.onrender.com  
**Repositório:** https://github.com/aloksi-sys/wissio