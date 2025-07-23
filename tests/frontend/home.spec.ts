import { test, expect } from '@playwright/test';
import { fillLoginForm, submitForm, goToLoginPage, TEST_USERS, disableJavaScript, isLoggedIn } from './helpers/auth-helpers';

test.describe('Home Page & Navigation', () => {
  test('should load /app home page and display main elements', async ({ page }) => {
    await page.goto('/app');
    await expect(page).toHaveTitle(/Home|LIM OS/);
    await expect(page.locator('h1')).toContainText('Welcome to LIM OS');
    await expect(page.locator('.lead')).toContainText('Laboratory Information Management Operating System');
    await expect(page.locator('nav.home-nav')).toBeVisible();
    // Check public navigation links (visible to guests)
    const publicLinks = [
      '/app/dashboard',
      '/app/admin/organization/',
      '/app/projects',
      '/app/processes',
      '/app/experiments',
      '/app/bioreactors',
      '/app/login',
      '/app/register'
    ];
    for (const href of publicLinks) {
      await expect(page.locator(`nav.home-nav a[href="${href}"]`)).toBeVisible();
    }
    // Profile link should NOT be visible for guests
    await expect(page.locator('nav.home-nav a[href="/app/admin/profile"]')).not.toBeVisible();
  });

  test('should show correct navigation for guest users', async ({ page }) => {
    await page.goto('/app');
    // Debug: print .home-nav HTML
    const navHtml = await page.locator('.home-nav').innerHTML().catch(() => 'not found');
    console.log('GUEST .home-nav HTML:', navHtml);
    // Debug: print full page HTML
    const fullHtml = await page.content();
    console.log('GUEST FULL PAGE HTML:', fullHtml);
    // Should see login link, not logout/profile, in .home-nav
    await expect(page.locator('.home-nav a[href="/app/login"]')).toBeVisible();
    await expect(page.locator('.home-nav a[href="/app/admin/profile"]')).not.toBeVisible();
  });

  test('should show correct navigation for authenticated users', async ({ page }) => {
    await page.goto('/app/login');
    await page.fill('input[name="email"]', TEST_USERS.valid.email);
    await page.fill('input[name="password"]', TEST_USERS.valid.password);
    await page.click('button[type="submit"], input[type="submit"]');
    await page.waitForURL(/\/app(\/dashboard)?/);
    await page.goto('/app');
    // Debug: print .home-nav HTML
    const navHtml = await page.locator('.home-nav').innerHTML().catch(() => 'not found');
    console.log('AUTH .home-nav HTML:', navHtml);
    // Should see profile and logout links in .home-nav
    await expect(page.locator('.home-nav a[href="/app/admin/profile"]')).toBeVisible();
    await expect(page.locator('.home-nav form[action="/app/logout"]')).toBeVisible();
    // Should not see login link
    await expect(page.locator('.home-nav a[href="/app/login"]')).not.toBeVisible();
  });

  test('navigation links should work for all major sections', async ({ page }) => {
    await page.goto('/app');
    const publicNavLinks = [
      { href: '/app/dashboard', text: 'Dashboard' },
      { href: '/app/admin/organization/', text: 'Organizations' },
      { href: '/app/projects', text: 'Projects' },
      { href: '/app/processes', text: 'Processes' },
      { href: '/app/experiments', text: 'Experiments' },
      { href: '/app/bioreactors', text: 'Bioreactors' },
      { href: '/app/login', text: 'Sign In' },
      { href: '/app/register', text: 'Register' }
    ];
    for (const { href, text } of publicNavLinks) {
      const link = page.locator(`nav.home-nav a[href="${href}"]`);
      await expect(link).toBeVisible();
      await expect(link).toContainText(text);
    }
    // Profile link should NOT be visible for guests
    await expect(page.locator('nav.home-nav a[href="/app/admin/profile"]')).not.toBeVisible();
  });

  test('should work without JavaScript (progressive enhancement)', async ({ page, context }) => {
    await disableJavaScript(page);
    await page.goto('/app');
    await expect(page.locator('h1')).toContainText('Welcome to LIM OS');
    await expect(page.locator('nav.home-nav')).toBeVisible();
    // Navigation links should still be present
    await expect(page.locator('a[href="/app/dashboard"]')).toBeVisible();
  });

  test('should have accessibility landmarks', async ({ page }) => {
    await page.goto('/app');
    // Check for both navs
    await expect(page.locator('nav.navbar')).toBeVisible();
    await expect(page.locator('nav.home-nav')).toBeVisible();
    await expect(page.locator('section.home-hero')).toBeVisible();
  });
}); 