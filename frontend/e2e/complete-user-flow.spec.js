import { test, expect } from '@playwright/test';

test.describe('Complete User Flow', () => {
	test('should complete full health assessment journey', async ({ page }) => {
		// Mock successful API response
		const mockResults = {
			diagnosis: 'Tension headache with possible stress-related symptoms',
			risk_level: 'moderate',
			urgency: 'routine',
			confidence_score: 0.88,
			recommendations: [
				'Get adequate rest and sleep',
				'Stay hydrated throughout the day',
				'Practice stress management techniques',
				'Consider over-the-counter pain relief if needed',
			],
			clinical_reasoning:
				'The symptoms described are consistent with tension-type headache, likely exacerbated by stress. The patient should monitor symptoms and implement lifestyle modifications.',
			emergency_flags: [],
			next_steps: [
				'Monitor symptoms for 2-3 days',
				'Schedule appointment with primary care if symptoms persist',
				'Return immediately if symptoms worsen significantly',
			],
		};

		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(mockResults),
			});
		});

		// Step 1: Start on homepage
		await page.goto('/');
		await expect(
			page.locator('h1:has-text("AI Health Assessment System")')
		).toBeVisible();

		// Step 2: Navigate to assessment form
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Step 3: Fill out the assessment form
		await page.locator('input[placeholder*="name" i]').fill('Alice Johnson');
		await page.locator('input[type="number"]').fill('32');

		// Handle gender selection
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

		// Fill symptoms with detailed description
		await page
			.locator('textarea[placeholder*="symptoms" i]')
			.fill(
				'I have been experiencing persistent headaches for the past week, particularly in the temples and forehead area. The pain is described as a tight band around my head, and it worsens during stressful work periods. I also notice some neck tension and occasional dizziness when the headache is severe.'
			);

		// Fill medical history
		await page
			.locator('textarea[placeholder*="medical history" i]')
			.fill(
				'No significant medical history. Occasional headaches in the past but not this persistent. No known allergies.'
			);

		// Fill current medications
		await page
			.locator('textarea[placeholder*="medications" i]')
			.fill('Multivitamin daily, occasionally ibuprofen for headaches');

		// Step 4: Submit the assessment
		await page.locator('button:has-text("Get Health Assessment")').click();

		// Step 5: Wait for loading state
		await expect(
			page.locator('text=Analyzing your health data...')
		).toBeVisible();

		// Step 6: Verify results are displayed
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});

		// Step 7: Verify all result sections are present
		await expect(page.locator('text=AI Diagnosis')).toBeVisible();
		await expect(page.locator(`text=${mockResults.diagnosis}`)).toBeVisible();

		await expect(page.locator('text=Risk Level')).toBeVisible();
		await expect(page.locator('text=moderate')).toBeVisible();

		await expect(page.locator('text=Confidence Score')).toBeVisible();
		await expect(page.locator('text=88%')).toBeVisible();

		await expect(page.locator('text=Recommendations')).toBeVisible();
		for (const recommendation of mockResults.recommendations) {
			await expect(page.locator(`text=${recommendation}`)).toBeVisible();
		}

		await expect(page.locator('text=Clinical Reasoning')).toBeVisible();
		await expect(
			page.locator(`text=${mockResults.clinical_reasoning}`)
		).toBeVisible();

		await expect(page.locator('text=Next Steps')).toBeVisible();
		for (const step of mockResults.next_steps) {
			await expect(page.locator(`text=${step}`)).toBeVisible();
		}

		// Step 8: Test new assessment functionality
		await page.locator('button:has-text("New Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Verify form is reset
		expect(
			await page.locator('input[placeholder*="name" i]').inputValue()
		).toBe('');
		expect(await page.locator('input[type="number"]').inputValue()).toBe('');
		expect(
			await page.locator('textarea[placeholder*="symptoms" i]').inputValue()
		).toBe('');
	});

	test('should handle emergency case flow', async ({ page }) => {
		// Mock emergency response
		const emergencyResults = {
			diagnosis:
				'Acute chest pain - possible cardiac event. IMMEDIATE MEDICAL ATTENTION REQUIRED.',
			risk_level: 'high',
			urgency: 'emergency',
			confidence_score: 0.92,
			recommendations: [
				'CALL 911 IMMEDIATELY',
				'Do not drive yourself to hospital',
				'Take aspirin if not allergic (325mg)',
				'Remain calm and still',
			],
			clinical_reasoning:
				'The constellation of symptoms including chest pain, shortness of breath, and associated symptoms suggests a possible acute coronary syndrome. This requires immediate emergency medical evaluation.',
			emergency_flags: [
				'Chest pain with radiation',
				'Shortness of breath',
				'Possible cardiac symptoms',
			],
			next_steps: [
				'EMERGENCY DEPARTMENT IMMEDIATELY',
				'Do not delay seeking medical care',
				'Have someone drive you or call ambulance',
			],
		};

		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(emergencyResults),
			});
		});

		// Navigate to assessment
		await page.goto('/');
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Fill emergency scenario
		await page
			.locator('input[placeholder*="name" i]')
			.fill('Emergency Patient');
		await page.locator('input[type="number"]').fill('55');

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
				'Severe crushing chest pain that started 30 minutes ago, radiating to my left arm and jaw. I am short of breath and feeling nauseous. The pain is unlike anything I have experienced before.'
			);

		await page
			.locator('textarea[placeholder*="medical history" i]')
			.fill(
				'History of high blood pressure, father had heart attack at age 60'
			);

		await page
			.locator('textarea[placeholder*="medications" i]')
			.fill('Lisinopril for blood pressure');

		// Submit emergency assessment
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});

		// Verify emergency indicators
		await expect(page.locator('text=high')).toBeVisible();
		await expect(page.locator('text=emergency')).toBeVisible();
		await expect(page.locator('text=CALL 911 IMMEDIATELY')).toBeVisible();
		await expect(
			page.locator('text=EMERGENCY DEPARTMENT IMMEDIATELY')
		).toBeVisible();
	});

	test('should handle API error gracefully in full flow', async ({ page }) => {
		// Mock API error
		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 500,
				contentType: 'application/json',
				body: JSON.stringify({ error: 'Internal server error' }),
			});
		});

		// Complete flow until error
		await page.goto('/');
		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Fill form
		await page.locator('input[placeholder*="name" i]').fill('Test User');
		await page.locator('input[type="number"]').fill('28');

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
			.fill('Test symptoms for error handling scenario');

		// Submit and expect error
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(page.locator('text=Error, text=failed')).toBeVisible({
			timeout: 15000,
		});

		// Verify user can retry
		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(page.locator('text=Error, text=failed')).toBeVisible({
			timeout: 15000,
		});
	});

	test('should work correctly on mobile devices', async ({
		page,
		isMobile,
	}) => {
		if (!isMobile) {
			test.skip();
		}

		// Mock response for mobile
		const mobileResults = {
			diagnosis: 'Common cold with upper respiratory symptoms',
			risk_level: 'low',
			urgency: 'routine',
			confidence_score: 0.78,
			recommendations: ['Rest', 'Fluids', 'Monitor symptoms'],
			clinical_reasoning: 'Typical viral upper respiratory infection symptoms.',
			next_steps: ['Self-care for 5-7 days', 'See doctor if symptoms worsen'],
		};

		await page.route('**/api/assess-health', (route) => {
			route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(mobileResults),
			});
		});

		// Complete mobile flow
		await page.goto('/');
		await expect(page.locator('h1')).toBeVisible();

		await page.locator('button:has-text("Start Health Assessment")').click();
		await expect(
			page.locator('h1:has-text("AI Health Assessment")')
		).toBeVisible({ timeout: 10000 });

		// Fill form on mobile
		await page.locator('input[placeholder*="name" i]').fill('Mobile User');
		await page.locator('input[type="number"]').fill('25');

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
			.fill('Runny nose, mild cough, and fatigue for 2 days');

		await page.locator('button:has-text("Get Health Assessment")').click();
		await expect(page.locator('text=Assessment Results')).toBeVisible({
			timeout: 15000,
		});

		// Verify mobile layout
		await expect(page.locator('text=78%')).toBeVisible();
		await expect(
			page.locator('button:has-text("New Assessment")')
		).toBeVisible();
	});
});
