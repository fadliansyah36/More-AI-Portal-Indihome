import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:3000';
const outputDir = process.env.SCREENSHOT_DIR || 'artifacts/phase00';
const widths = [360, 390, 768, 1024, 1440];
await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const failures = [];
for (const width of widths) {
  const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const response = await page.goto(baseURL, { waitUntil: 'networkidle', timeout: 60000 });
  if (!response || response.status() >= 400) failures.push(`HTTP ${response?.status() ?? 'NO_RESPONSE'} at ${width}px`);
  await page.screenshot({ path: `${outputDir}/home-${width}px.png`, fullPage: true });
  const title = await page.title();
  const bodyText = await page.locator('body').innerText().catch(() => '');
  if (!title || !bodyText.trim()) failures.push(`Empty title/body at ${width}px`);
  if (errors.length) failures.push(...errors.map(e => `Browser error at ${width}px: ${e}`));
  console.log(JSON.stringify({ width, status: response?.status(), title, bodyCharacters: bodyText.length, pageErrors: errors }));
  await page.close();
}

const authPage = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
for (const [path, expectedLabel] of [['/customer/register', 'Daftar Akun Baru'], ['/customer/login', 'Masuk ke Akun AI Workspace Anda']]) {
  const response = await authPage.goto(new URL(path, baseURL).toString(), { waitUntil: 'networkidle', timeout: 60000 });
  if (!response || response.status() >= 400) failures.push(`Auth route HTTP ${response?.status() ?? 'NO_RESPONSE'} at ${path}`);
  const body = await authPage.locator('body').innerText().catch(() => '');
  if (!body.includes(expectedLabel)) failures.push(`Expected auth screen label missing at ${path}`);
  if (await authPage.locator('input[type="tel"]').count()) failures.push(`Phone input must not be present at ${path}`);
  if (path.endsWith('/register')) {
    if (await authPage.locator('input[type="text"]').count() < 1) failures.push('Registration full-name input is missing');
    if (await authPage.locator('input[type="email"]').count() !== 1) failures.push('Registration email input is missing');
    if (await authPage.locator('input[type="password"]').count() !== 1) failures.push('Registration password input is missing');
  } else {
    if (await authPage.locator('input[type="email"]').count() !== 1) failures.push('Login email input is missing');
    if (await authPage.locator('input[type="password"]').count() !== 1) failures.push('Login password input is missing');
  }
  await authPage.screenshot({ path: `${outputDir}/${path.endsWith('/register') ? 'register' : 'login'}-390px.png`, fullPage: true });
}
await authPage.close();

await browser.close();
if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
