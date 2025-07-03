import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import AssessmentResults from '../../components/health/AssessmentResults';

// Wrapper component for Mantine provider
const TestWrapper = ({ children }) => (
	<MantineProvider>{children}</MantineProvider>
);

const renderWithProvider = (component) => {
	return render(component, { wrapper: TestWrapper });
};

describe('AssessmentResults', () => {
	const mockResults = {
		clinical_reasoning:
			'Based on your symptoms, you may be experiencing a common cold. The combination of headache, fatigue, and congestion suggests a viral infection.',
		recommendations: [
			'Get plenty of rest and sleep',
			'Stay hydrated by drinking lots of fluids',
			'Consider over-the-counter pain relievers for headache',
			'Use saline nasal spray for congestion',
		],
		urgency: 'routine',
		confidence_score: 0.85,
		risk_level: 'low',
		risk_score: 25,
		red_flags: ['No fever reported', 'Recent cold weather exposure'],
	};

	const mockOnNewAssessment = jest.fn();

	beforeEach(() => {
		mockOnNewAssessment.mockClear();
	});

	describe('Component Rendering', () => {
		test('renders nothing when no results provided', () => {
			const { container } = renderWithProvider(
				<AssessmentResults
					results={null}
					onNewAssessment={mockOnNewAssessment}
				/>
			);

			// Component returns null when no results, so container should only have Mantine styles
			expect(
				container.querySelector('.mantine-Container-root')
			).not.toBeInTheDocument();
		});

		test('renders assessment results when provided', () => {
			renderWithProvider(
				<AssessmentResults
					results={mockResults}
					onNewAssessment={mockOnNewAssessment}
				/>
			);

			expect(screen.getByText('AI Assessment Results')).toBeInTheDocument();
			expect(
				screen.getByText(mockResults.clinical_reasoning)
			).toBeInTheDocument();
		});

		test('displays confidence score as percentage', () => {
			renderWithProvider(
				<AssessmentResults
					results={mockResults}
					onNewAssessment={mockOnNewAssessment}
				/>
			);

			expect(screen.getByText('85%')).toBeInTheDocument();
			expect(screen.getByText('AI Confidence')).toBeInTheDocument();
		});

		test('displays urgency level with correct styling', () => {
			renderWithProvider(
				<AssessmentResults
					results={mockResults}
					onNewAssessment={mockOnNewAssessment}
				/>
			);

			expect(screen.getByText(mockResults.urgency)).toBeInTheDocument();
			expect(screen.getByText('Urgency')).toBeInTheDocument();
		});

		test('displays risk level when provided', () => {
			renderWithProvider(
				<AssessmentResults
					results={mockResults}
					onNewAssessment={mockOnNewAssessment}
				/>
			);

			expect(screen.getByText(mockResults.risk_level)).toBeInTheDocument();
			expect(screen.getByText('Risk Level')).toBeInTheDocument();
		});
	});

	describe('User Interactions', () => {
		test('calls onNewAssessment when new assessment button is clicked', async () => {
			const user = userEvent.setup();

			renderWithProvider(
				<AssessmentResults
					results={mockResults}
					onNewAssessment={mockOnNewAssessment}
				/>
			);

			const newAssessmentButton = screen.getByRole('button', {
				name: /new assessment/i,
			});
			await user.click(newAssessmentButton);

			expect(mockOnNewAssessment).toHaveBeenCalledTimes(1);
		});
	});
});
