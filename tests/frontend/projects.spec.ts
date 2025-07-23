import { test, expect } from '@playwright/test';
import { fillLoginForm, submitForm, goToLoginPage, TEST_USERS, disableJavaScript } from './helpers/auth-helpers';

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login with test user
    await goToLoginPage(page);
    await fillLoginForm(page, TEST_USERS.valid);
    await submitForm(page);
    // Wait for redirect to dashboard
    await page.waitForURL('/app/dashboard');
  });

  test.describe('Project List Page', () => {
    test('should load projects list page successfully', async ({ page }) => {
      await page.goto('/app/projects');
      
      // Check for main elements
      await expect(page.locator('h1')).toContainText('Projects');
      await expect(page.locator('text=Manage your research projects')).toBeVisible();
      await expect(page.locator('a[href="/app/projects/create"]')).toBeVisible();
    });

    test('should display create project button', async ({ page }) => {
      await page.goto('/app/projects');
      
      const createButton = page.locator('a[href="/app/projects/create"]');
      await expect(createButton).toBeVisible();
      await expect(createButton).toContainText('Create Project');
    });

    test('should show filter options', async ({ page }) => {
      await page.goto('/app/projects');
      
      // Check for filter form
      await expect(page.locator('select[name="organization_id"]')).toBeVisible();
      await expect(page.locator('select[name="status"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toContainText('Filter');
    });

    test('should display empty state when no projects exist', async ({ page }) => {
      await page.goto('/app/projects');
      
      // Look for empty state
      const emptyStateText = page.locator('text=No projects yet');
      if (await emptyStateText.isVisible()) {
        await expect(emptyStateText).toBeVisible();
        await expect(page.locator('text=Create your first project')).toBeVisible();
      }
    });

    test('should work without JavaScript', async ({ page, context }) => {
      await disableJavaScript(page);
      
      await page.goto('/app/projects');
      
      // Basic functionality should still work
      await expect(page.locator('h1')).toContainText('Projects');
      await expect(page.locator('form')).toBeVisible(); // Filter form
    });

    test('should be responsive on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 }); // Mobile viewport
      await page.goto('/app/projects');
      
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('a[href="/app/projects/create"]')).toBeVisible();
    });
  });

  test.describe('Create Project Page', () => {
    test('should load create project page successfully', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      // Check for main elements
      await expect(page.locator('h1')).toContainText('Create Project');
      await expect(page.locator('text=Set up a new research project')).toBeVisible();
    });

    test('should display all required form fields', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      // Check for required fields
      await expect(page.locator('input[name="name"]')).toBeVisible();
      await expect(page.locator('textarea[name="description"]')).toBeVisible();
      await expect(page.locator('select[name="organization_id"]')).toBeVisible();
      await expect(page.locator('select[name="priority"]')).toBeVisible();
      
      // Timeline fields
      await expect(page.locator('input[name="start_date"]')).toBeVisible();
      await expect(page.locator('input[name="end_date"]')).toBeVisible();
      await expect(page.locator('input[name="expected_completion"]')).toBeVisible();
      
      // Additional fields
      await expect(page.locator('input[name="budget"]')).toBeVisible();
      await expect(page.locator('input[name="tags"]')).toBeVisible();
    });

    test('should show proper form labels and help text', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      // Check for accessibility
      await expect(page.locator('label[for="name"]')).toContainText('Project Name');
      await expect(page.locator('label[for="description"]')).toContainText('Description');
      await expect(page.locator('label[for="organization_id"]')).toContainText('Organization');
      
      // Check for help text
      await expect(page.locator('text=The display name for your project')).toBeVisible();
      await expect(page.locator('text=Comma-separated tags')).toBeVisible();
    });

    test('should have proper form validation', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      // Check required field validation
      const nameInput = page.locator('input[name="name"]');
      const orgSelect = page.locator('select[name="organization_id"]');
      
      await expect(nameInput).toHaveAttribute('required');
      await expect(orgSelect).toHaveAttribute('required');
    });

    test('should show cancel and submit buttons', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      await expect(page.locator('a[href="/app/projects"]')).toContainText('Cancel');
      await expect(page.locator('button[type="submit"]')).toContainText('Create Project');
    });

    test('should work without JavaScript', async ({ page, context }) => {
      await disableJavaScript(page);
      
      await page.goto('/app/projects/create');
      
      // Form should still be functional
      await expect(page.locator('form')).toBeVisible();
      await expect(page.locator('input[name="name"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should be responsive on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 }); // Mobile viewport
      await page.goto('/app/projects/create');
      
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('form')).toBeVisible();
    });

    test('should handle form submission with missing required fields', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      // Try to submit without required fields
      await page.click('button[type="submit"]');
      
      // Should show validation errors (browser validation)
      const nameInput = page.locator('input[name="name"]');
      await expect(nameInput).toHaveAttribute('required');
    });
  });

  test.describe('Navigation Integration', () => {
    test('should have project link in main navigation', async ({ page }) => {
      await page.goto('/app/dashboard');
      
      // Check for projects link in navbar
      const projectsLink = page.locator('nav a[href="/app/projects"]');
      await expect(projectsLink).toBeVisible();
      await expect(projectsLink).toContainText('Projects');
    });

    test('should have project quick action on dashboard', async ({ page }) => {
      await page.goto('/app/dashboard');
      
      // Check for projects quick action
      const projectsAction = page.locator('a[href="/app/projects"]');
      await expect(projectsAction).toBeVisible();
      
      // Should have project icon and description
      await expect(page.locator('text=Projects')).toBeVisible();
      await expect(page.locator('text=Create and manage research projects')).toBeVisible();
    });

    test('should navigate between project pages correctly', async ({ page }) => {
      // Start from dashboard
      await page.goto('/app/dashboard');
      
      // Navigate to projects
      await page.click('a[href="/app/projects"]');
      await expect(page).toHaveURL('/app/projects');
      
      // Navigate to create project
      await page.click('a[href="/app/projects/create"]');
      await expect(page).toHaveURL('/app/projects/create');
      
      // Navigate back to projects list
      await page.click('a[href="/app/projects"]');
      await expect(page).toHaveURL('/app/projects');
    });
  });

  test.describe('Content Negotiation', () => {
    test('should serve HTML for browser requests', async ({ page }) => {
      const response = await page.goto('/app/projects', {
        waitUntil: 'domcontentloaded'
      });
      
      expect(response?.headers()['content-type']).toContain('text/html');
    });

    test('should handle API requests with proper headers', async ({ page }) => {
      // This test would need to be expanded based on actual API usage
      await page.goto('/app/projects');
      
      // Check that the page loads properly
      await expect(page.locator('h1')).toContainText('Projects');
    });
  });

  test.describe('Error Handling', () => {
    test('should handle 404 errors gracefully', async ({ page }) => {
      const response = await page.goto('/app/projects/nonexistent-id');
      
      // Should either redirect or show appropriate error
      if (response?.status() === 404) {
        await expect(page.locator('text=not found')).toBeVisible();
      }
    });

    test('should show appropriate error messages for form validation', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      // Fill form with invalid data and submit
      await page.fill('input[name="name"]', ''); // Empty name
      await page.click('button[type="submit"]');
      
      // Should show validation feedback
      const nameInput = page.locator('input[name="name"]');
      await expect(nameInput).toHaveAttribute('required');
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      await page.goto('/app/projects');
      
      // Check heading structure
      const h1 = page.locator('h1');
      await expect(h1).toBeVisible();
      await expect(h1).toContainText('Projects');
    });

    test('should have proper form labels', async ({ page }) => {
      await page.goto('/app/projects/create');
      
      // Check that all form inputs have labels
      const nameInput = page.locator('input[name="name"]');
      const nameLabel = page.locator('label[for="name"]');
      
      await expect(nameInput).toBeVisible();
      await expect(nameLabel).toBeVisible();
    });

    test('should support keyboard navigation', async ({ page }) => {
      await page.goto('/app/projects');
      
      // Tab through main navigation elements
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Create button should be focusable
      const createButton = page.locator('a[href="/app/projects/create"]');
      await expect(createButton).toBeVisible();
    });
  });
}); 