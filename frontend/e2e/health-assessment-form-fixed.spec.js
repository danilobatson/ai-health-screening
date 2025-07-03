import { test, expect } from '@playwright/test';

test.describe('Health Assessment Form - Fixed', () => {
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

		// Check form section title
		await expect(page.locator('text=Patient Information')).toBeVisible();

		// Check form fields are present (using Mantine-specific selectors)
		await expect(page.locator('label:has-text("Full Name")')).toBeVisible();
		await expect(page.locator('label:has-text("Age")')).toBeVisible();
		await expect(page.locator('label:has-text("Gender")')).toBeVisible();

		// Check submit button
		await expect(
			page.locator('button:has-text("Get AI Health Assessment")')
		).toBeVisible();
	});

	test('should fill form fields successfully', async ({ page }) => {
		// Fill out the form with valid data using more generic selectors
		await page.locator('input[placeholder*="full name" i]').fill('John Doe');
		await page.locator('input[placeholder*="age" i]').fill('30');

		// Select gender using Mantine Select
		await page.locator('input[placeholder*="gender" i]').click();
		// Wait for options to appear and click the first Male option
		await page
			.locator('[data-combobox-option="true"][value="male"]')
			.first()
			.click();

		// Fill symptoms
		await page
			.locator('textarea[placeholder*="headaches" i]')
			.fill(
				'I have been experiencing headaches and fatigue for the past few days.'
			);

		// Verify form fields are filled
		expect(
			await page.locator('input[placeholder*="full name" i]').inputValue()
		).toBe('John Doe');
		expect(await page.locator('input[placeholder*="age" i]').inputValue()).toBe(
			'30'
		);
		expect(
			await page.locator('textarea[placeholder*="headaches" i]').inputValue()
		).toContain('headaches');

		// Verify submit button is enabled
		await expect(
			page.locator('button:has-text("Get AI Health Assessment")')
		).toBeEnabled();
	});

	test('should handle keyboard navigation', async ({ page }) => {
		// Click on the form first to ensure focus
		await page.locator('input[placeholder*="full name" i]').click();

		const nameInput = page.locator('input[placeholder*="full name" i]');
		await expect(nameInput).toBeFocused();

		// Fill using keyboard
		await page.keyboard.type('Test User');
		expect(await nameInput.inputValue()).toBe('Test User');
	});

	test('should be responsive on mobile', async ({ page, isMobile }) => {
		if (isMobile) {
			// Check that form elements are visible and usable on mobile
			await expect(page.locator('label:has-text("Full Name")')).toBeVisible();
			await expect(
				page.locator('button:has-text("Get AI Health Assessment")')
			).toBeVisible();
		}
	});
});
