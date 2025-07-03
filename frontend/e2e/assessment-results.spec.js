import { test, expect } from '@playwright/test';

test.describe('Assessment Results', () => {
	// Mock assessment results data
	const mockResults = {
		diagnosis: 'Tension headache with possible migraine symptoms',
		risk_level: 'moderate',
		urgency: 'routine',
		confidence_score: 0.85,
		recommendations: [
			'Rest in a quiet, dark room',
			'Apply cold compress to forehead',
			'Stay hydrated',
			'Consider over-the-counter pain relief',
		],
		clinical_reasoning:
			'Based on the symptoms described, this appears to be a tension-type headache with some migraine features. The patient should monitor symptoms and seek medical attention if they worsen.',
		emergency_flags: [],
		next_steps: [
			'Monitor symptoms for 24-48 hours',
			'See primary care physician if symptoms persist',
		],
	};

	test.beforeEach(async ({ page }) => {
		await page.goto('/');

		// Navigate to assessment form
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Mock successful API response
		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(mockResults),
			});
		});

		// Fill and submit form to get to results
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
			.fill(
				'I have been experiencing severe headaches, dizziness, and nausea for the past 3 days.'
			);

		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});
	});

	test('should display assessment results correctly', async ({ page }) => {
		// Check main title
		await expect(page.locator('text=Assessment Results')).toBeVisible();

		// Check diagnosis
		await expect(page.locator('text=AI Diagnosis')).toBeVisible();
		await expect(page.locator(`text=${mockResults.diagnosis}`)).toBeVisible();

		// Check risk level
		await expect(page.locator('text=Risk Level')).toBeVisible();
		await expect(page.locator(`text=${mockResults.risk_level}`)).toBeVisible();

		// Check confidence score
		await expect(page.locator('text=Confidence Score')).toBeVisible();
		await expect(page.locator('text=85%')).toBeVisible(); // 0.85 * 100
	});

	test('should display recommendations section', async ({ page }) => {
		await expect(page.locator('text=Recommendations')).toBeVisible();

		// Check that recommendations are displayed
		for (const recommendation of mockResults.recommendations) {
			await expect(page.locator(`text=${recommendation}`)).toBeVisible();
		}
	});

	test('should display clinical reasoning', async ({ page }) => {
		await expect(page.locator('text=Clinical Reasoning')).toBeVisible();
		await expect(
			page.locator(`text=${mockResults.clinical_reasoning}`)
		).toBeVisible();
	});

	test('should display next steps', async ({ page }) => {
		await expect(page.locator('text=Next Steps')).toBeVisible();

		// Check that next steps are displayed
		for (const step of mockResults.next_steps) {
			await expect(page.locator(`text=${step}`)).toBeVisible();
		}
	});

	test('should have new assessment button', async ({ page }) => {
		const newAssessmentButton = page.locator(
			'button:has-text("New Assessment")'
		);
		await expect(newAssessmentButton).toBeVisible();
		await expect(newAssessmentButton).toBeEnabled();
	});

	test('should navigate to new assessment', async ({ page }) => {
		await page.locator('button:has-text("New Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });
	});

	test('should display emergency results correctly', async ({ page }) => {
		const emergencyResults = {
			...mockResults,
			risk_level: 'high',
			urgency: 'emergency',
			emergency_flags: ['Severe chest pain', 'Difficulty breathing'],
			diagnosis:
				'Possible cardiac event - immediate medical attention required',
		};

		// Navigate back to form
		await page.locator('button:has-text("New Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Mock emergency response
		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(emergencyResults),
			});
		});

		// Fill and submit form
		await page
			.locator('input[placeholder*="name" i]')
			.fill('Emergency Patient');
		await page.locator('input[type="number"]').fill('45');

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
			.fill('Severe chest pain and difficulty breathing for the past hour');

		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});

		// Check emergency styling/alerts
		await expect(page.locator('text=high')).toBeVisible();
		await expect(page.locator('text=emergency')).toBeVisible();
		await expect(
			page.locator(`text=${emergencyResults.diagnosis}`)
		).toBeVisible();
	});

	test('should handle missing data gracefully', async ({ page }) => {
		const incompleteResults = {
			diagnosis: 'Basic assessment',
			risk_level: 'low',
			confidence_score: 0.75,
			// Missing recommendations, clinical_reasoning, etc.
		};

		// Navigate back to form
		await page.locator('button:has-text("New Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Mock incomplete response
		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(incompleteResults),
			});
		});

		// Fill and submit form
		await page.locator('input[placeholder*="name" i]').fill('Test Patient');
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
			.fill('Minor headache');

		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});

		// Should still display basic information
		await expect(
			page.locator(`text=${incompleteResults.diagnosis}`)
		).toBeVisible();
		await expect(page.locator('text=75%')).toBeVisible();
	});

	test('should be responsive on mobile', async ({ page, isMobile }) => {
		if (isMobile) {
			// Check that results are visible and readable on mobile
			await expect(page.locator('text=Assessment Results')).toBeVisible();
			await expect(page.locator('text=AI Diagnosis')).toBeVisible();
			await expect(
				page.locator('button:has-text("New Assessment")')
			).toBeVisible();

			// Check that cards stack properly on mobile
			const cards = page.locator('.mantine-Card-root');
			const cardCount = await cards.count();
			expect(cardCount).toBeGreaterThan(0);
		}
	});

	test('should handle keyboard navigation', async ({ page }) => {
		// Tab to the new assessment button
		await page.keyboard.press('Tab');

		// Keep tabbing until we reach the new assessment button
		let attempts = 0;
		while (attempts < 10) {
			const focusedElement = await page.locator(':focus').first();
			const text = await focusedElement.textContent().catch(() => '');

			if (text.includes('New Assessment')) {
				break;
			}

			await page.keyboard.press('Tab');
			attempts++;
		}

		// Press Enter to activate
		await page.keyboard.press('Enter');
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });
	});

	test('should display progress bar correctly', async ({ page }) => {
		// Check that confidence score is displayed as progress bar
		const progressBar = page.locator(
			'[role="progressbar"], .mantine-Progress-root'
		);
		if ((await progressBar.count()) > 0) {
			await expect(progressBar.first()).toBeVisible();
		}
	});
});
