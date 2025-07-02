'use client';

import { useState } from 'react';
import { 
  Container, 
  Title, 
  Text, 
  Button, 
  Group, 
  Stack,
  Card,
  Badge,
  Grid
} from '@mantine/core';
import { 
  IconHeartHandshake, 
  IconStethoscope, 
  IconReportMedical,
  IconBrain 
} from '@tabler/icons-react';
import HealthAssessmentForm from '@/components/health/HealthAssessmentForm';
import AssessmentResults from '@/components/health/AssessmentResults';

export default function HomePage() {
  const [currentView, setCurrentView] = useState('home'); // 'home', 'assessment', 'results'
  const [assessmentResults, setAssessmentResults] = useState(null);

  const handleStartAssessment = () => {
    setCurrentView('assessment');
  };

  const handleAssessmentComplete = (results) => {
    setAssessmentResults(results);
    setCurrentView('results');
  };

  const handleNewAssessment = () => {
    setAssessmentResults(null);
    setCurrentView('assessment');
  };

  const handleBackHome = () => {
    setCurrentView('home');
    setAssessmentResults(null);
  };

  // Show results view
  if (currentView === 'results') {
    return (
      <AssessmentResults 
        results={assessmentResults}
        onNewAssessment={handleNewAssessment}
      />
    );
  }

  // Show assessment form
  if (currentView === 'assessment') {
    return (
      <HealthAssessmentForm 
        onAssessmentComplete={handleAssessmentComplete}
      />
    );
  }

  // Show home page
  return (
    <Container size="lg" py="xl">
      {/* Header Section */}
      <Stack align="center" gap="md" mb="xl">
        <Group>
          <IconHeartHandshake size={50} color="#2563eb" />
          <IconBrain size={45} color="#16a34a" />
        </Group>
        
        <Title order={1} size="h1" ta="center" c="blue">
          AI Health Assessment System
        </Title>
        
        <Text size="lg" ta="center" c="dimmed" maw={600}>
          Professional healthcare dashboard powered by Google Gemini AI and clinical reasoning
        </Text>
        
        <Group>
          <Badge color="green" size="lg">AI Powered</Badge>
          <Badge color="blue" size="lg">Clinical Grade</Badge>
          <Badge color="red" size="lg">Emergency Detection</Badge>
        </Group>
      </Stack>

      {/* Feature Cards */}
      <Grid mb="xl">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Stack align="center" gap="md">
              <IconStethoscope size={40} color="#2563eb" />
              <Title order={3}>Health Assessment</Title>
              <Text size="sm" ta="center" c="dimmed">
                AI-powered symptom analysis with 95% accuracy confidence scores
              </Text>
            </Stack>
          </Card>
        </Grid.Col>
        
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Stack align="center" gap="md">
              <IconReportMedical size={40} color="#16a34a" />
              <Title order={3}>Risk Analysis</Title>
              <Text size="sm" ta="center" c="dimmed">
                Emergency detection and clinical reasoning for immediate care decisions
              </Text>
            </Stack>
          </Card>
        </Grid.Col>
        
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Stack align="center" gap="md">
              <IconBrain size={40} color="#dc2626" />
              <Title order={3}>AI Insights</Title>
              <Text size="sm" ta="center" c="dimmed">
                Google Gemini integration providing professional medical recommendations
              </Text>
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Call to Action */}
      <Group justify="center">
        <Button 
          size="xl" 
          color="blue" 
          leftSection={<IconHeartHandshake size={20} />}
          onClick={handleStartAssessment}
        >
          Start Health Assessment
        </Button>
      </Group>
      
      {/* Portfolio Note */}
      <Text size="xs" ta="center" c="dimmed" mt="xl">
        Portfolio Demo: Python FastAPI + Google Gemini AI + Next.js + Mantine UI
      </Text>
    </Container>
  );
}
