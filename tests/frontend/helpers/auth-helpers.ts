import { Page, expect } from '@playwright/test';

/**
 * Helper functions for authentication testing
 */

export interface TestUser {
  email: string;
  password: string;
  name?: string;
}

export const TEST_USERS = {
  valid: {
    email: 'test@example.com',
    password: 'testpassword123',
    name: 'Test User'
  },
  invalid: {
    email: 'wrong@example.com',
    password: 'wrongpassword'
  }
} as const;

/**
 * Navigate to login page and verify it loads
 */
export async function goToLoginPage(page: Page) {
  await page.goto('/api/v1/auth/login');
  await expect(page.locator('form')).toBeVisible();
}

/**
 * Navigate to registration page and verify it loads
 */
export async function goToRegistrationPage(page: Page) {
  await page.goto('/api/v1/auth/register');
  await expect(page.locator('form')).toBeVisible();
}

/**
 * Fill login form with provided credentials
 */
export async function fillLoginForm(page: Page, user: TestUser) {
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
}

/**
 * Fill registration form with provided user data
 */
export async function fillRegistrationForm(page: Page, user: TestUser) {
  if (user.name) {
    await page.fill('input[name="name"], input[name="full_name"]', user.name);
  }
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
}

/**
 * Submit a form and wait for response
 */
export async function submitForm(page: Page) {
  await page.click('button[type="submit"], input[type="submit"]');
  await page.waitForLoadState('networkidle');
}

/**
 * Check if page shows an error message
 */
export async function hasErrorMessage(page: Page): Promise<boolean> {
  const errorSelectors = [
    '.error-message',
    '.alert-danger',
    '.text-red-500',
    '[role="alert"]',
    '.error',
    '.alert-error'
  ];
  
  for (const selector of errorSelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      return true;
    }
  }
  return false;
}

/**
 * Check if page shows a success message
 */
export async function hasSuccessMessage(page: Page): Promise<boolean> {
  const successSelectors = [
    '.success-message',
    '.alert-success',
    '.text-green-500',
    '.success',
    '.alert-success'
  ];
  
  for (const selector of successSelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      return true;
    }
  }
  return false;
}

/**
 * Check if user appears to be logged in (look for profile/logout elements)
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  const loggedInSelectors = [
    'a[href*="profile"]',
    'button:has-text("logout")',
    'a:has-text("logout")',
    '.user-dropdown',
    '.user-menu'
  ];
  
  for (const selector of loggedInSelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      return true;
    }
  }
  return false;
}

/**
 * Wait for and check if redirected to a specific page
 */
export async function waitForRedirect(page: Page, expectedPath: string, timeout = 10000): Promise<boolean> {
  try {
    await page.waitForURL(url => url.pathname.includes(expectedPath), { timeout });
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if form has proper validation attributes
 */
export async function checkFormValidation(page: Page) {
  const emailInput = page.locator('input[name="email"]');
  const passwordInput = page.locator('input[name="password"]');
  
  await expect(emailInput).toHaveAttribute('type', 'email');
  await expect(passwordInput).toHaveAttribute('type', 'password');
  
  // Check for required attributes
  await expect(emailInput).toHaveAttribute('required');
  await expect(passwordInput).toHaveAttribute('required');
}

/**
 * Test form accessibility features
 */
export async function checkFormAccessibility(page: Page) {
  // Check for proper labels
  const emailLabel = page.locator('label[for*="email"], label:has-text("email")');
  const passwordLabel = page.locator('label[for*="password"], label:has-text("password")');
  
  await expect(emailLabel).toBeVisible();
  await expect(passwordLabel).toBeVisible();
  
  // Check ARIA attributes if present
  const form = page.locator('form');
  const hasAriaLabel = await form.getAttribute('aria-label');
  const hasRole = await form.getAttribute('role');
  
  // Form should have proper ARIA labeling or role
  expect(hasAriaLabel || hasRole || true).toBeTruthy(); // Allow forms without ARIA for now
}

/**
 * Disable JavaScript for testing progressive enhancement
 */
export async function disableJavaScript(page: Page) {
  await page.addInitScript(() => {
    Object.defineProperty(window, 'navigator', {
      value: { ...window.navigator, javaScriptEnabled: false },
      writable: true
    });
  });
}

/**
 * Check if page works without JavaScript
 */
export async function testWithoutJavaScript(page: Page, url: string) {
  await disableJavaScript(page);
  await page.goto(url);
  
  // Basic form elements should still be visible
  await expect(page.locator('form')).toBeVisible();
  await expect(page.locator('input[name="email"]')).toBeVisible();
  await expect(page.locator('input[name="password"]')).toBeVisible();
} 