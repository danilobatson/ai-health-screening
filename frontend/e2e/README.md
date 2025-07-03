# E2E Testing with Playwright

This directory contains end-to-end tests for the AI Health Assessment System frontend using Playwright.

## Test Structure

### Test Files

- **`homepage.spec.js`** - Tests for the landing page functionality, responsiveness, and accessibility
- **`health-assessment-form.spec.js`** - Comprehensive tests for the health assessment form including validation, submissions, and error handling
- **`assessment-results.spec.js`** - Tests for the results display, different risk levels, and user interactions
- **`complete-user-flow.spec.js`** - End-to-end user journey tests covering the entire application flow
- **`performance-accessibility.spec.js`** - Performance benchmarks, accessibility checks, and load testing

### Configuration

- **`playwright.config.js`** - Main Playwright configuration with browser settings, test environments, and reporting
- **`global-setup.js`** - Global setup for test environment preparation

## Running Tests

### Prerequisites

Make sure you have:
1. Node.js 18+ installed
2. Frontend dependencies installed: `npm install`
3. Backend server running on `http://localhost:8000`
4. Frontend development server running on `http://localhost:3000`

### Basic Commands

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run all E2E tests
npm run test:e2e

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Debug tests step by step
npm run test:e2e:debug

# View test report
npm run test:e2e:report

# Run all tests (unit + E2E)
npm run test:all
```

### Running Specific Tests

```bash
# Run specific test file
npx playwright test homepage.spec.js

# Run specific test by name
npx playwright test --grep "should display the homepage correctly"

# Run tests for specific browser
npx playwright test --project chromium

# Run tests in parallel
npx playwright test --workers 4
```

## Test Coverage

### Functional Testing
- ✅ Homepage display and navigation
- ✅ Health assessment form validation
- ✅ Form submission and API integration
- ✅ Results display and interpretation
- ✅ Error handling and recovery
- ✅ New assessment workflow

### Cross-Browser Testing
- ✅ Chromium (Chrome/Edge)
- ✅ Firefox
- ✅ WebKit (Safari)
- ✅ Mobile Chrome
- ✅ Mobile Safari

### Accessibility Testing
- ✅ Keyboard navigation
- ✅ Screen reader compatibility
- ✅ Color contrast validation
- ✅ ARIA attributes
- ✅ Focus management

### Performance Testing
- ✅ Page load times
- ✅ API response handling
- ✅ Large form submissions
- ✅ Concurrent user simulation
- ✅ Network condition handling

### Responsive Testing
- ✅ Desktop (1920x1080)
- ✅ Tablet (768x1024)
- ✅ Mobile (375x667)
- ✅ Various viewport sizes

## Test Scenarios

### Normal User Flow
1. User visits homepage
2. Clicks "Start Health Assessment"
3. Fills out assessment form with valid data
4. Submits form and waits for analysis
5. Views detailed results
6. Can start new assessment

### Emergency Scenario
1. User submits symptoms indicating emergency
2. System displays high-risk results
3. Emergency recommendations are highlighted
4. Proper urgency indicators are shown

### Error Handling
1. API server errors are handled gracefully
2. Network timeouts display appropriate messages
3. Form validation prevents invalid submissions
4. User can retry after errors

### Accessibility Flow
1. User navigates entirely with keyboard
2. Screen reader announcements work correctly
3. Focus indicators are visible
4. All interactive elements are accessible

## Mocking and Test Data

### API Mocking
Tests use Playwright's built-in request interception to mock API responses:

```javascript
await page.route('**/api/assess-health', route => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(mockData)
  });
});
```

### Test Data Scenarios
- **Low Risk**: Common cold, minor symptoms
- **Moderate Risk**: Tension headache, stress-related symptoms
- **High Risk**: Emergency cardiac symptoms
- **Error Cases**: API failures, network issues

## Continuous Integration

### GitHub Actions
The E2E tests run automatically in CI/CD pipeline:
1. After backend and frontend unit tests pass
2. On pull requests to main branch
3. On pushes to main/develop branches

### Test Reports
- HTML reports with screenshots and videos
- JSON results for programmatic analysis
- Artifact uploads for failed test debugging

## Best Practices

### Writing Tests
1. Use descriptive test names that explain the scenario
2. Follow AAA pattern (Arrange, Act, Assert)
3. Mock external dependencies consistently
4. Test both happy path and error scenarios
5. Include accessibility checks in functional tests

### Maintenance
1. Update test data when API responses change
2. Verify tests work with new UI components
3. Keep browser versions updated
4. Monitor test performance and execution time

### Debugging
1. Use `--debug` flag for step-by-step debugging
2. Check screenshots and videos for failed tests
3. Use `page.pause()` for interactive debugging
4. Verify network requests in browser dev tools

## Performance Benchmarks

### Target Metrics
- Homepage load: < 5 seconds
- Form submission: < 10 seconds (including API)
- Assessment results display: < 15 seconds
- Mobile performance: < 2x desktop time

### Monitoring
Tests automatically fail if performance degrades beyond acceptable limits:
- Page load timeouts at 30 seconds
- API response timeouts at 15 seconds
- Individual action timeouts at 10 seconds

## Troubleshooting

### Common Issues

**Tests fail with "Target page, context or browser has been closed"**
- Check if development servers are running
- Verify base URL in config matches running server
- Ensure no port conflicts

**Flaky tests on CI**
- Increase timeouts for slower CI environment
- Add wait conditions for dynamic content
- Check for race conditions in async operations

**Browser installation issues**
- Run `npx playwright install --with-deps`
- Check system requirements for browser dependencies
- Consider using Docker for consistent environment

**Test timeout issues**
- Verify backend server is responding
- Check network conditions and API response times
- Increase timeout values if necessary

## Contributing

When adding new E2E tests:
1. Follow existing naming conventions
2. Add appropriate test documentation
3. Update this README if new scenarios are covered
4. Ensure tests are deterministic and reliable
5. Test locally before pushing to CI
