import {
	validateForm,
	sanitizeFormData,
	getRiskColor,
	formatConfidenceScore,
} from '../../lib/validation';

describe('Validation Utilities', () => {
	describe('validateForm', () => {
		test('returns valid for complete form data', () => {
			const validData = {
				name: 'John Doe',
				age: '30',
				gender: 'male',
				symptoms: 'Experiencing headaches and fatigue for the past week',
			};

			const result = validateForm(validData);

			expect(result.isValid).toBe(true);
			expect(Object.keys(result.errors)).toHaveLength(0);
		});

		test('validates name requirement', () => {
			const invalidData = {
				name: '',
				age: '30',
				gender: 'male',
				symptoms: 'Valid symptoms here',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.name).toBe('Name must be at least 2 characters');
		});

		test('validates name minimum length', () => {
			const invalidData = {
				name: 'A',
				age: '30',
				gender: 'male',
				symptoms: 'Valid symptoms here',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.name).toBe('Name must be at least 2 characters');
		});

		test('validates age requirement', () => {
			const invalidData = {
				name: 'John Doe',
				age: '',
				gender: 'male',
				symptoms: 'Valid symptoms here',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.age).toBe('Age must be between 1 and 120 years');
		});

		test('validates age range - too low', () => {
			const invalidData = {
				name: 'John Doe',
				age: '0',
				gender: 'male',
				symptoms: 'Valid symptoms here',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.age).toBe('Age must be between 1 and 120 years');
		});

		test('validates age range - too high', () => {
			const invalidData = {
				name: 'John Doe',
				age: '150',
				gender: 'male',
				symptoms: 'Valid symptoms here',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.age).toBe('Age must be between 1 and 120 years');
		});

		test('validates gender requirement', () => {
			const invalidData = {
				name: 'John Doe',
				age: '30',
				gender: '',
				symptoms: 'Valid symptoms here',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.gender).toBe('Please select a gender');
		});

		test('validates symptoms requirement', () => {
			const invalidData = {
				name: 'John Doe',
				age: '30',
				gender: 'male',
				symptoms: '',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.symptoms).toBe(
				'Please provide more detail about symptoms (minimum 10 characters)'
			);
		});

		test('validates symptoms minimum length', () => {
			const invalidData = {
				name: 'John Doe',
				age: '30',
				gender: 'male',
				symptoms: 'headache',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(result.errors.symptoms).toBe(
				'Please provide more detail about symptoms (minimum 10 characters)'
			);
		});

		test('returns multiple errors for multiple invalid fields', () => {
			const invalidData = {
				name: '',
				age: '0',
				gender: '',
				symptoms: '',
			};

			const result = validateForm(invalidData);

			expect(result.isValid).toBe(false);
			expect(Object.keys(result.errors)).toHaveLength(4);
			expect(result.errors.name).toBeDefined();
			expect(result.errors.age).toBeDefined();
			expect(result.errors.gender).toBeDefined();
			expect(result.errors.symptoms).toBeDefined();
		});
	});

	describe('sanitizeFormData', () => {
		test('sanitizes complete form data', () => {
			const rawData = {
				name: '  John Doe  ',
				age: '30',
				gender: 'male',
				symptoms: '  Headache and fatigue  ',
				medical_history: '  Previous surgery  ',
				current_medications: '  Aspirin  ',
			};

			const result = sanitizeFormData(rawData);

			expect(result).toEqual({
				name: 'John Doe',
				age: 30,
				gender: 'male',
				symptoms: 'Headache and fatigue',
				medical_history: 'Previous surgery',
				current_medications: 'Aspirin',
			});
		});

		test('handles missing fields gracefully', () => {
			const rawData = {
				name: 'John Doe',
				age: '30',
			};

			const result = sanitizeFormData(rawData);

			expect(result).toEqual({
				name: 'John Doe',
				age: 30,
				gender: '',
				symptoms: '',
				medical_history: '',
				current_medications: '',
			});
		});

		test('handles null and undefined values', () => {
			const rawData = {
				name: null,
				age: undefined,
				gender: 'male',
				symptoms: null,
				medical_history: undefined,
				current_medications: '',
			};

			const result = sanitizeFormData(rawData);

			expect(result).toEqual({
				name: '',
				age: 0,
				gender: 'male',
				symptoms: '',
				medical_history: '',
				current_medications: '',
			});
		});

		test('handles invalid age values', () => {
			const rawData = {
				name: 'John Doe',
				age: 'not-a-number',
				gender: 'male',
				symptoms: 'Valid symptoms',
			};

			const result = sanitizeFormData(rawData);

			expect(result.age).toBe(0);
		});

		test('converts non-string values to strings', () => {
			const rawData = {
				name: 123,
				age: '30',
				gender: true,
				symptoms: ['symptom1', 'symptom2'],
				medical_history: { history: 'test' },
				current_medications: null,
			};

			const result = sanitizeFormData(rawData);

			expect(typeof result.name).toBe('string');
			expect(typeof result.gender).toBe('string');
			expect(typeof result.symptoms).toBe('string');
			expect(typeof result.medical_history).toBe('string');
			expect(typeof result.current_medications).toBe('string');
		});
	});

	describe('getRiskColor', () => {
		test('returns correct color for low risk', () => {
			expect(getRiskColor('low')).toBe('green');
			expect(getRiskColor('LOW')).toBe('green');
			expect(getRiskColor('Low')).toBe('green');
		});

		test('returns correct color for moderate risk', () => {
			expect(getRiskColor('moderate')).toBe('yellow');
			expect(getRiskColor('MODERATE')).toBe('yellow');
			expect(getRiskColor('Moderate')).toBe('yellow');
		});

		test('returns correct color for high risk', () => {
			expect(getRiskColor('high')).toBe('red');
			expect(getRiskColor('HIGH')).toBe('red');
			expect(getRiskColor('High')).toBe('red');
		});

		test('returns default color for unknown risk levels', () => {
			expect(getRiskColor('unknown')).toBe('blue');
			expect(getRiskColor('medium')).toBe('blue');
			expect(getRiskColor('')).toBe('blue');
		});

		test('handles null and undefined values', () => {
			expect(getRiskColor(null)).toBe('blue');
			expect(getRiskColor(undefined)).toBe('blue');
		});
	});

	describe('formatConfidenceScore', () => {
		test('converts decimal to percentage', () => {
			expect(formatConfidenceScore(0.85)).toBe(85);
			expect(formatConfidenceScore(0.5)).toBe(50);
			expect(formatConfidenceScore(1.0)).toBe(100);
			expect(formatConfidenceScore(0.0)).toBe(0);
		});

		test('rounds to nearest integer', () => {
			expect(formatConfidenceScore(0.856)).toBe(86);
			expect(formatConfidenceScore(0.854)).toBe(85);
			expect(formatConfidenceScore(0.999)).toBe(100);
		});

		test('handles edge cases', () => {
			expect(formatConfidenceScore(0)).toBe(0);
			expect(formatConfidenceScore(1)).toBe(100);
			expect(formatConfidenceScore(1.5)).toBe(150); // Over 100%
		});

		test('handles invalid inputs', () => {
			expect(formatConfidenceScore(null)).toBe(0);
			expect(formatConfidenceScore(undefined)).toBe(0);
			expect(formatConfidenceScore('0.85')).toBe(0);
			expect(formatConfidenceScore(NaN)).toBe(0);
			expect(formatConfidenceScore({})).toBe(0);
			expect(formatConfidenceScore([])).toBe(0);
		});
	});
});
