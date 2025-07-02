'use client';

import { useState } from 'react';
import {
  Container,
  Card,
  Title,
  Text,
  TextInput,
  NumberInput,
  Select,
  MultiSelect,
  Button,
  Group,
  Stack,
  Chip,
  Loader,
  Alert,
  Badge,
  Grid,
} from '@mantine/core';
import { useForm, zodResolver } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconStethoscope, IconAlertTriangle, IconCheck, IconShieldCheck } from '@tabler/icons-react';
import { healthAssessmentSchema, validateSymptomName, VALID_MEDICAL_CONDITIONS } from '@/lib/validation';

const SEVERITY_OPTIONS = [
  { value: 'mild', label: 'Mild' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'severe', label: 'Severe' },
];

const COMMON_SYMPTOMS = [
  'chest pain', 'shortness of breath', 'dizziness', 'headache',
  'nausea', 'fatigue', 'fever', 'cough', 'abdominal pain',
  'back pain', 'joint pain', 'muscle pain'
];

export default function HealthAssessmentForm({ onAssessmentComplete }) {
  const [loading, setLoading] = useState(false);
  const [currentSymptoms, setCurrentSymptoms] = useState([]);

  const form = useForm({
    validate: zodResolver(healthAssessmentSchema),
    initialValues: {
      name: '',
      age: '',
      symptoms: [],
      medicalHistory: [],
    },
  });

  const addSymptom = (symptomName) => {
    // Validate symptom name for security
    if (!validateSymptomName(symptomName)) {
      notifications.show({
        title: 'Invalid Symptom',
        message: 'Please select from the provided symptom list',
        color: 'red',
        icon: <IconAlertTriangle size={16} />,
      });
      return;
    }

    if (!currentSymptoms.find(s => s.name === symptomName)) {
      const newSymptom = {
        name: symptomName,
        severity: 'mild',
        duration_days: 1
      };
      const updatedSymptoms = [...currentSymptoms, newSymptom];
      setCurrentSymptoms(updatedSymptoms);
      form.setFieldValue('symptoms', updatedSymptoms);
    }
  };

  const updateSymptom = (index, field, value) => {
    const updated = currentSymptoms.map((symptom, i) => 
      i === index ? { ...symptom, [field]: value } : symptom
    );
    setCurrentSymptoms(updated);
    form.setFieldValue('symptoms', updated);
  };

  const removeSymptom = (index) => {
    const updated = currentSymptoms.filter((_, i) => i !== index);
    setCurrentSymptoms(updated);
    form.setFieldValue('symptoms', updated);
  };

  const submitAssessment = async (values) => {
    setLoading(true);
    
    try {
      // Additional validation
      if (values.age < 1 || values.age > 120) {
        throw new Error('Invalid age provided');
      }

      // Sanitize medical history
      const sanitizedHistory = values.medicalHistory.filter(condition => 
        VALID_MEDICAL_CONDITIONS.includes(condition)
      );

      const response = await fetch('http://localhost:8000/api/assess-health', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: values.name.trim(),
          age: parseInt(values.age),
          symptoms: currentSymptoms,
          medical_history: sanitizedHistory,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      notifications.show({
        title: 'Assessment Complete',
        message: `AI analysis completed with ${Math.round(result.confidence_score * 100)}% confidence`,
        color: 'green',
        icon: <IconCheck size={16} />,
      });

      onAssessmentComplete(result);
      
    } catch (error) {
      console.error('Assessment error:', error);
      notifications.show({
        title: 'Assessment Error',
        message: error.message || 'Please ensure all fields are valid and try again',
        color: 'red',
        icon: <IconAlertTriangle size={16} />,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size="md" py="xl">
      <Card shadow="lg" padding="xl" radius="md" withBorder>
        <Group justify="space-between" mb="lg">
          <Group>
            <IconStethoscope size={32} color="#2563eb" />
            <Title order={2}>Health Assessment</Title>
          </Group>
          <Group>
            <Badge color="blue" size="lg">AI Powered</Badge>
            <Badge color="green" size="sm" leftSection={<IconShieldCheck size={12} />}>
              Validated
            </Badge>
          </Group>
        </Group>

        <form onSubmit={form.onSubmit(submitAssessment)}>
          <Stack gap="md">
            {/* Patient Information */}
            <Text fw={500} size="lg" mb="xs">Patient Information</Text>
            
            <Grid>
              <Grid.Col span={{ base: 12, md: 8 }}>
                <TextInput
                  label="Full Name"
                  placeholder="Enter patient name"
                  required
                  {...form.getInputProps('name')}
                />
              </Grid.Col>
              <Grid.Col span={{ base: 12, md: 4 }}>
                <NumberInput
                  label="Age"
                  placeholder="Age"
                  min={1}
                  max={120}
                  required
                  {...form.getInputProps('age')}
                />
              </Grid.Col>
            </Grid>

            {/* Medical History */}
            <MultiSelect
              label="Medical History"
              placeholder="Select existing conditions"
              data={VALID_MEDICAL_CONDITIONS}
              searchable
              maxValues={10}
              {...form.getInputProps('medicalHistory')}
            />

            {/* Symptoms Section */}
            <Text fw={500} size="lg" mt="md" mb="xs">Current Symptoms</Text>
            
            <Text size="sm" c="dimmed" mb="xs">
              Select symptoms from the validated list:
            </Text>

            <Chip.Group>
              <Group>
                {COMMON_SYMPTOMS.map((symptom) => (
                  <Chip
                    key={symptom}
                    variant="outline"
                    onClick={() => addSymptom(symptom)}
                    disabled={currentSymptoms.some(s => s.name === symptom)}
                  >
                    {symptom}
                  </Chip>
                ))}
              </Group>
            </Chip.Group>

            {/* Current Symptoms List */}
            {currentSymptoms.map((symptom, index) => (
              <Card key={index} withBorder p="md" bg="gray.0">
                <Grid align="end">
                  <Grid.Col span={{ base: 12, md: 4 }}>
                    <Text fw={500}>{symptom.name}</Text>
                  </Grid.Col>
                  <Grid.Col span={{ base: 6, md: 3 }}>
                    <Select
                      label="Severity"
                      data={SEVERITY_OPTIONS}
                      value={symptom.severity}
                      onChange={(value) => updateSymptom(index, 'severity', value)}
                    />
                  </Grid.Col>
                  <Grid.Col span={{ base: 6, md: 3 }}>
                    <NumberInput
                      label="Duration (days)"
                      min={1}
                      max={365}
                      value={symptom.duration_days}
                      onChange={(value) => updateSymptom(index, 'duration_days', value)}
                    />
                  </Grid.Col>
                  <Grid.Col span={{ base: 12, md: 2 }}>
                    <Button
                      variant="light"
                      color="red"
                      size="sm"
                      onClick={() => removeSymptom(index)}
                    >
                      Remove
                    </Button>
                  </Grid.Col>
                </Grid>
              </Card>
            ))}

            {/* Form Validation Errors */}
            {form.errors.symptoms && (
              <Alert color="red" variant="light">
                {form.errors.symptoms}
              </Alert>
            )}

            {form.errors.name && (
              <Alert color="red" variant="light">
                {form.errors.name}
              </Alert>
            )}

            {form.errors.age && (
              <Alert color="red" variant="light">
                {form.errors.age}
              </Alert>
            )}

            {/* Submit Button */}
            <Group justify="center" mt="xl">
              <Button
                type="submit"
                size="lg"
                loading={loading}
                leftSection={<IconStethoscope size={20} />}
                disabled={currentSymptoms.length === 0}
              >
                {loading ? 'Analyzing with AI...' : 'Get AI Health Assessment'}
              </Button>
            </Group>

            {/* Security Notice */}
            <Text size="xs" ta="center" c="dimmed">
              <IconShieldCheck size={12} style={{ display: 'inline', marginRight: '4px' }} />
              All inputs are validated and sanitized for security
            </Text>
          </Stack>
        </form>
      </Card>
    </Container>
  );
}
