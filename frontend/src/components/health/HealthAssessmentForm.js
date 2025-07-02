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
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconStethoscope, IconAlertTriangle, IconCheck } from '@tabler/icons-react';

const SEVERITY_OPTIONS = [
  { value: 'mild', label: 'Mild' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'severe', label: 'Severe' },
];

const COMMON_SYMPTOMS = [
  'chest pain', 'shortness of breath', 'dizziness', 'headache',
  'nausea', 'fatigue', 'fever', 'cough', 'abdominal pain'
];

const MEDICAL_CONDITIONS = [
  'hypertension', 'diabetes', 'heart disease', 'asthma',
  'high cholesterol', 'obesity', 'anxiety', 'depression'
];

export default function HealthAssessmentForm({ onAssessmentComplete }) {
  const [loading, setLoading] = useState(false);
  const [currentSymptoms, setCurrentSymptoms] = useState([]);

  const form = useForm({
    initialValues: {
      name: '',
      age: '',
      symptoms: [],
      medicalHistory: [],
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      age: (value) => (!value || value < 1 || value > 120 ? 'Valid age is required' : null),
      symptoms: (value) => (value.length === 0 ? 'At least one symptom is required' : null),
    },
  });

  const addSymptom = (symptomName) => {
    if (!currentSymptoms.find(s => s.name === symptomName)) {
      const newSymptom = {
        name: symptomName,
        severity: 'mild',
        duration_days: 1
      };
      setCurrentSymptoms([...currentSymptoms, newSymptom]);
      form.setFieldValue('symptoms', [...currentSymptoms, newSymptom]);
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
      const response = await fetch('http://localhost:8000/api/assess-health', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: values.name,
          age: parseInt(values.age),
          symptoms: currentSymptoms,
          medical_history: values.medicalHistory,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      notifications.show({
        title: 'Assessment Complete',
        message: 'AI analysis completed successfully',
        color: 'green',
        icon: <IconCheck size={16} />,
      });

      onAssessmentComplete(result);
      
    } catch (error) {
      console.error('Assessment error:', error);
      notifications.show({
        title: 'Assessment Failed',
        message: 'Please ensure Python backend is running on port 8000',
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
          <Badge color="blue" size="lg">AI Powered</Badge>
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
              data={MEDICAL_CONDITIONS}
              searchable
              {...form.getInputProps('medicalHistory')}
            />

            {/* Symptoms Section */}
            <Text fw={500} size="lg" mt="md" mb="xs">Current Symptoms</Text>
            
            <Text size="sm" c="dimmed" mb="xs">
              Select common symptoms or add custom ones:
            </Text>

            <Chip.Group>
              <Group>
                {COMMON_SYMPTOMS.map((symptom) => (
                  <Chip
                    key={symptom}
                    variant="outline"
                    onClick={() => addSymptom(symptom)}
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

            {form.errors.symptoms && (
              <Alert color="red" variant="light">
                {form.errors.symptoms}
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
          </Stack>
        </form>
      </Card>
    </Container>
  );
}
