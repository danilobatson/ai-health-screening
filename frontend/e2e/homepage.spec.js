import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/');
	});

	test('should display the homepage correctly', async ({ page }) => {
		// Check page title
		await expect(page).toHaveTitle(/AI Health Assessment System/);

		// Check main heading
		await expect(page.locator('h1')).toContainText(
			'AI Health Assessment System'
		);

		// Check subtitle
		await expect(
			page.locator(
				'text=Professional healthcare dashboard powered by Google Gemini AI'
			)
		).toBeVisible();

		// Check badges with more specific selectors
		await expect(
			page.locator('.mantine-Badge-label:has-text("AI Powered")')
		).toBeVisible();
		await expect(
			page.locator('.mantine-Badge-label:has-text("Clinical Grade")')
		).toBeVisible();
		await expect(
			page.locator('.mantine-Badge-label:has-text("Emergency Detection")')
		).toBeVisible();
	});

	test('should display feature cards', async ({ page }) => {
		// Check Health Assessment card with more specific selectors
		await expect(
			page.locator('h3:has-text("Health Assessment")')
		).toBeVisible();
		await expect(
			page.locator('text=AI-powered symptom analysis with 95% accuracy')
		).toBeVisible();

		// Check Risk Analysis card
		await expect(page.locator('h3:has-text("Risk Analysis")')).toBeVisible();
		await expect(
			page.locator('text=Emergency detection and clinical reasoning')
		).toBeVisible();

		// Check AI Insights card
		await expect(page.locator('h3:has-text("AI Insights")')).toBeVisible();
		await expect(
			page.locator(
				'text=Google Gemini integration providing professional medical'
			)
		).toBeVisible();
	});

	test('should have a functioning start assessment button', async ({
		page,
	}) => {
		const startButton = page.locator(
			'button:has-text("Start Health Assessment")'
		);
		await expect(startButton).toBeVisible();
		await expect(startButton).toBeEnabled();

		// Click the button and verify navigation
		await startButton.click();

		// Should navigate to assessment form
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });
	});

	test('should be responsive on mobile', async ({ page, isMobile }) => {
		if (isMobile) {
			// Check that elements are still visible on mobile
			await expect(page.locator('h1')).toBeVisible();
			await expect(
				page.locator('button:has-text("Start Health Assessment")')
			).toBeVisible();

			// Check that cards stack vertically on mobile
			const cards = page.locator(
				'[data-testid="feature-card"], .mantine-Card-root'
			);
			await expect(cards).toHaveCount(3);
		}
	});

	test('should have proper accessibility', async ({ page }) => {
		// Check for proper heading structure
		await expect(page.locator('h1')).toHaveCount(1);

		// Check button accessibility
		const startButton = page.locator(
			'button:has-text("Start Health Assessment")'
		);
		await expect(startButton).toHaveAttribute('type', 'button');

		// Check for alt text on icons (if any images)
		const images = page.locator('img');
		const imageCount = await images.count();

		for (let i = 0; i < imageCount; i++) {
			const img = images.nth(i);
			await expect(img).toHaveAttribute('alt');
		}
	});

	test('should handle keyboard navigation', async ({ page }) => {
		// Tab to the start button
		await page.keyboard.press('Tab');
		const startButton = page.locator(
			'button:has-text("Start Health Assessment")'
		);
		await expect(startButton).toBeFocused();

		// Press Enter to activate
		await page.keyboard.press('Enter');
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });
	});
});
