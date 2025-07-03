import '@testing-library/jest-dom';

// React 19 compatibility
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

// Mock Next.js router
jest.mock('next/navigation', () => ({
	useRouter() {
		return {
			push: jest.fn(),
			replace: jest.fn(),
			prefetch: jest.fn(),
			back: jest.fn(),
			forward: jest.fn(),
			refresh: jest.fn(),
		};
	},
	useSearchParams() {
		return new URLSearchParams();
	},
	usePathname() {
		return '/';
	},
}));

// Mock fetch globally
global.fetch = jest.fn();

// Mock environment variables
process.env.NODE_ENV = 'test';
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';

// Disable React strict mode warnings in tests
const originalError = console.error;
beforeAll(() => {
	console.error = (...args) => {
		if (
			(typeof args[0] === 'string' &&
				args[0].includes('Warning: ReactDOM.render')) ||
			args[0].includes('Warning: validateDOMNesting')
		) {
			return;
		}
		originalError.call(console, ...args);
	};
});

afterAll(() => {
	console.error = originalError;
});

// Clean up after each test
afterEach(() => {
	jest.clearAllMocks();
});
