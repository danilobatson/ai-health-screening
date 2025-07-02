// API configuration for development and production
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '' // Production: use relative URLs (same domain)
  : 'http://localhost:8000'\; // Development: use localhost

export const healthAPI = {
  async assessHealth(formData) {
    const response = await fetch(`${API_BASE_URL}/api/assess-health`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },

  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return await response.json();
  }
};

// For debugging
export const getApiUrl = () => API_BASE_URL;
