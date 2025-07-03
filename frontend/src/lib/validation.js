// Validation utility functions
export const validateForm = (data) => {
	const errors = {};

	if (!data.name || data.name.length < 2) {
		errors.name = 'Name must be at least 2 characters';
	}

	const age = parseInt(data.age);
	if (!age || age < 1 || age > 120) {
		errors.age = 'Age must be between 1 and 120 years';
	}

	if (!data.gender) {
		errors.gender = 'Please select a gender';
	}

	if (!data.symptoms || data.symptoms.length < 10) {
		errors.symptoms =
			'Please provide more detail about symptoms (minimum 10 characters)';
	}

	return { isValid: Object.keys(errors).length === 0, errors };
};

export const sanitizeFormData = (formData) => {
	return {
		name: String(formData.name || '').trim(),
		age: parseInt(formData.age) || 0,
		gender: String(formData.gender || ''),
		symptoms: String(formData.symptoms || '').trim(),
		medical_history: String(formData.medical_history || '').trim(),
		current_medications: String(formData.current_medications || '').trim(),
	};
};

export const getRiskColor = (riskLevel) => {
	switch (riskLevel?.toLowerCase()) {
		case 'low':
			return 'green';
		case 'moderate':
			return 'yellow';
		case 'high':
			return 'red';
		default:
			return 'blue';
	}
};

export const formatConfidenceScore = (score) => {
	if (typeof score !== 'number' || isNaN(score)) {
		return 0;
	}
	return Math.round(score * 100);
};
