// API configuration based on environment
const getApiUrl = () => {
  // In production (deployed), use relative paths to Vercel functions
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return '';  // Relative path for production
  }

  // In development, use localhost backend
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiUrl();

export const assessHealth = async (formData) => {
  const apiUrl = `${API_BASE_URL}/api/assess-health`;

  console.log('🔗 API Call:', apiUrl);  // Debug log

  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json();
};

export const checkApiHealth = async () => {
  const apiUrl = `${API_BASE_URL}/api/health`;
  const response = await fetch(apiUrl);
  return await response.json();
};
