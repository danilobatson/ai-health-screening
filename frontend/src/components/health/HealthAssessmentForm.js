'use client';

import { useState } from 'react';
import {
  TextInput, Select, Textarea, Button, Card, Title, Text, Alert,
  LoadingOverlay, Badge, Group, Stack, Divider, Paper, Progress,
  ActionIcon, Tooltip, NumberInput
} from '@mantine/core';
import {
  IconAlertCircle, IconCheck, IconUser, IconCalendar, IconGenderBigender,
  IconStethoscope, IconPill, IconBrain, IconShieldCheck, IconRefresh
} from '@tabler/icons-react';
import { validateHealthAssessment } from '../../lib/validation';

// API configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000';

export default function HealthAssessmentForm() {
  const [loading, setLoading] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  const [step, setStep] = useState(1);

  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    symptoms: '',
    medical_history: '',
    current_medications: ''
  });

  // Form validation
  const validateStep = (currentStep) => {
    const validation = validateHealthAssessment(formData);

    if (!validation.success) {
      setValidationErrors(validation.errors);
      return false;
    }

    setValidationErrors({});

    switch(currentStep) {
      case 1:
        return formData.name && formData.age && formData.gender;
      case 2:
        return formData.symptoms && formData.symptoms.length >= 10;
      default:
        return true;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Final validation
    const validation = validateHealthAssessment(formData);
    if (!validation.success) {
      setValidationErrors(validation.errors);
      return;
    }

    setLoading(true);
    setError('');
    setAssessmentResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/assess-health`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validation.data)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
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
    setStep(1);
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
      <Paper p="xl" mb="xl" bg="gradient(45deg, #667eea 0%, #764ba2 100%)" style={{ color: 'white' }}>
        <Group align="center" mb="md">
          <IconStethoscope size={40} />
          <div>
            <Title order={1} size="h2">AI Health Assessment</Title>
            <Text size="lg" opacity={0.9}>Professional medical analysis powered by AI</Text>
          </div>
        </Group>
        <Group>
          <Badge color="cyan" variant="light" size="lg">AI POWERED</Badge>
          <Badge color="green" variant="light" size="lg">VALIDATED</Badge>
          <Badge color="purple" variant="light" size="lg">SECURE</Badge>
        </Group>
      </Paper>

      <Card shadow="lg" padding="xl" radius="lg" withBorder>
        <LoadingOverlay visible={loading} overlayBlur={2} />

        {!assessmentResult ? (
          <form onSubmit={handleSubmit}>
            {/* Progress Indicator */}
            <Progress
              value={step === 1 ? 50 : 100}
              mb="xl"
              size="lg"
              radius="xl"
              color="blue"
            />

            {/* Step 1: Personal Information */}
            {step === 1 && (
              <Stack spacing="md">
                <Group>
                  <IconUser size={20} />
                  <Title order={3}>Personal Information</Title>
                </Group>

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
                    icon={<IconCalendar size={16} />}
                    label="Age"
                    placeholder="Enter age"
                    value={formData.age}
                    onChange={(value) => handleInputChange('age', value)}
                    error={validationErrors.age}
                    required
                    min={1}
                    max={120}
                    size="md"
                  />

                  <Select
                    icon={<IconGenderBigender size={16} />}
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

                <Button
                  onClick={() => validateStep(1) && setStep(2)}
                  disabled={!validateStep(1)}
                  size="lg"
                  fullWidth
                >
                  Continue to Medical Information →
                </Button>
              </Stack>
            )}

            {/* Step 2: Symptoms & Medical */}
            {step === 2 && (
              <Stack spacing="md">
                <Group>
                  <IconStethoscope size={20} />
                  <Title order={3}>Medical Information</Title>
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
                  error={validationErrors.medical_history}
                  minRows={3}
                  size="md"
                />

                <Textarea
                  icon={<IconPill size={16} />}
                  label="Current Medications"
                  description="Include dosage and frequency if known"
                  placeholder="Example: Metformin 500mg twice daily, Vitamin D 1000 IU daily..."
                  value={formData.current_medications}
                  onChange={(e) => handleInputChange('current_medications', e.target.value)}
                  error={validationErrors.current_medications}
                  minRows={2}
                  size="md"
                />

                <Group>
                  <Button
                    variant="subtle"
                    onClick={() => setStep(1)}
                    size="md"
                  >
                    ← Back
                  </Button>

                  <Button
                    type="submit"
                    disabled={!validateStep(2)}
                    loading={loading}
                    size="lg"
                    style={{ flex: 1 }}
                    leftIcon={<IconBrain size={20} />}
                  >
                    {loading ? 'Analyzing with AI...' : 'Get AI Health Assessment'}
                  </Button>
                </Group>
              </Stack>
            )}
          </form>
        ) : (
          /* Unified Assessment Results */
          <Stack spacing="xl">
            <Group position="apart">
              <Title order={2} color="blue">📋 Health Assessment Report</Title>
              <Tooltip label="Start new assessment">
                <ActionIcon
                  onClick={resetForm}
                  size="lg"
                  color="blue"
                  variant="light"
                >
                  <IconRefresh size={20} />
                </ActionIcon>
              </Tooltip>
            </Group>

            {/* Unified Assessment Display */}
            <Paper p="xl" withBorder radius="lg" bg="gradient(135deg, #667eea 0%, #764ba2 100%)" style={{ color: 'white' }}>
              <Group mb="lg">
                <IconBrain size={32} />
                <div>
                  <Title order={2}>AI Medical Assessment</Title>
                  <Text size="sm" opacity={0.9}>
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
                    <Text size="xs" weight={600} opacity={0.8}>CONFIDENCE</Text>
                    <Text size="xl" weight={700}>
                      {Math.round(assessmentResult.ml_assessment?.confidence * 100)}%
                    </Text>
                  </div>

                  <div style={{ textAlign: 'center' }}>
                    <Text size="xs" weight={600} opacity={0.8}>RISK FACTORS</Text>
                    <Text size="xl" weight={700}>
                      {assessmentResult.ml_assessment?.factors?.length || 0}
                    </Text>
                  </div>
                </Group>
              </Stack>
            </Paper>

            {/* Risk Factors Details */}
            <Paper p="lg" withBorder radius="md" bg="gray.0">
              <Title order={4} mb="md">Assessment Factors Considered</Title>
              <Stack spacing={4}>
                {assessmentResult.ml_assessment?.factors?.map((factor, index) => (
                  <Group key={index} spacing="xs">
                    <Text size="sm" color="dimmed">•</Text>
                    <Text size="sm">{factor}</Text>
                  </Group>
                ))}
              </Stack>
            </Paper>

            {/* Medical Disclaimer */}
            <Alert icon={<IconShieldCheck size="1rem" />} color="blue" variant="light">
              <Text size="sm">
                <strong>Medical Disclaimer:</strong> This AI assessment is for informational purposes only and does not replace professional medical advice.
                Please consult with healthcare professionals for medical concerns, especially for urgent symptoms.
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
