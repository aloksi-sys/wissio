# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e\flashcard_flow.spec.js >> Fluxo completo de flashcards
- Location: e2e\flashcard_flow.spec.js:11:1

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: page.fill: Test timeout of 120000ms exceeded.
Call log:
  - waiting for locator('input[name="nome"]')

```

# Test source

```ts
  1  | // e2e/flashcard_flow.spec.js
  2  | // Playwright end‑to‑end test validating o fluxo completo de flashcards:
  3  | // 1. Cadastro
  4  | // 2. Onboarding (objetivo + plano)
  5  | // 3. Criação de texto → geração automática de flashcards
  6  | // 4. Resposta a um flashcard → verificação de correção
  7  | // 5. Revisão (FSRS) automática
  8  | 
  9  | const { test, expect } = require('@playwright/test');
  10 | 
  11 | test('Fluxo completo de flashcards', async ({ page }) => {
  12 |   test.setTimeout(120000); // 2 min timeout to allow processing
  13 |   // 1. Cadastro
  14 |   await page.waitForLoadState('networkidle'); // after navigation
  15 | 
> 16 |   await page.fill('input[name="nome"]', 'E2E User');
     |              ^ Error: page.fill: Test timeout of 120000ms exceeded.
  17 |   await page.fill('input[name="email"]', 'e2e@example.com');
  18 |   await page.fill('input[name="senha"]', 'senha123');
  19 |   await page.fill('input[name="confirmar_senha"]', 'senha123');
  20 |   // CSRF token is in hidden input
  21 |   const csrf = await page.getAttribute('input[name="csrf_token"]', 'value');
  22 |   await page.fill('input[name="csrf_token"]', csrf);
  23 |   await page.waitForNavigation(); // ensure page load after submit
  24 | 
  25 |   await expect(page).toURL(/dashboard/);
  26 | 
  27 |   // 2. Onboarding – objetivo
  28 |   await page.goto('http://localhost:5000/onboarding/objetivos');
  29 |   const csrfObj = await page.getAttribute('input[name="csrf_token"]', 'value');
  30 |   await page.fill('input[name="csrf_token"]', csrfObj);
  31 |   await page.check('input[value="estudos"]');
  32 |   await page.waitForNavigation(); // ensure page load after submit
  33 | 
  34 |   await expect(page).toURL(/onboarding\/plano/);
  35 | 
  36 |   // 3. Onboarding – plano
  37 |   const csrfPlano = await page.getAttribute('input[name="csrf_token"]', 'value');
  38 |   await page.fill('input[name="csrf_token"]', csrfPlano);
  39 |   await page.fill('input[name="meta_diaria_minutos"]', '10');
  40 |   await page.fill('input[name="meta_semanal_textos"]', '5');
  41 |   await page.fill('input[name="meta_flashcards_iniciais"]', '30');
  42 |   await page.selectOption('select[name="nivel_atual"]', 'A1');
  43 |   await page.waitForNavigation(); // ensure page load after submit
  44 | 
  45 |   await expect(page).toURL(/dashboard/);
  46 | 
  47 |   // 4. Cria novo texto
  48 |   await page.goto('http://localhost:5000/novo-texto');
  49 |   const csrfTexto = await page.getAttribute('input[name="csrf_token"]', 'value');
  50 |   await page.fill('input[name="csrf_token"]', csrfTexto);
  51 |   await page.fill('input[name="titulo"]', 'Teste E2E');
  52 |   await page.fill('textarea[name="conteudo"]', 'Ich lebe in Berlin. Die Stadt ist klein.');
  53 |   await page.waitForNavigation(); // ensure page load after submit
  54 | 
  55 |   await expect(page).toURL(/texto\/\d+/);
  56 | 
  57 |   // 5. Vai para flashcards do texto
  58 |   const flashcardsLink = await page.$('a[href*="/flashcards"]');
  59 |   await flashcardsLink.click();
  60 |   await expect(page).toURL(/flashcards/);
  61 | 
  62 |   // 6. Responde ao primeiro flashcard (assume que há botões com data-alternativa)
  63 |   const primeiraBotao = await page.locator('button[data-alternativa]').first();
  64 |   await primeiraBotao.click();
  65 |   // Verifica feedback visual (classe .correta ou .incorreta)
  66 |   await expect(primeiraBotao).toHaveClass(/correta|incorreta/);
  67 | });
  68 | 
```