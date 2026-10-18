# DEPLOY.md

## Deploy da aplicação Wissio

Esta seção descreve como colocar a aplicação em produção usando Docker. O fluxo pode ser adaptado para Render, Railway, Fly.io, ou um VPS tradicional.

---

### 1️⃣ Pré‑requisitos
- **Docker** (versão 24 ou superior). 
- **Conta Supabase** (ou outro provedor PostgreSQL) para o banco de produção. Crie um banco e copie a URI no formato:
  ```
  postgresql://USER:PASSWORD@HOST:PORT/DATABASE
  ```
- **Variáveis de ambiente** (definidas no serviço de nuvem ou no Docker Compose):
  - `SECRET_KEY` – chave secreta aleatória (ex.: `openssl rand -hex 32`).
  - `DATABASE_URL` – URI do PostgreSQL ou omitido para uso de SQLite local.
  - `FLASK_ENV` – `production` para desativar debug.

---

### 2️⃣ Build da imagem Docker
```bash
# No diretório raiz do projeto
docker build -t wissio-app:latest .
```
A imagem usa **python:3.12‑slim**, instala dependências a partir de `requirements.txt` e expõe a porta 5000.

---

### 3️⃣ Execução local (modo desenvolvimento) 
```bash
# Opcional: usar SQLite local (padrão)
# Se quiser usar o Supabase, exporte a URL antes de iniciar
export DATABASE_URL=postgresql://USER:PASS@HOST:5432/dbname
export SECRET_KEY=$(openssl rand -hex 32)
export FLASK_ENV=development   # habilita hot‑reload

docker run -p 5000:5000 \
    -e DATABASE_URL=$DATABASE_URL \
    -e SECRET_KEY=$SECRET_KEY \
    -e FLASK_ENV=$FLASK_ENV \
    wissio-app
```
Acesse `http://localhost:5000`.

---

### 4️⃣ Deploy em Render (exemplo)
1. Crie um **New Web Service** → **Docker**.
2. No campo *Dockerfile path* indique `Dockerfile` (padrão).
3. Defina as variáveis de ambiente:
   - `SECRET_KEY` – valor gerado.
   - `DATABASE_URL` – a URL do Supabase.
   - `FLASK_ENV=production`.
4. Salve e aguarde o build.
5. Quando o deploy terminar, a URL fornecida será a sua aplicação.

---

### 5️⃣ Deploy em Railway (exemplo) 
1. Crie um novo projeto e selecione *Add Service* → *Docker*.
2. Conecte seu repositório (GitHub) e escolha a branch `main`.
3. Em *Variables*, adicione:
   - `SECRET_KEY` – valor aleatório.
   - `DATABASE_URL` – URL do PostgreSQL gerado pelo Railway ou Supabase.
   - `FLASK_ENV=production`.
4. Clique em *Deploy*; Railway fará o build e expondrá a porta 5000.

---

### 6️⃣ Migrações de banco em produção
Após o container estar rodando, execute as migrações dentro do container (ou via CLI remota):
```bash
# Se o container já está rodando, abra um shell nele
docker exec -it <container_id> /bin/sh

# Dentro do container
flask db upgrade
```
Isso criará as tabelas, inclusive `respostas_flashcards`.

---

### 7️⃣ Estratégia de atualização
1. **Atualize o código** (push no repositório). 
2. **Render/Railway** redeploya automaticamente. 
3. **Execute `flask db upgrade`** novamente para aplicar novas migrações.

---

## 📦 Dicas de produção
- **HTTPS** – Use o domínio fornecido pela plataforma ou configure um proxy (NGINX, Caddy) que faça TLS termination. 
- **Escala** – As containers são stateless; o banco deve permanecer externo (Supabase). 
- **Logs** – As plataformas já capturam `stdout`/`stderr`. Para persistir logs, configure um serviço externo (Papertrail, Logtail). 
- **Backup do banco** – Supabase tem snapshots automáticos; para outra instância PostgreSQL, habilite pg_dump regular.

---

## 🛡️ Segurança
- Nunca commite o `.env` nem a `SECRET_KEY`. Eles já estão listados em `.gitignore`. 
- Use `CSRFProtect` (já habilitado). 
- As rotas sensíveis exigem `login_required`. 
- O `DATABASE_URL` deve usar SSL (`?sslmode=require` quando aplicável).

---

## 📚 Referências
- Docker: https://docs.docker.com/
- Flask‑Migrate: https://flask-migrate.readthedocs.io/
- Supabase: https://supabase.com/
- Render: https://render.com/docs
- Railway: https://railway.app/docs

---

*Este documento pode ser expandido com instruções específicas de cada provedor.*
