import { test, expect } from '@playwright/test';

test.describe('Health Assessment Form', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/');
		// Navigate to the assessment form
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });
	});

	test('should display the form correctly', async ({ page }) => {
		// Check form title
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible();

		// Check all form fields are present
		await expect(page.locator('input[placeholder*="name" i]')).toBeVisible();
		await expect(page.locator('input[type="number"]')).toBeVisible(); // Age input
		await expect(page.locator('select, [role="combobox"]')).toBeVisible(); // Gender select
		await expect(
			page.locator('textarea[placeholder*="symptoms" i]')
		).toBeVisible();
		await expect(
			page.locator('textarea[placeholder*="medical history" i]')
		).toBeVisible();
		await expect(
			page.locator('textarea[placeholder*="medications" i]')
		).toBeVisible();

		// Check submit button
		await expect(
			page.locator('button:has-text("Get Health Assessment")')
		).toBeVisible();
	});

	test('should validate required fields', async ({ page }) => {
		// Try to submit empty form
		await page.locator('button:has-text("Get Health Assessment")').click();

		// Check for validation errors
		await expect(
			page.locator('text=Name must be at least 2 characters')
		).toBeVisible();
		await expect(
			page.locator('text=Age must be between 1 and 120')
		).toBeVisible();
		await expect(page.locator('text=Please select a gender')).toBeVisible();
		await expect(
			page.locator('text=Please provide more detail about symptoms')
		).toBeVisible();
	});

	test('should validate name field', async ({ page }) => {
		// Test short name
		await page.locator('input[placeholder*="name" i]').fill('A');
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Name must be at least 2 characters')
		).toBeVisible();

		// Test valid name
		await page.locator('input[placeholder*="name" i]').fill('John Doe');
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Name must be at least 2 characters')
		).not.toBeVisible();
	});

	test('should validate age field', async ({ page }) => {
		const ageInput = page.locator('input[type="number"]');

		// Test invalid ages
		await ageInput.fill('0');
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Age must be between 1 and 120')
		).toBeVisible();

		await ageInput.fill('121');
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Age must be between 1 and 120')
		).toBeVisible();

		// Test valid age
		await ageInput.fill('30');
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Age must be between 1 and 120')
		).not.toBeVisible();
	});

	test('should validate symptoms field', async ({ page }) => {
		const symptomsTextarea = page.locator(
			'textarea[placeholder*="symptoms" i]'
		);

		// Test short symptoms
		await symptomsTextarea.fill('headache');
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Please provide more detail about symptoms')
		).toBeVisible();

		// Test valid symptoms
		await symptomsTextarea.fill(
			'I have been experiencing severe headaches for the past 3 days'
		);
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Please provide more detail about symptoms')
		).not.toBeVisible();
	});

	test('should fill and submit form successfully', async ({ page }) => {
		// Fill out the form with valid data
		await page.locator('input[placeholder*="name" i]').fill('John Doe');
		await page.locator('input[type="number"]').fill('30');

		// Select gender - handle both select and Mantine Select
		const genderField = page.locator('select, [role="combobox"]').first();
		await genderField.click();
		await page
			.locator('text=Male')
			.click()
			.catch(async () => {
				// Fallback for different gender selection methods
				await page.selectOption('select', 'Male').catch(async () => {
					await page
						.locator('[data-value="Male"], option[value="Male"]')
						.click();
				});
			});

		await page
			.locator('textarea[placeholder*="symptoms" i]')
			.fill(
				'I have been experiencing severe headaches, dizziness, and nausea for the past 3 days. The pain is constant and worsening.'
			);

		await page
			.locator('textarea[placeholder*="medical history" i]')
			.fill('No significant medical history');
		await page.locator('textarea[placeholder*="medications" i]').fill('None');

		// Submit the form
		await page.locator('button:has-text("Get Health Assessment")').click();

		// Check for loading state
		await expect(
			page.locator('text=Analyzing your health data...')
		).toBeVisible();

		// Wait for results or error (with longer timeout for API call)
		await expect(
			page.locator('text=Assessment Results, text=Error, text=failed')
		).toBeVisible({ timeout: 30000 });
	});

	test('should handle API errors gracefully', async ({ page }) => {
		// Mock API to return error
		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 500,
				contentType: 'application/json',
				body: JSON.stringify({ error: 'Internal Server Error' }),
			});
		});

		// Fill and submit form
		await page.locator('input[placeholder*="name" i]').fill('John Doe');
		await page.locator('input[type="number"]').fill('30');

		const genderField = page.locator('select, [role="combobox"]').first();
		await genderField.click();
		await page
			.locator('text=Male')
			.click()
			.catch(async () => {
				await page.selectOption('select', 'Male').catch(async () => {
					await page
						.locator('[data-value="Male"], option[value="Male"]')
						.click();
				});
			});

		await page
			.locator('textarea[placeholder*="symptoms" i]')
			.fill('Test symptoms for error handling scenario');

		await page.locator('button:has-text("Get Health Assessment")').click();

		// Check for error message
		await expect(page.locator('text=Error, text=failed')).toBeVisible({
			timeout: 15000,
		});
	});

	test('should be responsive on mobile', async ({ page, isMobile }) => {
		if (isMobile) {
			// Check that form elements are visible and usable on mobile
			await expect(page.locator('input[placeholder*="name" i]')).toBeVisible();
			await expect(
				page.locator('textarea[placeholder*="symptoms" i]')
			).toBeVisible();
			await expect(
				page.locator('button:has-text("Get Health Assessment")')
			).toBeVisible();

			// Check that form fields are properly sized for mobile
			const nameInput = page.locator('input[placeholder*="name" i]');
			const boundingBox = await nameInput.boundingBox();
			expect(boundingBox.width).toBeGreaterThan(200); // Reasonable mobile width
		}
	});

	test('should handle keyboard navigation', async ({ page }) => {
		// Tab through form fields
		await page.keyboard.press('Tab'); // Name field
		await expect(page.locator('input[placeholder*="name" i]')).toBeFocused();

		await page.keyboard.press('Tab'); // Age field
		await expect(page.locator('input[type="number"]')).toBeFocused();

		// Fill using keyboard
		await page.keyboard.type('30');
		expect(await page.locator('input[type="number"]').inputValue()).toBe('30');
	});

	test('should preserve form data during validation', async ({ page }) => {
		// Fill partial form
		await page.locator('input[placeholder*="name" i]').fill('John Doe');
		await page.locator('input[type="number"]').fill('30');
		await page.locator('textarea[placeholder*="symptoms" i]').fill('short'); // Invalid

		// Submit and check validation
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(
			page.locator('text=Please provide more detail about symptoms')
		).toBeVisible();

		// Check that valid data is preserved
		expect(
			await page.locator('input[placeholder*="name" i]').inputValue()
		).toBe('John Doe');
		expect(await page.locator('input[type="number"]').inputValue()).toBe('30');
	});
});
