'use client';

import { useState } from 'react';
import {
  TextInput, Select, Textarea, Button, Card, Title, Text, Alert,
  Loader, Badge, Group, Stack, Paper, NumberInput, Overlay
} from '@mantine/core';
import {
  IconAlertCircle, IconCheck, IconUser, IconStethoscope,
  IconBrain, IconShieldCheck
} from '@tabler/icons-react';

// Simple validation
const validateForm = (data) => {
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
    errors.symptoms = 'Please provide more detail about symptoms (minimum 10 characters)';
  }

  return { isValid: Object.keys(errors).length === 0, errors };
};

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000';

export default function HealthAssessmentForm() {
  const [loading, setLoading] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});

  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    symptoms: '',
    medical_history: '',
    current_medications: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate form
    const validation = validateForm(formData);
    if (!validation.isValid) {
      setValidationErrors(validation.errors);
      return;
    }

    setValidationErrors({});
    setLoading(true);
    setError('');
    setAssessmentResult(null);

    try {
      // Create clean data object with no duplicates
      const submitData = {
        name: String(formData.name).trim(),
        age: parseInt(formData.age),
        gender: String(formData.gender),
        symptoms: String(formData.symptoms).trim(),
        medical_history: String(formData.medical_history || '').trim(),
        current_medications: String(formData.current_medications || '').trim()
      };

      // Validate data before sending
      if (!submitData.name || submitData.name.length < 2) {
        throw new Error('Name must be at least 2 characters');
      }
      if (!submitData.age || submitData.age < 1 || submitData.age > 120) {
        throw new Error('Age must be between 1 and 120');
      }
      if (!submitData.gender) {
        throw new Error('Gender must be selected');
      }
      if (!submitData.symptoms || submitData.symptoms.length < 10) {
        throw new Error('Symptoms must be at least 10 characters');
      }

      console.log('Submitting clean data:', submitData);

      const response = await fetch(`${API_BASE_URL}/api/assess-health`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData)
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      // Handle different response types
      let result;
      const contentType = response.headers.get('content-type');

      if (contentType && contentType.includes('application/json')) {
        result = await response.json();
      } else {
        const textResponse = await response.text();
        console.log('Non-JSON response:', textResponse);
        throw new Error(`Server returned non-JSON response: ${response.status}`);
      }

      if (!response.ok) {
        const errorMessage = result.error || result.message || `HTTP ${response.status}: ${response.statusText}`;
        throw new Error(errorMessage);
      }

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

    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      age: '',
      gender: '',
      symptoms: '',
      medical_history: '',
      current_medications: ''
    });
    setAssessmentResult(null);
    setError('');
    setValidationErrors({});
  };

  const getRiskColor = (level) => {
    switch(level?.toLowerCase()) {
      case 'high': return 'red';
      case 'moderate': return 'orange';
      case 'low': return 'green';
      default: return 'blue';
    }
  };

  const getUrgencyIcon = (level) => {
    switch(level?.toLowerCase()) {
      case 'high': return '🚨';
      case 'moderate': return '⚠️';
      case 'low': return '✅';
      default: return '📋';
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '20px' }}>
      {/* Header */}
      <Paper p="xl" mb="xl" style={{ background: 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Group align="center" mb="md">
          <IconStethoscope size={40} />
          <div>
            <Title order={1} size="h2">AI Health Assessment</Title>
            <Text size="lg" style={{ opacity: 0.9 }}>Professional medical analysis powered by AI</Text>
          </div>
        </Group>
        <Group>
          <Badge color="cyan" variant="light" size="lg">AI POWERED</Badge>
          <Badge color="green" variant="light" size="lg">VALIDATED</Badge>
          <Badge color="purple" variant="light" size="lg">SECURE</Badge>
        </Group>
      </Paper>

      <Card shadow="lg" padding="xl" radius="lg" withBorder style={{ position: 'relative' }}>
        {/* Custom Loading Overlay */}
        {loading && (
          <Overlay color="#000" backgroundOpacity={0.1} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Loader size="lg" />
              <Text mt="md" size="lg" weight={500}>Analyzing with AI...</Text>
            </div>
          </Overlay>
        )}

        {!assessmentResult ? (
          <form onSubmit={handleSubmit}>
            <Stack spacing="md">
              <Title order={3} mb="md">Patient Information</Title>

              <TextInput
                icon={<IconUser size={16} />}
                label="Full Name"
                placeholder="Enter your full name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                error={validationErrors.name}
                required
                size="md"
              />

              <Group grow>
                <NumberInput
                  label="Age"
                  placeholder="Enter age"
                  value={formData.age}
                  onChange={(value) => handleInputChange('age', value || '')}
                  error={validationErrors.age}
                  required
                  min={1}
                  max={120}
                  size="md"
                />

                <Select
                  label="Gender"
                  placeholder="Select gender"
                  value={formData.gender}
                  onChange={(value) => handleInputChange('gender', value)}
                  error={validationErrors.gender}
                  data={[
                    { value: 'male', label: 'Male' },
                    { value: 'female', label: 'Female' },
                    { value: 'other', label: 'Other' },
                    { value: 'prefer-not-to-say', label: 'Prefer not to say' }
                  ]}
                  required
                  size="md"
                />
              </Group>

              <Textarea
                icon={<IconBrain size={16} />}
                label="Current Symptoms"
                description="Describe your symptoms in detail (minimum 10 characters)"
                placeholder="Example: Experiencing headaches for the past 3 days, mild nausea, difficulty concentrating..."
                value={formData.symptoms}
                onChange={(e) => handleInputChange('symptoms', e.target.value)}
                error={validationErrors.symptoms}
                required
                minRows={4}
                size="md"
              />

              <Textarea
                icon={<IconStethoscope size={16} />}
                label="Medical History"
                description="Any relevant medical conditions, allergies, or previous diagnoses"
                placeholder="Example: Diabetes Type 2, allergic to penicillin, previous surgery in 2020..."
                value={formData.medical_history}
                onChange={(e) => handleInputChange('medical_history', e.target.value)}
                minRows={3}
                size="md"
              />

              <Textarea
                label="Current Medications"
                description="Include dosage and frequency if known"
                placeholder="Example: Metformin 500mg twice daily, Vitamin D 1000 IU daily..."
                value={formData.current_medications}
                onChange={(e) => handleInputChange('current_medications', e.target.value)}
                minRows={2}
                size="md"
              />

              <Button
                type="submit"
                loading={loading}
                size="lg"
                fullWidth
                disabled={loading}
              >
                {loading ? 'Analyzing with AI...' : '🧠 Get AI Health Assessment'}
              </Button>
            </Stack>
          </form>
        ) : (
          /* Assessment Results */
          <Stack spacing="xl">
            <Group position="apart">
              <Title order={2} color="blue">📋 Health Assessment Report</Title>
              <Button
                onClick={resetForm}
                variant="light"
              >
                🔄 New Assessment
              </Button>
            </Group>

            {/* Unified Assessment Display */}
            <Paper p="xl" withBorder radius="lg" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <Group mb="lg">
                <IconBrain size={32} />
                <div>
                  <Title order={2}>AI Medical Assessment</Title>
                  <Text size="sm" style={{ opacity: 0.9 }}>
                    Powered by {assessmentResult.backend} • Risk Score: {assessmentResult.ml_assessment?.risk_score}/1.0
                  </Text>
                </div>
                <Badge
                  color={getRiskColor(assessmentResult.ai_analysis?.urgency)}
                  size="xl"
                  variant="filled"
                >
                  {getUrgencyIcon(assessmentResult.ai_analysis?.urgency)} {assessmentResult.ai_analysis?.urgency?.toUpperCase()} PRIORITY
                </Badge>
              </Group>

              <Stack spacing="md">
                <div>
                  <Text weight={600} mb="xs">CLINICAL ASSESSMENT</Text>
                  <Text>{assessmentResult.ai_analysis?.reasoning}</Text>
                </div>

                <div>
                  <Text weight={600} mb="xs">MEDICAL RECOMMENDATIONS</Text>
                  <Stack spacing={4}>
                    {assessmentResult.ai_analysis?.recommendations?.map((rec, index) => (
                      <Group key={index} spacing="xs">
                        <IconCheck size={14} />
                        <Text size="sm">{rec}</Text>
                      </Group>
                    ))}
                  </Stack>
                </div>

                <Group grow>
                  <div style={{ textAlign: 'center' }}>
                    <Text size="xs" weight={600} style={{ opacity: 0.8 }}>CONFIDENCE</Text>
                    <Text size="xl" weight={700}>
                      {Math.round(assessmentResult.ml_assessment?.confidence * 100)}%
                    </Text>
                  </div>

                  <div style={{ textAlign: 'center' }}>
                    <Text size="xs" weight={600} style={{ opacity: 0.8 }}>RISK FACTORS</Text>
                    <Text size="xl" weight={700}>
                      {assessmentResult.ml_assessment?.factors?.length || 0}
                    </Text>
                  </div>
                </Group>
              </Stack>
            </Paper>

            {/* Medical Disclaimer */}
            <Alert icon={<IconShieldCheck size="1rem" />} color="blue" variant="light">
              <Text size="sm">
                <strong>Medical Disclaimer:</strong> This AI assessment is for informational purposes only and does not replace professional medical advice.
                Please consult with healthcare professionals for medical concerns.
              </Text>
            </Alert>
          </Stack>
        )}

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Assessment Error" color="red" mt="md">
            {error}
            <Button variant="subtle" size="xs" onClick={() => setError('')} mt="xs">
              Dismiss
            </Button>
          </Alert>
        )}
      </Card>
    </div>
  );
}
