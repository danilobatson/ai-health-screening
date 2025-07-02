export const assessHealth = async (formData) => {
  const response = await fetch('/api/assess-health', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Assessment failed');
  }
  
  return await response.json();
};

export const checkHealth = async () => {
  const response = await fetch('/api/health');
  return await response.json();
};
