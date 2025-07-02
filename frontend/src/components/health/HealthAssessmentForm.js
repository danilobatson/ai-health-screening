'use client';

import { useState } from 'react';
import { TextInput, Select, Textarea, Button, Card, Title, Text, Alert, LoadingOverlay } from '@mantine/core';
import { IconAlertCircle, IconCheck } from '@tabler/icons-react';

// API configuration - works for both dev and production
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '' // Use relative URLs in production (same domain)
  : 'http://localhost:8000'\; // Use localhost in development

export default function HealthAssessmentForm() {
  const [loading, setLoading] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    symptoms: '',
    age: '',
    gender: '',
    medical_history: '',
    current_medications: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setAssessmentResult(null);

    try {
      console.log('Making API call to:', `${API_BASE_URL}/api/assess-health`);
      
      const response = await fetch(`${API_BASE_URL}/api/assess-health`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Assessment result:', result);
      setAssessmentResult(result);
      
    } catch (error) {
      console.error('Assessment error:', error);
      setError(error.message || 'Assessment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '20px' }}>
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Title order={2} mb="md">🏥 AI Health Assessment</Title>
        
        <form onSubmit={handleSubmit}>
          <TextInput
            label="Full Name"
            placeholder="Enter your full name"
            value={formData.name || ''}
            onChange={(e) => handleInputChange('name', e.target.value)}
            required
            mb="md"
          />

          <TextInput
            label="Age"
            type="number"
            placeholder="Enter your age"
            value={formData.age}
            onChange={(e) => handleInputChange('age', e.target.value)}
            required
            mb="md"
          />

          <Select
            label="Gender"
            placeholder="Select gender"
            value={formData.gender}
            onChange={(value) => handleInputChange('gender', value)}
            data={[
              { value: 'male', label: 'Male' },
              { value: 'female', label: 'Female' },
              { value: 'other', label: 'Other' },
              { value: 'prefer-not-to-say', label: 'Prefer not to say' }
            ]}
            required
            mb="md"
          />

          <Textarea
            label="Current Symptoms"
            placeholder="Describe your current symptoms in detail..."
            value={formData.symptoms}
            onChange={(e) => handleInputChange('symptoms', e.target.value)}
            required
            minRows={3}
            mb="md"
          />

          <Textarea
            label="Medical History"
            placeholder="Any relevant medical history, conditions, or allergies..."
            value={formData.medical_history}
            onChange={(e) => handleInputChange('medical_history', e.target.value)}
            minRows={2}
            mb="md"
          />

          <Textarea
            label="Current Medications"
            placeholder="List any medications you're currently taking..."
            value={formData.current_medications}
            onChange={(e) => handleInputChange('current_medications', e.target.value)}
            minRows={2}
            mb="md"
          />

          <Button 
            type="submit" 
            fullWidth 
            loading={loading}
            disabled={!formData.symptoms || !formData.age || !formData.gender}
          >
            {loading ? 'Analyzing...' : '🔍 Get AI Health Assessment'}
          </Button>
        </form>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" mt="md">
            {error}
          </Alert>
        )}

        {assessmentResult && (
          <Card mt="xl" p="md" withBorder>
            <Title order={3} mb="md">📋 Assessment Results</Title>
            
            {/* AI Analysis */}
            <Card mb="md" p="sm" bg="blue.0">
              <Title order={4} size="h5" mb="xs">🤖 AI Analysis</Title>
              <Text size="sm" mb="xs">
                <strong>Reasoning:</strong> {assessmentResult.ai_analysis?.reasoning}
              </Text>
              <Text size="sm" mb="xs">
                <strong>Urgency Level:</strong> 
                <span style={{ 
                  color: assessmentResult.ai_analysis?.urgency === 'high' ? 'red' : 
                        assessmentResult.ai_analysis?.urgency === 'moderate' ? 'orange' : 'green',
                  fontWeight: 'bold',
                  marginLeft: '8px'
                }}>
                  {assessmentResult.ai_analysis?.urgency?.toUpperCase()}
                </span>
              </Text>
              <Text size="sm">
                <strong>Recommendations:</strong>
              </Text>
              <ul style={{ fontSize: '14px', marginTop: '4px' }}>
                {assessmentResult.ai_analysis?.recommendations?.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </Card>

            {/* ML Assessment */}
            <Card mb="md" p="sm" bg="green.0">
              <Title order={4} size="h5" mb="xs">📊 ML Risk Assessment</Title>
              <Text size="sm" mb="xs">
                <strong>Risk Score:</strong> {assessmentResult.ml_assessment?.risk_score}/1.0
              </Text>
              <Text size="sm" mb="xs">
                <strong>Confidence:</strong> {Math.round(assessmentResult.ml_assessment?.confidence * 100)}%
              </Text>
              <Text size="sm" mb="xs">
                <strong>Risk Level:</strong> 
                <span style={{ 
                  color: assessmentResult.ml_assessment?.risk_level === 'high' ? 'red' : 
                        assessmentResult.ml_assessment?.risk_level === 'moderate' ? 'orange' : 'green',
                  fontWeight: 'bold',
                  marginLeft: '8px'
                }}>
                  {assessmentResult.ml_assessment?.risk_level?.toUpperCase()}
                </span>
              </Text>
              <Text size="sm">
                <strong>Assessment Factors:</strong>
              </Text>
              <ul style={{ fontSize: '14px', marginTop: '4px' }}>
                {assessmentResult.ml_assessment?.factors?.map((factor, index) => (
                  <li key={index}>{factor}</li>
                ))}
              </ul>
            </Card>

            <Alert icon={<IconCheck size="1rem" />} color="blue" variant="light">
              <Text size="sm">
                <strong>Disclaimer:</strong> This AI assessment is for informational purposes only and does not replace professional medical advice. 
                Please consult with healthcare professionals for medical concerns.
              </Text>
            </Alert>

            {/* Backend Info */}
            {assessmentResult.backend && (
              <Text size="xs" color="dimmed" mt="sm">
                Powered by: {assessmentResult.backend}
              </Text>
            )}
          </Card>
        )}
      </Card>
    </div>
  );
}
