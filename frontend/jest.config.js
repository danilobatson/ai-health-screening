const nextJest = require('next/jest');

const createJestConfig = nextJest({
	// Provide the path to your Next.js app to load next.config.js and .env files
	dir: './',
});

// Add any custom config to be passed to Jest
const customJestConfig = {
	setupFilesAfterEnv: ['<rootDir>/src/__tests__/setup.js'],
	testEnvironment: 'jsdom',
	testMatch: [
		'<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
		'<rootDir>/src/**/*.(test|spec).{js,jsx,ts,tsx}',
	],
	testPathIgnorePatterns: ['<rootDir>/src/__tests__/setup.js'],
	collectCoverageFrom: [
		'src/**/*.{js,jsx,ts,tsx}',
		'!src/**/*.d.ts',
		'!src/app/layout.js',
		'!src/__tests__/**/*',
	],
	coverageThreshold: {
		global: {
			branches: 37,
			functions: 26,
			lines: 31,
			statements: 31,
		},
	},
	coverageDirectory: 'coverage',
	coverageReporters: ['text', 'lcov', 'html'],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig);
