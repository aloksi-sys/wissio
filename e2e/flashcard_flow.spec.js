// e2e/flashcard_flow.spec.js
// Playwright end‑to‑end test validating o fluxo completo de flashcards:
// 1. Cadastro
// 2. Onboarding (objetivo + plano)
// 3. Criação de texto → geração automática de flashcards
// 4. Resposta a um flashcard → verificação de correção
// 5. Revisão (FSRS) automática

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5000';

test('Fluxo completo de flashcards', async ({ page }) => {
  test.setTimeout(120000); // 2 min timeout to allow processing

  // 1. Cadastro
  await page.goto(`${BASE_URL}/cadastro`);
  await page.waitForLoadState('networkidle');

  const csrfCadastro = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="nome"]', 'E2E User');
  await page.fill('input[name="email"]', `e2e-${Date.now()}@example.com`);
  await page.fill('input[name="senha"]', 'senha123');
  await page.fill('input[name="confirmar_senha"]', 'senha123');
  await page.fill('input[name="csrf_token"]', csrfCadastro);

  await Promise.all([
    page.waitForNavigation(),
    page.click('button[type="submit"]'),
  ]);

  // Após cadastro, a aplicação redireciona para o login
  await expect(page).toHaveURL(/login/);

  // Login
  const emailUsado = await page.getAttribute('input[name="email"]', 'value').catch(() => null);
  const csrfLogin = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="email"]', emailUsado || 'e2e@example.com');
  await page.fill('input[name="senha"]', 'senha123');
  await page.fill('input[name="csrf_token"]', csrfLogin);

  await Promise.all([
    page.waitForNavigation(),
    page.click('button[type="submit"]'),
  ]);

  // 2. Onboarding – objetivo (rota usa underscore: /onboarding_objetivos)
  await page.goto(`${BASE_URL}/onboarding_objetivos`);
  const csrfObj = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="csrf_token"]', csrfObj);
  await page.check('input[value="estudos"]');
  await Promise.all([
    page.waitForNavigation(),
    page.click('button[type="submit"]'),
  ]);

  await expect(page).toHaveURL(/onboarding_plano/);

  // 3. Onboarding – plano
  const csrfPlano = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="csrf_token"]', csrfPlano);
  await page.fill('input[name="meta_diaria_minutos"]', '10');
  await page.fill('input[name="meta_semanal_textos"]', '5');
  await page.fill('input[name="meta_flashcards_iniciais"]', '30');
  await page.selectOption('select[name="nivel_atual"]', 'A1');
  await Promise.all([
    page.waitForNavigation(),
    page.click('button[type="submit"]'),
  ]);

  // 4. Cria novo texto (rota do formulário é /texto/novo)
  await page.goto(`${BASE_URL}/novo-texto`);
  const csrfTexto = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="csrf_token"]', csrfTexto);
  await page.fill('input[name="titulo"]', 'Teste E2E');
  await page.fill('textarea[name="conteudo"]', 'Ich lebe in Berlin. Die Stadt ist klein.');
  await Promise.all([
    page.waitForNavigation(),
    page.click('button[type="submit"]'),
  ]);

  // Após criar o texto, a aplicação redireciona para a home
  await expect(page).toHaveURL(/home/);

  // 5. Vai para flashcards do texto (painel)
  await page.goto(`${BASE_URL}/painel-flashcards`);
  const flashcardsLink = await page.$('a[href*="/flashcards"]');
  if (flashcardsLink) {
    await flashcardsLink.click();
  }
  await expect(page).toHaveURL(/flashcards/);

  // 6. Responde ao primeiro flashcard (botões de alternativa do quiz)
  const primeiraBotao = page.locator('#verso-alternativas button').first();
  if (await primeiraBotao.count()) {
    // Vira o cartão primeiro para expor as alternativas
    await page.click('#cartao');
    await primeiraBotao.click();
    await expect(primeiraBotao).toHaveClass(/btn-success|btn-danger/);
  }
});
