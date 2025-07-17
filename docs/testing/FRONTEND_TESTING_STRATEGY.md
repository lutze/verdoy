# Frontend Testing Strategy: Playwright Smoke Tests

## Overview

This document outlines the frontend testing strategy for the LMS Core platform, focusing on Playwright-based smoke tests for all major user-facing pages and components. The goal is to ensure robust, reliable, and maintainable quality assurance for the HTML-first, progressively enhanced frontend described in [FRONTEND_PLAN.md](../FRONTEND_PLAN.md).

---

## 1. Rationale & Goals

- **Early Bug Detection:** Catch regressions and critical UI failures as soon as possible.
- **Confidence in Core Flows:** Ensure all critical pages and navigation work after every change.
- **Progressive Enhancement:** Validate that the HTML-first experience works with and without JavaScript.
- **CI Integration:** Run smoke tests automatically in CI before every release.
- **Maintainability:** Keep tests fast, focused, and easy to update as the UI evolves.

---

## 2. Test Types & Coverage

### **A. Smoke Tests (Required for All Core Pages)**
- **Page Load:** Verify each core page loads without error (HTTP 200, no JS errors).
- **Key Elements Present:** Check for presence of main forms, tables, navigation, and headings.
- **Navigation:** Ensure navbar, sidebar, and footer links work as expected.
- **Form Visibility:** Confirm that all forms (login, registration, create org, etc.) are visible and interactable.
- **Basic Interactions:** Submit forms with valid/invalid data, check for error/success messages.
- **Auth State:** Validate navigation and page access for both guest and authenticated users.

### **B. Progressive Enhancement Checks**
- **No-JS Mode:** Run a subset of smoke tests with JavaScript disabled to ensure HTML-first functionality.
- **HTMX/JS Features:** For pages using HTMX or custom JS, verify that dynamic content loads and updates as expected.

### **C. Accessibility & Responsiveness (Optional, Recommended)**
- **Mobile Viewports:** Run smoke tests on mobile and desktop viewport sizes.
- **Accessibility Landmarks:** Check for presence of semantic landmarks (nav, main, header, etc.).

---

## 3. Test Coverage Requirements

- **Authentication:** Login, registration, profile, logout flows.
- **Dashboard:** Organization cards, stats, activity feed.
- **Organization Management:** List, create, detail, member management.
- **Project Management:** List, create, detail.
- **Process Designer:** List, detail, interactive designer.
- **Experiment Management:** Create, detail, monitor, controls.
- **Bioreactor Management:** Enrollment, dashboard, manual control.
- **User Profile:** View/edit, password change, API key management.
- **Navigation:** Navbar, user dropdown, mobile menu.

**All new Core Pages & Components must include Playwright smoke tests before merging.**

---

## 4. Test Process & Workflow

### **A. Adding New Tests**
1. **Create/Update Test File:** Add a new Playwright test file under `frontend/tests/` (e.g., `dashboard.spec.ts`).
2. **Write Smoke Test Cases:** Cover page load, key elements, navigation, and basic interactions.
3. **Progressive Enhancement:** Add at least one test with JS disabled for HTML-first validation.
4. **Run Locally:** Ensure all tests pass locally before pushing.
5. **Pull Request:** All new/updated pages must include or update Playwright smoke tests.

### **B. Test Naming & Structure**
- Use descriptive test names (e.g., `should display login form`, `should show error on invalid credentials`).
- Group related tests in a single file per page/feature.
- Use Playwright's `test.describe` and `test.step` for clarity.

### **C. Test Data & State**
- Use test accounts and seed data where possible.
- Clean up created data after tests if needed.
- Avoid relying on production data or state.

---

## 5. CI Integration

- **Automated Runs:** Playwright smoke tests must run in CI (GitHub Actions, GitLab CI, etc.) on every push and pull request.
- **Fail Fast:** Any smoke test failure should block the build/release.
- **Artifacts:** Store screenshots and traces for failed tests to aid debugging.
- **Environment:** Use a dedicated test environment with a seeded database for reliable results.

---

## 6. Best Practices

- **Keep Tests Fast:** Focus on critical flows, avoid slow or flaky tests.
- **Be Resilient:** Use robust selectors (data-testid, role, text) to avoid brittle tests.
- **Minimal Setup:** Prefer direct navigation and minimal setup for each test.
- **Progressive Enhancement:** Always include at least one no-JS test per page.
- **Review Regularly:** Update tests as UI and flows change; remove obsolete tests.
- **Document:** Add comments for any non-obvious test logic or workarounds.

---

