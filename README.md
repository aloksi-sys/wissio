# Wissio – Aplicação de Flashcards de Alemão

## Visão geral
Esta aplicação Flask permite ao usuário:
- Criar textos em alemão e gerar automaticamente **flashcards** com alternativas de resposta.
- Responder a flashcards, armazenando cada tentativa na tabela **`respostas_flashcards`**.
- Revisar flashcards usando um algoritmo simplificado de repetição espaçada (FSRS).
- Visualizar estatísticas diárias, progresso e métricas CEFR.

A aplicação foi adaptada para rodar tanto localmente (SQLite) quanto em produção (Supabase/PostgreSQL) via a variável de ambiente `DATABASE_URL`.

---

## 📦 Requisitos
- **Python ≥3.12**
- **Docker** (opcional, para implantação containerizada)
- **Supabase** (ou outro PostgreSQL) para produção – configure a URL em `DATABASE_URL`.

---

## ⚙️ Configuração local
1. **Clone o repositório**
   ```bash
   git clone <repo-url>
   cd wissio
   ```

2. **Crie um ambiente virtual e instale dependências**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Variáveis de ambiente**
   ```bash
   cp .env.example .env   # copie e ajuste se necessário
   # Opcional: defina uma secret key personalizada
   export SECRET_KEY=$(openssl rand -hex 32)
   ```

4. **Banco de dados**
   - **Desenvolvimento (SQLite)** – padrão `sqlite:///wissio.db`.
   - **Produção** – exporte `DATABASE_URL=postgresql://user:pass@host:port/dbname`.

5. **Migrações**
   ```bash
   flask db upgrade   # cria todas as tabelas, incluindo respostas_flashcards
   ```

6. **Execute a aplicação**
   ```bash
   flask run       # ou: gunicorn --bind 0.0.0.0:5000 app:app
   ```
   Acesse em `http://127.0.0.1:5000`.

---

## 🐳 Docker
Um **Dockerfile** está incluído para facilitar o deploy.
```bash
# Build da imagem
docker build -t wissio-app .
# Executar
docker run -p 5000:5000 -e DATABASE_URL=sqlite:///wissio.db wissio-app
```

### 📦 Publicar no Docker Hub

1. Crie um repositório no Docker Hub (ex.: `username/wissio-app`).
2. No repositório GitHub, adicione os segredos:
   - `DOCKER_USERNAME` – seu usuário Docker Hub
   - `DOCKER_PASSWORD` – sua senha ou token de acesso
3. O workflow CI já faz login e push automaticamente ao fazer push na branch `main`.

Para publicar manualmente:

```bash
docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
docker tag wissio-app:latest $DOCKER_USERNAME/wissio-app:latest
docker push $DOCKER_USERNAME/wissio-app:latest
```


---

## 📈 CI / CD (GitHub Actions)
O workflow **`.github/workflows/ci.yml`** realiza:
1. **Checkout** do código.
2. **Setup** do Python 3.12.
3. **Instalação** das dependências.
4. **Lint** usando **ruff**.
5. **Testes** (`pytest`). Um banco SQLite temporário (`test.db`) é criado e descartado a cada execução.
6. **Build** da imagem Docker.
   (Opcional) Push para Docker Hub via segredos `DOCKER_USERNAME` e `DOCKER_PASSWORD`.

---

## 🧪 Testes
- **Unitários** – em `tests/` cobrem rotas, modelo `RespostaFlashcard`, processador CEFR e lógica de revisão.
- **E2E (Playwright)** – exemplo de fluxo completo (login → criação de texto → flashcards → responder → revisar).

Execute tudo localmente:
```bash
python -m pytest -q
```

---

## 📚 Documentação adicional
- **`DEPLOY.md`** – instruções detalhadas para deploy em Render, Railway ou outro provedor.
- **`SECURITY.md`** – política de segurança, gerenciamento de segredos e CSRF.
- **`PRIVACY.md`** – informações sobre coleta de dados (e‑mail, progresso) e conformidade GDPR.

---

## 🤝 Contribuição
1. Fork o repositório.
2. Crie uma branch para sua feature (`git checkout -b feature/nome`).
3. Rode os testes (`pytest`) e o lint (`ruff`).
4. Abra um Pull Request apontando para `main`.

---

## 📜 Licença
Este projeto está licenciado sob a **MIT License** – veja o arquivo `LICENSE`.
