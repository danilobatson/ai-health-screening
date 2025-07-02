'use client';

import { useState } from 'react';
import { 
  TextInput, Select, Textarea, Button, Card, Title, Text, Alert, 
  LoadingOverlay, Badge, Group, Stack, Divider, Paper, Progress,
  ActionIcon, Tooltip
} from '@mantine/core';
import { 
  IconAlertCircle, IconCheck, IconUser, IconCalendar, IconGenderBigender,
  IconStethoscope, IconPill, IconBrain, IconChartBar, IconShieldCheck,
  IconRefresh
} from '@tabler/icons-react';

// API configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000'\;

export default function HealthAssessmentForm() {
  const [loading, setLoading] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [error, setError] = useState('');
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
    switch(currentStep) {
      case 1:
        return formData.name && formData.age && formData.gender;
      case 2:
        return formData.symptoms && formData.symptoms.length > 10;
      default:
        return true;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setAssessmentResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/assess-health`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
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
            <Text size="lg" opacity={0.9}>Professional healthcare analysis powered by AI</Text>
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
              value={step === 1 ? 33 : step === 2 ? 66 : 100} 
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
                  required
                  size="md"
                />

                <Group grow>
                  <TextInput
                    icon={<IconCalendar size={16} />}
                    label="Age"
                    type="number"
                    placeholder="Enter age"
                    value={formData.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
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
                  onClick={() => setStep(2)}
                  disabled={!validateStep(1)}
                  size="lg"
                  fullWidth
                >
                  Continue to Symptoms →
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
                  required
                  minRows={4}
                  size="md"
                  error={formData.symptoms.length > 0 && formData.symptoms.length < 10 ? 'Please provide more detail (minimum 10 characters)' : null}
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
                  icon={<IconPill size={16} />}
                  label="Current Medications"
                  description="Include dosage and frequency if known"
                  placeholder="Example: Metformin 500mg twice daily, Vitamin D 1000 IU daily..."
                  value={formData.current_medications}
                  onChange={(e) => handleInputChange('current_medications', e.target.value)}
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
          /* Results Display */
          <Stack spacing="xl">
            <Group position="apart">
              <Title order={2} color="blue">📋 Assessment Results</Title>
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

            {/* AI Analysis Card */}
            <Paper p="lg" withBorder radius="md" bg="blue.0">
              <Group mb="md">
                <IconBrain size={24} color="#1976d2" />
                <Title order={3} color="blue">🤖 AI Analysis</Title>
              </Group>
              
              <Stack spacing="sm">
                <div>
                  <Text size="sm" weight={600} color="dimmed">REASONING</Text>
                  <Text>{assessmentResult.ai_analysis?.reasoning}</Text>
                </div>

                <Group>
                  <Text size="sm" weight={600} color="dimmed">URGENCY LEVEL</Text>
                  <Badge 
                    color={getRiskColor(assessmentResult.ai_analysis?.urgency)}
                    size="lg"
                    variant="filled"
                  >
                    {getUrgencyIcon(assessmentResult.ai_analysis?.urgency)} {assessmentResult.ai_analysis?.urgency?.toUpperCase()}
                  </Badge>
                </Group>

                <div>
                  <Text size="sm" weight={600} color="dimmed" mb="xs">RECOMMENDATIONS</Text>
                  <Stack spacing={4}>
                    {assessmentResult.ai_analysis?.recommendations?.map((rec, index) => (
                      <Group key={index} spacing="xs">
                        <IconCheck size={14} color="green" />
                        <Text size="sm">{rec}</Text>
                      </Group>
                    ))}
                  </Stack>
                </div>
              </Stack>
            </Paper>

            {/* ML Assessment Card */}
            <Paper p="lg" withBorder radius="md" bg="green.0">
              <Group mb="md">
                <IconChartBar size={24} color="#388e3c" />
                <Title order={3} color="green">📊 ML Risk Assessment</Title>
              </Group>
              
              <Group grow mb="md">
                <div style={{ textAlign: 'center' }}>
                  <Text size="xs" color="dimmed" weight={600}>RISK SCORE</Text>
                  <Text size="xl" weight={700} color={getRiskColor(assessmentResult.ml_assessment?.risk_level)}>
                    {assessmentResult.ml_assessment?.risk_score}/1.0
                  </Text>
                </div>
                
                <div style={{ textAlign: 'center' }}>
                  <Text size="xs" color="dimmed" weight={600}>CONFIDENCE</Text>
                  <Text size="xl" weight={700}>
                    {Math.round(assessmentResult.ml_assessment?.confidence * 100)}%
                  </Text>
                </div>
                
                <div style={{ textAlign: 'center' }}>
                  <Text size="xs" color="dimmed" weight={600}>RISK LEVEL</Text>
                  <Badge 
                    color={getRiskColor(assessmentResult.ml_assessment?.risk_level)}
                    size="lg"
                    variant="filled"
                  >
                    {assessmentResult.ml_assessment?.risk_level?.toUpperCase()}
                  </Badge>
                </div>
              </Group>

              <div>
                <Text size="sm" weight={600} color="dimmed" mb="xs">ASSESSMENT FACTORS</Text>
                <Stack spacing={4}>
                  {assessmentResult.ml_assessment?.factors?.map((factor, index) => (
                    <Group key={index} spacing="xs">
                      <IconChartBar size={14} color="#388e3c" />
                      <Text size="sm">{factor}</Text>
                    </Group>
                  ))}
                </Stack>
              </div>
            </Paper>

            {/* Disclaimer */}
            <Alert icon={<IconShieldCheck size="1rem" />} color="blue" variant="light">
              <Text size="sm">
                <strong>Medical Disclaimer:</strong> This AI assessment is for informational purposes only and does not replace professional medical advice. 
                Please consult with healthcare professionals for medical concerns, especially for urgent symptoms.
              </Text>
            </Alert>

            {/* Technical Info */}
            <Paper p="sm" bg="gray.0" radius="md">
              <Group position="apart">
                <Text size="xs" color="dimmed">
                  Powered by: {assessmentResult.backend || 'AI Healthcare System'}
                </Text>
                <Text size="xs" color="dimmed">
                  Assessment completed in real-time
                </Text>
              </Group>
            </Paper>
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
