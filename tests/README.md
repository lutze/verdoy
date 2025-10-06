# Frontend Testing with Playwright

This directory contains frontend smoke tests for the VerdoyLab platform using Playwright.

## Overview

The test suite covers all major user-facing pages and components to ensure robust, reliable quality assurance for the HTML-first, progressively enhanced frontend.

## Test Structure

```
tests/
├── frontend/
│   ├── auth.spec.ts           # Authentication page tests
│   └── helpers/
│       └── auth-helpers.ts    # Reusable test utilities
└── README.md                  # This file
```

## Test Coverage

### ✅ Authentication Pages (Completed)
- **Login Page**: Form visibility, error handling, accessibility
- **Registration Page**: Form validation, organization selection
- **Profile Page**: Access control, structure
- **Navigation Component**: Responsive design, guest/authenticated states
- **Content Negotiation**: HTML/JSON responses
- **Progressive Enhancement**: No-JS functionality

### 🚀 Future Test Coverage
- **Dashboard**: Organization cards, stats, activity feed
- **Organization Management**: List, create, detail, member management
- **Project Management**: List, create, detail
- **Process Designer**: List, detail, interactive designer
- **Experiment Management**: Create, detail, monitor, controls
- **Bioreactor Management**: Enrollment, dashboard, manual control

## Running Tests

### Prerequisites
1. Ensure the backend is running at `http://localhost:8000`
2. Docker containers should be up: `cd backend && docker compose up -d`

### Commands

```bash
# Run all tests
npm test

# Run tests with browser visible (headed mode)
npm run test:headed

# Run only authentication tests
npm run test:auth

# Debug tests interactively
npm run test:debug

# Run tests with UI mode
npm run test:ui

# View test report
npm run test:report
```

### Test Browsers

Tests run on multiple browsers and devices:
- **Desktop**: Chrome, Firefox, Safari
- **Mobile**: Chrome (Pixel 5), Safari (iPhone 12)
- **Progressive Enhancement**: Chrome with JavaScript disabled

## Test Philosophy

### Smoke Tests Focus
- **Page Load**: Verify each page loads without error
- **Key Elements**: Check for presence of main forms, tables, navigation
- **Basic Interactions**: Submit forms, check for error/success messages
- **Progressive Enhancement**: Ensure HTML-first functionality works

### HTML-First Testing
- All tests verify that core functionality works without JavaScript
- Tests use semantic selectors (roles, labels, form elements)
- Accessibility is verified where applicable

### Resilient Selectors
Tests use robust selectors that are less likely to break:
- Form element names: `input[name="email"]`
- Semantic roles: `[role="alert"]`
- Text content: `:has-text("login")`
- Multiple fallbacks: `.error-message, .alert-danger, .text-red-500`

## Test Data

Test users and data are defined in `helpers/auth-helpers.ts`:
- Valid test user credentials
- Invalid credentials for error testing
- Reusable form filling functions

## CI Integration

Tests are configured to run in CI with:
- Retry logic for flaky tests
- Screenshot and video capture on failure
- HTML report generation
- Fail-fast behavior for critical failures

## Best Practices

1. **Keep Tests Fast**: Focus on critical flows, avoid slow operations
2. **Be Resilient**: Use multiple selector strategies for robustness
3. **Progressive Enhancement**: Always include no-JS tests
4. **Semantic Testing**: Test functionality, not implementation details
5. **Clear Assertions**: Use descriptive test names and clear expectations

## Configuration

The Playwright configuration is in `playwright.config.ts` at the project root:
- Base URL: `http://localhost:8000`
- Test directory: `./tests/frontend`
- Automatic server startup via Docker Compose
- Multiple browser and device configurations

## Troubleshooting

### Common Issues

1. **Server not running**: Ensure backend Docker containers are up
2. **Test timeouts**: Check if the application is responding at localhost:8000
3. **Element not found**: Check if selectors match actual HTML structure
4. **JavaScript disabled tests failing**: Ensure forms work without JS

### Debugging

Use the debug mode to step through tests:
```bash
npm run test:debug
```

Or use the UI mode for interactive debugging:
```bash
npm run test:ui
```

## Contributing

When adding new pages or features:

1. Add corresponding smoke tests to verify basic functionality
2. Include both JavaScript-enabled and disabled test scenarios
3. Test across different viewport sizes
4. Update this README with new test coverage

## References

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Frontend Plan](../FRONTEND_PLAN.md)
- [Frontend Testing Strategy](../docs/testing/FRONTEND_TESTING_STRATEGY.md) 