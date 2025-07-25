import { test, expect } from '@playwright/test';
import { TEST_USERS, fillLoginForm, submitForm } from './helpers/auth-helpers';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/app/login');
    await fillLoginForm(page, TEST_USERS.valid);
    await submitForm(page);
    // Wait for redirect to dashboard or check if we're logged in
    await page.waitForURL(/\/dashboard|\/profile/);
  });

  test('should load dashboard page and display main elements', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check page loads without errors
    await expect(page).toHaveTitle(/Dashboard/);
    
    // Check main sections are present
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('.stats-section')).toBeVisible();
    await expect(page.locator('.organizations-section')).toBeVisible();
    await expect(page.locator('.activity-section')).toBeVisible();
    await expect(page.locator('.quick-actions')).toBeVisible();
  });

  test('should display organization cards', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check organization cards are present
    const orgCards = page.locator('.org-card');
    await expect(orgCards).toHaveCount(2); // Mock data has 2 organizations
    
    // Check first organization card content
    const firstCard = orgCards.first();
    await expect(firstCard.locator('h3')).toContainText('Acme Research Lab');
    await expect(firstCard.locator('.org-description')).toContainText('Primary research organization');
    await expect(firstCard.locator('.org-stats')).toBeVisible();
  });

  test('should display summary statistics', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check stats cards are present
    const statCards = page.locator('.stat-card');
    await expect(statCards).toHaveCount(6); // 6 stat cards
    
    // Check specific stats are visible
    await expect(page.locator('text=Organizations')).toBeVisible();
    await expect(page.locator('text=Total Experiments')).toBeVisible();
    await expect(page.locator('text=Bioreactors')).toBeVisible();
    await expect(page.locator('text=Online')).toBeVisible();
  });

  test('should display activity feed', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check activity section is present
    await expect(page.locator('.activity-section h2')).toContainText('Recent Activity');
    await expect(page.locator('#activity-feed')).toBeVisible();
    
    // Check activity items are present
    const activityItems = page.locator('.activity-item');
    await expect(activityItems.first()).toBeVisible();
  });

  test('should display quick action cards', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check quick actions section
    await expect(page.locator('.quick-actions h2')).toContainText('Quick Actions');
    
    // Check action cards are present
    const actionCards = page.locator('.action-card');
    await expect(actionCards).toHaveCount(6); // 6 action cards
    
    // Check specific action cards
    await expect(page.locator('text=Manage Organizations')).toBeVisible();
    await expect(page.locator('text=Bioreactor Management')).toBeVisible();
    await expect(page.locator('text=Experiments')).toBeVisible();
    await expect(page.locator('text=Process Designer')).toBeVisible();
    await expect(page.locator('text=Analytics')).toBeVisible();
    await expect(page.locator('text=Alerts')).toBeVisible();
  });

  test('should have working navigation links', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check organization links work
    const orgLinks = page.locator('.org-actions a');
    await expect(orgLinks.first()).toHaveAttribute('href', /\/api\/v1\/organizations\/1/);
    
    // Check quick action links work
    const actionLinks = page.locator('.action-card');
    await expect(actionLinks.first()).toHaveAttribute('href', '/api/v1/organizations');
  });

  test('should work with JavaScript disabled', async ({ page }) => {
    // Disable JavaScript using the helper function
    await page.addInitScript(() => {
      Object.defineProperty(window, 'navigator', {
        value: { ...window.navigator, javaScriptEnabled: false },
        writable: true
      });
    });
    
    await page.goto('/app/dashboard');
    
    // Check page loads and displays content
    await expect(page).toHaveTitle(/Dashboard/);
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('.stats-section')).toBeVisible();
    await expect(page.locator('.organizations-section')).toBeVisible();
    
    // Check forms and links are still functional
    await expect(page.locator('.org-actions a')).toBeVisible();
    await expect(page.locator('.action-card')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/app/dashboard');
    
    // Check page loads on mobile
    await expect(page).toHaveTitle(/Dashboard/);
    await expect(page.locator('h1')).toContainText('Dashboard');
    
    // Check mobile-specific layout adjustments
    await expect(page.locator('.stats-grid')).toBeVisible();
    await expect(page.locator('.organizations-grid')).toBeVisible();
    await expect(page.locator('.actions-grid')).toBeVisible();
  });

  test('should handle HTMX updates gracefully', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check HTMX attributes are present
    await expect(page.locator('.stats-grid')).toHaveAttribute('hx-get', '/api/v1/dashboard/stats');
    await expect(page.locator('#activity-feed')).toHaveAttribute('hx-get', '/api/v1/dashboard/activity');
    
    // Check refresh button works
    const refreshButton = page.locator('button:has-text("Refresh")');
    await expect(refreshButton).toBeVisible();
    await expect(refreshButton).toHaveAttribute('hx-get', '/api/v1/dashboard/activity');
  });

  test('should show user information in header', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check welcome message is present
    await expect(page.locator('.subtitle')).toContainText('Welcome back');
    
    // Check user name or email is displayed
    const subtitle = page.locator('.subtitle');
    const subtitleText = await subtitle.textContent();
    expect(subtitleText).toMatch(/Welcome back, .+/);
  });

  test('should have proper semantic structure', async ({ page }) => {
    await page.goto('/app/dashboard');
    
    // Check semantic HTML elements
    await expect(page.locator('main.dashboard')).toBeVisible();
    await expect(page.locator('header.page-header')).toBeVisible();
    await expect(page.locator('section.stats-section')).toBeVisible();
    await expect(page.locator('section.organizations-section')).toBeVisible();
    await expect(page.locator('section.activity-section')).toBeVisible();
    await expect(page.locator('section.quick-actions')).toBeVisible();
    
    // Check proper heading hierarchy
    await expect(page.locator('h1')).toHaveCount(1);
    const h2Elements = page.locator('h2');
    await expect(h2Elements).toHaveCount(3); // Organizations, Recent Activity, Quick Actions
  });
}); 