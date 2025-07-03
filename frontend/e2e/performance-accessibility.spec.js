import { test, expect } from '@playwright/test';

test.describe('Performance and Accessibility', () => {
	test('should load homepage within acceptable time', async ({ page }) => {
		const startTime = Date.now();

		await page.goto('/');
		await expect(
			page.locator('h1:has-text("AI Health Assessment System")')
		).toBeVisible();

		const loadTime = Date.now() - startTime;
		expect(loadTime).toBeLessThan(5000); // Should load within 5 seconds
	});

	test('should have proper accessibility features', async ({ page }) => {
		await page.goto('/');

		// Check for proper heading hierarchy
		await expect(page.locator('h1')).toHaveCount(1);
		const h1Text = await page.locator('h1').textContent();
		expect(h1Text).toContain('AI Health Assessment System');

		// Check for proper button accessibility
		const startButton = page.locator(
			'button:has-text("Start Health Assessment")'
		);
		await expect(startButton).toBeVisible();

		// Check that button is keyboard accessible
		await page.keyboard.press('Tab');
		await expect(startButton).toBeFocused();

		// Check for proper color contrast (basic check)
		const buttonStyles = await startButton.evaluate((el) => {
			const styles = window.getComputedStyle(el);
			return {
				backgroundColor: styles.backgroundColor,
				color: styles.color,
			};
		});

		expect(buttonStyles.backgroundColor).not.toBe('transparent');
		expect(buttonStyles.color).not.toBe('transparent');
	});

	test('should be keyboard navigable throughout the app', async ({ page }) => {
		await page.goto('/');

		// Start with Tab navigation
		await page.keyboard.press('Tab');
		const startButton = page.locator(
			'button:has-text("Start Health Assessment")'
		);
		await expect(startButton).toBeFocused();

		// Navigate to form using keyboard
		await page.keyboard.press('Enter');
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Tab through form fields
		await page.keyboard.press('Tab'); // Name field
		await expect(page.locator('input[placeholder*="name" i]')).toBeFocused();

		await page.keyboard.press('Tab'); // Age field
		await expect(page.locator('input[type="number"]')).toBeFocused();

		// Fill using keyboard
		await page.keyboard.type('John Doe');
		await page.keyboard.press('Tab');
		await page.keyboard.type('30');
	});

	test('should handle large form submissions efficiently', async ({ page }) => {
		await page.goto('/');
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Mock response with delay to test performance
		await page.route('**/api/assess-health', async (route) => {
			await new Promise((resolve) => setTimeout(resolve, 2000)); // 2 second delay
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					diagnosis: 'Test diagnosis',
					risk_level: 'low',
					confidence_score: 0.8,
					recommendations: ['Test recommendation'],
					clinical_reasoning: 'Test reasoning',
					next_steps: ['Test step'],
				}),
			});
		});

		// Fill form with large amounts of data
		await page
			.locator('input[placeholder*="name" i]')
			.fill('Performance Test User');
		await page.locator('input[type="number"]').fill('35');

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

		// Large symptoms description
		const largeSymptoms =
			'This is a very detailed description of symptoms that includes multiple aspects of the patient presentation. '.repeat(
				10
			);
		await page
			.locator('textarea[placeholder*="symptoms" i]')
			.fill(largeSymptoms);

		const largeMedicalHistory =
			'Extensive medical history with multiple conditions and treatments over many years. '.repeat(
				5
			);
		await page
			.locator('textarea[placeholder*="medical history" i]')
			.fill(largeMedicalHistory);

		const largeMedications =
			'Multiple medications including dosages and schedules for various conditions. '.repeat(
				3
			);
		await page
			.locator('textarea[placeholder*="medications" i]')
			.fill(largeMedications);

		// Submit and verify it handles the load
		const submitTime = Date.now();
		await page.locator('button:has-text("Get Health Assessment")').click();

		// Should show loading state
		await expect(
			page.locator('text=Analyzing your health data...')
		).toBeVisible();

		// Should complete within reasonable time
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});

		const totalTime = Date.now() - submitTime;
		expect(totalTime).toBeLessThan(10000); // Should complete within 10 seconds
	});

	test('should handle multiple rapid submissions gracefully', async ({
		page,
	}) => {
		await page.goto('/');
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Mock fast response
		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					diagnosis: 'Quick test',
					risk_level: 'low',
					confidence_score: 0.7,
					recommendations: ['Rest'],
					clinical_reasoning: 'Simple case',
					next_steps: ['Monitor'],
				}),
			});
		});

		// Fill form quickly
		await page.locator('input[placeholder*="name" i]').fill('Rapid Test');
		await page.locator('input[type="number"]').fill('25');

		const genderField = page.locator('select, [role="combobox"]').first();
		await genderField.click();
		await page
			.locator('text=Female')
			.click()
			.catch(async () => {
				await page.selectOption('select', 'Female').catch(async () => {
					await page
						.locator('[data-value="Female"], option[value="Female"]')
						.click();
				});
			});

		await page
			.locator('textarea[placeholder*="symptoms" i]')
			.fill('Quick symptoms test');

		// Try multiple rapid submissions (should be prevented)
		const submitButton = page.locator(
			'button:has-text("Get Health Assessment")'
		);

		await submitButton.click();

		// Button should be disabled during submission
		await expect(submitButton).toBeDisabled();

		// Wait for completion
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 10000,
		});
	});

	test('should maintain performance with different viewport sizes', async ({
		page,
	}) => {
		// Test desktop size
		await page.setViewportSize({ width: 1920, height: 1080 });
		const desktopStart = Date.now();
		await page.goto('/');
		await expect(page.locator('h1')).toBeVisible();
		const desktopTime = Date.now() - desktopStart;

		// Test tablet size
		await page.setViewportSize({ width: 768, height: 1024 });
		const tabletStart = Date.now();
		await page.reload();
		await expect(page.locator('h1')).toBeVisible();
		const tabletTime = Date.now() - tabletStart;

		// Test mobile size
		await page.setViewportSize({ width: 375, height: 667 });
		const mobileStart = Date.now();
		await page.reload();
		await expect(page.locator('h1')).toBeVisible();
		const mobileTime = Date.now() - mobileStart;

		// All should load within reasonable time
		expect(desktopTime).toBeLessThan(5000);
		expect(tabletTime).toBeLessThan(5000);
		expect(mobileTime).toBeLessThan(5000);

		// Mobile shouldn't be significantly slower
		expect(mobileTime).toBeLessThan(desktopTime * 2);
	});

	test('should handle network conditions gracefully', async ({ page }) => {
		// Simulate slow network
		await page.route('**/api/assess-health', (route) => {
			setTimeout(() => {
				route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						diagnosis: 'Slow network test',
						risk_level: 'low',
						confidence_score: 0.75,
						recommendations: ['Network test'],
						clinical_reasoning: 'Tested under slow conditions',
						next_steps: ['Continue monitoring'],
					}),
				});
			}, 5000); // 5 second delay
		});

		await page.goto('/');
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Fill and submit
		await page
			.locator('input[placeholder*="name" i]')
			.fill('Slow Network Test');
		await page.locator('input[type="number"]').fill('30');

		const genderField = page.locator('select, [role="combobox"]').first();
		await genderField.click();
		await page
			.locator('text=Other')
			.click()
			.catch(async () => {
				await page.selectOption('select', 'Other').catch(async () => {
					await page
						.locator('[data-value="Other"], option[value="Other"]')
						.click();
				});
			});

		await page
			.locator('textarea[placeholder*="symptoms" i]')
			.fill('Testing slow network conditions');

		await page.locator('button:has-text("Get Health Assessment")').click();

		// Should show loading state immediately
		await expect(
			page.locator('text=Analyzing your health data...')
		).toBeVisible({ timeout: 1000 });

		// Should eventually complete
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});
	});

	test('should handle concurrent users simulation', async ({ browser }) => {
		// Create multiple browser contexts to simulate concurrent users
		const contexts = await Promise.all([
			browser.newContext(),
			browser.newContext(),
			browser.newContext(),
		]);

		const pages = await Promise.all(
			contexts.map((context) => context.newPage())
		);

		// Mock API for all pages
		for (const page of pages) {
			await page.route('**/api/assess-health', (route) => {
				route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						diagnosis: 'Concurrent user test',
						risk_level: 'low',
						confidence_score: 0.8,
						recommendations: ['Test passed'],
						clinical_reasoning: 'Concurrent testing successful',
						next_steps: ['Continue testing'],
					}),
				});
			});
		}

		// Run concurrent user flows
		const userFlows = pages.map(async (page, index) => {
			await page.goto('/');
			await page.locator('button:has-text("Start Health Assessment")').click();
			await expect(
				page.locator('h1:has-text("AI Health Assessment")')
			).toBeVisible({ timeout: 10000 });

			await page
				.locator('input[placeholder*="name" i]')
				.fill(`User ${index + 1}`);
			await page.locator('input[type="number"]').fill(`${25 + index}`);

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
				.fill(`Symptoms for user ${index + 1}`);
			await page.locator('button:has-text("Get Health Assessment")').click();

			await expect(page.locator('text=Assessment Results')).toBeVisible({
				timeout: 15000,
			});
		});

		// All users should complete successfully
		await Promise.all(userFlows);

		// Clean up
		await Promise.all(contexts.map((context) => context.close()));
	});
});
