'use client';

import {
  Container,
  Card,
  Title,
  Text,
  Badge,
  Group,
  Stack,
  List,
  Alert,
  Progress,
  Grid,
  Button,
} from '@mantine/core';
import { 
  IconAlertTriangle, 
  IconCheck, 
  IconStethoscope,
  IconBrain,
  IconClipboardList 
} from '@tabler/icons-react';

function getRiskColor(riskLevel) {
  switch (riskLevel?.toLowerCase()) {
    case 'low': return 'green';
    case 'moderate': return 'yellow';
    case 'high': return 'red';
    default: return 'blue';
  }
}

function getUrgencyIcon(urgency) {
  switch (urgency?.toLowerCase()) {
    case 'emergency': return <IconAlertTriangle color="red" />;
    case 'urgent': return <IconAlertTriangle color="orange" />;
    default: return <IconCheck color="green" />;
  }
}

export default function AssessmentResults({ results, onNewAssessment }) {
  if (!results) return null;

  const confidencePercentage = Math.round((results.confidence_score || 0) * 100);

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        {/* Header */}
        <Card shadow="lg" padding="xl" radius="md" withBorder>
          <Group justify="space-between" mb="md">
            <Group>
              <IconBrain size={32} color="#16a34a" />
              <Title order={2}>AI Assessment Results</Title>
            </Group>
            <Badge color="green" size="lg">Analysis Complete</Badge>
          </Group>

          <Grid>
            <Grid.Col span={{ base: 12, md: 3 }}>
              <Stack align="center" gap="xs">
                <Text size="sm" c="dimmed">Risk Level</Text>
                <Badge 
                  size="xl" 
                  color={getRiskColor(results.risk_level)}
                  variant="filled"
                >
                  {results.risk_level}
                </Badge>
              </Stack>
            </Grid.Col>
            
            <Grid.Col span={{ base: 12, md: 3 }}>
              <Stack align="center" gap="xs">
                <Text size="sm" c="dimmed">Risk Score</Text>
                <Text size="2xl" fw={700} c={getRiskColor(results.risk_level)}>
                  {results.risk_score}/100
                </Text>
              </Stack>
            </Grid.Col>
            
            <Grid.Col span={{ base: 12, md: 3 }}>
              <Stack align="center" gap="xs">
                <Text size="sm" c="dimmed">Urgency</Text>
                <Group>
                  {getUrgencyIcon(results.urgency)}
                  <Text fw={500}>{results.urgency}</Text>
                </Group>
              </Stack>
            </Grid.Col>
            
            <Grid.Col span={{ base: 12, md: 3 }}>
              <Stack align="center" gap="xs">
                <Text size="sm" c="dimmed">AI Confidence</Text>
                <Text size="xl" fw={600}>{confidencePercentage}%</Text>
                <Progress 
                  value={confidencePercentage} 
                  color="blue" 
                  size="sm" 
                  style={{ width: '100%' }}
                />
              </Stack>
            </Grid.Col>
          </Grid>
        </Card>

        {/* Clinical Reasoning */}
        {results.clinical_reasoning && (
          <Card shadow="md" padding="lg" radius="md" withBorder>
            <Group mb="md">
              <IconStethoscope size={24} color="#2563eb" />
              <Title order={3}>Clinical Reasoning</Title>
            </Group>
            <Text>{results.clinical_reasoning}</Text>
          </Card>
        )}

        {/* Recommendations */}
        {results.recommendations && results.recommendations.length > 0 && (
          <Card shadow="md" padding="lg" radius="md" withBorder>
            <Group mb="md">
              <IconClipboardList size={24} color="#16a34a" />
              <Title order={3}>Recommendations</Title>
            </Group>
            <List spacing="sm">
              {results.recommendations.map((rec, index) => (
                <List.Item key={index}>
                  <Text>{rec}</Text>
                </List.Item>
              ))}
            </List>
          </Card>
        )}

        {/* Red Flags */}
        {results.red_flags && results.red_flags.length > 0 && (
          <Alert 
            color="red" 
            title="⚠️ Important Warnings" 
            icon={<IconAlertTriangle size={16} />}
          >
            <List spacing="xs">
              {results.red_flags.map((flag, index) => (
                <List.Item key={index}>
                  <Text size="sm">{flag}</Text>
                </List.Item>
              ))}
            </List>
          </Alert>
        )}

        {/* Actions */}
        <Group justify="center">
          <Button 
            variant="outline" 
            onClick={onNewAssessment}
            leftSection={<IconStethoscope size={16} />}
          >
            New Assessment
          </Button>
        </Group>

        {/* AI Attribution */}
        <Text size="xs" ta="center" c="dimmed">
          Analysis powered by Google Gemini AI • Python FastAPI Backend
        </Text>
      </Stack>
    </Container>
  );
}
