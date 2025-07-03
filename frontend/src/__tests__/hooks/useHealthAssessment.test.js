import { renderHook, act } from '@testing-library/react';
import { useHealthAssessment } from '../../hooks/useHealthAssessment';

// Mock fetch globally
global.fetch = jest.fn();

describe('useHealthAssessment', () => {
	beforeEach(() => {
		fetch.mockClear();
	});

	describe('Initial State', () => {
		test('returns initial state correctly', () => {
			const { result } = renderHook(() => useHealthAssessment());

			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe('');
			expect(result.current.result).toBe(null);
			expect(typeof result.current.submitAssessment).toBe('function');
			expect(typeof result.current.reset).toBe('function');
		});
	});

	describe('submitAssessment', () => {
		const validFormData = {
			name: 'John Doe',
			age: '30',
			gender: 'male',
			symptoms: 'Experiencing headaches and fatigue for the past week',
			medical_history: 'No significant medical history',
			current_medications: 'None',
		};

		test('successfully submits valid form data', async () => {
			const mockResponse = {
				assessment: 'Based on the symptoms, this could be stress-related.',
				recommendations: ['Get adequate rest', 'Stay hydrated'],
				urgency: 'routine',
				confidence_score: 0.85,
			};

			fetch.mockResolvedValueOnce({
				ok: true,
				status: 200,
				headers: { get: () => 'application/json' },
				json: async () => mockResponse,
			});

			const { result } = renderHook(() => useHealthAssessment());

			let response;
			await act(async () => {
				response = await result.current.submitAssessment(validFormData);
			});

			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe('');
			expect(result.current.result).toEqual(mockResponse);
			expect(response).toEqual(mockResponse);

			expect(fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/assess-health',
				expect.objectContaining({
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						name: 'John Doe',
						age: 30,
						gender: 'male',
						symptoms: 'Experiencing headaches and fatigue for the past week',
						medical_history: 'No significant medical history',
						current_medications: 'None',
					}),
				})
			);
		});

		test('sets loading state during submission', async () => {
			let resolvePromise;
			const mockPromise = new Promise((resolve) => {
				resolvePromise = resolve;
			});

			fetch.mockReturnValueOnce(mockPromise);

			const { result } = renderHook(() => useHealthAssessment());

			act(() => {
				result.current.submitAssessment(validFormData);
			});

			expect(result.current.loading).toBe(true);
			expect(result.current.error).toBe('');
			expect(result.current.result).toBe(null);

			// Resolve the promise
			await act(async () => {
				resolvePromise({
					ok: true,
					status: 200,
					headers: { get: () => 'application/json' },
					json: async () => ({ assessment: 'Test result' }),
				});
			});

			expect(result.current.loading).toBe(false);
		});

		test('handles validation errors', async () => {
			const invalidFormData = {
				name: '', // Invalid - too short
				age: '30',
				gender: 'male',
				symptoms: 'Valid symptoms here',
			};

			const { result } = renderHook(() => useHealthAssessment());

			await act(async () => {
				try {
					await result.current.submitAssessment(invalidFormData);
				} catch (error) {
					expect(error.message).toBe('Name must be at least 2 characters');
				}
			});

			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe('Name must be at least 2 characters');
			expect(result.current.result).toBe(null);
			expect(fetch).not.toHaveBeenCalled();
		});

		test('handles API errors', async () => {
			fetch.mockResolvedValueOnce({
				ok: false,
				status: 500,
				statusText: 'Internal Server Error',
				headers: { get: () => 'application/json' },
				json: async () => ({ error: 'Server error occurred' }),
			});

			const { result } = renderHook(() => useHealthAssessment());

			await act(async () => {
				try {
					await result.current.submitAssessment(validFormData);
				} catch (error) {
					expect(error.message).toBe('Server error occurred');
				}
			});

			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe('Server error occurred');
			expect(result.current.result).toBe(null);
		});

		test('handles network errors', async () => {
			fetch.mockRejectedValueOnce(new Error('Network error'));

			const { result } = renderHook(() => useHealthAssessment());

			await act(async () => {
				try {
					await result.current.submitAssessment(validFormData);
				} catch (error) {
					expect(error.message).toBe('Network error');
				}
			});

			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe('Network error');
			expect(result.current.result).toBe(null);
		});

		test('handles non-JSON responses', async () => {
			fetch.mockResolvedValueOnce({
				ok: true,
				status: 200,
				headers: { get: () => 'text/html' },
				json: async () => {
					throw new Error('Not JSON');
				},
			});

			const { result } = renderHook(() => useHealthAssessment());

			await act(async () => {
				try {
					await result.current.submitAssessment(validFormData);
				} catch (error) {
					expect(error.message).toBe('Server returned non-JSON response: 200');
				}
			});

			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe(
				'Server returned non-JSON response: 200'
			);
			expect(result.current.result).toBe(null);
		});

		test('handles API errors with different error message formats', async () => {
			// Test with 'message' field instead of 'error'
			fetch.mockResolvedValueOnce({
				ok: false,
				status: 400,
				statusText: 'Bad Request',
				headers: { get: () => 'application/json' },
				json: async () => ({ message: 'Invalid input data' }),
			});

			const { result } = renderHook(() => useHealthAssessment());

			await act(async () => {
				try {
					await result.current.submitAssessment(validFormData);
				} catch (error) {
					expect(error.message).toBe('Invalid input data');
				}
			});

			expect(result.current.error).toBe('Invalid input data');
		});

		test('handles API errors without error message', async () => {
			fetch.mockResolvedValueOnce({
				ok: false,
				status: 404,
				statusText: 'Not Found',
				headers: { get: () => 'application/json' },
				json: async () => ({}), // No error or message field
			});

			const { result } = renderHook(() => useHealthAssessment());

			await act(async () => {
				try {
					await result.current.submitAssessment(validFormData);
				} catch (error) {
					expect(error.message).toBe('HTTP 404: Not Found');
				}
			});

			expect(result.current.error).toBe('HTTP 404: Not Found');
		});
	});

	describe('reset function', () => {
		test('resets all state to initial values', async () => {
			const { result } = renderHook(() => useHealthAssessment());

			// First, set some state by triggering an error
			await act(async () => {
				try {
					await result.current.submitAssessment({
						name: '', // Invalid data
						age: '30',
						gender: 'male',
						symptoms: 'Valid symptoms',
					});
				} catch (error) {
					// Expected error
				}
			});

			// Verify error state is set
			expect(result.current.error).toBe('Name must be at least 2 characters');

			// Reset
			act(() => {
				result.current.reset();
			});

			// Verify reset
			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe('');
			expect(result.current.result).toBe(null);
		});

		test('resets state after successful submission', async () => {
			const mockResponse = { assessment: 'Test result' };

			fetch.mockResolvedValueOnce({
				ok: true,
				status: 200,
				headers: { get: () => 'application/json' },
				json: async () => mockResponse,
			});

			const { result } = renderHook(() => useHealthAssessment());

			// Submit successfully
			await act(async () => {
				await result.current.submitAssessment({
					name: 'John Doe',
					age: '30',
					gender: 'male',
					symptoms: 'Valid symptoms here',
				});
			});

			// Verify result is set
			expect(result.current.result).toEqual(mockResponse);

			// Reset
			act(() => {
				result.current.reset();
			});

			// Verify reset
			expect(result.current.loading).toBe(false);
			expect(result.current.error).toBe('');
			expect(result.current.result).toBe(null);
		});
	});

	describe('Multiple submissions', () => {
		test('handles multiple consecutive submissions', async () => {
			const { result } = renderHook(() => useHealthAssessment());

			const validData = {
				name: 'John Doe',
				age: '30',
				gender: 'male',
				symptoms: 'Valid symptoms here',
			};

			// First submission - success
			fetch.mockResolvedValueOnce({
				ok: true,
				status: 200,
				headers: { get: () => 'application/json' },
				json: async () => ({ assessment: 'First result' }),
			});

			await act(async () => {
				await result.current.submitAssessment(validData);
			});

			expect(result.current.result.assessment).toBe('First result');

			// Second submission - different result
			fetch.mockResolvedValueOnce({
				ok: true,
				status: 200,
				headers: { get: () => 'application/json' },
				json: async () => ({ assessment: 'Second result' }),
			});

			await act(async () => {
				await result.current.submitAssessment(validData);
			});

			expect(result.current.result.assessment).toBe('Second result');
			expect(fetch).toHaveBeenCalledTimes(2);
		});
	});
});
