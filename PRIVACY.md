# PRIVACY.md

## Política de Privacidade da aplicação Wissio

Esta política descreve como coletamos, usamos, armazenamos e protegemos os dados dos usuários da aplicação.

---

### 1️⃣ Dados coletados
| Tipo de dado | Descrição | Finalidade |
|--------------|-----------|------------|
| **Endereço de e‑mail** | Necessário para login, verificação de conta e comunicação (ex.: redefinição de senha). | Identificação única do usuário e comunicação. |
| **Nome** | Exibe o nome do usuário nas telas. | Personalização da UI. |
| **Objetivo de aprendizagem** | Valor enum (`viajar`, `estudos`, …). | Configura o plano de estudos. |
| **Nível CEFR** | Valor enum (`A1`‑`C2`). | Ajusta o nível de complexidade dos textos. |
| **Preferência de tema** (`tema_escuro`) | Booleano. | UI/UX personalizada. |
| **Estatísticas de uso** (`EstatisticaDiaria`) | Dados de atividade diária (texto lido, flashcards revisados, XP ganho). | Métricas de progresso e gamificação. |
| **Respostas de flashcards** (`RespostaFlashcard`) | Cada alternativa escolhida pelo usuário e o resultado (correta ou não). | Histórico de aprendizado e cálculo do algoritmo FSRS. |
| **Respostas de C‑Test** | Respostas enviadas no C‑Test. | Avaliação de compreensão de leitura. |

---

### 2️⃣ Como os dados são armazenados
- **Banco de dados** – Todos os dados estão armazenados em um banco PostgreSQL hospedado no Supabase (ou SQLite local para desenvolvimento). 
- **Criptografia em repouso** – Supabase fornece armazenamento criptografado por padrão.
- **Backups** – Supabase realiza snapshots automáticos diários.

---

### 3️⃣ Uso dos dados
- **Autenticação** – E‑mail + senha (hash scrypt). 
- **Personalização** – Exibir nome, tema e metas. 
- **Aprendizado adaptativo** – Histórico de respostas alimenta o algoritmo FSRS para agendar revisões. 
- **Estatísticas** – Exibir progresso ao usuário (XP, contagem de flashcards, etc.).

---

### 4️⃣ Compartilhamento de dados
- **Nenhum dado pessoal é compartilhado com terceiros**.
- **Serviços externos** – Apenas o Supabase (banco) e provedores de e‑mail (para envio de links de verificação, se habilitado) têm acesso.
- **Logs de servidor** – Contêm apenas informações de request (IP, user‑agent) e são retidos por no máximo 30 dias para diagnóstico.

---

### 5️⃣ Retenção e exclusão
- **Usuário pode solicitar exclusão** enviando e‑mail para `support@wissio.app`. A aplicação remove todos os registros associados ao usuário (contas, textos, flashcards, respostas, estatísticas). 
- **Retenção padrão** – Dados permanecem enquanto a conta estiver ativa. Backups podem conter cópias temporárias por até 7 dias.

---

### 6️⃣ Segurança dos dados
- **Transmissão** – Todas as comunicações são feitas via HTTPS (TLS 1.2+). 
- **Armazenamento** – Senhas são armazenadas como hash scrypt; nunca em texto puro. 
- **Controle de acesso** – Cada recurso verifica `usuario_id` antes de permitir acesso.
- **CSRF** – Protegido por `Flask‑WTF`. 
- **Limpeza de sessões** – `session.clear()` ao logout.

---

### 7️⃣ Direitos do usuário (GDPR/LGPD)
- **Acesso** – Usuário pode solicitar exportação dos seus dados (por contato). 
- **Correção** – Usuário pode atualizar nome, e‑mail e preferências nas telas de perfil. 
- **Apagamento** – Conforme item 5, o usuário pode solicitar remoção total da conta.
- **Portabilidade** – Dados podem ser entregues em formato JSON mediante solicitação.

---

### 8️⃣ Alterações nesta política
Esta política pode ser atualizada periodicamente. Alterações significativas serão comunicadas aos usuários via e‑mail ou banner na aplicação.

---

**Contato**
Para dúvidas ou solicitações relacionadas à privacidade, entre em contato pelo e‑mail `privacy@wissio.app`.
