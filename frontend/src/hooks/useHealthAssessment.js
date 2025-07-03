import { useState, useCallback } from 'react';
import { validateForm, sanitizeFormData } from '../lib/validation';

const API_BASE_URL =
	process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000';

export const useHealthAssessment = () => {
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');
	const [result, setResult] = useState(null);

	const submitAssessment = useCallback(async (formData) => {
		// Validate form
		const validation = validateForm(formData);
		if (!validation.isValid) {
			const errorMessage = Object.values(validation.errors)[0];
			setError(errorMessage);
			throw new Error(errorMessage);
		}

		setLoading(true);
		setError('');
		setResult(null);

		try {
			// Sanitize data
			const cleanData = sanitizeFormData(formData);

			const response = await fetch(`${API_BASE_URL}/api/assess-health`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(cleanData),
			});

			const contentType = response.headers.get('content-type');
			if (!contentType || !contentType.includes('application/json')) {
				throw new Error(
					`Server returned non-JSON response: ${response.status}`
				);
			}

			const data = await response.json();

			if (!response.ok) {
				const errorMessage =
					data.error ||
					data.message ||
					`HTTP ${response.status}: ${response.statusText}`;
				throw new Error(errorMessage);
			}

			setResult(data);
			return data;
		} catch (err) {
			const errorMessage =
				err.message || 'Assessment failed. Please try again.';
			setError(errorMessage);
			throw err;
		} finally {
			setLoading(false);
		}
	}, []);

	const reset = useCallback(() => {
		setLoading(false);
		setError('');
		setResult(null);
	}, []);

	return {
		loading,
		error,
		result,
		submitAssessment,
		reset,
	};
};