## 7. Example Playwright Smoke Test (Login Page)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('should load and display login form', async ({ page }) => {
    await page.goto('/api/v1/auth/login');
    await expect(page.locator('form')).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/api/v1/auth/login');
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'badpassword');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should work with JavaScript disabled', async ({ page, context }) => {
    await context.grantPermissions([]); // Remove all permissions
    await page.setJavaScriptEnabled(false);
    await page.goto('/api/v1/auth/login');
    await expect(page.locator('form')).toBeVisible();
  });
});
```

---

## 8. References

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [FRONTEND_PLAN.md](../FRONTEND_PLAN.md)
- [Testing Strategy for Backend](./backend/guides/TESTING_STRATEGY.md)

---

**This strategy ensures that all critical frontend flows are always working, providing confidence for every release.** 

---

## 9. Critique of Current Playwright Authentication Tests

This section provides a detailed critique of the Playwright tests written for authentication flows, referencing the standards and goals set out in [FRONTEND_PLAN.md](../FRONTEND_PLAN.md) and the earlier sections of this strategy document.

### Coverage & Alignment with Plan

- **Authentication Flows:** Login, registration, and profile pages are tested for load, form presence, and basic validation.
- **Navigation:** Tests check for correct navbar links for guests and responsiveness on mobile.
- **Content Negotiation:** Verifies HTML is served for browsers and checks API response for JSON requests.
- **API Prefix Consistency:** Ensures `/api/v1` prefix is used for all auth endpoints.
- **Accessibility:** Tests for form labels and input types.
- **Progressive Enhancement:** Includes tests with JavaScript disabled.

These areas align well with the requirements in the frontend plan and this strategy, especially for the authentication milestone.

### Strengths

- **Comprehensive Auth Coverage:** All major user flows (login, register, profile) are tested for both happy and unhappy paths.
- **Progressive Enhancement:** Each page is tested with JS disabled, ensuring HTML-first functionality.
- **Accessibility:** Checks for form labels and input types, supporting a11y goals.
- **Responsiveness:** Mobile viewport is tested for navigation.
- **Content Negotiation:** Explicitly tests Accept headers and response types.
- **Helpers:** The `helpers/auth-helpers.ts` file is well-structured, making tests DRY and readable.

### Areas for Improvement & Recommendations

1. **Error Handling & Validation**
   - Assert that specific error messages are visible after failed login/registration, not just that the form is present.
   - For registration, assert that visible error messages appear for invalid email or missing fields, not just input validity.

2. **Accessibility**
   - Add checks for semantic landmarks (`nav`, `main`, `header`, etc.) as recommended.
   - Consider adding a test for keyboard navigation (tab order, submit via keyboard).

3. **Progressive Enhancement**
   - Use `context.setJavaScriptEnabled(false)` for no-JS tests for robustness, rather than custom scripts.

4. **Test Data & State**
   - Ensure the test environment is seeded with known users, or use setup/teardown hooks to create and clean up test users.

5. **Maintainability**
   - Prefer `data-testid` attributes for all critical elements to make selectors more robust.
   - As the app grows, consider splitting tests by feature/page (e.g., `login.spec.ts`, `register.spec.ts`).

6. **CI Integration**
   - Ensure Playwright config and CI pipeline store screenshots and traces on test failure, as described in this strategy.

7. **Future Coverage**
   - As new pages are implemented (dashboard, organizations, projects, etc.), replicate this thoroughness for each core section.
   - Add tests for HTMX/JS dynamic features as they are built.
   - Consider integrating automated accessibility checks (e.g., Playwright a11y snapshot, axe-core).
   - Expand mobile/responsive tests to all new pages.

### Summary Table

| Area                | Status      | Notes/Suggestions                                                                 |
|---------------------|-------------|-----------------------------------------------------------------------------------|
| Auth Flows          | ✅ Complete | Covers login, register, profile, errors, and content negotiation                  |
| Progressive Enhance | ✅ Good     | JS-disabled tests present; use context-level JS disable for robustness            |
| Accessibility       | 🟡 Partial  | Checks labels/types; add landmarks, keyboard nav, and consider a11y snapshots     |
| Responsiveness      | ✅ Good     | Mobile nav tested; expand to other pages as built                                 |
| Error Handling      | 🟡 Partial  | Check for visible error messages, not just form presence                          |
| Maintainability     | ✅ Good     | Helpers used; consider `data-testid` for selectors                                |
| CI Integration      | 🟡 Partial  | Ensure screenshots/traces are saved on failure                                    |
| Future Coverage     | ❌ Missing  | Add tests for dashboard, orgs, projects, etc. as you implement                    |

### Actionable Recommendations

1. Assert error messages after failed login/registration, not just form presence.
2. Use `context.setJavaScriptEnabled(false)` for no-JS tests.
3. Add semantic landmark checks (`nav`, `main`, etc.) for accessibility.
4. Adopt `data-testid` attributes for all critical elements.
5. Seed test users or use setup/teardown for test data.
6. Expand tests to new pages as you implement them, following the same structure.
7. Integrate a11y tools for automated accessibility checks.
8. Ensure CI saves artifacts (screenshots, traces) on test failure.

---

**Overall:**

The Playwright tests for authentication are well-aligned with the project's frontend plan and testing strategy. They provide a solid foundation for quality assurance. With a few tweaks for error handling, accessibility, and maintainability, and by expanding coverage as you build new features, you'll have a robust, future-proof test suite. 