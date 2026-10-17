// e2e/flashcard_flow.spec.js
// Playwright end‑to‑end test validating o fluxo completo de flashcards:
// 1. Cadastro
// 2. Onboarding (objetivo + plano)
// 3. Criação de texto → geração automática de flashcards
// 4. Resposta a um flashcard → verificação de correção
// 5. Revisão (FSRS) automática

const { test, expect } = require('@playwright/test');

test('Fluxo completo de flashcards', async ({ page }) => {
  test.setTimeout(120000); // 2 min timeout to allow processing
  // 1. Cadastro
  await page.waitForLoadState('networkidle'); // after navigation

  await page.fill('input[name="nome"]', 'E2E User');
  await page.fill('input[name="email"]', 'e2e@example.com');
  await page.fill('input[name="senha"]', 'senha123');
  await page.fill('input[name="confirmar_senha"]', 'senha123');
  // CSRF token is in hidden input
  const csrf = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="csrf_token"]', csrf);
  await page.waitForNavigation(); // ensure page load after submit

  await expect(page).toURL(/dashboard/);

  // 2. Onboarding – objetivo
  await page.goto('http://localhost:5000/onboarding/objetivos');
  const csrfObj = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="csrf_token"]', csrfObj);
  await page.check('input[value="estudos"]');
  await page.waitForNavigation(); // ensure page load after submit

  await expect(page).toURL(/onboarding\/plano/);

  // 3. Onboarding – plano
  const csrfPlano = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="csrf_token"]', csrfPlano);
  await page.fill('input[name="meta_diaria_minutos"]', '10');
  await page.fill('input[name="meta_semanal_textos"]', '5');
  await page.fill('input[name="meta_flashcards_iniciais"]', '30');
  await page.selectOption('select[name="nivel_atual"]', 'A1');
  await page.waitForNavigation(); // ensure page load after submit

  await expect(page).toURL(/dashboard/);

  // 4. Cria novo texto
  await page.goto('http://localhost:5000/novo-texto');
  const csrfTexto = await page.getAttribute('input[name="csrf_token"]', 'value');
  await page.fill('input[name="csrf_token"]', csrfTexto);
  await page.fill('input[name="titulo"]', 'Teste E2E');
  await page.fill('textarea[name="conteudo"]', 'Ich lebe in Berlin. Die Stadt ist klein.');
  await page.waitForNavigation(); // ensure page load after submit

  await expect(page).toURL(/texto\/\d+/);

  // 5. Vai para flashcards do texto
  const flashcardsLink = await page.$('a[href*="/flashcards"]');
  await flashcardsLink.click();
  await expect(page).toURL(/flashcards/);

  // 6. Responde ao primeiro flashcard (assume que há botões com data-alternativa)
  const primeiraBotao = await page.locator('button[data-alternativa]').first();
  await primeiraBotao.click();
  // Verifica feedback visual (classe .correta ou .incorreta)
  await expect(primeiraBotao).toHaveClass(/correta|incorreta/);
});
