# SECURITY.md

## Segurança da aplicação Wissio

Esta página descreve como a aplicação lida com segurança e quais medidas devem ser mantidas pelos desenvolvedores e operadores.

---

### 1️⃣ Segurança nas dependências
- **Gerenciamento de dependências** – Todas as bibliotecas estão listadas em `requirements.txt`. Use o CI (`ruff` + `pytest`) para garantir que nenhuma vulnerabilidade conhecida seja introduzida.
- **Atualizações** – Periodicamente execute `pip list --outdated` e atualize dependências críticas (Flask, Werkzeug, SQLAlchemy).

---

### 2️⃣ Configurações sensíveis
- **`SECRET_KEY`** – Usada pelo Flask para assinar cookies e CSRF tokens. Deve ser uma string aleatória de 32 bytes ou mais. Não deve ser versionada; está incluída em `.gitignore`.
- **`DATABASE_URL`** – URI de conexão ao PostgreSQL (Supabase). Também não versionada.
- **Variáveis de ambiente** – São carregadas via `os.environ`. O `.env` local pode ser usado em desenvolvimento, mas NÃO deve ser comitado.

---

### 3️⃣ Proteção CSRF
- **Flask‑WTF CSRFProtect** está habilitado globalmente (`csrf = CSRFProtect(app)`).
- Todos os formulários HTML incluem `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- Requests AJAX enviam o token via header `X-CSRFToken` (exemplo incluído em `templates/flashcards.html`).

---

### 4️⃣ Autenticação e senhas
- **Hash de senha** – Utiliza `werkzeug.security.generate_password_hash` com o algoritmo `scrypt`, que oferece resistência a ataques de força‑bruta.
- **Verificação de senha** – `check_password_hash` compara de forma segura.
- **Bloqueio de conta** – Não implementado ainda; pode‑se adicionar limite de tentativas e bloqueio temporário.

---

### 5️⃣ Controle de acesso
- **Decoradores** – `login_required` protege rotas que exigem usuário autenticado.
- **`email_verificado_required`** garante que certas áreas só sejam acessíveis após verificação de e‑mail.
- **Verificação de propriedade** – Em cada recurso (`Flashcard`, `Texto`, etc.) há checagem `if recurso.usuario_id != usuario.id: abort(403)`.

---

### 6️⃣ Segurança do banco de dados
- **SQLAlchemy ORM** – Evita SQL injection ao usar parâmetros bind.
- **Enum** – Campos `NivelCEFR` e `ObjetivoAprendizagem` armazenam apenas valores pré‑definidos.
- **Unique constraints** – `uq_usuario_flashcard` impede múltiplos registros de progresso duplicados.
- **Migrações** – `flask db upgrade` aplica alterações de schema de forma controlada.

---

### 7️⃣ HTTPS e cabeçalhos de segurança
- Quando implantado em Render/Railway, o tráfego já é servido via HTTPS.
- Recomenda‑se usar um reverse‑proxy (NGINX, Caddy) que adicione cabeçalhos de segurança:
  ```
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  ```

---

### 8️⃣ Monitoramento e logs
- O Flask loga via `app.logger`. Configure o nível de log (`INFO` em produção) e encaminhe para um serviço externo (Papertrail, Logtail).
- Erros 500 são capturados por `@app.errorhandler(500)` que renderiza uma página amigável.

---

### 9️⃣ Auditoria de código
- **Revisões de Pull Request** – Sempre revise mudanças que afetam rotas, modelos ou lógica de autenticação.
- **Testes** – O CI roda `pytest -q`; inclua testes de segurança (ex.: tentativa de acessar recursos de outro usuário).

---

## 📋 Checklist de segurança para releases
- [ ] `SECRET_KEY` e `DATABASE_URL` configurados como variáveis de ambiente.
- [ ] Dependências atualizadas e sem vulnerabilidades críticas (`pip-audit`).
- [ ] Todas as rotas sensíveis protegidas por `login_required`.
- [ ] CSRF token presente em todos os formulários.
- [ ] Testes de acesso não autorizado (`assert 403`).
- [ ] `flask db upgrade` executado no ambiente de produção.
- [ ] Cabeçalhos de segurança aplicados no proxy ou CDN.
- [ ] Logs de erro monitorados.

---

*Este documento deve ser revisado periodicamente e atualizado com novas práticas ou alterações na arquitetura.*
